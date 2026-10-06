"""Standalone installed-package services proof with fake local APIs/processes only."""
import argparse
import asyncio
from contextlib import ExitStack
import json
import hashlib
import io
from pathlib import Path
import signal
import subprocess
import tempfile
import tarfile
import threading
from types import SimpleNamespace
from unittest.mock import patch
from unittest.mock import AsyncMock


def require(value, message):
    if not value:
        raise RuntimeError(message)


def runtime_fixture(root):
    """An inert, in-memory checksummed archive with the real source provenance."""
    sources = json.loads((root / 'sources.json').read_text())
    binary = b'inert services fixture runtime; never executed\n'
    release = {**sources['runtime'], 'watermark_library': sources['watermark_library'],
               'binary_sha256': hashlib.sha256(binary).hexdigest(), 'minimum_macos': '15.0',
               'version': 'services fixture', 'url': 'https://example.invalid/services-runtime.tar.gz'}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, data in [('mistralrs', binary), ('build.json', json.dumps(release).encode()),
                           ('LICENSE-mistral', b'fixture'), ('LICENSE-llm_watermarking', b'fixture'),
                           ('THIRD_PARTY_NOTICES.txt', b'fixture')]:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    archive = stream.getvalue()
    release.update(bytes=len(archive), sha256=hashlib.sha256(archive).hexdigest())
    return release, archive


async def check(root, evidence=None):
    root = root.resolve()
    from ai_lab.paths import load_backend
    from ai_lab.setup import prepare
    prepare(root)
    load_backend(root)
    import inference
    import decisions
    import ai_lab.model_servers as servers
    from ai_lab import downloads, runtime, decision_processes
    from ai_lab.service import atomic_json
    from ai_lab.service_manager import NativeServices, ServicesApp, select_service, add_parser
    from model_profiles import ModelProfiles, profile_values
    import httpx

    public_parser = argparse.ArgumentParser()
    public_parser.add_argument('--json', action='store_true')
    add_parser(public_parser.add_subparsers(dest='command'))
    require(public_parser.parse_args(['services']).action is None, 'Interactive services requires no flags')
    for argv in (['--json', 'services', '--action', 'list'], ['services', '--action', 'list', '--json']):
        parsed = public_parser.parse_args(argv)
        require(parsed.command == 'services' and parsed.json and parsed.action == 'list',
                'Installed add_parser did not preserve canonical/global argument contract')

    key = 'ab' * 32
    profiles = {
        'plain': profile_values('Plain exact', None, 'DeepSeekR1'),
        'marked': profile_values('[Marked] exact', '77', 'DeepSeekR1', {'scheme': 'synthid', 'key': key}),
        'qwen': profile_values('Qwen exact', None, 'Qwen3-8B'),
    }
    atomic_json(root / 'harness/models.json', ModelProfiles(root).document(profiles))
    release, archive = runtime_fixture(root)
    models = {}
    for name in ('deepseek', 'qwen', 'clm', 'laya'):
        data = ('tiny services fixture ' + name).encode()
        file = {'path': f'.models/services-fixture-{name}/weights', 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(), 'url': 'https://example.invalid/weights'}
        models[name] = {'label': name, 'dependencies': 'fixture', 'files': [file]}
        target = root / file['path']
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
    managed = root / '.runtime/mistral/mistralrs'
    managed.parent.mkdir(parents=True)
    managed.write_bytes(b'stale services fixture runtime')
    build_file = root / '.state/mistral-build.json'
    atomic_json(build_file, {**release, 'commit': 'old-pin', 'binary': str(managed), 'distribution': 'prebuilt'})
    (root / '.runtime/decisions').mkdir(parents=True)
    (root / '.runtime/decisions/mistralrs').write_text('inert fixture; never executed')
    (root / '.models/clm-v0.1-8b').mkdir(parents=True)
    (root / '.models/clm-v0.1-8b/config.json').write_text('{}')
    backend = NativeServices(root)
    live, commands, processes, requests, signals, launches, artifacts = {}, {}, {}, [], [], [], []
    from urllib.parse import urlsplit
    port_names = {11435: 'deepseek', 11439: 'qwen',
                  urlsplit(decisions.LOCAL_URL).port: 'contrastive',
                  urlsplit(decisions.UPSTREAM_URL).port: 'clm-upstream',
                  urlsplit(decisions.LAYA_URL).port: 'laya'}
    occupied = set()
    real_client = httpx.AsyncClient

    class Process:
        returncode = None

        def __init__(self, pid):
            self.pid = pid

        async def wait(self):
            require(self.returncode is not None, 'Fake process must be stopped before wait')
            return self.returncode

        def terminate(self):
            kill(self.pid, signal.SIGTERM)

        def kill(self):
            kill(self.pid, signal.SIGKILL)

    def api_response(name):
        if name in {'deepseek', 'qwen'}:
            return {'data': [{'id': 'default'}]}
        return {'workspace': str(root), 'models': [{'name': {
            'contrastive': 'fixture-clm', 'clm-upstream': 'clm-latest', 'laya': 'laya'}[name]}]}

    def http(request):
        requests.append((request.url.port, request.method, request.url.path))
        require(request.method == 'GET' and request.url.path == '/v1/models', 'Only model discovery is authorized')
        name = port_names[request.url.port]
        if name not in occupied:
            raise httpx.ConnectError('fixture stopped', request=request)
        return httpx.Response(200, json=api_response(name))

    def client(*args, **kwargs):
        kwargs['transport'] = httpx.MockTransport(http)
        return real_client(*args, **kwargs)

    def ps(argv, **kwargs):
        require(argv[:2] == ['ps', '-p'], 'No real subprocess is allowed')
        pid = int(argv[2])
        if argv[3:] == ['-o', 'command=']:
            value = ' '.join(commands[pid]) if pid in live else ''
        else:
            value = live.get(pid, '')
        return subprocess.CompletedProcess(argv, 0, value, '')

    async def spawn(*argv, **kwargs):
        require(kwargs.get('start_new_session') is True, 'Each owned API needs its own process group')
        flag = '--port' if '--port' in argv else '-p'
        port = int(argv[argv.index(flag) + 1])
        name = port_names[port]
        require(name not in occupied, 'Duplicate shared API launch')
        pid = 800 + len(launches)
        process = Process(pid)
        commands[pid] = list(argv[3:]) if argv[0] == '/usr/bin/sandbox-exec' else list(argv)
        live[pid] = f'Tue Oct 6 01:00:00 2026 {pid} ' + ' '.join(commands[pid])
        processes[pid] = (name, process)
        occupied.add(name)
        launches.append(name)
        return process

    def kill(pid, sig):
        require(pid in live and pid in processes, 'Only a known fixture-owned process may be signalled')
        name, process = processes[pid]
        process.returncode = -sig
        live.pop(pid)
        occupied.remove(name)
        signals.append((name, int(sig)))

    def fake_native_api(path, body=None, timeout=10, *, model=None):
        name = inference.generation_backend(model).family
        require(path == '/v1/models' and body is None, 'Only native discovery is authorized')
        if name not in occupied:
            raise OSError('fixture stopped')
        return api_response(name)

    def artifact(request, **kwargs):
        require(request.full_url == release['url'], 'No real network or weight transfer is allowed')
        artifacts.append(request.full_url)
        return io.BytesIO(archive)

    def version(argv, **kwargs):
        require(argv[-1] == '--version' and Path(argv[0]).is_relative_to(root / '.runtime/mistral'),
                'No real binary/CLI process is allowed')
        return release['version']

    def installed(_):
        rows = {row['name']: row for row in downloads.status(root)}
        return {name: rows[name]['installed'] if name in {'deepseek', 'qwen'} else True
                for name in servers.LOCAL_MODELS}

    class Reporter:
        def __init__(self):
            self.states = []
            self.closed = False

        async def report(self, state, **kwargs):
            self.states.append(state)

        async def close(self):
            self.closed = True

    with ExitStack() as stack:
        stack.enter_context(patch('subprocess.run', side_effect=ps))
        stack.enter_context(patch('subprocess.Popen', side_effect=AssertionError('No real process')))
        stack.enter_context(patch('asyncio.create_subprocess_exec', side_effect=spawn))
        stack.enter_context(patch('httpx.AsyncClient', side_effect=client))
        stack.enter_context(patch('os.killpg', side_effect=kill))
        stack.enter_context(patch('inference.verify_installation', side_effect=lambda *_: json.loads(build_file.read_text())))
        stack.enter_context(patch('inference.api', side_effect=fake_native_api))
        stack.enter_context(patch('inference.port_available', side_effect=lambda model: inference.generation_backend(model).family not in occupied))
        stack.enter_context(patch('ai_lab.decision_processes.port_available', side_effect=lambda url: port_names[urlsplit(url).port] not in occupied))
        stack.enter_context(patch('ai_lab.decision_processes.listener_owner', return_value=None))
        stack.enter_context(patch('ai_lab.paths.known_model_roots', return_value=[]))
        stack.enter_context(patch('ai_lab.service_manager.endpoint_available', side_effect=lambda url: port_names[int(url.rsplit(':', 1)[1])] not in occupied))
        stack.enter_context(patch('ai_lab.model_servers.installed_models', side_effect=installed))
        stack.enter_context(patch('ai_lab.model_servers.download_status', side_effect=downloads.status))
        stack.enter_context(patch('ai_lab.downloads.catalog', return_value=models))
        stack.enter_context(patch('ai_lab.downloads.known_model_roots', return_value=[]))
        stack.enter_context(patch('ai_lab.model_servers.jev_key', return_value=None))
        stack.enter_context(patch('ai_lab.model_servers.decisions_ready', return_value=True))
        stack.enter_context(patch('ai_lab.model_servers._upstream_ready', return_value=True))
        stack.enter_context(patch('decisions.upstream_installed', return_value=True))
        stack.enter_context(patch('decisions.laya_installed', return_value=True))
        stack.enter_context(patch('ai_lab.laya.setup', return_value=None))
        # The real accepted repair/install path sees only tiny files and a memory
        # artifact. Model/weight installation and every real process remain forbidden.
        stack.enter_context(patch('ai_lab.downloads.install', side_effect=AssertionError('No weight download')))
        stack.enter_context(patch('ai_lab.downloads.download_file', side_effect=AssertionError('No weight transfer')))
        stack.enter_context(patch('ai_lab.runtime.descriptor', return_value=release))
        stack.enter_context(patch('ai_lab.runtime.install_decisions', return_value={'distribution': 'inert fixture'}))
        stack.enter_context(patch('ai_lab.runtime.supported', return_value=True))
        stack.enter_context(patch('urllib.request.urlopen', side_effect=artifact))
        stack.enter_context(patch('subprocess.check_output', side_effect=version))
        # Native GGUF verification has separate proof; our tiny catalog deliberately
        # differs from native file locations while retaining shared routing/settings.
        stack.enter_context(patch.object(servers, 'prime_generation_verification'))

        inventory = await backend.snapshot()
        require(len(inventory['profiles']) == 3 and len(inventory['services']) == 5, 'Saved inventory missing')
        require({row['name'] for row in inventory['services']} == {'deepseek', 'qwen', 'contrastive', 'laya', 'jev'},
                'Public Services included a legacy adapter or omitted an inference backend')
        require(select_service(inventory, name='[Marked] exact') == 'deepseek', 'Exact name mapping failed')
        require(key not in json.dumps(inventory) and 'seed_literal' not in json.dumps(inventory), 'Private settings leaked')
        require(all(Path(row['log_path']).is_relative_to(root / '.state') for row in inventory['services']
                    if row['ownership'] != 'hosted'), 'Local log paths missing or outside the workspace')
        require(not launches and not signals, 'Opening performed a lifecycle action')
        reporter = Reporter()
        app = ServicesApp(backend, name='[Marked] exact', reporter=reporter)
        async with app.run_test(size=(112, 36)) as pilot:
            async def settle():
                for _ in range(200):
                    await pilot.pause(.01)
                    if app.operation_task is None:
                        return
                raise RuntimeError('Mounted fixture did not settle')
            await settle()
            require(app.selected == 'deepseek', 'Mounted selection did not resolve exact name')
            from textual.widgets import DataTable
            require(app.query_one(DataTable).row_count == 5 and app.selected_key == 'service:deepseek',
                    'Saved profiles created duplicate lifecycle rows instead of selecting their shared server')
            for action in ('start', 'restart', 'interrupt'):
                await pilot.click('#' + action)
                await settle()
            require(launches == ['deepseek', 'deepseek'], 'Shared profile started duplicate or wrong API')
            require(signals == [('deepseek', int(signal.SIGTERM)), ('deepseek', int(signal.SIGINT))], 'Interrupt/Restart signal semantics changed')
            if evidence:
                evidence.mkdir(parents=True, exist_ok=True)
                (evidence / 'services-desktop.svg').write_text(app.export_screenshot())
            require(key not in app.export_screenshot(), 'Secret appeared on screen')
            await pilot.click('#exit')
        require(reporter.closed and 'working' in reporter.states and 'idle' in reporter.states, 'Herdr lifecycle did not settle')
        await backend.perform('start', 'qwen')
        await backend.perform('stop', 'qwen')
        await backend.perform('start', 'laya')
        require(decision_processes.owned_state(root, family='laya') == backend.created['laya'].state,
                'Laya durable process identity missing')
        await backend._launch('clm-upstream')  # Internal timeout isolation retains the legacy adapter.
        kept = {name: backend.created[name] for name in ('clm-upstream', 'laya')}
        before = len(signals)
        from ai_lab.service_manager import ServiceError
        with patch.object(decisions.DecisionRuntime, 'local_model', new=AsyncMock(return_value=None)), \
                patch('decisions.STARTUP_SECONDS', 0):
            try:
                await backend.perform('start', 'contrastive')
            except ServiceError:
                pass
            else:
                raise RuntimeError('Actual Contrastive timeout path was not exercised')
        require(signals[before:] == [('contrastive', int(signal.SIGTERM))], 'Timeout stopped an unrelated provider')
        require(all(backend.created[name] == identity and identity.pid in live for name, identity in kept.items()),
                'Contrastive timeout lost other providers or their ownership')
        await backend.perform('stop', 'laya')
        await backend._stop('clm-upstream', backend.created['clm-upstream'], signal.SIGTERM)
        await backend.perform('start', 'contrastive')
        require(decision_processes.owned_state(root) == backend.created['contrastive'].state, 'Native CLM durable identity missing')
        await backend.perform('restart', 'contrastive')
        await backend.perform('interrupt', 'contrastive')
        await backend.perform('start', 'contrastive')
        await backend.perform('stop', 'contrastive')
        require(not decision_processes.state_path(root).exists(), 'Native CLM identity receipt leaked after Stop')
        require(not live and not backend.created, 'Fixture-owned service leaked')
        require(len(artifacts) == 1 and downloads.dependencies_ready(root, 'deepseek')
                and downloads.dependencies_ready(root, 'qwen'), 'Accepted shared runtime repair did not verify/reuse')
        await backend.close()
        # Regress SERVICES-C51-R1 through installed production startup, mounted
        # Cancel/Exit, and a deterministic final identity worker gate.
        entered, release_capture, settled = threading.Event(), threading.Event(), threading.Event()
        original_capture = backend._capture
        worker_receipts, receipt_threads = [], []
        loop_thread = threading.get_ident()
        class Receipts(dict):
            def __setitem__(self, name, identity):
                receipt_threads.append(threading.get_ident())
                super().__setitem__(name, identity)
        backend.created = Receipts()
        def gated_capture(name):
            entered.set()
            try:
                require(release_capture.wait(5), 'Installed final capture gate did not release')
                identity = original_capture(name)
                worker_receipts.append(dict(backend.created))
                return identity
            finally:
                settled.set()
        capture_reporter = Reporter()
        capture_app = ServicesApp(backend, model='qwen', reporter=capture_reporter)
        with patch.object(backend, '_capture', side_effect=gated_capture):
            async with capture_app.run_test(size=(112, 36)) as pilot:
                for _ in range(200):
                    await pilot.pause(.01)
                    if capture_app.operation_task is None:
                        break
                exiting = None
                try:
                    await pilot.click('#start')
                    require(await asyncio.to_thread(entered.wait, 2), 'Final capture worker did not reach gate')
                    capture_pid = backend._process('qwen').pid
                    before_capture_signals = len(signals)
                    await pilot.click('#cancel')
                    exiting = asyncio.create_task(capture_app.action_leave())
                    await asyncio.sleep(.03)
                    require(not exiting.done() and backend.lock.locked() and not settled.is_set(),
                            'Exit or operation lock escaped final capture settlement')
                    require(not capture_reporter.closed and capture_pid in live and not backend.created,
                            'Lifecycle completed while the capture child was untracked/live')
                finally:
                    release_capture.set()
                    if exiting is not None:
                        await asyncio.wait_for(exiting, 2)
        await asyncio.sleep(.02)
        require(settled.is_set() and worker_receipts == [{}] and receipt_threads == [loop_thread],
                'Final capture did not settle or mutated receipts off the event loop')
        require(signals[before_capture_signals:] == [('qwen', int(signal.SIGTERM))]
                and not live and not backend.created and not backend.pending,
                'Cancelled final capture left an owned process or late receipt')
        require(capture_reporter.closed and 'idle' in capture_reporter.states,
                'Capture cancellation did not settle/release lifecycle reporting')
        return {'status': 'passed', 'package': str(Path(__import__('ai_lab').__file__).resolve()),
                'scope': ('installed' if (Path(__import__('ai_lab').__file__).parent / '_bundle').is_dir() else 'source')
                         + ' support/parser and mounted Textual; real lifecycle adapters with fake processes/API',
                'profiles': 3, 'shared_generation_apis': 2, 'fixture_launches': launches,
                'fixture_signals': signals, 'discovery_requests': len(requests),
                'native_processes': 0, 'downloads': 0, 'gpu': False, 'sdk_calls': 0,
                'runtime_repair': {'accepted_base': '6801487d8321227f6e8368190fee43f69282c344',
                                   'real_helper_and_installer': True, 'memory_artifacts': len(artifacts),
                                   'tiny_weights_unchanged': all((root / m['files'][0]['path']).stat().st_size == m['files'][0]['bytes']
                                                                for m in models.values())},
                'actual_decision_timeout_isolation': 'passed',
                'final_capture_cancel_exit': {'status': 'passed', 'worker_settled_before_exit': True,
                                             'event_loop_only_receipt_mutation': True,
                                             'owned_children_and_receipts_remaining': 0,
                                             'lifecycle_settled': True},
                'public_cli_registration': 'owned by CLI/root integration'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, help='Write mounted fixture SVG evidence')
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix='ai-lab-services-fixture-') as folder:
            value = asyncio.run(check(Path(folder), args.evidence))
        print(json.dumps(value, indent=2))
    except Exception as error:
        # Do not render native/HTTP exception payloads or private profiles.
        print(json.dumps({'status': 'failed', 'error': str(error) if type(error) is RuntimeError else type(error).__name__}))
        raise SystemExit(1)
