"""Generate local SVG profile cards using only public, owned, non-fork repos.

Requires Python 3.10+ and GitHub CLI. On GitHub Actions GH_TOKEN is provided
by the workflow; no personal access token or third-party stats host is needed.
"""

import json
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USERNAME = 'TheDarkGuardian'
ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    'TypeScript': '#3178c6', 'JavaScript': '#f1d05a', 'Go': '#00add8',
    'Python': '#6098ca', 'Shell': '#89c65b', 'C': '#a8b9cc',
    'CSS': '#b475ed', 'C#': '#52b56b', 'Rust': '#e2a178',
    'HTML': '#e96b4c', 'Dockerfile': '#468ac4', 'Other': '#8b949e',
}


def api(endpoint, paginate=False):
    args = ['gh', 'api', endpoint]
    if paginate:
        args += ['--paginate', '--slurp']
    process = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
    if process.returncode:
        raise RuntimeError(f'GitHub API request failed for {endpoint}: {process.stderr.strip()}')
    return json.loads(process.stdout)


def collect():
    pages = api(f'users/{USERNAME}/repos?type=owner&per_page=100', paginate=True)
    repos = [repo for page in pages for repo in page
             if repo['owner']['login'].lower() == USERNAME.lower()
             and not repo['private'] and not repo['fork'] and not repo['disabled']
             and repo['name'].lower() != USERNAME.lower()]
    totals = Counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(lambda repo: api(f"repos/{repo['full_name']}/languages"), repos)
        for languages in results:
            totals.update(languages)
    profile = api(f'users/{USERNAME}')
    return {
        'username': USERNAME,
        'updated_utc': datetime.now(timezone.utc).date().isoformat(),
        'scope': 'Public owned repositories, excluding forks, disabled repos and the profile repository',
        'public_projects': len(repos),
        'stars': sum(repo['stargazers_count'] for repo in repos),
        'joined_year': profile['created_at'][:4],
        'languages_bytes': dict(sorted(totals.items(), key=lambda item: (-item[1], item[0]))),
    }


def svg_card(data, dark=True):
    bg, surface, stroke = ('#0d1117', '#151b25', '#30394a') if dark else ('#ffffff', '#f6f8fc', '#d7dfeb')
    text, muted, accent = ('#edf1f7', '#a8b3c5', '#b7a4ff') if dark else ('#182133', '#52617b', '#6e4bce')
    totals = data['languages_bytes']
    total = sum(totals.values())
    items = list(totals.items())
    if len(items) > 10:
        items = items[:9] + [('Other', sum(size for _, size in items[9:]))]
    rows = (len(items) + 1) // 2
    height = max(280, 243 + rows * 34)
    date = datetime.strptime(data['updated_utc'], '%Y-%m-%d').strftime('%d %b %Y')
    body = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(USERNAME)} — public code snapshot</title>
<desc id="desc">{data['public_projects']} public original projects. Language shares are measured by code bytes, excluding forks and the profile repository. Updated {date}.</desc>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}}.mono{{font-family:Consolas,'Liberation Mono',monospace}}</style>
<rect x=".5" y=".5" width="899" height="{height-1}" rx="16" fill="{bg}" stroke="{stroke}"/>
<text x="30" y="36" font-size="12" font-weight="700" letter-spacing="2" fill="{accent}" class="mono">PUBLIC CODE / AT A GLANCE</text>
<text x="870" y="36" text-anchor="end" font-size="11" fill="{muted}" class="mono">{date}</text>''']
    metrics = [(str(data['public_projects']), 'PUBLIC PROJECTS'),
               (str(len(totals)), 'LANGUAGES'),
               (str(data['stars']), 'STARS EARNED'),
               (data['joined_year'], 'ON GITHUB SINCE')]
    for index, (value, label) in enumerate(metrics):
        x = 30 + index * 214
        body.append(f'<rect x="{x}" y="57" width="198" height="86" rx="9" fill="{surface}"/>')
        body.append(f'<text x="{x+18}" y="96" fill="{text}" font-size="29" font-weight="700">{escape(value)}</text>')
        body.append(f'<text x="{x+18}" y="122" fill="{muted}" font-size="10" letter-spacing="1" class="mono">{label}</text>')
    body.append(f'<text x="30" y="181" fill="{text}" font-size="16" font-weight="600">Most used languages</text>')
    # Two columns share the same linear percentage scale.
    for index, (language, size) in enumerate(items):
        column, row = index // max(rows, 1), index % max(rows, 1)
        x, y = 30 + column * 440, 210 + row * 34
        share = size / total * 100 if total else 0
        color = COLORS.get(language, COLORS['Other'])
        body.append(f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{color}"/>')
        body.append(f'<text x="{x+17}" y="{y}" fill="{text}" font-size="12">{escape(language)}</text>')
        body.append(f'<rect x="{x+115}" y="{y-9}" width="215" height="6" rx="3" fill="{surface}"/>')
        body.append(f'<rect x="{x+115}" y="{y-9}" width="{215*share/100:.3f}" height="6" rx="3" fill="{color}"/>')
        body.append(f'<text x="{x+395}" y="{y}" text-anchor="end" fill="{muted}" font-size="12" class="mono">{share:.2f}%</text>')
    if not items:
        body.append(f'<text x="30" y="220" font-size="13" fill="{muted}">No public language data yet.</text>')
    body.append(f'<path d="M30 {height-49}H870" stroke="{stroke}"/>')
    body.append(f'<text x="30" y="{height-24}" fill="{muted}" font-size="11">Public source bytes · Forks and this profile are excluded</text></svg>')
    return '\n'.join(body) + '\n'


def write_cards(data):
    output = ROOT / 'assets'
    output.mkdir(exist_ok=True)
    for theme in ['dark', 'light']:
        (output / f'stats-{theme}.svg').write_text(svg_card(data, theme == 'dark'), encoding='utf-8')
    (output / 'stats.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    snapshot = collect()
    write_cards(snapshot)
    print(f"Updated cards: {snapshot['public_projects']} public projects, {len(snapshot['languages_bytes'])} languages.")
