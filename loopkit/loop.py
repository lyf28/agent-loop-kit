from pathlib import Path
import subprocess
import sys
import datetime


ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"


def load_agent(name: str) -> str:
    path = AGENTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def run_codex(prompt: str, cwd: Path, read_only: bool = False) -> str:
    command = ["codex", "exec"]

    if read_only:
        command += ["--sandbox", "read-only"]

    command.append(prompt)

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = result.stdout

    if result.stderr:
        output += "\n" + result.stderr

    return output


def save_log(run_dir: Path, filename: str, content: str):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / filename).write_text(content, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print('Usage: python loop.py "task"')
        sys.exit(1)

    task = sys.argv[1]
    repo = Path.cwd()

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = repo / ".agent-loop" / "runs" / timestamp

    planner = load_agent("planner")
    implementer = load_agent("implementer")
    reviewer = load_agent("reviewer")

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

    max_rounds = 5

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
    main()
