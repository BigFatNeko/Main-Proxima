# Vendored: caveman (on-demand skill)

Invokable terse-output mode. **Off until you call it.**

- Invoke : `/caveman` (default level `full`) or
  `/caveman lite|full|ultra|wenyan-lite|wenyan-full|wenyan-ultra`
- Stop   : say "normal mode" / "stop caveman"
- Scope  : compresses output prose only — code, commits, PRs, and reasoning stay normal.

## Provenance
- Upstream: https://github.com/JuliusBrussee/caveman  (MIT, © 2026 Julius Brussee)
- Pinned commit: `655b7d9`
- Vendored: the **core `caveman` skill only** (`SKILL.md` + `README.md`).

## Intentionally NOT included
- The upstream SessionStart / UserPromptSubmit Node hooks — those force caveman
  ON every session. Omitted so this stays strictly on-demand.
- The extra skills (`caveman-commit`, `caveman-review`, `caveman-help`,
  `caveman-stats`, `caveman-compress`, `cavecrew`). Ask to add any of them.
