#!/usr/bin/env python3
"""Exercise the installed uvx wheel over real MCP stdio in an empty workspace.

Run with uv sync --extra mcp, then .venv/bin/python packaging/check_mcp.py.
Does not install into a user's client config or download/start model APIs.
"""
import argparse
import asyncio
from datetime import timedelta
import json
from pathlib import Path
import sys
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(executable=None):
    project = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='ai-lab-mcp-check-') as folder:
        root = Path(folder).resolve()
        if executable:
            configured = subprocess.run([executable, '--root', str(root), 'mcp', 'config', '--codex', '--json'],
                                        capture_output=True, text=True, check=True)
            entry = json.loads(configured.stdout)['entry']
        else:
            from ai_lab.mcp_install import launch_config
            entry = launch_config(root)
        env = {**entry['env'], 'UV_CACHE_DIR': str(project / '.runtime/uv-cache')}
        # Keep any installed credential environment out of this offline check.
        env.update(TYPESAFE_API_KEY='', JEV_API_KEY='')
        env.update(AI_LAB_LAYA_URL='http://127.0.0.1:1', AI_LAB_DECISIONS_URL='http://127.0.0.1:1',
                   AI_LAB_CLM_UPSTREAM_URL='http://127.0.0.1:1')
        parameters = StdioServerParameters(command=entry['command'], args=entry['args'], env=env)
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=120)) as session:
                await session.initialize()
                catalog = await session.list_tools()
                assert len(catalog.tools) == 14

                async def call(name, arguments=None, error=False):
                    result = await session.call_tool(name, arguments or {})
                    assert bool(result.isError) == error, (name, result)
                    if error: return '\n'.join(getattr(item, 'text', '') for item in result.content)
                    return result.structuredContent or json.loads(result.content[0].text)

                models = await call('list_models')
                assert {row['name'] for row in models['models']} == {'jev', 'deepseek', 'contrastive', 'clm-upstream', 'laya'}
                assert models['default_decision_model'] == 'jev'
                schemes = await call('explain_watermarks')
                assert len(schemes['schemes']) == 6
                seeded = await call('create_seeded_model', {'name': 'MCP smoke seed', 'seed': '0x2A'})
                assert seeded['seed'] == 42
                watermarked = await call('create_watermarked_model', {'name': 'MCP smoke SynthID', 'scheme': 'synthid', 'seed': 42})
                assert watermarked['watermark']['has_key'] and 'key' not in watermarked['watermark']
                config = await call('get_model_config', {'model': watermarked['key'], 'include_watermark_key': True})
                saved_key = config['watermark']['key']
                updated = await call('update_watermarked_model', {'model': watermarked['key'], 'settings': {'depth': 3}})
                assert updated['watermark']['depth'] == 3
                config = await call('get_model_config', {'model': watermarked['key'], 'include_watermark_key': True})
                assert config['watermark']['key'] == saved_key
                assert 'key' not in (await call('get_model_config', {'model': watermarked['key']}))['watermark']
                assert root.joinpath('harness/models.json').stat().st_mode & 0o777 == 0o600
                stopped = await call('answer_decisions', {'model': 'laya', 'state': 'test', 'questions': {'ok': {'type': 'noul'}}}, error=True)
                assert 'models run --laya' in stopped
                missing = await call('answer_decisions', {'state': 'test', 'questions': {'ok': {'type': 'noul'}}}, error=True)
                assert 'Jev needs' in missing
                detector = await call('detect_watermark', {'text': 'External text', 'model': watermarked['key']}, error=True)
                assert 'models run --deepseek' in detector
                assert (await call('list_results'))['results'] == []
                assert not list(root.glob('.state/*server*.json'))
                result = {'status': 'passed', 'transport': 'stdio', 'launcher': 'uvx',
                          'tool_count': len(catalog.tools), 'tools': [tool.name for tool in catalog.tools],
                          'checked': ['isolated packaged wheel', 'missing-model discovery', 'paper catalog',
                                      'seeded/watermarked profiles', 'private watermark keys',
                                      'persisted config updates', 'explicit watermark key retrieval', 'detector manual API requirement',
                                      'stopped API instructions', 'Jev default', 'no CLI daemon or model starts']}
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', help='Exercise an installed ai-lab CLI and its packaged installer')
    args = parser.parse_args()
    result = asyncio.run(check(args.executable))
    print(json.dumps(result, indent=2))
