AGENTS.md

# Coding Guidelines (Andrej Karpathy / ECC)

## Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Every changed line should trace directly to the user's request.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

## Security First

Before any commit:
- No hardcoded secrets (API keys, passwords, tokens)
- All user inputs validated at system boundaries
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitized HTML)
- Error messages don't leak sensitive data

## Agent Orchestration (ECC)

Use agents proactively:
- Complex feature → **planner** first
- Code written/modified → **code-reviewer** immediately
- Bug fix or new feature → **tdd-guide**
- Architectural decision → **architect**
- Security-sensitive code → **security-reviewer**

## Git Workflow

Commit format: `<type>: <description>`
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

# LLM Council (separate app — branch: LLM-Council)

Multi-LLM deliberation system: 3-stage pipeline where multiple models answer
in parallel, peer-rank each other anonymously, then a chairman synthesizes.

Backend: FastAPI on port 8001. Frontend: React/Vite on port 5173.
Run: `python -m backend.main` from project root.
See branch `LLM-Council` for full source.

# currentDate
Today's date is 2026-04-20.
