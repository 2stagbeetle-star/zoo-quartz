# Auto Run All Prompts

## Purpose
Run every existing prompt skill under `.claude/skills/*.md` automatically, with support for both Claude CLI and Codex CLI.

## Default Run
From the repository root, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both
```

## Common Variants
- Claude only:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine claude
```
- Codex only:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine codex
```
- Preview without execution:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both -DryRun
```
- Exclude specific skills:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both -ExcludeSkills auto-run-all-prompts,deploy
```

## Output
- Per-run logs: `_drafts/automation-logs/`
- Machine-readable summary JSON: `_drafts/automation-logs/summary-*.json`
