# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository is in the **scaffolding stage**. There is no application code yet — only the OpenSpec workflow infrastructure under `openspec/`, `.claude/`, and `.codex/`. New features should be specified through OpenSpec *before* code is written. When implementation begins, this file should be expanded with build/test/lint commands and architecture notes.

The directory name (`cli_mcp`) hints at the eventual scope (a CLI-based MCP server/client), but no design or proposal artifacts have been authored to confirm that. Treat the eventual product as undefined until a proposal lands in `openspec/changes/`.

## OpenSpec workflow

This project uses the `spec-driven` OpenSpec schema (see `openspec/config.yaml`). All non-trivial work flows through four stages, each backed by a slash command and a skill of the same name:

| Stage   | Command          | Skill                     | Output                                          |
|---------|------------------|---------------------------|-------------------------------------------------|
| Explore | `/opsx:explore`  | `openspec-explore`        | Thinking, diagrams — **no code, no files**      |
| Propose | `/opsx:propose`  | `openspec-propose`        | `proposal.md`, `design.md`, `tasks.md`          |
| Apply   | `/opsx:apply`    | `openspec-apply-change`   | Code changes; checks off boxes in `tasks.md`    |
| Archive | `/opsx:archive`  | `openspec-archive-change` | Moves change to `openspec/changes/archive/`     |

Identical skills live in `.codex/skills/` for the Codex CLI — keep the two trees in sync if you edit one.

### CLI commands the skills rely on

The skills shell out to the `openspec` binary. The recurring calls are:

```bash
openspec list --json                                  # list active changes
openspec new change "<name>"                          # scaffold openspec/changes/<name>/
openspec status --change "<name>" --json              # artifact graph + applyRequires
openspec instructions <artifact-id> --change "<name>" --json   # per-artifact template/rules
openspec instructions apply --change "<name>" --json  # contextFiles + task progress
```

The skill files (`.claude/skills/openspec-*/SKILL.md`) document the exact JSON fields each command returns and how to consume them — read the relevant SKILL.md before improvising on a workflow step.

### Workflow rules that aren't obvious from the code

- **Explore mode never writes application code.** Creating OpenSpec artifacts (proposals, designs, specs) is allowed; writing implementation is not. If the user asks to implement while in explore, redirect them to `/opsx:propose`.
- **`context` and `rules` from `openspec instructions` are constraints for you, not content for the artifact file.** Never copy `<context>` / `<rules>` / `<project_context>` blocks into the output.
- **Apply uses `contextFiles` from `openspec instructions apply --json` to discover artifacts.** Don't hardcode `proposal.md` / `design.md` / `tasks.md` paths — the set varies by schema.
- **Archive uses today's date for the target folder name** (`openspec/changes/archive/YYYY-MM-DD-<name>`) and refuses to overwrite an existing archive on the same day.
- **Mark tasks complete inline** in `tasks.md` (`- [ ]` → `- [x]`) immediately after finishing each one during apply — don't batch.

## Repository layout

```
openspec/
  config.yaml          # schema + optional project context/rules (currently empty)
  specs/               # canonical capability specs (empty until first sync)
  changes/             # active changes
    archive/           # completed changes, dated
.claude/
  commands/opsx/       # slash commands invoking the OpenSpec workflow
  skills/openspec-*/   # SKILL.md files driving each workflow stage
.codex/
  skills/openspec-*/   # Codex-CLI mirror of the same skills
```

Adding project-wide conventions (tech stack, style guide, domain notes) is done by populating the `context:` field of `openspec/config.yaml` — it is then surfaced to every artifact-generation step.
