"""Render self-contained GitHub profile cards. Requires Python 3.11+ and gh.

STATIC=1 renders final frames. OFFLINE=1 reuses the last public data snapshot.
No dependency installation, credentials in files, or network calls from SVGs.
"""
import base64
from collections import defaultdict
from datetime import date, timedelta
from html import escape
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
USER = 'Ziadtareks'
STATIC = os.environ.get('STATIC') == '1'
BLUE, RED, YELLOW = '#78b4ff', '#ff827a', '#edcc79'
BG, FG, MUTED = '#11161e', '#f1f3f6', '#9daaba'
FEATURED = [
    ('paysync-gateway', 'ANDROID', 'Kotlin', BLUE,
     '24/7 SMS payment verification for Egyptian mobile wallets.\nKotlin + Jetpack Compose. Wallet SMS in, HMAC-signed results out.'),
    ('WinVelo', 'WINDOWS', 'C#', RED,
     'A transparent, open-source tweak tool for Windows 10/11.\nBuilt for people who want control. Available in English and Arabic.'),
    ('GuildForge', 'DISCORD', 'Python', YELLOW,
     "Your Discord server structure, copied with one command.\nRoles, channels, permissions and settings. No messages or members."),
    ('prompt-stash', 'LIBRARY', 'Python', BLUE,
     '135 copy-paste prompts for debugging, work, study and more.\nPlain text, zero setup. Includes Arabic and Egyptian dialect.'),
]


def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], encoding='utf-8'))


def fetch():
    profile = gh('api', f'users/{USER}')
    repos = gh('repo', 'list', USER, '--limit', '100', '--json',
               'name,description,stargazerCount,primaryLanguage,url,pushedAt,isPrivate')
    # Never publish metadata of private repositories returned by a local login.
    repos = [r for r in repos if not r['isPrivate']]
    query = '''query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{totalContributions weeks{contributionDays{
        date contributionCount weekday}}}}}}'''
    result = gh('api', 'graphql', '-f', f'query={query}', '-f', f'login={USER}')
    calendar = result['data']['user']['contributionsCollection']['contributionCalendar']
    return {'username': profile['login'], 'name': profile['name'],
            'repos': repos, 'calendar': calendar}


def txt(x, y, value, size=16, color=FG, cls='', extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" class="{cls}" {extra}>{escape(str(value))}</text>'


def enter(body, delay=0, cls='rise'):
    return f'<g class="{cls}" style="animation-delay:{delay:.3f}s">{body}</g>'


def card(name, height, body, label, width=900):
    fonts = ''.join(f"@font-face{{font-family:{family};font-style:normal;font-weight:400;src:url(data:font/woff;base64,{base64.b64encode((ROOT / ('assets/fonts/' + file + '.woff')).read_bytes()).decode()}) format('woff')}}"
                    for family, file in [('Display', 'serif'), ('Body', 'sans')])
    animations = '' if STATIC else '''
      .rise {animation:rise .85s cubic-bezier(.2,.8,.2,1) both}
      .pop {transform-box:fill-box;transform-origin:center;animation:pop .5s ease both}
      .bar {transform-box:fill-box;transform-origin:center bottom;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}
      .swing {transform-box:fill-box;transform-origin:center bottom;animation:swing .9s cubic-bezier(.2,.8,.2,1) both}
      .print {animation:print .15s steps(1,end) both}
      .shine {animation:shine 7s 1.3s ease-in-out infinite}
      .arrow {animation:nudge 3s 3s ease-in-out infinite}
      .count-step {animation:counter .12s steps(1,end)}
      .count-final {animation:final var(--count-duration) steps(1,end) both}
      @keyframes rise {from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
      @keyframes pop {from{opacity:0;transform:scale(.15)}to{opacity:1;transform:scale(1)}}
      @keyframes grow {from{transform:scaleY(0)}to{transform:scaleY(1)}}
      @keyframes swing {0%{opacity:0;transform:perspective(600px) rotateX(25deg) translateY(14px)}75%{opacity:1;transform:translateY(-3px)}100%{opacity:1;transform:none}}
      @keyframes print {from{opacity:0}to{opacity:1}}
      @keyframes shine {0%,55%{transform:translateX(-950px)}85%,100%{transform:translateX(950px)}}
      @keyframes nudge {0%,70%,100%{transform:translateX(0)}85%{transform:translateX(4px)}}
      @keyframes counter {0%,99.9%{visibility:visible}100%{visibility:hidden}}
      @keyframes final {from{visibility:hidden}to{visibility:visible}}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.count-step{visibility:hidden!important}.count-final{visibility:visible!important}.shine{display:none}}
    '''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
    <title id="title">{escape(label)}</title>
    <defs><style>{fonts}text{{font-family:Body,Arial,sans-serif;font-weight:400}}.serif{{font-family:Display,Georgia,serif}}.count-step{{visibility:hidden}}{animations}</style>
    <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath></defs>
    <g clip-path="url(#frame)"><rect width="{width}" height="{height}" rx="20" fill="{BG}"/>
    <rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="19.5" fill="none" stroke="#2b3543"/>{body}</g></svg>'''
    (ROOT / 'cards' / (name + '.svg')).write_text(svg, encoding='utf-8')


def metrics(days):
    months = defaultdict(int)
    longest = current = 0
    for d in days:
        months[d['date'][:7]] += d['contributionCount']
        current = current + 1 if d['contributionCount'] else 0
        longest = max(longest, current)
    return months, longest, sum(d['contributionCount'] > 0 for d in days), max(days, key=lambda d: d['contributionCount'])


def main():
    for folder in ('cards', 'data'):
        (ROOT / folder).mkdir(exist_ok=True)
    cache = ROOT / 'data/contributions.json'
    data = json.loads(cache.read_text(encoding='utf-8')) if os.environ.get('OFFLINE') == '1' else fetch()
    repos = {r['name']: r for r in data['repos']}
    for name, *_ in FEATURED:
        if name not in repos:
            raise RuntimeError(f'Featured repository {name} is missing or private; refusing to generate a broken link')
    weeks = data['calendar']['weeks']
    days = [d for w in weeks for d in w['contributionDays']]
    assert days and all(d['contributionCount'] >= 0 for d in days)
    months, streak, active, busiest = metrics(days)
    total = sum(d['contributionCount'] for d in days)
    cache.write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    eyebrow = txt(40, 44, 'ZIADTAREKS / SELF-TAUGHT DEVELOPER', 13, BLUE)
    hero = eyebrow + enter(txt(38, 123, 'Ziad Tarek', 76, cls='serif'), .1)
    hero += enter(txt(42, 171, 'I build tools:', 25), .25)
    hero += enter(txt(42, 207, 'Android, Windows and Discord.', 25, MUTED), .4)
    hero += txt(42, 263, 'From an idea to something useful.', 15, MUTED)
    hero += '<path d="M650 58v190" stroke="#2b3543"/>'
    for i, row in enumerate(['+--------------+', '|              |', '|   &lt; ZT /&gt;    |', '|              |', '+--------------+']):
        # ASCII logo drawn in fixed cells; only the two embedded fonts are used.
        import html
        for j, ch in enumerate(html.unescape(row)):
            hero += enter(txt(691 + j * 10, 101 + i * 23, ch, 17, BLUE), .5 + i * .13, 'print')
    hero += txt(698, 254, 'BUILD. LEARN. REPEAT.', 11, MUTED)
    if not STATIC:
        hero += '<defs><linearGradient id="sheen"><stop stop-color="white" stop-opacity="0"/><stop offset=".5" stop-color="white" stop-opacity=".09"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient></defs><path class="shine" d="M0 0h90L0 310h-90z" fill="url(#sheen)"/>'
    card('hero', 310, hero, 'Ziad Tarek. Self-taught developer. I build tools: Android, Windows and Discord.')

    graph = txt(32, 42, 'A year of building', 29, cls='serif') + txt(868, 40, f'{total:,} contributions', 15, BLUE, extra='text-anchor="end"')
    max_count = max(1, max(d['contributionCount'] for d in days))
    pitch = min(15.5, 822 / len(weeks))
    last_month = None
    for col, week in enumerate(weeks):
        month = week['contributionDays'][0]['date'][:7]
        if month != last_month:
            graph += txt(32 + col * pitch, 72, date.fromisoformat(month + '-01').strftime('%b'), 10, MUTED)
            last_month = month
        for d in week['contributionDays']:
            count = d['contributionCount']
            fill = '#202b3a' if not count else ['#294970', '#3c6fa8', '#5693d6', BLUE][min(3, (count * 4 - 1) // max_count)]
            square = f'<rect x="{32+col*pitch:.2f}" y="{85+d["weekday"]*16}" width="12" height="12" rx="3" fill="{fill}"><title>{d["date"]}: {count} contributions</title></rect>'
            graph += enter(square, .7 + col * .018 + d['weekday'] * .012, 'pop')
    graph += txt(32, 226, f'{days[0]["date"]}  /  {days[-1]["date"]}  /  GitHub contribution calendar', 11, MUTED)
    card('contributions', 248, graph, f'Contribution calendar: {total} contributions from {days[0]["date"]} to {days[-1]["date"]}')

    activity = txt(32, 42, 'Consistency, in context', 29, cls='serif')
    activity += txt(868, 40, 'CONTRIBUTIONS / MONTH', 11, MUTED, extra='text-anchor="end"')
    best = max(months, key=months.get)
    peak = max(1, months[best])
    bw = 830 / len(months)
    for i, (month, count) in enumerate(sorted(months.items())):
        x, h = 38 + i * bw, 100 * count / peak
        activity += enter(f'<rect x="{x:.1f}" y="{179-h:.1f}" width="{bw-17:.1f}" height="{h:.1f}" rx="4" fill="{BLUE if month==best else "#304b6c"}"/>', 1.3 + i * .045, 'bar')
        if month == best:
            activity += enter(txt(x + (bw - 17) / 2, 179-h-10, count, 16, BLUE, extra='text-anchor="middle"'), 2.5, 'pop')
        activity += txt(x + (bw - 17) / 2, 201, date.fromisoformat(month+'-01').strftime('%b'), 11, MUTED, extra='text-anchor="middle"')
    activity += '<path d="M32 223h836" stroke="#2b3543"/>'
    for x, value, label in [(32, f'{streak} days', 'Longest streak'), (316, str(active), 'Active days'), (600, str(busiest['contributionCount']), 'Busiest day / '+busiest['date'])]:
        activity += enter(txt(x, 264, value, 28, BLUE) + txt(x, 289, label, 12, MUTED), 2)
    card('activity', 314, activity, f'Monthly activity. Longest streak {streak} days, {active} active days. Busiest day {busiest["date"]}: {busiest["contributionCount"]} contributions. First and last months may be partial.')

    for i, (name, category, language, color, description) in enumerate(FEATURED):
        repo = repos[name]
        stars = repo['stargazerCount']
        lang = (repo['primaryLanguage'] or {}).get('name', language)
        if i < 3:
            tile = f'<path d="M24 24h36" stroke="{color}" stroke-width="3"/>' + txt(24, 51, category, 12, color)
            tile += txt(22, 94, name, 26 if i == 0 else 32, cls='serif')
            tile += txt(24, 153, lang, 15, MUTED)
            # Each intermediate number has one discrete CSS frame; final value is the fallback.
            delay = 2.5 + i * .15
            values = sorted(set(round(stars * step / 9) for step in range(9))) if stars else []
            for step, value in enumerate(values):
                tile += txt(24, 210, value, 36, color, 'count-step', f'style="animation-delay:{delay + step * .12}s"')
            tile += txt(24, 210, stars, 36, color, 'count-final', f'style="--count-duration:{delay + len(values) * .12}s"')
            tile += txt(65, 209, 'GitHub stars', 12, MUTED)
            tile += '<g class="arrow">' + txt(244, 210, '>', 25, color) + '</g>'
            card(f'tile-{name}', 240, enter(tile, 2.1 + i * .16, 'swing'), f'{category}: {name}. {lang}. {stars} GitHub stars. Open repository.', 280)
        body = txt(32, 39, f'0{i+1} / {category}', 11, color)
        body += txt(32, 84, name, 36, cls='serif')
        body += txt(866, 82, '>', 28, color, 'arrow', 'text-anchor="end"')
        for line, value in enumerate(description.splitlines()):
            body += txt(33, 120 + line*25, value, 16, MUTED)
        body += txt(33, 182, f'{lang}    /    {stars} '+('star' if stars == 1 else 'stars'), 13, color)
        card(f'repo-{name}', 208, enter(body, 2.8 + i*.15), f'{name}. {description.replace(chr(10), " ")} {lang}. {stars} stars.')

    # Local achievement artwork; user-provided tiers, no third-party image calls.
    for slug, title, subtitle, color, symbol in [('pull-shark', 'Pull Shark', 'x2', BLUE, '><>'), ('yolo', 'YOLO', 'SHIP IT', YELLOW, '!')]:
        art = base64.b64encode((ROOT / f'assets/achievements/{slug}.png').read_bytes()).decode()
        body = f'<image x="1" y="1" width="54" height="54" href="data:image/png;base64,{art}"/>'
        body += txt(56, 25, title, 13) + txt(56, 43, subtitle, 10, color)
        card('badge-'+slug, 56, body, title+' '+subtitle, 164)

    readme = '<!-- Generated by scripts/render_readme_cards.py. SVGs contain all visual styling. -->\n\n'
    for file, alt in [('hero', 'Ziad Tarek - I build tools: Android, Windows and Discord.'), ('contributions', 'GitHub contribution calendar'), ('activity', 'Monthly contributions, longest streak, active days and busiest day')]:
        readme += f'<p align="center">\n  <img src="cards/{file}.svg" width="100%" alt="{alt}">\n</p>\n\n'
    readme += '<p align="center">\n'
    for name, category, *_ in FEATURED[:3]:
        # Adjacent links avoid text-space widths wrapping tile 3 on narrow GitHub pages.
        readme += f'<a href="{repos[name]["url"]}"><img src="cards/tile-{name}.svg" width="32.5%" alt="{category}: {name}"></a>'
    readme += '</p>\n\n'
    for name, *_ in FEATURED:
        readme += f'<p align="center">\n  <a href="{repos[name]["url"]}"><img src="cards/repo-{name}.svg" width="100%" alt="{name}: {escape(repos[name]["description"], quote=True)}"></a>\n</p>\n\n'
    readme += '<p align="center">\n'
    for slug, alt in [('pull-shark', 'Pull Shark x2'), ('yolo', 'YOLO')]:
        readme += f'  <a href="https://github.com/{USER}?tab=achievements"><img src="cards/badge-{slug}.svg" width="132" alt="{alt}"></a>\n'
    readme += '</p>\n'
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')
    print(f'Rendered {len(list((ROOT / "cards").glob("*.svg")))} cards; {total} contributions; {len(days)} days; STATIC={STATIC}')


if __name__ == '__main__':
    main()
