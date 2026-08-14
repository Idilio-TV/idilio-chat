"""
title: Idilio Dashboard Reference
author: Idilio
description: Live read-only access to the idilio-dashboard repo (GitHub) -- search for and fetch the actual code/docs that define company metrics, instead of relying on a snapshot that goes stale as the dashboard evolves. Backs the Idilio Analytics skill.
required_open_webui_version: 0.5.0
version: 0.1.0
"""

import base64
import json
import logging
import os

import aiohttp
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

GITHUB_API = 'https://api.github.com'
MAX_FILE_CHARS = 20000
MAX_SEARCH_RESULTS = 10


def _github_token() -> str:
    # A credential, not a Valve -- same reasoning as REDSHIFT_URL in redshift.py.
    # Recommend a fine-grained PAT scoped to just Idilio-TV/idilio-dashboard with
    # read-only Contents access, not a broad personal token -- this tool only ever
    # needs read access to one repo.
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('GITHUB_TOKEN is not configured')
    return token


class Tools:
    class Valves(BaseModel):
        REPO: str = Field(
            default='Idilio-TV/idilio-dashboard',
            description='GitHub "owner/repo" to search and read from.',
        )
        REF: str = Field(
            default='main',
            description='Git ref (branch, tag, or commit SHA) to read files at.',
        )

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {_github_token()}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

    async def search_dashboard_repo(self, query: str) -> str:
        """
        Search the idilio-dashboard repo's code for a term -- use this to find which
        file defines a metric (e.g. "MRR", "mart_subscription_daily", "retention") before
        fetching it with get_dashboard_file. Prefer this over guessing a file path.

        :param query: Search term, e.g. a metric name or a mart/table name
        :return: JSON array of {path, url} matches, or an error
        """
        try:
            scoped_query = f'{query} repo:{self.valves.REPO}'
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{GITHUB_API}/search/code',
                    headers=self._headers(),
                    params={'q': scoped_query, 'per_page': MAX_SEARCH_RESULTS},
                ) as resp:
                    body = await resp.json()
                    if resp.status != 200:
                        return json.dumps({'error': body.get('message', f'GitHub API returned {resp.status}')})
            results = [{'path': item['path'], 'url': item['html_url']} for item in body.get('items', [])]
            return json.dumps(results)
        except Exception as e:
            log.warning(f'search_dashboard_repo error: {e}')
            return json.dumps({'error': str(e)})

    async def get_dashboard_file(self, path: str) -> str:
        """
        Fetch the current content of a file in the idilio-dashboard repo, live from GitHub
        -- e.g. "CLAUDE.md" for the plain-English metric definitions,
        "api/chat/prompt_assets/canonical_rules.md" for the LLM-formatted canonical rules,
        or "api/metrics/handlers.py" for the actual SQL behind each metric. Use
        search_dashboard_repo first if you don't know the exact path.

        :param path: File path within the repo, e.g. "CLAUDE.md" or "api/metrics/handlers.py"
        :return: The file's text content (truncated if very large), or an error
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{GITHUB_API}/repos/{self.valves.REPO}/contents/{path}',
                    headers=self._headers(),
                    params={'ref': self.valves.REF},
                ) as resp:
                    body = await resp.json()
                    if resp.status != 200:
                        return json.dumps({'error': body.get('message', f'GitHub API returned {resp.status}')})

            if body.get('encoding') != 'base64':
                return json.dumps({'error': f'unexpected encoding: {body.get("encoding")}'})

            content = base64.b64decode(body['content']).decode('utf-8', errors='replace')
            truncated = len(content) > MAX_FILE_CHARS
            if truncated:
                content = content[:MAX_FILE_CHARS] + '\n\n[Content truncated...]'

            return json.dumps({'path': path, 'content': content, 'truncated': truncated})
        except Exception as e:
            log.warning(f'get_dashboard_file error: {e}')
            return json.dumps({'error': str(e)})
