#!/usr/bin/env python3
"""Fetch a frozen draft candidate for trusted dispatch CI; never publish it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = 'iamorlando/homebrew-ai_lab'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == 'https' and parsed.hostname in {
            'api.github.com', 'release-assets.githubusercontent.com',
            'objects.githubusercontent.com', 'github.com'}, 'Unexpected asset redirect')
        new = super().redirect_request(request, response, code, message, headers, url)
        if parsed.hostname != 'api.github.com':
            new.remove_header('Authorization')
        return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-id', type=int, required=True)
    parser.add_argument('--tap-sha', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--version', default='0.1.14')
    parser.add_argument('--wheel-sha256', required=True)
    parser.add_argument('--sdist-sha256', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.release_id > 0, 'Invalid draft release ID')
    for value in (args.tap_sha, args.source_sha):
        require(re.fullmatch(r'[0-9a-f]{40}', value), 'Expected exact commit SHA')
    for value in (args.wheel_sha256, args.sdist_sha256, args.manifest_sha256):
        require(re.fullmatch(r'[0-9a-f]{64}', value), 'Expected exact artifact SHA256')
    require(re.fullmatch(r'0\.1\.[0-9]+', args.version), 'Invalid candidate version')
    require(os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch', 'Trusted dispatch only')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/ai-lab/0.1.14-release-20261006',
            'Trusted candidate release branch only')
    require(os.environ.get('GITHUB_SHA') == args.tap_sha, 'Dispatch must target exact tap candidate')
    token = os.environ.get('GH_TOKEN', '')
    require(token and os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'Missing scoped staging token')
    require(not args.output.exists(), 'Staging output must be new')
    args.output.mkdir(parents=True)
    opener = urllib.request.build_opener(Redirect())

    def get(path, *, asset=False):
        request = urllib.request.Request('https://api.github.com/repos/' + REPOSITORY + path,
            headers={'Authorization': 'Bearer ' + token,
                     'Accept': 'application/octet-stream' if asset else 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'AI-Lab-release-validation'})
        with opener.open(request, timeout=60) as response:
            return response.read(64 * 1024 * 1024 + 1)

    release = json.loads(get('/releases/' + str(args.release_id)))
    require(release['draft'] is True and release['target_commitish'] == args.tap_sha,
            'Staged release must remain draft and target the exact tap commit')
    require(release['tag_name'] == 'ai_lab-v' + args.version, 'Unexpected candidate release tag')
    expected = {
        'ai_lab-' + args.version + '-py3-none-any.whl': args.wheel_sha256,
        'ai_lab-' + args.version + '.tar.gz': args.sdist_sha256,
        'candidate-binding.json': args.manifest_sha256,
    }
    assets = {entry['name']: entry for entry in release['assets']}
    require(set(expected) <= set(assets), 'Draft lacks required immutable candidate assets')
    evidence = {'draft': True, 'release_id': args.release_id, 'tap_sha': args.tap_sha,
                'source_sha': args.source_sha, 'assets': {}}
    for name, checksum in expected.items():
        asset = assets[name]
        require(0 < asset['size'] <= 64 * 1024 * 1024, 'Invalid asset size')
        content = get('/releases/assets/' + str(asset['id']), asset=True)
        require(len(content) == asset['size'], 'Asset length mismatch: ' + name)
        require(hashlib.sha256(content).hexdigest() == checksum, 'Asset hash mismatch: ' + name)
        (args.output / name).write_bytes(content)
        evidence['assets'][name] = {'id': asset['id'], 'size': len(content), 'sha256': checksum}
    binding = json.loads((args.output / 'candidate-binding.json').read_text())
    require(binding['source_sha'] == args.source_sha and binding['version'] == args.version,
            'Manifest source identity mismatch')
    require(binding['package_binding']['wheel_sha256'] == args.wheel_sha256 and
            binding['package_binding']['sdist_sha256'] == args.sdist_sha256,
            'Manifest artifact identity mismatch')
    final = json.loads(get('/releases/' + str(args.release_id)))
    require(final['draft'] is True and final['target_commitish'] == args.tap_sha,
            'Release changed during staging')
    require(final['tag_name'] == release['tag_name'], 'Release tag changed during staging')
    final_assets = {entry['name']: entry for entry in final['assets']}
    require(all(name in final_assets and all(final_assets[name][key] == assets[name][key]
                for key in ('id', 'name', 'size')) for name in expected),
            'Release asset identity changed during staging')
    (args.output / 'staging-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, KeyError, ValueError, urllib.error.URLError) as error:
        # HTTP errors must never expose request headers/token or response payloads.
        print(json.dumps({'status': 'FAIL', 'error': str(error) if isinstance(error, RuntimeError)
                          else type(error).__name__}))
        raise SystemExit(1)
