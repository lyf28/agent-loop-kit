import json
import subprocess


def parse_github_repo(repo_url: str) -> str:
    repo_url = repo_url.rstrip("/")

    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    if "github.com/" not in repo_url:
        raise ValueError("Only GitHub repositories are supported.")

    return repo_url.split("github.com/")[1]


def fetch_file(repo_url: str, path: str) -> str:
    repo = parse_github_repo(repo_url)

    command = [
        "gh",
        "api",
        f"repos/{repo}/contents/{path}",
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
            f"Failed to fetch {path}:\n{result.stderr}"
        )

    return result.stdout


def load_manifest(repo_url: str) -> dict:
    content = fetch_file(
        repo_url,
        "agent-loop.json",
    )

    return json.loads(content)


def load_agents(repo_url: str, manifest: dict) -> dict:
    agents = {}

    for name, path in manifest["agents"].items():
        print(f"Loading agent: {name}")

        agents[name] = fetch_file(
            repo_url,
            path,
        )

    return agents


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python remote_loader.py "
            "https://github.com/user/repo"
        )
        sys.exit(1)

    repo_url = sys.argv[1]

    manifest = load_manifest(repo_url)

    print("\nManifest:")
    print(json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
    ))

    agents = load_agents(
        repo_url,
        manifest,
    )

    print("\nLoaded agents:")

    for name, content in agents.items():
        print(f"\n--- {name} ---")
        print(content[:200])
        print("...")
