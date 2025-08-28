from __future__ import annotations

from git import InvalidGitRepositoryError, Remote, Repo

from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.helpers.file import file_resolve_path
from wexample_helpers.helpers.shell import shell_run


def git_is_init(path: FileStringOrPath) -> bool:
    path = file_resolve_path(path)

    if not path.exists():
        return False

    try:
        Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False


def git_remote_create_once(repo: Repo, name: str, url: str) -> Remote | None:
    try:
        repo.remote(name=name)
        return None
    except ValueError:
        return repo.create_remote(name, url)


def git_current_branch(*, cwd: FileStringOrPath, inherit_stdio: bool = False) -> str:
    """Return the current branch name."""
    return shell_run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()


def git_get_upstream(*, cwd: FileStringOrPath, inherit_stdio: bool = False) -> str:
    """Return the symbolic upstream (e.g., origin/main) or empty string if none is set."""
    try:
        return shell_run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            inherit_stdio=inherit_stdio,
            cwd=file_resolve_path(cwd),
        ).stdout.strip()
    except Exception:
        return ""


def git_set_upstream(
        branch: str,
        *,
        cwd: FileStringOrPath,
        remote: str = "origin",
        inherit_stdio: bool = True,
) -> None:
    """Set the upstream of the current branch to remote/branch."""
    shell_run(
        ["git", "branch", "--set-upstream-to", f"{remote}/{branch}", branch],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_pull_rebase_autostash(
        *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Pull latest changes with rebase and autostash to preserve local modifications."""
    shell_run(
        ["git", "pull", "--rebase", "--autostash"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_has_working_changes(*, cwd: FileStringOrPath, inherit_stdio: bool = True) -> bool:
    """Return True if there are unstaged changes in tracked files."""
    out = shell_run(
        ["bash", "-lc", "git diff --quiet || echo CHANGED"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out == "CHANGED"


def git_has_index_changes(*, cwd: FileStringOrPath, inherit_stdio: bool = True) -> bool:
    """Return True if there are staged (indexed) changes."""
    out = shell_run(
        ["bash", "-lc", "git diff --cached --quiet || echo CHANGED"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out == "CHANGED"


def git_commit_all_with_message(
        message: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Commit all tracked changes with the provided message if any are present (callers should check)."""
    shell_run(
        ["git", "commit", "-am", message],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_push_follow_tags(*, cwd: FileStringOrPath, inherit_stdio: bool = True) -> None:
    """Push the current branch to its upstream and follow tags."""
    shell_run(
        ["git", "push", "--follow-tags"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_ensure_upstream(
        *, cwd: FileStringOrPath, default_remote: str = "origin", inherit_stdio: bool = True
) -> str:
    """Ensure current branch has an upstream. If missing, set to <default_remote>/<branch> and return it.

    Returns the upstream (e.g., "origin/main").
    """
    cwd_resolved = file_resolve_path(cwd)
    branch = git_current_branch(cwd=cwd_resolved, inherit_stdio=False)
    upstream = git_get_upstream(cwd=cwd_resolved, inherit_stdio=False)
    if not upstream:
        git_set_upstream(
            branch, cwd=cwd_resolved, remote=default_remote, inherit_stdio=inherit_stdio
        )
        upstream = f"{default_remote}/{branch}"
    return upstream
