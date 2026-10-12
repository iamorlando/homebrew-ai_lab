#!/usr/bin/env python3
"""Bounded actual-Qwen acceptance driver. Requires root-owned live-lane grant.

By default this only uses an already-running, receipt-verified Qwen API.
--start-through-app explicitly lets AI Lab own automatic startup and cleanup.
This script never downloads weights or executes the model's requested tools.
"""
import argparse
import asyncio
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--schemes', nargs='+', default=['kgw', 'synthid', 'textgrain'],
                        choices=['kgw', 'synthid', 'textgrain'])
    parser.add_argument('--start-through-app', action='store_true')
    parser.add_argument('--mcp-wire', action='store_true',
                        help='One additional borrow-only native MCP generation, at most 32 tokens.')
    parser.add_argument('--only-tool-roundtrip', action='store_true',
                        help='Only startup and two tool-chat turns, at most 192 tokens.')
    args = parser.parse_args()
    if args.only_tool_roundtrip and args.mcp_wire:
        parser.error('--only-tool-roundtrip cannot be combined with --mcp-wire')
    return args


async def main(args):
    if os.environ.get('AI_LAB_GENERATION_FIXTURE_FILE'):
        raise ValueError('Refusing native acceptance with generation fixtures enabled.')
    root = args.root.resolve()
    from ai_lab.paths import load_backend
    load_backend(root)
    from ai_lab.mcp_tools import LabTools
    from ai_lab.native_chat import NativeChat
    from harness.generation_models import supported_generation_backend
    from watermark_runtime import WatermarkRuntime
    import inference
    backend = supported_generation_backend('qwen38')
    assert backend.port == 11440 and backend.vocab_size == 248320
    assert backend.model_dir == root / '.models/qwen3.8-27b'
    started = time.monotonic()
    report = {'kind': 'actual-native-Qwen3.8-27B', 'fixture': False,
              'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'root': str(root), 'python': sys.executable, 'module': inference.__file__,
              'endpoint': backend.base_url, 'start_through_app': args.start_through_app,
              'maximum_generated_tokens': (192 if args.only_tool_roundtrip else
                  48 + 2 * 96 + sum(128 if s == 'kgw' else 64 for s in args.schemes) + (32 if args.mcp_wire else 0)),
              'cases': []}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')

    async def case(name, operation, timeout=180):
        began = time.monotonic()
        print(f'BEGIN {name}', flush=True)
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout)
            row = {'name': name, 'status': 'PASS', 'result': result}
        except Exception as error:
            row = {'name': name, 'status': 'FAIL', 'error': str(error),
                   'type': type(error).__name__, 'traceback': traceback.format_exc()}
        row['elapsed_seconds'] = round(time.monotonic() - began, 3)
        report['cases'].append(row)
        save()
        print(f'{row["status"]} {name} ({row["elapsed_seconds"]}s)', flush=True)
        return row

    profile_path = root / 'harness/models.json'
    original_profiles = profile_path.read_bytes() if profile_path.exists() else None
    original_mode = profile_path.stat().st_mode & 0o777 if original_profiles is not None else None
    original_document = json.loads(original_profiles) if original_profiles is not None else None
    created_profile_keys = set()
    runtime = None if args.start_through_app else WatermarkRuntime(allow_start=False)
    lab = LabTools(root, watermark_runtime=runtime)
    # Profile writes normalize historical records; permit only that known
    # deterministic serialization plus this driver's explicitly tracked keys.
    canonical_baseline = lab.registry.document(lab.registry.profiles())
    adapters = []
    try:
        async def startup():
            await lab.runtime.ensure_server(backend)
            state = inference.owned_state(backend)
            assert state, 'Acceptance requires this workspace\'s process receipt.'
            assert inference.launch_matches(state, backend), 'Runtime/template/launch provenance differs.'
            command = state['command']
            assert str(backend.model_dir) in command and backend.filename in command
            assert str(root / backend.template_file) in command
            return {'pid': state['pid'], 'command': command, 'build': state.get('build'),
                    'template_sha256': state.get('chat_template_sha256')}
        if (await case('owned_qwen_startup_identity', startup, timeout=600))['status'] != 'PASS':
            return 1

        async def plain():
            result = await lab.generate_text('Compute 6 times 7. Reply with only the number.',
                model='qwen38', scheme='none', max_tokens=48, temperature=0, seed=42)
            assert result['underlying_model'] == 'Qwen3.8-27B' and not result.get('fixture')
            assert result['answer'].strip() == '42', repr(result['answer'])
            assert 0 < result['usage'].get('completion_tokens', 0) <= 48
            return result
        if not args.only_tool_roundtrip:
            await case('selected_qwen_plain_generation', plain)

        async def tool_roundtrip():
            adapter = NativeChat(root, 'qwen38', seed=42, temperature=0, max_tokens=96, timeout=150)
            adapters.append(adapter)
            messages = [{'role': 'system', 'content': 'Use the supplied addition tool when asked to add numbers. After receiving its result, answer with only the result number.'},
                        {'role': 'user', 'content': 'Use add_numbers to add 17 and 25.'}]
            tools = [{'type': 'function', 'function': {'name': 'add_numbers',
                      'description': 'Add two integers and return their sum.',
                      'parameters': {'type': 'object', 'properties': {
                          'a': {'type': 'integer'}, 'b': {'type': 'integer'}},
                          'required': ['a', 'b'], 'additionalProperties': False}}}]
            call = await adapter.complete(messages, tools, tool_choice='required')
            first_metadata = dict(adapter.last_result)
            report['tool_roundtrip_attempt'] = {'call': call, 'call_metadata': first_metadata}
            save()
            calls = call.get('tool_calls', [])
            assert 1 <= len(calls) <= 8, call
            assert len({selected['id'] for selected in calls}) == len(calls), call
            for selected in calls:
                assert selected['function']['name'] == 'add_numbers', selected
                values = json.loads(selected['function']['arguments'])
                assert values == {'a': 17, 'b': 25}, values
                assert type(values['a']) is int and type(values['b']) is int
            # A deterministic owned local arithmetic result only; no tool execution.
            messages.append(call)
            messages.extend({'role': 'tool', 'tool_call_id': selected['id'], 'content': '{"result":42}'}
                            for selected in calls)
            answer = await adapter.complete(messages, tools, tool_choice='none')
            assert not answer.get('tool_calls'), answer
            assert answer.get('content', '').strip() == '42', answer
            assert adapter.last_result['underlying_model'] == 'Qwen3.8-27B'
            return {'call': call, 'call_metadata': first_metadata, 'answer': answer,
                    'answer_metadata': adapter.last_result}
        await case('native_xml_tool_call_and_result_turn', tool_roundtrip)

        for scheme in (() if args.only_tool_roundtrip else args.schemes):
            async def watermark_case(scheme=scheme):
                # This key is synthetic acceptance data, not a user secret.
                profile = await lab.create_watermarked_model(
                    f'Qwen native acceptance {scheme} {time.time_ns()}', scheme,
                    seed=20261012, key='61' * 32, underlying_model='qwen38')
                created_profile_keys.add(profile['key'])
                config = lab.get_model_config(profile['key'], include_watermark_key=True)
                if 'vocab_size' in config['watermark']:
                    assert config['watermark']['vocab_size'] == 248320
                if scheme == 'synthid':
                    assert config['watermark']['generation_policy'] == 'tournament'
                    assert config['watermark']['depth'] == 4
                generated = await lab.generate_text(
                    'Explain how rain forms, then describe why forests matter for rivers. Use several clear sentences.',
                    model=profile['key'], max_tokens=128 if scheme == 'kgw' else 64,
                    temperature=0.8, capture_trace=True)
                assert generated['underlying_model'] == 'Qwen3.8-27B'
                assert not generated.get('fixture') and not generated.get('trace_error'), generated.get('trace_error')
                steps = generated.get('sampling_trace', {}).get('steps', [])
                assert steps, 'No actual native sampling trace.'
                detected = await lab.detect_text(generated['answer'], model=profile['key'],
                    eos_token_ids=list(backend.eos_token_ids))
                assert detected['underlying_model'] == 'Qwen3.8-27B' and not detected.get('fixture')
                assert detected['tokens_scored'] > 0, detected
                p = detected['p_value']
                assert type(p) in (float, int) and math.isfinite(p) and 0 <= p <= 1, detected
                return {'profile': profile, 'generation': generated, 'detection': detected,
                        'statistical_match_required': False,
                        'note': 'Short bounded smoke proves real evidence paths, not guaranteed watermark power.'}
            await case(f'saved_qwen_{scheme}_generation_trace_detection', watermark_case)
        if args.mcp_wire:
            async def mcp_wire():
                path = Path(__file__).with_name('check_qwen_mcp_wire.py')
                spec = importlib.util.spec_from_file_location('qwen_acceptance_mcp_wire', path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return await module.check(root, args.output.with_suffix('.mcp-stderr.log'))
            await case('real_mcp_stdio_selected_qwen_generation', mcp_wire)
    finally:
        for adapter in adapters:
            await adapter.aclose()
        try:
            async with lab.lock:
                if created_profile_keys:
                    current = json.loads(profile_path.read_bytes())
                    remaining = dict(current)
                    remaining['models'] = [row for row in current['models'] if row['key'] not in created_profile_keys]
                    # Restore exact original bytes/mode only if every other field
                    # is unchanged. Never overwrite concurrent or user changes.
                    if original_document is None or remaining != canonical_baseline:
                        raise ValueError('Profiles changed beyond acceptance-owned keys; refusing original-byte restoration.')
                    descriptor, temporary = tempfile.mkstemp(dir=profile_path.parent, prefix='.qwen-acceptance-')
                    try:
                        with os.fdopen(descriptor, 'wb') as stream:
                            stream.write(original_profiles)
                        os.chmod(temporary, original_mode)
                        os.replace(temporary, profile_path)
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                assert original_profiles is None or profile_path.read_bytes() == original_profiles
                report['profile_cleanup'] = {'status': 'PASS', 'removed_keys': sorted(created_profile_keys),
                    'original_bytes_restored': original_profiles is not None,
                    'original_sha256': hashlib.sha256(original_profiles).hexdigest() if original_profiles is not None else None}
        except Exception as error:
            report['profile_cleanup'] = {'status': 'FAIL', 'error': str(error),
                                         'owned_keys': sorted(created_profile_keys)}
        finally:
            await lab.close()
        report['result'] = 'PASS' if report['cases'] and all(c['status'] == 'PASS' for c in report['cases']) else 'FAIL'
        if report.get('profile_cleanup', {}).get('status') != 'PASS':
            report['result'] = 'FAIL'
        save()
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main(arguments())))
