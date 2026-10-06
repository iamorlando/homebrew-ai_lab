#!/usr/bin/env python3
"""Check installed profile inheritance through own stdio MCP and chat.

Model and local decision HTTP replies are explicit owned fixtures. Real MCP
discovery/calls/continuation prove packaging and transport, not native efficacy.
No downloads, native APIs, GPU or hosted credentials are needed.
"""
import argparse
import asyncio
from contextlib import contextmanager
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading

# Only the verification scripts are source-loaded; application imports below
# must come from the supplied installed wheel, including its bundled backend.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_cross_model_profiles import FAMILIES, installed_service, private_json, require, require_stopped_api_guidance


def decoded(result):
    require(result.get('status') == 'ok' and not result.get('isError'), 'Own MCP tool failed')
    value = result.get('structuredContent')
    if value is None:
        value = json.loads(result['content'][0]['text'])
    return value


def key_free(value, records, extra=()):
    text = json.dumps(value)
    require(all(record.get('watermark', {}).get('key', 'not-a-private-key') not in text
                for record in records.values() if record.get('watermark')), 'Public result exposed a saved key')
    require(all(key not in text for key in extra), 'Public result exposed an override key')


def public_watermark(config):
    return None if config is None else {**{k: v for k, v in config.items() if k != 'key'}, 'has_key': True}


def tools_hash(tools):
    return hashlib.sha256(json.dumps(tools, sort_keys=True).encode()).hexdigest()


def discovered_tools(client):
    tools = client.model_tools()
    require(len(tools) == 15 and {t['function']['name'] for t in tools} ==
            {t['name'] for t in client.catalog()}, 'Discovery transport lost shipped tool identities')
    require(all(t['function']['strict'] is True for t in tools), 'Discovery transport lost strict validation')
    return tools_hash(tools)


def cases():
    values = [(name, {}) for name in ('deepseek marked', 'qwen marked', 'deepseek plain',
              'qwen seeded', 'qwen plain', 'deepseek seeded', 'deepseek marked')]
    for family in FAMILIES:
        values.extend([(family + ' marked', {'scheme': 'none'}), (family + ' marked', {
            'key': secrets.token_hex(32), 'settings': {'delta': 9}, 'seed': 99})])
        # Explicit non-default inputs make scheme changes distinguishable from
        # the saved KGW profile. Expected transport does not use its normalizer.
        schemes = {
            'synthid': {'ngram_len': 3, 'depth': 4, 'generation_policy': 'tournament'},
            'unigram': {'vocab_size': 151936, 'delta': 4, 'green_fraction': .75, 'ignore_repeated_tokens': True},
            'exponential': {'vocab_size': 151936, 'sequence_len': 17, 'start_position': 9},
            'inverse_transform': {'vocab_size': 151936, 'sequence_len': 19, 'start_position': 11},
            'mpac': {'vocab_size': 151936, 'context_width': 2, 'radix': 3, 'payload': [0, 2, 1],
                     'delta': 5, 'ignore_repeated_ngrams': True},
        }
        values.extend((family + ' marked', {'scheme': scheme, 'key': secrets.token_hex(32), 'settings': settings})
                      for scheme, settings in schemes.items())
    return values


def effective(record, override):
    watermark = deepcopy(record.get('watermark'))
    if override.get('scheme') == 'none':
        watermark = None
    elif override.get('scheme'):
        watermark = {'scheme': override['scheme'], 'key': override['key'], **override['settings']}
    elif override:
        watermark.update(key=override['key'], delta=9)
    return override.get('seed', record['seed']), watermark


@contextmanager
def fixtures():
    events, servers, threads = [], [], []
    health = {'valid': True}

    def handler(family):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, value):
                payload = json.dumps(value).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                value = {'models': [{'name': 'laya'}]} if family == 'laya' else {
                    'data': [{'id': 'ai-lab-fixture-' + family if health['valid'] else 'default'}]}
                self.respond(value)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                events.append({'family': family, 'path': self.path, 'body': body,
                               'authorization': self.headers.get('Authorization')})
                if family == 'laya':
                    self.respond({'model': 'laya', 'answers': {'ok': {'type': 'noul', 'noul': .8}},
                                  'usage': {'input_tokens': 3}})
                elif self.path == '/v1/completions':
                    self.respond({'choices': [{'text': family + ' fixture text', 'finish_reason': 'stop'}]})
                elif self.path == '/v1/chat/completions':
                    if body['messages'][-1]['role'] == 'tool':
                        message = {'role': 'assistant', 'content': family + ' fixture continuation: 0.8'}
                    else:
                        tool = next(t['function']['name'] for t in body['tools']
                                    if 'answer_decisions' in t['function']['name'])
                        message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                            'id': family + '-fixture-call', 'type': 'function', 'function': {
                                'name': tool, 'arguments': json.dumps({'model': 'laya', 'state': 'fixture state',
                                    'questions': {'ok': {'type': 'noul'}}})}}]}
                    self.respond({'choices': [{'message': message, 'finish_reason':
                                  'tool_calls' if message.get('tool_calls') else 'stop'}]})
                else:
                    self.send_error(404)
        return Handler

    try:
        for family in (*FAMILIES, 'laya'):
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler(family))
            servers.append((family, server))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            threads.append(thread)
            thread.start()
        yield {family: f'http://127.0.0.1:{server.server_port}' for family, server in servers}, events, health
    finally:
        for _, server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=5)
            require(not thread.is_alive(), 'Owned fixture did not close')


def create(root):
    records = {}
    with installed_service(root) as (url, package):
        environment = {**os.environ, 'AI_LAB_SERVER': url}
        for family, canonical in FAMILIES.items():
            for kind in ('plain', 'seeded', 'marked'):
                name = family + ' ' + kind
                seed = None if kind == 'plain' else 42 if family == 'deepseek' else 43
                command = [sys.executable, '-I', '-m', 'ai_lab', '--root', str(root), 'models', 'create',
                           '--name', name, '--underlying-model', family, '--json']
                if seed is not None:
                    command.extend(['--seed', str(seed)])
                config = None
                if kind == 'marked':
                    config = {'scheme': 'kgw', 'key': secrets.token_hex(32), 'delta': 3 if seed == 42 else 5,
                              'context_width': 2, 'green_fraction': .25 if seed == 42 else .75}
                    path = root / (family + '-watermark.json')
                    private_json(path, config)
                    command.extend(['--watermark-file', str(path)])
                result = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=20)
                require(result.returncode == 0, 'Installed CLI creation failed')
                record = json.loads(result.stdout)
                require(record['name'] == name and record['underlying_model'] == canonical
                        and record['seed'] == seed, 'Installed CLI changed supplied identity/seed')
                if config is None:
                    require(record.get('watermark') is None, 'Plain/seeded profile inherited watermark')
                else:
                    require(all(record['watermark'].get(k) == v for k, v in config.items()),
                            'Installed CLI lost supplied key/settings')
                records[name] = record
        require(len({p['key'] for p in records.values()}) == 6, 'Profile IDs collide')
        private_json(root / 'profiles.json', records)
        return {'phase': 'create', 'package': package, 'profile_count': 6}


async def probe(root, phase):
    import ai_lab
    from ai_lab.paths import BUNDLE, load_backend
    require(BUNDLE.is_dir() and Path(ai_lab.__file__).resolve().parent == BUNDLE.parent,
            'Application is not the installed wheel')
    load_backend(root)
    import inference
    require(Path(inference.__file__).is_relative_to(BUNDLE), 'Backend is not the installed bundle')
    from ai_lab.mcp_client import ai_lab_client, ToolTurn
    from ai_lab.native_chat import NativeChat

    records = json.loads((root / 'profiles.json').read_text())
    saved = (root / 'harness/models.json').read_bytes()
    expected = []
    allowed = ('generate_text', 'answer_decisions', 'get_model_config', 'list_models')
    async with ai_lab_client(root, allow_tools=allowed, env={
            'AI_LAB_GENERATION_FIXTURE_FILE': os.environ['AI_LAB_GENERATION_FIXTURE_FILE'],
            'AI_LAB_LAYA_URL': os.environ['AI_LAB_LAYA_URL']}) as client:
        tools = {t['tool']: t for t in client.catalog()}
        require(all(name in tools for name in allowed), 'Own MCP discovery is incomplete')
        require(len(tools) == 15, 'Own MCP discovery omitted shipped tools')
        discovery_hash = discovered_tools(client)

        async def call(tool, arguments):
            return decoded(await client.call_tool(tools[tool]['name'], arguments))

        catalog = await call('list_models', {})
        key_free(catalog, records)
        for record in records.values():
            actual = await call('get_model_config', {'model': record['key'], 'include_watermark_key': True})
            require(actual == record, 'Own MCP lost persisted profile identity/key/settings')
            key_free(await call('get_model_config', {'model': record['name']}), records)

        if phase == 'reject':
            for family in FAMILIES:
                failed = await client.call_tool(tools['generate_text']['name'], {
                    'model': family + ' marked', 'prompt': 'wrong readiness'})
                require(failed['isError'] is True,
                        'Own MCP accepted a generic readiness alias')
                require_stopped_api_guidance(json.dumps(failed), family)
                adapter = NativeChat(root, model_name=family + ' marked')
                try:
                    try:
                        await adapter.complete([{'role': 'user', 'content': 'wrong readiness'}], client.model_tools())
                    except ValueError as error:
                        require_stopped_api_guidance(str(error), family)
                    else:
                        require(False, 'Chat accepted a generic readiness alias')
                finally:
                    await adapter.aclose()
        else:
            # Interleave both saved marked/plain/seeded profiles, then explicitly
            # disable and override. Expected configs derive from known inputs.
            for name, override in cases():
                record = records[name]
                family = name.split()[0]
                seed, watermark = effective(record, override)
                result = await call('generate_text', {'model': name, 'prompt': 'fixture prefix',
                                    'max_tokens': 2, **override})
                require(result.get('fixture') is True and result['profile_key'] == record['key']
                        and result['underlying_model'] == FAMILIES[family] and result['seed'] == seed
                        and result['answer'] == family + ' fixture text', 'Own MCP changed selected profile')
                require(result['watermark'] == public_watermark(watermark), 'Own MCP reported wrong effective settings')
                key_free(result, records, (override['key'],) if 'key' in override else ())
                expected.append({'family': family, 'path': '/v1/completions', 'seed': seed, 'watermark': watermark})

                adapter = NativeChat(root, model_name=name, **override)
                try:
                    require((adapter.temperature, adapter.max_tokens, adapter.timeout) == (.8, 1024, 180),
                            'NativeChat changed shipped sampling/request defaults')
                    selection = adapter.selection
                    require(selection['profile_key'] == record['key'] and selection['underlying_model'] == FAMILIES[family]
                            and selection['seed'] == seed and selection['watermark'] == public_watermark(watermark),
                            'Chat selected wrong profile/backend/seed/settings')
                    turn = ToolTurn(client, [{'role': 'user', 'content': 'fixture prompt'}], adapter.complete)
                    result = await turn.run()
                    require(result['status'] == 'completed' and len(result['messages']) == 4,
                            'Own MCP chat did not complete one genuine protocol round trip')
                    messages = result['messages']
                    require(messages[1]['tool_calls'][0]['id'] == family + '-fixture-call'
                            and messages[1]['tool_calls'][0]['function']['name'] == tools['answer_decisions']['name']
                            and messages[2]['role'] == 'tool'
                            and messages[2]['tool_call_id'] == family + '-fixture-call'
                            and decoded(json.loads(messages[2]['content']))['answers']['ok']['noul'] == .8,
                            'Chat lost matching actual MCP result')
                    require(messages[-1]['content'] == family + ' fixture continuation: 0.8',
                            'Chat changed the fixture assistant continuation')
                    require(adapter.last_result.get('fixture') is True, 'Chat fixture provenance missing')
                    key_free({'selection': selection, 'result': result, 'last_result': adapter.last_result}, records,
                             (override['key'],) if 'key' in override else ())
                    expected.extend([{'family': family, 'path': '/v1/chat/completions', 'seed': seed,
                                      'watermark': watermark, 'messages': [messages[0]], 'tools_hash': discovery_hash},
                                     {'family': 'laya', 'path': '/v1/systemone'},
                                     {'family': family, 'path': '/v1/chat/completions', 'seed': seed,
                                      'watermark': watermark, 'messages': messages[:3], 'tools_hash': discovery_hash}])
                finally:
                    await adapter.aclose()
                require((root / 'harness/models.json').read_bytes() == saved, 'Overrides rewrote saved profiles')
            failed = await client.call_tool(tools['generate_text']['name'], {'model': 'unknown profile', 'prompt': 'invalid'})
            require(failed['isError'] is True, 'Own MCP silently substituted an unknown profile')
            for name in ('unknown profile', 'Deepseek marked'):
                try:
                    NativeChat(root, model_name=name)
                except ValueError:
                    pass
                else:
                    require(False, 'Chat silently substituted an unknown exact name')
            # Offline constraints are checked before protocol dispatch.
            invalid = await client.call_tool(tools['answer_decisions']['name'], {
                'state': 'must specify local provider', 'questions': {'ok': {'type': 'noul'}}})
            require(invalid.get('error', {}).get('code') == 'invalid_arguments', 'Own MCP accepted omitted provider')
    require((root / 'harness/models.json').read_bytes() == saved, 'Own MCP/chat changed persisted profiles')
    require(not (root / '.models').exists() and not list(root.glob('.state/*server*.json')),
            'Checker provisioned weights or started a native API')
    private_json(root / (phase + '-expected.json'), expected)
    return {'phase': phase, 'package': str(Path(ai_lab.__file__).resolve()), 'fixture': True,
            'own_mcp': 'real stdio', 'profile_count': 6, 'http_requests': len(expected),
            'discovered_tools_sha256': discovery_hash}


async def agent_probe(root, phase):
    import ai_lab
    from ai_lab.paths import BUNDLE, load_backend
    require(BUNDLE.is_dir(), 'Agent is not installed')
    load_backend(root)
    from ai_lab.agent_backend import AgentBackend, SYSTEM
    from ai_lab.agent_tui import AgentChatApp, ApprovalScreen
    from ai_lab.herdr import HerdrReporter
    from ai_lab.cli import parser, json_file
    require(Path(sys.modules[AgentBackend.__module__].__file__).resolve() == BUNDLE.parent / 'agent_backend.py',
            'AgentBackend came from outside the installed wheel')
    records = json.loads((root / 'profiles.json').read_text())
    saved = (root / 'harness/models.json').read_bytes()
    expected, checked = [], []
    required_check = phase == 'agent-required'
    values = [(family + ' marked', {}) for family in FAMILIES] if required_check else cases()
    for name, override in values:
        record = records[name]
        family = name.split()[0]
        seed, watermark = effective(record, override)
        # Exercise the real public parser's exact-name and unsaved-file forms.
        arguments = ['chat', '--name', name, '--self-mcp']
        if required_check:
            if family == 'qwen':
                arguments.extend(['--tool-choice', 'required'])
        else:
            arguments.extend(['--allow-tool', 'answer_decisions'])
        settings = None
        if override.get('scheme') == 'none':
            arguments.extend(['--scheme', 'none'])
        elif override:
            settings = {**override['settings'], 'key': override['key']}
            path = root / 'agent-override.json'
            private_json(path, settings)
            arguments.extend(['--scheme', override.get('scheme', 'kgw'), '--watermark-file', str(path)])
            if 'seed' in override:
                arguments.extend(['--seed', str(override['seed'])])
        args = parser().parse_args(arguments)
        require(args.model_name == name and args.self_mcp
                and args.allow_tool == ([] if required_check else ['answer_decisions']),
                'Public agent parser changed the exact selection/own-MCP controls')
        backend = AgentBackend(root, model_name=args.model_name, scheme=args.scheme, settings=json_file(args.watermark_file),
                               seed=args.seed, max_tokens=args.max_tokens, self_mcp=args.self_mcp,
                               timeout=args.timeout, allow_tools=args.allow_tool, tool_choice=args.tool_choice)
        require((backend.chat.temperature, backend.chat.max_tokens, backend.chat.timeout, backend.timeout) ==
                (.8, 1024, 180, 180), 'Agent parser/backend changed shipped sampling/request defaults')
        selection = backend.selection
        require(selection['profile_key'] == record['key'] and selection['underlying_model'] == FAMILIES[family]
                and selection['seed'] == seed and selection['watermark'] == public_watermark(watermark),
                'Installed AgentBackend lost profile/backend/seed/watermark')
        require(backend.profile_label == name and backend.backend_label == FAMILIES[family], 'Agent labels differ from selection')
        app = AgentChatApp(backend, profile_label=backend.profile_label, backend_label=backend.backend_label,
                           watermark_label=backend.watermark_label,
                           reporter=HerdrReporter('cross-model-fixture', environment={}), close_callback=backend.aclose)
        try:
            # The UI intentionally hides action buttons in compact (<22-row)
            # terminals; choose a visible Send control for this interaction.
            async with app.run_test(size=(80, 26)) as pilot:
                discovery_hash = discovered_tools(await backend._connect())
                from textual.widgets import Button, Input
                choice_control = app.query_one('#agent-tool-choice', Button)
                async def click_tool_choice():
                    # Textual ignores another click during the pressed effect.
                    # Wait for that real UI state, then exercise the next click.
                    async with asyncio.timeout(5):
                        while choice_control.has_class('-active'):
                            await pilot.pause(.01)
                    require(await pilot.click('#agent-tool-choice'), 'Tool mode button was not clickable')
                require(app.tool_choice == args.tool_choice, 'UI lost CLI-selected/default tool mode')
                history = []
                approvals = 0
                for index in range(2):
                    chosen = 'required' if required_check and index == 0 else 'auto'
                    if required_check:
                        # DeepSeek starts at default auto; Qwen starts at the
                        # public CLI's required option. Exercise both controls.
                        if family == 'qwen' and index == 0:
                            await click_tool_choice()
                            require(app.tool_choice == 'auto', 'Visible control did not select auto')
                        if (family == 'deepseek' and index == 0) or (family == 'qwen' and index == 1):
                            await pilot.press('ctrl+t')
                        else:
                            await click_tool_choice()
                        require(app.tool_choice == chosen and chosen.title() in str(choice_control.label),
                                'Visible mode did not match submitted tool choice')
                    prompt = 'first fixture turn' if index == 0 else 'second fixture turn'
                    app.query_one('#agent-input', Input).value = prompt
                    if index == 0:
                        await pilot.press('enter')
                    else:
                        # Exercise the app's Send control, preserving successful history.
                        require(await pilot.click('#agent-send'), 'Send control was not visible/clickable')
                    task = app._turn_task
                    if required_check:
                        # Use the public mounted approval instead of bypassing
                        # it; each turn dispatches one actual own MCP call.
                        async with asyncio.timeout(30):
                            while app.busy:
                                if isinstance(app.screen, ApprovalScreen):
                                    await pilot.pause()
                                    require(choice_control.disabled, 'Busy turn left tool mode editable')
                                    await pilot.press('ctrl+t')
                                    require(app.tool_choice == chosen, 'Busy turn changed submitted mode')
                                    screen = app.screen
                                    require('ai-lab: answer_decisions' in screen.message
                                            and '"laya"' in screen.message, 'Approval lost exact own local tool')
                                    require(await pilot.click('#allow'), 'Public Allow was not clickable')
                                    approvals += 1
                                    while app.busy and app.screen is screen:
                                        await asyncio.sleep(.01)
                                else:
                                    await asyncio.sleep(.01)
                    if task is not None:
                        await asyncio.wait_for(task, 30)
                    require(app.last_error is None and len(app.history) == 4 * (index + 1),
                            f'Installed agent {name} turn {index + 1} did not settle: '
                            f'error={app.last_error is not None}, history={len(app.history)}, busy={app.busy}, '
                            f'task={task is not None}, state={app.lifecycle_state}')
                    require(app.history[:len(history)] == history, 'Agent rewrote previous successful tool history')
                    continuation = app.history[len(history) + 1:]
                    require([m['role'] for m in continuation] == ['assistant', 'tool', 'assistant']
                            and continuation[1]['tool_call_id'] == continuation[0]['tool_calls'][0]['id']
                            and decoded(json.loads(continuation[1]['content']))['answers']['ok']['noul'] == .8
                            and continuation[-1]['content'] == family + ' fixture continuation: 0.8',
                            'Agent changed actual tool call/result/answer')
                    require(backend.last_result.get('fixture') is True and backend.selection == selection,
                            'Agent lost fixture provenance or changed its selection')
                    key_free({'selection': selection, 'history': app.history, 'last_result': backend.last_result}, records,
                             (override['key'],) if 'key' in override else ())
                    sent = [{'role': 'system', 'content': SYSTEM}] + history + [{'role': 'user', 'content': prompt}]
                    expected.extend([{'family': family, 'path': '/v1/chat/completions', 'seed': seed,
                                      'watermark': watermark, 'messages': sent, 'tools_hash': discovery_hash,
                                      'tool_choice': chosen},
                                     {'family': 'laya', 'path': '/v1/systemone'},
                                     {'family': family, 'path': '/v1/chat/completions', 'seed': seed,
                                      'watermark': watermark, 'messages': sent + continuation[:2],
                                      'tools_hash': discovery_hash, 'tool_choice': 'auto'}])
                    history = deepcopy(app.history)
                if required_check:
                    require(approvals == 2, 'Focused check bypassed or repeated actual approval')
        finally:
            await backend.aclose()
        require(backend._closed and backend._client is None and backend.chat._closed
                and not backend.chat._requests, 'Agent left owned MCP/chat resources open')
        require((root / 'harness/models.json').read_bytes() == saved, 'Agent override changed saved profiles')
        checked.append({'family': family, 'kind': name.split()[1], 'override': bool(override), 'turns': 2,
                        'scheme': watermark['scheme'] if watermark else 'none', 'tools_sha256': discovery_hash,
                        'tool_choices': ['required', 'auto', 'auto', 'auto'] if required_check else ['auto'] * 4,
                        'mounted_public_allow': required_check, 'profile_snapshot_preserved': True})
    require(len(expected) == (12 if required_check else 126), 'Agent checker omitted intended turns')
    require(not (root / '.models').exists() and not list(root.glob('.state/*server*.json')), 'Agent started native processes')
    private_json(root / (phase + '-expected.json'), expected)
    return {'phase': phase, 'package': str(Path(ai_lab.__file__).resolve()), 'fixture': True,
            'own_mcp': 'real stdio', 'http_requests': len(expected), 'checked': checked, 'owned_resources_closed': True}


def check(python, *, required_only=False):
    python = Path(python).absolute()
    require(python.is_file(), 'Installed Python executable does not exist')
    with tempfile.TemporaryDirectory(prefix='ai-lab-cross-chat-') as directory, fixtures() as (endpoints, events, health):
        root = Path(directory)
        private_json(root / 'fixtures.json', {'version': 1, 'endpoints': {k: endpoints[k] for k in FAMILIES}})
        environment = {k: os.environ[k] for k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}
        environment.update(AI_LAB_GENERATION_FIXTURE_FILE=str(root / 'fixtures.json'), AI_LAB_LAYA_URL=endpoints['laya'])
        phases = []
        requested = ('create', 'agent-required') if required_only else ('create', 'mcp', 'reload', 'agent', 'agent-reload', 'reject')
        for phase in requested:
            offset = len(events)
            health['valid'] = phase != 'reject'
            result = subprocess.run([str(python), '-I', str(Path(__file__).resolve()), '--probe', str(root), '--phase', phase],
                                    cwd=root, env=environment, capture_output=True, text=True, timeout=180)
            if result.returncode:
                try:
                    reason = json.loads(result.stderr.splitlines()[-1])['error']
                except (ValueError, IndexError, KeyError):
                    reason = 'child output withheld to protect keys'
                raise RuntimeError('Installed ' + phase + ' phase failed: ' + reason)
            phases.append(json.loads(result.stdout))
            expected = [] if phase == 'create' else json.loads((root / (phase + '-expected.json')).read_text())
            actual = events[offset:]
            require(len(actual) == len(expected), 'Missing requests, retry or unexpected fallback')
            for event, wanted in zip(actual, expected):
                require(event['family'] == wanted['family'] and event['path'] == wanted['path'], 'Wrong HTTP backend/path')
                body = event['body']
                require(event['authorization'] is None, 'HTTP request carried hosted authorization')
                if wanted['family'] == 'laya':
                    require(body['model'] == 'laya' and body['questions'] == {'ok': {'type': 'noul'}},
                            'Own MCP changed explicit local decision request')
                else:
                    require(body['model'] == 'default' and body.get('seed') == wanted['seed']
                            and body.get('watermark') == wanted['watermark'], 'Wrong model alias/seed/private key/settings')
                    if wanted['path'] == '/v1/chat/completions':
                        require(body['messages'] == wanted['messages']
                                and body['tool_choice'] == wanted.get('tool_choice', 'auto'),
                                'Chat changed actual messages or selected tool mode')
                        require(body['temperature'] == .8 and body['max_tokens'] == 1024 and body['stream'] is False,
                                'Chat changed shipped wire sampling defaults')
                        require(tools_hash(body['tools']) == wanted['tools_hash'],
                                'Chat changed discovered tool schemas on request/continuation')
                        functions = [tool['function'] for tool in body['tools']]
                        require(len(functions) == 15 and len({tool['name'] for tool in functions}) == 15,
                                'Chat did not send all 15 shipped tool schemas')
                        require(all(tool['strict'] is True for tool in functions), 'Chat lost strict tool schemas')
                        for remote in ('answer_decisions', 'rank_decisions'):
                            tool = next(t for t in functions if remote in t['name'])
                            schema = tool['parameters']
                            require('model' in schema['required'] and set(schema['properties']['model']['enum']) ==
                                    {'laya', 'contrastive', 'clm-upstream'}, 'Chat changed offline provider policy')
        require(len(events) == (12 if required_only else 420), 'Checker did not perform every intended call/continuation')
        return {'status': 'passed', 'fixture': True, 'scope': 'installed own stdio MCP + NativeChat + AgentBackend/UI profile inheritance',
                'phases': phases, 'http_requests': len(events), 'native_inference_proof': False,
                'shipped_tools_per_chat_request': 15,
                'strict_discovery_hash_preserved': True,
                'chat_defaults': {'tool_choice': 'auto', 'temperature': .8, 'max_tokens': 1024, 'timeout_seconds': 180},
                'watermark_schemes_per_family': ['kgw'] if required_only else
                    ['kgw', 'synthid', 'unigram', 'exponential', 'inverse_transform', 'mpac', 'none'],
                'required_mode_focused_check': required_only,
                'downloads_or_native_starts': False, 'hosted_credentials': False, 'agent_ui': 'installed Enter/Send + two-turn history'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', help='Python interpreter of the installed wheel')
    parser.add_argument('--required-only', action='store_true', help='Check only saved-profile required-mode UI/wire inheritance')
    parser.add_argument('--probe', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--phase', choices=['create', 'mcp', 'reload', 'agent', 'agent-reload', 'agent-required', 'reject'], help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.probe:
            if args.phase == 'create':
                value = create(args.probe)
            elif args.phase.startswith('agent'):
                value = asyncio.run(agent_probe(args.probe, args.phase))
            else:
                value = asyncio.run(probe(args.probe, args.phase))
        else:
            require(args.python is not None, '--python is required')
            value = check(args.python, required_only=args.required_only)
        print(json.dumps(value, indent=2))
    except Exception as error:
        message = str(error) if type(error) is RuntimeError else type(error).__name__
        print(json.dumps({'status': 'failed', 'error': message}), file=sys.stderr)
        sys.exit(1)
