#!/usr/bin/env python3
"""Public picker/Completion proof through real current and legacy HTTP APIs.

Owned ephemeral HTTP/Unix sockets, real shared session routes, mounted Textual.
Historical native trace replay only: no new model, GPU, SDK or provider call.
"""
import argparse
import asyncio
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
import multiprocessing
import time
from unittest.mock import patch


def require(value, message):
    if not value:
        raise AssertionError(message)


def fixture_server(root, role, legacy, sock, started, stopped, views=False):
    """Spawned CPU fixture process; the only runtime is a recorded trace replay."""
    import uvicorn
    from ai_lab.paths import load_backend
    from ai_lab.service import create_app, SessionInput
    from ai_lab.coordination import proxy_private_sessions
    from pydantic import BaseModel, ConfigDict, Field, StrictStr
    root = Path(root)
    load_backend(root)
    step = json.loads(Path(__file__).with_name('completion-native-fixture.json').read_text())['step']
    recordings = (json.loads(Path(__file__).with_name('completion-views-fixture.json').read_text())['records']
                  if views else None)
    stop_gate = asyncio.Event()

    def record(event):
        with (root / 'proof-events.jsonl').open('a') as output:
            output.write(json.dumps(event) + '\n')

    class RecordedRuntime:
        async def complete_next(self, prompt, watermark, **options):
            if role != 'owner':
                raise AssertionError('website must not become a parallel session owner')
            name = None
            if views:
                scheme = (watermark or {}).get('scheme', 'none')
                name = scheme
                if scheme == 'synthid':
                    name = 'full' if watermark['generation_policy'] == 'tournament' else 'probability-updates'
                    if name == 'full':
                        name = next((variant for variant in ('collapsed', 'root-only', 'warmup')
                                     if prompt.startswith('[' + variant + ']')), name)
            record({'method': 'FAILED' if prompt == 'fixture backend failure' else 'REPLAY',
                    'path': prompt, 'options': options, **({'recording': name} if views else {})})
            if prompt == 'fixture backend failure':
                raise ValueError('Fixture backend unavailable. Start the selected local API explicitly.')
            if views and prompt.startswith('[slow]'):
                # Deterministic CPU proof: finish this captured decision only
                # after the real owner has accepted Stop. A missing Stop fails.
                await asyncio.wait_for(stop_gate.wait(), timeout=10)
            return {'prompt': prompt, 'step': copy.deepcopy(recordings[name]['step'] if views else step),
                    'finish_reason': 'length'}

    app = create_app(root, RecordedRuntime())
    if role == 'website':
        proxy_private_sessions(app, root)
    else:
        @app.middleware('http')
        async def capture(request, call_next):
            event = {'method': request.method, 'path': request.url.path}
            if request.method == 'POST':
                body = await request.body()
                event['body'] = json.loads(body) if body else None
                if views and request.url.path.endswith('/complete') and (event['body'] or {}).get('prompt', '').startswith('[slow]'):
                    stop_gate.clear()
            record(event)
            response = await call_next(request)
            if views and request.method == 'POST' and request.url.path.endswith('/stop') and response.status_code == 200:
                record({'method': 'GATE_RELEASE', 'path': request.url.path})
                stop_gate.set()
            return response

        if legacy:
            # The old validator wraps the actual shared session implementation.
            class LegacySessionInput(BaseModel):
                model_config = ConfigDict(extra='forbid')
                model: StrictStr
                scheme: StrictStr = 'model'
                watermark: dict | None = None
                name: StrictStr = Field(default='', max_length=80, pattern=r'^[^\x00-\x1f]*$')
                temperature: float = Field(default=1, ge=0, le=2)
            app.router.routes[:] = [route for route in app.router.routes
                if not (getattr(route, 'path', None) == '/api/lab/sessions'
                        and 'POST' in (getattr(route, 'methods', None) or set()))]

            @app.post('/api/lab/sessions', status_code=201)
            async def legacy_create(body: LegacySessionInput):
                return await app.state.ai_lab.create(SessionInput(**body.model_dump()))

    async def run():
        server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))
        task = asyncio.create_task(server.serve(sockets=[sock]))
        while not server.started and not task.done():
            await asyncio.sleep(.01)
        if server.started:
            started.set()
        while not stopped.is_set() and not task.done():
            await asyncio.sleep(.02)
        server.should_exit = True
        await task
    asyncio.run(run())


@contextmanager
def serve(root, role, *, legacy=False, uds=None, views=False):
    sock = socket.socket(socket.AF_UNIX if uds else socket.AF_INET)
    sock.bind(str(uds) if uds else ('127.0.0.1', 0))
    port = None if uds else sock.getsockname()[1]
    context = multiprocessing.get_context('spawn')
    started, stopped = context.Event(), context.Event()
    process = context.Process(target=fixture_server, args=(str(root), role, legacy, sock, started, stopped, views))
    process.start()
    try:
        require(started.wait(10), 'owned API fixture did not start')
        yield {'pid': process.pid, 'role': role, 'transport': str(uds) if uds else f'http://127.0.0.1:{port}'}
    finally:
        stopped.set()
        process.join(5)
        if process.is_alive():
            process.terminate()
            process.join(5)
        sock.close()
        if uds:
            uds.unlink(missing_ok=True)
        require(not process.is_alive() and process.exitcode == 0, 'owned API fixture did not stop cleanly')


def check(*, installed=False, evidence=None):
    import ai_lab
    from ai_lab.paths import RESOURCES, BUNDLE, load_backend
    from ai_lab.cli import main
    from ai_lab.cli_screens import ProfilePicker
    from ai_lab.client import Client, socket_path
    from ai_lab.tui import LabApp
    from ai_lab.views import candidate_rows, probability
    from textual.widgets import DataTable, Select, Static, TextArea, Tree
    import httpx
    if installed:
        require(BUNDLE.is_dir(), 'proof must import the normally installed bundled application')
        require(Path(ai_lab.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
                'installed package is outside this Python environment')
    load_backend(RESOURCES)
    from model_profiles import ModelProfiles, profile_values
    from watermarks import validate_watermark
    fixture_file = Path(__file__).with_name('completion-native-fixture.json')
    fixture = json.loads(fixture_file.read_text())
    step = fixture['step']
    require(fixture['provenance']['new_native_generation'] is False, 'fixture replay provenance')
    private_key = '42' * 32

    reports = []
    with tempfile.TemporaryDirectory(prefix='ai-lab-completion-proof-') as folder:
        for legacy in (False, True):
            root = Path(folder).resolve() / ('legacy' if legacy else 'current')
            root.mkdir()
            (root / 'sources.json').write_bytes((RESOURCES / 'sources.json').read_bytes())
            registry = ModelProfiles(root)
            registry.path.parent.mkdir()
            registry.path.write_text(json.dumps(registry.document({
                'profile-jet': profile_values('jet', 42, 'deepseek', validate_watermark({
                    'scheme': 'synthid', 'key': private_key, 'depth': 4,
                    'generation_policy': 'tournament'})),
                'profile-qwen': profile_values('Qwen saved', 17, 'qwen')})))
            profiles_before = registry.path.read_bytes()
            def events():
                path = root / 'proof-events.jsonl'
                return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

            def replays():
                return [event for event in events() if event['method'] == 'REPLAY']

            socket_file = socket_path(root)
            with serve(root, 'owner', legacy=legacy, uds=socket_file) as owner, serve(root, 'website') as website:
                endpoint = website['transport']
                with httpx.Client(base_url=endpoint, trust_env=False) as http:
                    schema = http.get('/api/lab/schema').json()
                    # A modern website genuinely forwards the private owner's legacy schema.
                    ref = schema['paths']['/api/lab/sessions']['post']['requestBody']['content']['application/json']['schema']['$ref'].split('/')[-1]
                    require(('model_name' in schema['components']['schemas'][ref]['properties']) is not legacy,
                            'schema must come from the actual existing session owner')
                    if legacy:
                        before = http.post('/api/lab/sessions', json={'model_name': 'jet', 'scheme': 'model',
                            'watermark': None, 'name': '', 'temperature': 1})
                        require(before.status_code == 422, 'old validator must reproduce the original failure')
                        require([(error['type'], error['loc']) for error in before.json()['detail']] == [
                            ('missing', ['body', 'model']), ('extra_forbidden', ['body', 'model_name'])],
                            'exact original validation failure')
                        (root / 'proof-events.jsonl').write_text('')
                captured = {}

                def workspace_run(app, **kwargs):
                    async def mounted():
                        async with app.run_test(size=(150, 48)) as pilot:
                            await pilot.pause()
                            await app.workers.wait_for_complete()
                            if captured.get('preselect'):
                                require(app.record['model'] == 'profile-jet', 'CLI selector preselects the model in Completion')
                                require(app.query_one('#completion-model', Select).value == 'profile-jet', 'picker shows CLI selection')
                                require(app.query_one('#chat-panel').display, 'preselected CLI opens Completion')
                            elif app.view == 'all' and 'session' not in captured:
                                require(app.session_id is None and app.record is None, 'bare CLI mounts Completion before selection')
                                require(app.query_one('#chat-panel').display, 'wide launch displays Completion')
                                require(not [e for e in events() if e['method'] == 'POST'], 'bare open does not write')
                                await pilot.resize_terminal(80, 24)
                                await pilot.pause()
                                require(app.query_one('#chat-panel').display, 'compact launch displays Completion')
                                if evidence:
                                    app.save_screenshot(('legacy' if legacy else 'current') + '-bare-compact.svg', path=str(evidence))
                                app.query_one('#completion-model', Select).focus()
                                await pilot.press('enter', 'down', 'enter')
                                await pilot.pause()
                                await app.workers.wait_for_complete()
                                require(app.record['profile']['name'] == 'jet', 'in-screen picker routes saved name')
                                require(app.record['model'] == 'profile-jet', 'in-screen picker routes saved ID')
                                captured['session'] = app.session_id
                                require(not replays(), 'opening and selection must not generate')
                                await pilot.resize_terminal(150, 48)
                                await pilot.pause()
                                app.query_one('#prompt', TextArea).load_text('the quick brown')
                                await pilot.pause()
                                require(await pilot.click('#run'), 'actual Run button must be reachable')
                                await app.workers.wait_for_complete()
                                deadline = time.monotonic() + 4
                                while app.record['status'] == 'running' and time.monotonic() < deadline:
                                    await app.refresh_session()
                                    await pilot.pause(.02)
                                require(app.record['status'] == 'complete', 'recorded trace replay must complete')
                                require(app.record['results'][0]['step'] == step, 'every captured numeric value/order preserved')
                                require(all(app.query_one('#' + name).display for name in (
                                    'chat-panel', 'prob-panel', 'tokens-panel', 'tournament-panel')), 'wide all-view panels visible')
                                require(app.selected_match_id == step['generation_tournament']['winner']['match_id'],
                                        'actual captured final match selected')
                                await pilot.press('ctrl+t', 'down', 'enter')
                                require(app.selected_match_id != step['generation_tournament']['winner']['match_id'],
                                        'keyboard inspects another real match')
                                tree = app.query_one('#bracket', Tree)
                                node = app.match_nodes[0]
                                require(await pilot.click('#bracket', offset=(30, node.line - int(tree.scroll_offset.y))),
                                        'mouse can inspect a recorded match')
                                await pilot.pause()
                                require(app.selected_match_id == 0, 'mouse chooses genuine match0')
                                rows = candidate_rows(app.record)
                                table = app.query_one('#tokens', DataTable)
                                require(table.row_count == len(rows), 'all captured token candidates rendered')
                                for row in rows:
                                    actual = table.get_row(str(row['token_id']))
                                    require(actual[4] == probability(row.get('reporting_probability')), 'model probabilities unchanged')
                                    require(actual[6] == '—', 'uncaptured tournament after-probability remains unavailable')
                                require('unavailable' in str(app.query_one('#prob-note', Static).content), 'probability limitation visible')
                                saved = copy.deepcopy(app.record)
                                await pilot.click('#refresh-models')
                                await pilot.pause()
                                await app.workers.wait_for_complete()
                                require(app.record == saved, 'model list reload preserves recorded session')
                                app.query_one('#completion-model', Select).value = 'profile-qwen'
                                await pilot.pause()
                                await app.workers.wait_for_complete()
                                require(app.record['profile']['underlying_model'] == 'Qwen3-8B', 'switch selects Qwen backend')
                                require(app.record['profile']['seed'] == 17, 'switch inherits Qwen seed')
                                require(app.session_id != captured['session'], 'switch has a separate session')
                                app.query_one('#prompt', TextArea).load_text('fixture backend failure')
                                await pilot.click('#run')
                                await app.workers.wait_for_complete()
                                deadline = time.monotonic() + 4
                                while app.record['status'] == 'running' and time.monotonic() < deadline:
                                    await app.refresh_session()
                                    await pilot.pause(.02)
                                require(app.record['status'] == 'error', 'actual API exposes fixture backend failure')
                                require('Fixture backend unavailable' in str(app.query_one('#status', Static).content),
                                        'backend failure is visible in persistent screen')
                                require(app.is_running, 'backend failure does not exit Completion')
                                app.query_one('#completion-model', Select).value = 'profile-jet'
                                await pilot.pause()
                                await app.workers.wait_for_complete()
                                require(app.session_id == captured['session'] and app.record == saved,
                                        'switch back reuses the recorded session and preserves trace')
                                if evidence:
                                    app.save_screenshot(('legacy' if legacy else 'current') + '-completion-wide.svg', path=str(evidence))
                                await pilot.resize_terminal(80, 24)
                                await pilot.pause()
                                for view, panel in [('probabilities', 'prob-panel'), ('tokens', 'tokens-panel'), ('tournament', 'tournament-panel'), ('chat', 'chat-panel')]:
                                    clicked = await pilot.click('#tab-' + view)
                                    button = app.query_one('#tab-' + view)
                                    require(clicked, 'compact tab must be reachable: ' + view + '; geometry=' + str({
                                        'app': app.size, 'screen': app.screen.size, 'button': button.region,
                                        'tabs': app.query_one('#view-tabs').region, 'classes': sorted(app.screen.classes)}))
                                    await pilot.pause()
                                    require(app.query_one('#' + panel).display, 'compact panel visible: ' + view)
                                answer = app.query_one('#answer')
                                require(answer.region.height > 0 and app.query_one('#answer-scroll').content_region.contains_region(answer.region),
                                        'compact Completion answer is actually visible')
                                if evidence:
                                    app.save_screenshot(('legacy' if legacy else 'current') + '-completion-compact.svg', path=str(evidence))
                                await pilot.resize_terminal(50, 18)
                                await pilot.pause()
                                await pilot.press('ctrl+t')
                                require(app.query_one('#tournament-panel').display, 'tiny terminal bracket remains accessible')
                                require(private_key not in app.export_screenshot(), 'workspace must not expose watermark keys')
                            else:
                                require(app.session_id == captured['session'], 'standalone view retains same session')
                                require(app.record['results'][0]['step'] == step, 'standalone view retains same trace')
                            require(app.is_running, 'workspace stays alive until explicit Quit')
                            await pilot.press('ctrl+q')
                    asyncio.run(mounted())

                with patch.dict('os.environ', {'AI_LAB_SERVER': endpoint}), \
                        patch('ai_lab.cli.sys.stdin.isatty', return_value=True), \
                        patch.object(ProfilePicker, 'run', side_effect=AssertionError('no separate selector app')), \
                        patch.object(LabApp, 'run', new=workspace_run), \
                        patch('ai_lab.downloads.offer', side_effect=AssertionError('no download offer')), \
                        patch('ai_lab.client.subprocess.Popen', side_effect=AssertionError('no parallel private owner')):
                    require(main(['--root', str(root), 'completion']) == 0, 'public bare CLI→Completion→in-screen picker→API')
                    session = captured['session']
                    client = Client(root, server=endpoint).connect()
                    before = client.request('GET', '/api/lab/sessions/' + session)
                    for view in ('tournament', 'probabilities', 'tokens'):
                        require(main(['--root', str(root), 'completion', '--view', view, '--session', session]) == 0,
                                'public standalone view: ' + view)
                    after = client.request('GET', '/api/lab/sessions/' + session)
                    require(before == after, 'resuming/closing read-only panes preserves the existing record')
                    for flag, selected in [('--name', 'jet'), ('--model', 'profile-jet')]:
                        captured['preselect'] = True
                        require(main(['--root', str(root), 'completion', flag, selected]) == 0,
                                'public CLI preselection: ' + flag)
                creations = [event for event in events() if event['method'] == 'POST' and event['path'] == '/api/lab/sessions']
                require(len(creations) == 4, 'one create per chosen/new launch model, no write on refresh/switch-back')
                selector = 'model' if legacy else 'model_name'
                require(creations[0]['body'].get(selector) == ('profile-jet' if legacy else 'jet'), 'negotiated correct selector')
                require(registry.path.read_bytes() == profiles_before, 'saved profiles/settings preserved')
                require(len(replays()) == 1, 'exactly one recorded replay, no generation on view attachment')
                failures = [event for event in events() if event['method'] == 'FAILED']
                require(len(failures) == 1 and failures[0]['options']['model']['underlying_model'] == 'Qwen3-8B'
                        and failures[0]['options']['seed'] == 17, 'actual runtime dispatch uses the switched backend and seed')
                reports.append({'backend': 'legacy' if legacy else 'current', 'schema_from_proxied_session_owner': True,
                                'session_create_posts': 4, 'selector': selector, 'recorded_replays': 1,
                                'visible_backend_failure_attempts': 1, 'model_switch_and_refresh_preserve_session': True,
                                'name_and_model_preselection': True,
                                'owned_apis': [owner, website],
                                'bare_completion_with_in_screen_picker': True, 'owned_api_processes': 2, 'wide_compact_tiny_panels': True,
                                'standalone_views_preserve_record': True, 'profiles_preserved': True})
    return {'status': 'COMPLETION_HTTP_MOUNTED_FIXTURE_PASS', 'package': str(Path(ai_lab.__file__).resolve().parent),
            'installed': installed, 'fixture_sha256': hashlib.sha256(fixture_file.read_bytes()).hexdigest(),
            'source_files_sha256': {name: hashlib.sha256((Path(ai_lab.__file__).parent / name).read_bytes()).hexdigest()
                                    for name in ('cli.py', 'cli_screens.py', 'tui.py', 'session_compat.py')},
            'fixture_provenance': fixture['provenance'], 'phases': reports,
            'owned_process_cleanup': True, 'new_native_generation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed', action='store_true')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    if not args.installed:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    if args.evidence:
        args.evidence.mkdir(parents=True, exist_ok=True)
    result = check(installed=args.installed, evidence=args.evidence)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
