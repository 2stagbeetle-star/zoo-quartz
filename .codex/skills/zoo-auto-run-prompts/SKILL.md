---
name: zoo-auto-run-prompts
description: Run all historical prompt workflows in this repository through one command, using Claude CLI, Codex CLI, or both. Use when the user asks to execute every existing prompt under `.claude/skills`, to run a full batch job, or to automate repeated prompt sweeps.
---

# Zoo Auto Run Prompts

## Overview

Use the shared runner script at `automation/run-all-prompts.ps1`.
Execute from repository root and choose `claude`, `codex`, or `both`.

## Workflow

1. Validate prerequisites.
- Confirm `automation/run-all-prompts.ps1` exists.
- Confirm `codex` is installed for `codex`/`both`.
- Confirm `claude` is installed for `claude`/`both`.

2. Run the batch job.
- Default:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both
```
- Codex only:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine codex
```
- Claude only:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine claude
```

3. Preview first when risk is unclear.
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both -DryRun
```

4. Review outputs.
- Check per-run logs in `_drafts/automation-logs/`.
- Check `summary-*.json` in the same directory for status by engine and skill.

5. Rerun failed slices with filters when needed.
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both -ExcludeSkills auto-run-all-prompts,deploy
```

## Notes

- Keep `auto-run-all-prompts` in the exclusion list to avoid self-recursion.
- Use `-StopOnError` when early abort is required.
- Use options in [runner-options.md](references/runner-options.md) for operational details.
