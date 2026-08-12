#!/usr/bin/env python3
"""
Write the statistics strip into index.html, between its fences.

WHY THE NUMBERS ARE BAKED IN AND NOT FETCHED IN THE BROWSER. This site's support
page states it makes no third-party requests. Calling api.github.com from the
page would put every visitor's IP address on GitHub's servers and make that
claim false. Fetching at build time keeps the promise; the cost is that the
numbers are only true on the day they were written, which is what the weekly
workflow is for.

🔥 NOTHING HERE IS TYPED IN BY HAND. An earlier version of this file carried
"60k lines of C++" as a literal, and the real figure was 75.0k -- a made-up
number, live on a public page. Every value is now either read from the GitHub
API or counted off the QuickImageViewer source tree, exactly the way that
project's own tools/build-site.py does it. If a figure cannot be computed it is
dropped rather than guessed.

THE SOURCE TREE. Code facts -- lines, formats, shortcuts -- cannot come from the
API; they are counted by walking the repository. Locally that is the working
copy next door. In CI the workflow checks the public repo out into _qiv/ and
passes --qiv-src. If neither is there those three pills are simply absent.

WHY THIS LIVES HERE AND NOT IN THE QuickImageViewer REPO. That repo has its own
stats workflow, but a workflow can only push to its own repository without a
personal access token stored as a secret. A second small script with no
credentials beats a cross-repo token.

Usage:  python tools/build-stats.py [--qiv-src DIR] [--check]
"""

import argparse
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

REPO = 'icyhoty2k/QuickImageViewer'
API = 'https://api.github.com/repos/' + REPO
REPO_URL = 'https://github.com/' + REPO
SITE = 'https://icyhoty2k.github.io/QuickImageViewer/'

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(HERE, 'index.html')

START = '<!-- STATS-START -->'
END = '<!-- STATS-END -->'

# Where the QuickImageViewer checkout usually is on this machine.
DEFAULT_QIV = r'I:\30_CppSources\QuickImageViewer'


# --------------------------------------------------------------------------
# Icons. Inline SVG, not emoji.
#
# QuickImageViewer's strip uses emoji; this one does not, for the same reason
# its navigation stopped: an emoji is drawn by whoever made the font, so a row
# of twelve is twelve illustration styles that match neither each other nor
# anything else on the page.
#
# Line art in the same family as the nav icons and the hero glyph row, so the
# whole site draws from one set. currentColor throughout, so hover recolours
# them for free.
# --------------------------------------------------------------------------

def _svg(paths):
    return ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
            + paths + '</svg>')


ICON = {
    'download': _svg('<path d="M12 3v11m0 0 4-4m-4 4-4-4"/>'
                     '<path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16"/>'),
    'star': _svg('<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1.1 5.9-5.3-2.9-5.3 2.9 1.1-5.9'
                 'L3.5 9.7l5.9-.8z"/>'),
    'eye': _svg('<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/>'
                '<circle cx="12" cy="12" r="2.8"/>'),
    'rocket': _svg('<path d="M13.5 3.5c4 1 7 4 8 8-2.5 2.5-5.5 3.5-8 3.5-1.5-3-3-4.5-6-6'
                   '0-2.5 1-5.5 3.5-8 1.3.3 1.8.4 2.5.5Z"/>'
                   '<path d="M8 16c-1.5 1.5-1.5 4-1.5 4s2.5 0 4-1.5"/>'),
    'tag': _svg('<path d="M3.5 11.2V4.5a1 1 0 0 1 1-1h6.7a1 1 0 0 1 .7.3l8.1 8.1a1 1 0 0 1 0 1.4'
                'l-6.7 6.7a1 1 0 0 1-1.4 0L3.8 11.9a1 1 0 0 1-.3-.7Z"/>'
                '<circle cx="7.8" cy="7.8" r="1.3"/>'),
    'clock': _svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
    'box': _svg('<path d="M20.5 7.8v8.4a1 1 0 0 1-.5.9l-7.5 4.2a1 1 0 0 1-1 0L4 17.1a1 1 0 0 1'
                '-.5-.9V7.8a1 1 0 0 1 .5-.9L11.5 2.7a1 1 0 0 1 1 0L20 6.9a1 1 0 0 1 .5.9Z"/>'
                '<path d="m3.7 7.4 8.3 4.6 8.3-4.6M12 21.5V12"/>'),
    'image': _svg('<rect x="3" y="4.5" width="18" height="15" rx="2"/>'
                  '<circle cx="8.3" cy="9.3" r="1.6"/>'
                  '<path d="m3.6 17.4 4.9-4.6 3.4 3.2 3.1-2.7 5.4 4.7"/>'),
    'keyboard': _svg('<rect x="2.5" y="6" width="19" height="12" rx="2"/>'
                     '<path d="M6 9.5h.01M9.5 9.5h.01M13 9.5h.01M16.5 9.5h.01'
                     'M6 13h.01M9.5 13h.01M13 13h.01M16.5 13h.01M8 16h8"/>'),
    'code': _svg('<path d="m8.5 8.5-4 3.5 4 3.5M15.5 8.5l4 3.5-4 3.5M13.5 5.5l-3 13"/>'),
    'licence': _svg('<path d="M6 3.5h8l4 4v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1Z"/>'
                    '<path d="M14 3.5v4h4M8.5 12.5h7M8.5 16h5"/>'),
    'monitor': _svg('<rect x="2.5" y="4" width="19" height="12.5" rx="1.8"/>'
                    '<path d="M12 16.5v3M8 19.5h8"/>'),
}


def fetch(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'icyhoty2k-site'}
    # Unauthenticated the API allows 60 requests an hour per IP, plenty for one
    # person locally. On a CI runner that IP is shared, so the token matters
    # there -- but its absence is not an error.
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def read(path):
    with io.open(path, encoding='utf-8', errors='ignore') as f:
        return f.read()


def human(n):
    return '{:,}'.format(n)


def code_facts(src_root):
    """
    Lines, formats and shortcuts, counted off the source tree.

    Identical method to QuickImageViewer's own tools/build-site.py, so the two
    strips cannot disagree -- which they did: this file once claimed 60k lines
    against the real 75.0k.
    """
    out = {}
    src = os.path.join(src_root, 'src')
    if not os.path.isdir(src):
        return out

    loc = 0
    for dirpath, _, names in os.walk(src):
        for n in names:
            if n.endswith(('.cpp', '.h', '.hpp')):
                loc += read(os.path.join(dirpath, n)).count('\n')
    if loc:
        out['loc'] = '%.1fk' % (loc / 1000.0)

    helpwnd = os.path.join(src, 'UI', 'FloatingPanels', 'HelpWnd.cpp')
    if os.path.exists(helpwnd):
        n = len(re.findall(r'\bAdd\(', read(helpwnd)))
        if n:
            out['shortcuts'] = str(n)

    consts = os.path.join(src, 'Platform', 'Constants.h')
    if os.path.exists(consts):
        n = len(set(re.findall(r'L"\.([a-z0-9]{2,5})"', read(consts))))
        if n:
            out['formats'] = str(n)
    return out


def gather(qiv_src):
    repo = fetch(API)
    releases = fetch(API + '/releases?per_page=100')

    downloads = 0
    exe_mb = 0.0
    for rel in releases:
        for asset in rel.get('assets') or []:
            downloads += asset.get('download_count') or 0
    for rel in releases:
        if rel.get('prerelease'):
            continue
        for asset in rel.get('assets') or []:
            if asset.get('name', '').lower().endswith('.exe'):
                exe_mb = (asset.get('size') or 0) / 1048576.0
                break
        if exe_mb:
            break

    latest = next((r.get('tag_name') for r in releases if not r.get('prerelease')), '')

    updated = ''
    try:
        pushed = datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
        days = (datetime.now(timezone.utc).replace(tzinfo=None) - pushed).days
        updated = ('today' if days <= 0 else
                   'yesterday' if days == 1 else
                   '%d days ago' % days if days < 31 else
                   '%d months ago' % (days // 30))
    except Exception:
        pass

    live = {
        'downloads': downloads,
        'stars': repo.get('stargazers_count') or 0,
        'watching': repo.get('subscribers_count') or 0,
        'releases': len(releases),
        'latest': latest,
        'updated': updated,
        'exe_mb': exe_mb,
        # "AGPL-3.0" is the SPDX identifier; the desktop strip says "AGPLv3" and
        # the two sitting side by side saying different things about the same
        # licence looks like one of them is wrong.
        'licence': (((repo.get('license') or {}).get('spdx_id') or '')
                    .replace('-only', '').replace('-3.0', 'v3').replace('-2.0', 'v2')),
    }
    live.update(code_facts(qiv_src))
    return live


def render(s):
    """
    Value first, then label, because that is the reading order: "406 downloads".
    An entry whose value is missing or zero is DROPPED, not printed -- "0 forks"
    on a page meant to persuade argues the opposite case for you.
    """
    rows = [
        ('download', human(s['downloads']), 'downloads', REPO_URL + '/releases', s['downloads']),
        ('star', human(s['stars']), 'stars', REPO_URL + '/stargazers', s['stars']),
        ('eye', human(s['watching']), 'watching', REPO_URL + '/watchers', s['watching']),
        ('rocket', str(s['releases']), 'releases', REPO_URL + '/releases', s['releases']),
        ('tag', s['latest'], 'latest release', REPO_URL + '/releases/latest', s['latest']),
        ('clock', s['updated'], 'last updated', REPO_URL + '/commits', s['updated']),
        ('box', '%.1f MB' % s['exe_mb'] if s['exe_mb'] else '', 'single .exe',
         REPO_URL + '/releases/latest', s['exe_mb']),
        ('image', s.get('formats', ''), 'image formats', SITE + '#format-support',
         s.get('formats')),
        ('keyboard', s.get('shortcuts', ''), 'keyboard shortcuts', SITE + 'shortcuts.html',
         s.get('shortcuts')),
        ('code', s.get('loc', ''), 'lines of C++', REPO_URL, s.get('loc')),
        ('licence', s['licence'], 'licence', REPO_URL + '/blob/main/LICENSE', s['licence']),
        ('monitor', 'Windows', '10 &amp; 11', SITE, 'Windows'),
    ]

    out = [START,
           '<!-- Generated by tools/build-stats.py. Do not edit between the fences. -->',
           '<div class="statstrip">']
    for icon, value, label, href, present in rows:
        if not present or not value:
            continue
        out.append('    <a class="stat" href="%s">%s'
                   '<span class="stat-value">%s</span>'
                   '<span class="stat-label">%s</span></a>'
                   % (href, ICON[icon], value, label))
    out.append('</div>')
    out.append(END)
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--qiv-src', default=DEFAULT_QIV,
                    help='QuickImageViewer checkout, for the code facts')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    text = io.open(INDEX, encoding='utf-8').read()
    if START not in text or END not in text:
        sys.exit('ERROR: fences %s / %s not found in index.html' % (START, END))

    try:
        stats = gather(args.qiv_src)
    except Exception as e:
        # Offline or rate-limited is not a failure. Leaving yesterday's numbers
        # in place is strictly better than blanking the strip.
        print('could not reach the API (%s) - leaving the strip alone' % type(e).__name__)
        return

    if 'loc' not in stats:
        print('note: no source tree at %s - the code pills are omitted' % args.qiv_src)

    block = render(stats)
    current = text[text.index(START):text.index(END) + len(END)]
    count = block.count('class="stat"')

    if current == block:
        print('current - %d pills' % count)
        return
    if args.check:
        print('STALE - would write %d pills' % count)
        sys.exit(1)

    io.open(INDEX, 'w', encoding='utf-8', newline='\n').write(text.replace(current, block))
    print('wrote - %d pills (%s downloads, %s lines)'
          % (count, human(stats['downloads']), stats.get('loc', '?')))


if __name__ == '__main__':
    main()
