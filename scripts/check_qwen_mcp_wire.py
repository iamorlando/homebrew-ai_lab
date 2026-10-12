#!/usr/bin/env python3
"""One real MCP stdio generation against an already-owned native Qwen API.

The child uses installed AI Lab's unmodified create_server registration/handlers,
injecting its supported read-only native runtime so it cannot start any model.
"""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys


def bind_root(root):
    if os.environ.get('AI_LAB_GENERATION_FIXTURE_FILE'):
        raise ValueError('Native acceptance refuses fixture endpoints.')
    from ai_lab.paths import load_backend
    load_backend(root)
    from harness.generation_models import supported_generation_backend
    import inference
    backend = supported_generation_backend('qwen38')
    state = inference.owned_state(backend)
    if not state or not inference.launch_matches(state, backend):
        raise ValueError('Start the receipt-verified, root-owned Qwen server first.')
    return backend, state


def serve(root):
    bind_root(root)
    from ai_lab.mcp_tools import LabTools
    from ai_lab.mcp_server import create_server
    from watermark_runtime import WatermarkRuntime
    lab = LabTools(root, watermark_runtime=WatermarkRuntime(allow_start=False))
    # This child borrows the owner's API. It cannot start or adopt one.
    lab.lifecycle.allow_start = False
    create_server(root, tools=lab).run(transport='stdio')


async def check(root, stderr_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    backend, before = bind_root(root)
    script = Path(__file__).resolve()
    params = StdioServerParameters(command=sys.executable,
        args=['-I', str(script), '--server', '--root', str(root)],
        env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/private/tmp'),
             'TYPESAFE_API_KEY': '', 'JEV_API_KEY': '', 'AI_LAB_ROOT': str(root)},
        cwd=str(script.parent))
    with stderr_path.open('w') as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=150)) as session:
                await session.initialize()
                catalog = await session.list_tools()
                names = {tool.name for tool in catalog.tools}
                assert {'generate_text', 'create_seeded_model', 'detect_watermark'} <= names
                created_schema = next(t.inputSchema for t in catalog.tools if t.name == 'create_seeded_model')
                assert 'qwen38' in created_schema['properties']['underlying_model']['enum']
                response = await session.call_tool('generate_text', {
                    'model': 'qwen38', 'prompt': 'Compute 9 plus 8. Reply with only the number.',
                    'scheme': 'none', 'seed': 42, 'max_tokens': 32, 'temperature': 0})
                assert not response.isError, response
                result = response.structuredContent or json.loads(response.content[0].text)
                assert result['underlying_model'] == 'Qwen3.8-27B' and not result.get('fixture'), result
                assert result['answer'].strip() == '17', result
                assert 0 < result['usage'].get('completion_tokens', 0) <= 32, result
    _, after = bind_root(root)
    assert before == after, 'Borrow-only MCP changed the root owner receipt.'
    return {'transport': 'real stdio MCP', 'server': 'installed ai_lab.mcp_server.create_server',
            'native_runtime': 'WatermarkRuntime(allow_start=False), no fixtures',
            'tools': sorted(names), 'result': result, 'owner_pid': before['pid'],
            'owner_receipt_unchanged': True, 'endpoint': backend.base_url}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--server', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.server:
        serve(root)
    else:
        if args.output is None:
            parser.error('--output is required outside --server mode')
        result = asyncio.run(check(root, args.output.with_suffix('.stderr.log')))
        args.output.write_text(json.dumps(result, indent=2) + '\n')
