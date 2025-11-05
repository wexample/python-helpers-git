from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git import Remote, Repo
    from wexample_helpers.const.types import FileStringOrPath


def git_checkout_new_branch(
    branch: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Create and switch to a new branch using `git checkout -b <branch>` (compat)."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "checkout", "-b", branch],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_commit_all_with_message(
    message: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Commit all tracked changes with the provided message if any are present (callers should check)."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "commit", "-am", message],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_create_or_switch_branch(
    branch: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Try to create and switch to a branch; fallback to legacy checkout; finally switch existing.

    Order:
    - git switch -c <branch>
    - git checkout -b <branch>
    - git switch <branch>
    """
    try:
        git_switch_new_branch(branch, cwd=cwd, inherit_stdio=inherit_stdio)
    except Exception:
        try:
            git_checkout_new_branch(branch, cwd=cwd, inherit_stdio=inherit_stdio)
        except Exception:
            git_switch_branch(branch, cwd=cwd, inherit_stdio=inherit_stdio)


def git_current_branch(*, cwd: FileStringOrPath, inherit_stdio: bool = False) -> str:
    """Return the current branch name."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    return shell_run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        inherit_stdio=False,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()


def git_ensure_upstream(
    *, cwd: FileStringOrPath, default_remote: str = "origin", inherit_stdio: bool = True
) -> str:
    """Ensure current branch has an upstream. If missing, set to <default_remote>/<branch> and return it.

    Returns the upstream (e.g., "origin/main").
    """
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    cwd_resolved = file_resolve_path(cwd)
    branch = git_current_branch(cwd=cwd_resolved, inherit_stdio=False)
    upstream = git_get_upstream(cwd=cwd_resolved, inherit_stdio=False)
    if not upstream:
        try:
            # Try to set upstream to an existing remote branch.
            git_set_upstream(
                branch,
                cwd=cwd_resolved,
                remote=default_remote,
                inherit_stdio=inherit_stdio,
            )
            upstream = f"{default_remote}/{branch}"
        except Exception:
            # Remote branch likely does not exist yet; create it and set upstream in one go.
            shell_run(
                ["git", "push", "-u", default_remote, branch],
                inherit_stdio=inherit_stdio,
                cwd=cwd_resolved,
            )
            upstream = f"{default_remote}/{branch}"
    return upstream


def git_get_current_commit_hash(*, cwd: FileStringOrPath, short: bool = False) -> str:
    """Return the current commit hash (full or short)."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    cmd = ["git", "rev-parse"]
    if short:
        cmd.append("--short")
    cmd.append("HEAD")

    return shell_run(
        cmd, inherit_stdio=False, cwd=file_resolve_path(cwd)
    ).stdout.strip()


def git_get_upstream(*, cwd: FileStringOrPath, inherit_stdio: bool = False) -> str:
    """Return the symbolic upstream (e.g., origin/main) or empty string if none is set."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    try:
        return shell_run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            inherit_stdio=False,
            cwd=file_resolve_path(cwd),
        ).stdout.strip()
    except Exception:
        return ""


def git_has_changes_since_tag(
    tag: str, pathspec: str = ".", *, cwd: FileStringOrPath
) -> bool:
    """Return True if there are changes in pathspec since the given tag.

    Runs: git diff --quiet <tag> -- <pathspec> || echo CHANGED
    """
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    out = shell_run(
        [
            "bash",
            "-lc",
            f"git diff --quiet {tag} -- '{pathspec}' || echo CHANGED",
        ],
        inherit_stdio=False,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out == "CHANGED"


def git_has_index_changes(*, cwd: FileStringOrPath) -> bool:
    """Return True if there are staged (indexed) changes."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    # Always capture output here regardless of inherit_stdio so we can safely read stdout.
    out = shell_run(
        ["bash", "-lc", "git diff --cached --quiet || echo CHANGED"],
        inherit_stdio=False,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out == "CHANGED"


def git_has_uncommitted_changes(*, cwd: FileStringOrPath) -> bool:
    """Return True if there are any uncommitted changes (staged or unstaged)."""
    return git_has_index_changes(cwd=cwd) or git_has_working_changes(cwd=cwd)


def git_has_working_changes(*, cwd: FileStringOrPath) -> bool:
    """Return True if there are unstaged changes in tracked files."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    # Always capture output here regardless of inherit_stdio so we can safely read stdout.
    # When inherit_stdio=True, stdout would be None and .strip() would fail.
    out = shell_run(
        ["bash", "-lc", "git diff --quiet || echo CHANGED"],
        inherit_stdio=False,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out == "CHANGED"


def git_is_init(path: FileStringOrPath) -> bool:
    from git import InvalidGitRepositoryError, Repo
    from wexample_helpers.helpers.file import file_resolve_path

    path = file_resolve_path(path)

    if not path.exists():
        return False

    try:
        Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False


def git_last_tag_for_prefix(
    prefix: str, *, cwd: FileStringOrPath, inherit_stdio: bool = False
) -> str | None:
    """Return the last tag (sorted -V) matching the given glob prefix, e.g. "name/v*".

    Returns None if no tag matches.
    """
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    out = shell_run(
        [
            "bash",
            "-lc",
            f"git tag --list '{prefix}' | sort -V | tail -n1",
        ],
        inherit_stdio=False,
        cwd=file_resolve_path(cwd),
    ).stdout.strip()
    return out or None


def git_pull_rebase_autostash(
    *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Pull latest changes with rebase and autostash to preserve local modifications."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "pull", "--rebase", "--autostash"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_push_follow_tags(*, cwd: FileStringOrPath, inherit_stdio: bool = True) -> None:
    """Push the current branch to its upstream and follow tags."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "push", "--follow-tags"],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_push_tag(
    tag: str,
    *,
    cwd: FileStringOrPath,
    remote: str = "origin",
    inherit_stdio: bool = True,
) -> None:
    """Push a specific tag to the remote."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "push", remote, tag],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_remote_create_once(repo: Repo, name: str, url: str) -> Remote | None:
    try:
        repo.remote(name=name)
        return None
    except ValueError:
        return repo.create_remote(name, url)


def git_set_upstream(
    branch: str,
    *,
    cwd: FileStringOrPath,
    remote: str = "origin",
    inherit_stdio: bool = True,
) -> None:
    """Set the upstream of the current branch to remote/branch."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "branch", "--set-upstream-to", f"{remote}/{branch}", branch],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_switch_branch(
    branch: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Switch to an existing branch using `git switch <branch>`."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "switch", branch],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


# Branch switching/creation helpers
def git_switch_new_branch(
    branch: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Create and switch to a new branch using `git switch -c <branch>`."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "switch", "-c", branch],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_tag_annotated(
    tag: str, message: str, *, cwd: FileStringOrPath, inherit_stdio: bool = True
) -> None:
    """Create an annotated tag. Raises if the tag already exists."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    shell_run(
        ["git", "tag", "-a", tag, "-m", message],
        inherit_stdio=inherit_stdio,
        cwd=file_resolve_path(cwd),
    )


def git_tag_exists(
    tag: str, *, cwd: FileStringOrPath, inherit_stdio: bool = False
) -> bool:
    """Return True if a tag with the given name exists locally."""
    from wexample_helpers.helpers.file import file_resolve_path
    from wexample_helpers.helpers.shell import shell_run

    try:
        out = shell_run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
            inherit_stdio=False,
            cwd=file_resolve_path(cwd),
        ).stdout.strip()
        return len(out) > 0
    except Exception:
        return False
