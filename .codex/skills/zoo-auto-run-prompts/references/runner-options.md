# Runner Options

`automation/run-all-prompts.ps1` supports the parameters below.

## Parameters

- `-Engine claude|codex|both`
  - Select execution target.
  - Default: `both`.

- `-SkillDirectory <path>`
  - Prompt skill source directory.
  - Default: `.claude/skills`.

- `-LogDirectory <path>`
  - Output directory for logs and summary JSON.
  - Default: `_drafts/automation-logs`.

- `-ExcludeSkills <name1,name2,...>`
  - Exclude skill base names from execution.
  - Default includes `auto-run-all-prompts` to avoid recursion.

- `-DryRun`
  - Print run targets without executing any prompt.

- `-StopOnError`
  - Abort batch at first failure.
  - Without this flag, continue running and report failures in summary.

## Example Commands

```powershell
# Full run on both engines
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both

# Codex only and stop on first error
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine codex -StopOnError

# Dry run with exclusions
powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\run-all-prompts.ps1 -Engine both -DryRun -ExcludeSkills auto-run-all-prompts,deploy
```
