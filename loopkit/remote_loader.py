import json
import subprocess


def parse_github_repo(repo_url: str):
    repo_url = repo_url.rstrip("/")

    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    if "github.com/" not in repo_url:
        raise ValueError("Only GitHub repositories are supported.")

    return repo_url.split("github.com/")[1]


def load_manifest(repo_url: str) -> dict:
    repo = parse_github_repo(repo_url)

    command = [
        "gh",
        "api",
        f"repos/{repo}/contents/agent-loop.json",
        "-H",
        "Accept: application/vnd.github.raw+json",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to load harness manifest:\n{result.stderr}"
        )

    return json.loads(result.stdout)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python remote_loader.py "
            "https://github.com/user/repo"
        )
        sys.exit(1)

    manifest = load_manifest(sys.argv[1])

    print(json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
    ))
