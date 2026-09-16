import json
import urllib.request


def github_raw_url(repo_url: str, path: str, branch: str = "main") -> str:
    repo_url = repo_url.rstrip("/")

    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    parts = repo_url.split("github.com/")

    if len(parts) != 2:
        raise ValueError("Only GitHub repositories are supported for now.")

    owner_repo = parts[1]

    return (
        f"https://raw.githubusercontent.com/"
        f"{owner_repo}/{branch}/{path}"
    )


def load_manifest(repo_url: str) -> dict:
    url = github_raw_url(
        repo_url,
        "agent-loop.json",
    )

    print(f"Loading manifest from:\n{url}\n")

    with urllib.request.urlopen(url) as response:
        data = response.read().decode("utf-8")

    return json.loads(data)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python remote_loader.py "
            "https://github.com/user/agent-loop-kit"
        )
        sys.exit(1)

    manifest = load_manifest(sys.argv[1])

    print(json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
    ))
