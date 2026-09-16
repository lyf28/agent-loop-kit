from pathlib import Path
import subprocess
import sys
import datetime

from remote_loader import load_manifest, load_agents


def run_codex(prompt: str, cwd: Path, read_only: bool = False) -> str:
    command = [
        "cmd",
        "/c",
        "codex",
        "exec",
    ]

    if read_only:
        command += [
            "--sandbox",
            "read-only",
        ]

    # "-" means: read the prompt from stdin
    command.append("-")

    result = subprocess.run(
        command,
        cwd=cwd,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if result.returncode != 0:
        raise RuntimeError(
            "Codex execution failed.\n"
            f"Exit code: {result.returncode}\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}"
        )

    return stdout


def save_log(run_dir: Path, filename: str, content: str):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / filename).write_text(content, encoding="utf-8")


def main():
    if len(sys.argv) < 3:
        print(
            'Usage: python loop.py '
            '<harness-url> "task"'
        )
        sys.exit(1)

    harness_url = sys.argv[1]
    task = sys.argv[2]
    repo = Path.cwd()

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = repo / ".agent-loop" / "runs" / timestamp

    print("🌐 Loading remote harness...")

    manifest = load_manifest(harness_url)
    agents = load_agents(harness_url, manifest)

    planner = agents["planner"]
    implementer = agents["implementer"]
    reviewer = agents["reviewer"]

    max_rounds = manifest["loop"]["max_rounds"]

    print("\n🧠 Planning...\n")

    plan_prompt = f"""
{planner}

USER TASK:
{task}
"""

    plan = run_codex(
        plan_prompt,
        cwd=repo,
        read_only=True,
    )

    save_log(run_dir, "plan.md", plan)

    print(plan)

    feedback = ""

    for round_number in range(1, max_rounds + 1):

        print(f"\n{'=' * 50}")
        print(f"🔨 Round {round_number}")
        print(f"{'=' * 50}\n")

        implement_prompt = f"""
{implementer}

ORIGINAL TASK:
{task}

IMPLEMENTATION PLAN:
{plan}

REVIEWER FEEDBACK:
{feedback if feedback else "None yet."}
"""

        implementation = run_codex(
            implement_prompt,
            cwd=repo,
        )

        save_log(
            run_dir,
            f"round-{round_number}-implementation.md",
            implementation,
        )

        print("\n🔍 Reviewing...\n")

        review_prompt = f"""
{reviewer}

ORIGINAL TASK:
{task}

IMPLEMENTATION PLAN:
{plan}

Review the CURRENT repository state.
"""

        review = run_codex(
            review_prompt,
            cwd=repo,
            read_only=True,
        )

        save_log(
            run_dir,
            f"round-{round_number}-review.md",
            review,
        )

        print(review)

        if "LOOP_STATUS: PASS" in review:
            print(
                f"\n✅ Loop completed successfully "
                f"after {round_number} round(s)."
            )
            return

        feedback = review

    print(
        f"\n⚠️ Reached maximum of {max_rounds} rounds."
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n\n⛔ Loop cancelled by user.")
        sys.exit(130)

    except Exception as error:
        print("\n\n❌ Agent loop failed:")
        print(error)
        sys.exit(1)
