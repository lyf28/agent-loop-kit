# agent-loop-kit

`agent-loop-kit` runs a planner, implementer, and reviewer Codex loop from a
remote GitHub-hosted harness. The local repository is the workspace being
changed; the remote harness supplies `agent-loop.json` and the agent prompt
files that control the loop.

## How It Works

1. Load `agent-loop.json` from the remote GitHub repository.
2. Fetch the planner, implementer, and reviewer prompt files named by the
   manifest.
3. Run Codex once with the planner prompt to produce an implementation plan.
4. Run Codex with the implementer prompt to make changes in the local
   workspace.
5. Run Codex with the reviewer prompt to inspect the current repository state.
6. Repeat implementation and review until the reviewer returns
   `LOOP_STATUS: PASS` or `loop.max_rounds` is reached.
7. Save plans, implementation output, and review output under
   `.agent-loop/runs/<timestamp>/`.

## Requirements

- Python
- Codex CLI available as `codex`
- GitHub CLI available as `gh`
- Authenticated GitHub access for the remote harness repository

## Usage

### Windows MVP install

From PowerShell in this repository, install the user-local `agent-loop`
command by running the script directly:

```powershell
.\bootstrap.ps1
```

The command is available immediately in that same PowerShell session. Run the
agent loop from the repository you want Codex to work on:

```powershell
agent-loop "your task"
```

The installer also updates your persistent User PATH. Already-running parent
applications such as VS Code may need to be restarted before newly created
terminals inherit that PATH update.

If the harness repository is not this kit's `origin` remote, pass it explicitly:

```powershell
.\bootstrap.ps1 -HarnessUrl https://github.com/user/repo
```

### Direct Python usage

Run the full agent loop from the root of the repository you want Codex to work
on:

```sh
python path/to/agent-loop-kit/loopkit/loop.py https://github.com/user/repo "your task"
```

Smoke test remote harness loading:

```sh
python path/to/agent-loop-kit/loopkit/remote_loader.py https://github.com/user/repo
```

The remote harness must be a GitHub repository containing `agent-loop.json` and
all prompt files referenced by that manifest.

## Configuration

Loop configuration lives in the remote harness repository's
`agent-loop.json`:

- `agents` maps role names to prompt file paths. The default roles are
  `planner`, `implementer`, and `reviewer`.
- `loop.max_rounds` limits how many implementation and review cycles can run
  after planning.
- `loop.flow` records the intended planner, implementer, reviewer order.

## Repository Structure

- `agent-loop.json` - remote harness manifest for agent prompt paths and loop
  settings.
- `loopkit/loop.py` - main CLI loop runner.
- `loopkit/remote_loader.py` - GitHub manifest and prompt loader.
- `agents/*.md` - default remote harness planner, implementer, and reviewer
  prompt templates.
- `.agent-loop/runs/` - generated run logs in the target workspace.

## Operational Notes

- Planner and reviewer Codex runs use the read-only sandbox.
- Implementer Codex runs use the workspace-write sandbox.
- Logs are written under `.agent-loop/runs/<timestamp>/`.
- Only GitHub-hosted harness repositories are supported.

## Validation

Verify that the remote manifest and prompt files can be loaded:

```sh
python path/to/agent-loop-kit/loopkit/remote_loader.py https://github.com/user/repo
```

Run an end-to-end check:

```sh
python path/to/agent-loop-kit/loopkit/loop.py https://github.com/user/repo "test task"
```

For documentation-only changes, you can also confirm the Python files still
compile:

```sh
python -m py_compile loopkit/loop.py loopkit/remote_loader.py
```
