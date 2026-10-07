#!/usr/bin/env python3
"""Public Completion view actions with owned CPU APIs and historical replay.

The inherited dog/picker/legacy proof remains in check_completion.py. This proof
uses separate fox and scheme recordings; it never starts native inference.
"""
import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

from check_completion import require, serve


def check(*, installed=False, evidence=None):
    import ai_lab
    from ai_lab.paths import RESOURCES, BUNDLE, load_backend
    from ai_lab.cli import main
    from ai_lab.client import Client, socket_path
    from ai_lab.cli_screens import ProfilePicker
    from ai_lab.tui import LabApp
    from ai_lab.views import candidate_rows, token_detail
    from textual.widgets import DataTable, Input, Select, Static, TextArea, Tree
    load_backend(RESOURCES)
    from model_profiles import ModelProfiles, profile_values
    from watermarks import validate_watermark
    if installed:
        require(BUNDLE.is_dir() and Path(ai_lab.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
                'installed proof must import this environment, outside the checkout')
    fixture_file = Path(__file__).with_name('completion-views-fixture.json')
    fixture = json.loads(fixture_file.read_text())
    records = fixture['records']
    sizes = ((150, 48), (80, 24), (50, 18))
    schemes = ('full', 'probability-updates', 'none', 'kgw', 'unigram', 'exponential', 'inverse_transform', 'mpac')
    observations = []
    with tempfile.TemporaryDirectory(prefix='completion-views-') as directory:
        root = Path(directory).resolve()
        (root / 'sources.json').write_bytes((RESOURCES / 'sources.json').read_bytes())
        profiles = {}
        for name in schemes:
            wm = None if name == 'none' else validate_watermark({
                'scheme': 'synthid' if name in ('full', 'probability-updates') else name,
                'key': '42' * 32,
                **({'depth': 4, 'generation_policy': 'tournament' if name == 'full' else 'probability_updates'}
                   if name in ('full', 'probability-updates') else {})})
            profiles[name.replace('_', '-')] = profile_values('Replay ' + name, 42, 'deepseek', wm)
        registry = ModelProfiles(root)
        registry.path.parent.mkdir()
        registry.path.write_text(json.dumps(registry.document(profiles)))
        saved_profiles = registry.path.read_bytes()

        def events():
            path = root / 'proof-events.jsonl'
            return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

        def creates():
            return [e for e in events() if e['method'] == 'POST' and e['path'] == '/api/lab/sessions']

        sessions = {}
        with serve(root, 'owner', uds=socket_path(root), views=True) as owner, serve(root, 'website', views=True) as website:
            client = Client(root, server=website['transport']).connect()

            async def settle(app, pilot):
                await pilot.pause()
                await app.workers.wait_for_complete()
                for _ in range(100):
                    await app.refresh_session()
                    if not app.record or app.record['status'] != 'running':
                        break
                    await pilot.pause(.02)
                require(not app.record or app.record['status'] != 'running', 'bounded CPU replay completion')
                await pilot.pause()

            async def choose(app, pilot, name):
                key = name.replace('_', '-')
                require(key in app.models, 'fixture inventory loaded: ' + str(app.query_one('#completion-error', Static).content))
                await pilot.press('f2', 'enter', 'home')
                await pilot.press(*(['down'] * (list(app.models).index(key) + 1)), 'enter')
                await settle(app, pilot)
                require(app.record is not None and app.record['model'] == key,
                        'keyboard picker routes ' + name + ': ' + str(app.query_one('#completion-error', Static).content)
                        + '; selected=' + str(app.query_one('#completion-model', Select).value))
                sessions[name] = app.session_id

            async def select_step(app, pilot, index):
                await pilot.press('f3', 'enter', 'home', *(['down'] * (index + 1)), 'enter')
                await settle(app, pilot)
                require(app.record['selected_step'] == index, 'public captured-step selector')

            async def run(app, pilot, prompt, count=1, *, keyboard=False):
                await pilot.press('ctrl+p')
                app.query_one('#prompt', TextArea).load_text(prompt)
                app.query_one('#token-count', Input).value = str(count)
                await pilot.pause()
                if keyboard:
                    await pilot.press('ctrl+enter')
                else:
                    require(await pilot.click('#run'), 'visible Run button')
                await settle(app, pilot)
                require(app.record['status'] == 'complete', 'replay completed: ' + str(app.record.get('error')))
                require(app.record['prompt'] == prompt, 'prefix whitespace preserved')

            def visible(app, ident):
                widget = app.screen.query_one(ident)
                require(widget.display and widget.region.width > 0 and widget.region.height > 0
                        and app.screen.region.contains_region(widget.region),
                        f'{ident} visible at {app.size}: {widget.region}')

            async def inspect_layers(app, pilot, size):
                await pilot.resize_terminal(*size)
                await pilot.pause()
                await pilot.press('f4', 'enter', 'home', 'down', 'enter')
                await settle(app, pilot)
                require(app.record['selected_layer'] == 0, 'first captured layer via keyboard')
                row = next(c for c in candidate_rows(app.record) if c['token_id'] == 38835)
                require(row['post_watermark_probability'] == .4874087129594427, 'captured layer probability, never renormalized')
                require('Final log p -3.649384648105211e-05' in token_detail(app.record), 'numeric logprob remains explicitly final')
                if app.query('#tokens'):
                    require(app.query_one('#tokens', DataTable).get_row('38835')[-1] == '-3.649384648105211e-05', 'numeric logprob in rendered token row')
                await pilot.press('f4', 'enter', 'home', 'enter')
                await settle(app, pilot)
                require(app.record['selected_layer'] == -1, 'final distribution selectable')
                observations.append({'entry_view': app.view, 'size': list(size), 'session': app.session_id,
                                     'layer_and_log_probability': True, 'historical_replay_only': True})

            async def inspect(app, pilot, size):
                # Selectors are global in both joined and standalone views.
                visible(app, '#history')
                visible(app, '#round')
                await select_step(app, pilot, 0)
                await select_step(app, pilot, 1)
                if app.view in ('all', 'tournament'):
                    await pilot.press('ctrl+t', 'down', 'enter')
                    require(app.selected_match_id == 12, 'keyboard chooses captured match 12; actual=' + str(app.selected_match_id))
                    tree = app.query_one('#bracket', Tree)
                    await pilot.press('down')
                    node = tree.cursor_node
                    require(node.data['match']['match_id'] == 8, 'next captured match')
                    require(await pilot.click('#bracket', offset=(18, node.line - int(tree.scroll_offset.y))), 'match mouse target')
                    require(app.selected_match_id == 8, 'mouse selects match without generation')
                    frozen = copy.deepcopy(app.record['results'])
                    await pilot.press('down', 'down', 'enter')
                    await settle(app, pilot)
                    require(app.record['results'] == frozen, 'draw inspection preserves recorded winners/trace')
                    require('Inspecting' in str(app.query_one('#tournament-token-detail', Static).content), 'standalone tournament token details')
                    await pilot.press('f5', 'end')
                    await pilot.wait_for_scheduled_animations()
                    detail = app.query_one('#match-scroll')
                    require(detail.scroll_y == detail.max_scroll_y, 'full match and token detail reachable')
                if app.view in ('all', 'tokens'):
                    await pilot.press('ctrl+k')
                    visible(app, '#tokens')
                    await pilot.press('down', 'enter')
                    await settle(app, pilot)
                    require(app.query_one('#tokens', DataTable).row_count == 128, 'all historical candidates available')
                    require('Final log p unavailable' in str(app.query_one('#details', Static).content), 'tournament logprob is unavailable')
                    await pilot.press('f5', 'end')
                    await pilot.wait_for_scheduled_animations()
                    detail = app.query_one('#token-detail-scroll')
                    require(detail.scroll_y == detail.max_scroll_y, 'token details keyboard scroll to bottom')
                if app.view in ('all', 'probabilities'):
                    await pilot.press('ctrl+o', 'end')
                    await pilot.wait_for_scheduled_animations()
                    scroll = app.query_one('#probability-scroll')
                    visible(app, '#probability-scroll')
                    require(scroll.scroll_y == scroll.max_scroll_y, 'all probability rows reachable')
                    require('unavailable' in str(app.query_one('#prob-note', Static).content), 'actual tournament final probability limitation')
                if app.view in ('all', 'chat'):
                    await pilot.press('ctrl+p')
                    for ident in ('#prompt', '#run', '#append', '#stop', '#token-count', '#answer-scroll'):
                        visible(app, ident)
                    require('fox' in str(app.query_one('#answer', Static).content), 'decoded historical completion visible')
                if app.view == 'all' and size[0] < 110:
                    for name in ('probabilities', 'tokens', 'tournament', 'chat'):
                        require(await pilot.click('#tab-' + name), 'compact mouse navigation ' + name)
                        await pilot.pause()
                        require(app.compact_view == name, 'compact tab switched ' + name)
                await pilot.press('f1')
                await pilot.pause()
                visible(app, '#help-box')
                await pilot.press('escape')
                if evidence:
                    for key, view in [('ctrl+p', 'chat'), ('ctrl+t', 'tournament'), ('ctrl+o', 'probabilities'), ('ctrl+k', 'tokens')]:
                        if app.view in ('all', view):
                            await pilot.press(key)
                            app.save_screenshot(f'{app.view}-{view}-{size[0]}x{size[1]}.svg', path=str(evidence))
                observations.append({'entry_view': app.view, 'size': list(size), 'session': app.session_id,
                                     'keyboard_and_buttons': True, 'historical_replay_only': True})
                print(f'VIEW_ACTIONS_OK {app.view} {size[0]}x{size[1]}', file=sys.stderr, flush=True)

            def drive(app, **kwargs):
                async def mounted():
                    async with app.run_test(size=sizes[0]) as pilot:
                        await settle(app, pilot)
                        if not app.session_id:
                            require(not creates(), 'bare public entry creates no session')
                            await choose(app, pilot, 'full')
                            for size in sizes:
                                await pilot.resize_terminal(*size)
                                await pilot.pause()
                                await run(app, pilot, 'the quick brown  \n', 2, keyboard=size == sizes[-1])
                                require(all(r['step'] == records['full']['step'] for r in app.record['results']), 'fox trace byte-equivalent projection')
                                await inspect(app, pilot, size)
                            # Explicit Append while the prefix editor is focused.
                            await select_step(app, pilot, 0)
                            await pilot.press('ctrl+k', 'down', 'enter')
                            await settle(app, pilot)
                            token = next(c for c in candidate_rows(app.record) if c['token_id'] == app.record['selected_token_id'])
                            expected = app.record['results'][0]['prompt'] + token['text']
                            await pilot.press('ctrl+p', 'ctrl+a')
                            await settle(app, pilot)
                            require(app.record['prompt'] == expected and len(app.record['results']) == 1, 'keyboard Append sends inspected token separately')
                            # Public Stop releases an owned CPU fixture gate only
                            # after the real session owner has accepted its POST.
                            app.query_one('#prompt', TextArea).load_text('[slow] the quick brown')
                            app.query_one('#token-count', Input).value = '32'
                            require(await pilot.click('#run'), 'tiny Run for stop proof')
                            for _ in range(100):
                                await pilot.pause(.01)
                                if (app.record['status'] == 'running' and not app.mutating
                                        and any(e['method'] == 'REPLAY' and e['path'].startswith('[slow]') for e in events())):
                                    break
                            await app.workers.wait_for_complete()
                            require(app.record['status'] == 'running' and not app.query_one('#stop').disabled,
                                    'Run acknowledged and Stop enabled')
                            require(await pilot.click('#stop'), 'tiny Stop button')
                            await settle(app, pilot)
                            require(not app.query_one('#completion-error').display, 'Stop reports no API error')
                            require(len([e for e in events() if e['method'] == 'GATE_RELEASE']) == 1,
                                    'exactly one accepted Stop POST reached the owner and released the fixture')
                            require(app.record['status'] == 'stopped' and len(app.record['results']) == 1,
                                    'Stop persisted and bounded: ' + str((app.record['status'], len(app.record['results'])))
                                    + '; actions=' + str([e['path'] for e in events() if e['method'] == 'POST'][-4:]))
                            await run(app, pilot, 'the quick brown', 2)
                            # Genuine per-scheme captures, no bracket invented from alternatives.
                            for name in schemes[1:]:
                                await choose(app, pilot, name)
                                await run(app, pilot, 'historical scheme replay')
                                require(app.record['results'][0]['step'] == records[name]['step'], 'scheme-specific recorded evidence: ' + name)
                                require(not app.match_nodes, 'non-tournament scheme has no fabricated bracket: ' + name)
                                if name == 'probability-updates':
                                    for size in sizes:
                                        await inspect_layers(app, pilot, size)
                                    rows = sorted(candidate_rows(app.record), key=lambda c:c.get('reporting_probability') or 0, reverse=True)[:10]
                                    require(abs(sum(c['reporting_probability'] for c in rows) - .723414095) < 1e-12, 'full-vocabulary mass preserved')
                            await choose(app, pilot, 'full')
                            for name, matches in [('collapsed', 1), ('root-only', 0), ('warmup', 0)]:
                                await run(app, pilot, '[' + name + '] replay')
                                require(app.record['results'][0]['step'] == records[name]['step'], name + ' historical projection')
                                require(len(app.match_nodes) == matches, name + ' only captured matches')
                            await pilot.resize_terminal(50, 18)
                            await pilot.press('ctrl+p')
                            app.query_one('#prompt', TextArea).load_text('fixture backend failure')
                            await pilot.press('ctrl+enter')
                            await settle(app, pilot)
                            require(app.record['status'] == 'error', 'persisted backend failure at 50x18')
                            require('Fixture backend unavailable' in str(app.query_one('#answer', Static).content),
                                    'tiny error explanation in scrollable completion output')
                            require(not app.match_nodes and app.query_one('#tokens', DataTable).row_count == 0,
                                    'empty failed run clears prior trace in joined views')
                            await pilot.press('f5', 'end')
                            await run(app, pilot, 'the quick brown', 2)
                        elif app.session_id == sessions.get('probability-updates'):
                            for size in sizes:
                                await inspect_layers(app, pilot, size)
                        else:
                            require(app.session_id == sessions['full'], 'public standalone resumes exact session')
                            for size in sizes:
                                await pilot.resize_terminal(*size)
                                await pilot.pause()
                                await inspect(app, pilot, size)
                        require(app.is_running, 'public view remains mounted')
                        await pilot.press('ctrl+q')
                asyncio.run(mounted())

            with patch.dict('os.environ', {'AI_LAB_SERVER': website['transport']}), \
                    patch('ai_lab.cli.sys.stdin.isatty', return_value=True), \
                    patch.object(ProfilePicker, 'run', side_effect=AssertionError('no separate picker')), \
                    patch.object(LabApp, 'run', new=drive), \
                    patch('ai_lab.downloads.offer', side_effect=AssertionError('no downloads')), \
                    patch('ai_lab.client.subprocess.Popen', side_effect=AssertionError('no parallel API owner')):
                require(main(['--root', str(root), 'completion']) == 0, 'public bare Completion')
                session = sessions['full']
                before = client.request('GET', '/api/lab/sessions/' + session)
                create_count = len(creates())
                for view in ('chat', 'tournament', 'probabilities', 'tokens'):
                    require(main(['--root', str(root), 'completion', '--session', session, '--view', view]) == 0,
                            'public standalone ' + view)
                for view in ('probabilities', 'tokens'):
                    require(main(['--root', str(root), 'completion', '--session', sessions['probability-updates'], '--view', view]) == 0,
                            'standalone captured layers/log probabilities ' + view)
                after = client.request('GET', '/api/lab/sessions/' + session)
                require(after['results'] == before['results'] and after['answer'] == before['answer'], 'resume/inspection preserves captured evidence')
                require(len(creates()) == create_count == len(profiles), 'no new session on resume or switch-back')
                require(registry.path.read_bytes() == saved_profiles, 'profiles unchanged')
            replay_events = [e for e in events() if e['method'] == 'REPLAY']
            require(set(e['recording'] for e in replay_events) == set(records), 'every scheme/capture actually traversed owned API')
            require(not (root / '.models').exists(), 'no model files')
            requests = events()
    return dict(status='COMPLETION_VIEWS_HTTP_PASS', installed=installed,
                package=str(Path(ai_lab.__file__).resolve()),
                source_files_sha256={name: hashlib.sha256((Path(ai_lab.__file__).parent / name).read_bytes()).hexdigest()
                                     for name in ('tui.py', 'views.py', 'cli.py', 'session_compat.py', 'service.py')},
                fixture_sha256=hashlib.sha256(fixture_file.read_bytes()).hexdigest(),
                fixture_provenance=fixture['provenance'], observations=observations,
                recorded_replays=len(replay_events), session_creates=create_count,
                owned_apis=[owner, website], owned_process_cleanup=True,
                post_actions=sorted(set(e['path'].rsplit('/', 1)[-1] for e in requests if e['method'] == 'POST')),
                new_native_generation=False)


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
