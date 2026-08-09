from crewai.tools import tool
from github import Github, Auth
import os
import tomllib
from dotenv import load_dotenv

load_dotenv()

@tool("Requirements File Fetcher")
def fetch_requirements_file(repo_name: str) -> str:
    """
    Fetches dependency info from a GitHub repo by checking requirements.txt first,
    then pyproject.toml (parsed properly, not with regex). repo_name format: 'owner/repo'.
    Returns a comma-separated list of package names, or a message if none are found.
    """
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # Try requirements.txt first
    try:
        file_content = repo.get_contents("requirements.txt")
        content = file_content.decoded_content.decode("utf-8")
        packages = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("~=")[0].strip()
            if pkg_name:
                packages.append(pkg_name)
        if packages:
            return ", ".join(packages)
    except Exception:
        pass

    # Try pyproject.toml with REAL parsing (not regex)
    try:
        file_content = repo.get_contents("pyproject.toml")
        content = file_content.decoded_content.decode("utf-8")
        data = tomllib.loads(content)

        packages = []

        # Standard PEP 621 format: [project] dependencies
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            pkg_name = dep.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("~=")[0].split("[")[0].strip()
            if pkg_name:
                packages.append(pkg_name)

        # Poetry format: [tool.poetry.dependencies]
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for pkg_name in poetry_deps.keys():
            if pkg_name.lower() != "python":  # skip the python version entry
                packages.append(pkg_name)

        if packages:
            return ", ".join(sorted(set(packages)))

    except Exception:
        pass

    return "No requirements.txt or pyproject.toml with parseable dependencies found in this repository."