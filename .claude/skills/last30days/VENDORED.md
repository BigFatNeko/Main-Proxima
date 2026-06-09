# Vendored: last30days

This directory is a vendored copy of the **last30days** Claude Code skill, so it
is permanently available as `/last30days` in every session of this repo —
including Claude Code on the web, where the interactive `/plugin` installer is
unavailable and the container is reset each session.

- Upstream: https://github.com/mvanhorn/last30days-skill
- Version: `3.3.2`
- Pinned commit: `122158415ae421da83e739f2668032f6bc78d39c`
- License: MIT (see `./LICENSE`) — © 2026 Matt Van Horn
- Vendored: 2026-06-09

## What it does
Researches any topic across Reddit, X, YouTube, TikTok, Instagram, Hacker News,
Polymarket, GitHub, Bluesky, the web, and more from the last 30 days, scores by
real engagement, and synthesizes a cited brief. Invoke with `/last30days <topic>`.

## What differs from upstream
- Packaged as a **project skill** under `.claude/skills/last30days/` (upstream
  ships it as a plugin). The engine resolves its scripts relative to `SKILL.md`,
  so this layout runs identically.
- Excluded `assets/` (~14 MB of upstream README/demo media — unused at runtime).
- Excluded `__pycache__/` and `*.pyc`.
- Added `hooks/check-config.sh` (upstream `hooks/scripts/check-config.sh`), wired
  as a SessionStart status line via the repo's `.claude/settings.json`.
- **No engine source was modified.**

## Requirements & configuration
- **Python 3.12+** only. The engine has **zero pip dependencies** (its libs are
  bundled under `scripts/lib/`), so nothing to install.
- API keys for full coverage: copy `.claude/last30days.env.example` to
  `.claude/last30days.env` (gitignored) and fill it in, **or** set the same
  variable names as environment variables (required on Claude Code on the web).

## Verify it works (no keys/network needed)
```bash
python3.12 .claude/skills/last30days/scripts/last30days.py --diagnose
python3.12 .claude/skills/last30days/scripts/last30days.py "ai video tools" --mock --emit compact
```

## Updating
Re-clone upstream at the desired tag, re-copy `skills/last30days/` here
(excluding `assets/`, `__pycache__/`, `*.pyc`), refresh `hooks/check-config.sh`
and `LICENSE`, then bump the version/commit above.
