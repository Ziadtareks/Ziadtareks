# Profile cards

Run `python scripts/render_readme_cards.py` with GitHub CLI authenticated.
Only public repository metadata is saved. Contribution data is GitHub's rolling
calendar; first and last monthly bars may cover partial months. Streak means
longest consecutive run of active days in that calendar. Ties use the earliest
date/month. No usage or download counts are invented: tile counters show stars.

Use `STATIC=1` to render final frames without animations. Use `OFFLINE=1` to
reuse `data/contributions.json`. PowerShell example:

```powershell
$env:STATIC = '1'
python scripts/render_readme_cards.py
Remove-Item Env:STATIC
$env:OFFLINE = '1'
python scripts/render_readme_cards.py
```

Normal generation restores animations. Every animation is CSS-based and disabled
under `prefers-reduced-motion: reduce`; final content remains visible. Cards use
embedded fonts and never load external resources. Badges are custom local
representations of the profile owner's Pull Shark x2 and YOLO achievements.
Achievement artwork is vendored from the community archive
`Schweinepriester/github-profile-achievements` (Pull Shark bronze and YOLO),
downloaded through `gh api` and embedded into the local badges.

Fonts are DM Serif Display Regular and Inter Regular, from google/fonts (OFL).
They were fetched with `gh api`, Inter was instanced at opsz=14, wght=400 using
fontTools, and both were subset with `pyftsubset --unicodes=U+0020-007E --flavor=woff`.
The name tables report Regular and the italic flags are unset. Licenses are in
`assets/fonts/`. Runtime rendering uses only the Python standard library.

Daily refresh is at 06:23 UTC. To run manually after publishing:

```sh
gh workflow run update-readme.yml --repo Ziadtareks/Ziadtareks
```

The workflow needs no personal token; its GitHub token has `contents: write`.
