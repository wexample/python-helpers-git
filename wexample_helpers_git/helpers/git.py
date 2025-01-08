from typing import Optional

from git import InvalidGitRepositoryError, Remote, Repo
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.helpers.file import file_resolve_path


def git_is_init(path: FileStringOrPath) -> bool:
    path = file_resolve_path(path)

    if not path.exists():
        return False

    try:
        Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False


def git_remote_create_once(repo: Repo, name: str, url: str) -> Optional[Remote]:
    try:
        repo.remote(name=name)
        return None
    except ValueError:
        return repo.create_remote(name, url)
