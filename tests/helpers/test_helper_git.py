import os
import pytest
from git import Repo
from pathlib import Path
from typing import Generator

from wexample_helpers.helpers.git import (
    git_is_init,
    git_remote_create_once,
)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture providing a temporary directory."""
    yield tmp_path


@pytest.fixture
def git_repo(temp_dir: Path) -> Generator[Repo, None, None]:
    """Fixture providing an initialized git repository."""
    repo = Repo.init(temp_dir)
    yield repo


def test_git_is_init(temp_dir: Path, git_repo: Repo) -> None:
    # Test with initialized repository
    assert git_is_init(temp_dir) is True
    
    # Test with non-git directory
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()
    assert git_is_init(empty_dir) is False
    
    # Test with non-existent directory
    non_existent = temp_dir / "non_existent"
    assert git_is_init(non_existent) is False


def test_git_remote_create_once(git_repo: Repo) -> None:
    remote_name = "origin"
    remote_url = "https://github.com/test/repo.git"
    
    # Test creating new remote
    remote = git_remote_create_once(git_repo, remote_name, remote_url)
    assert remote is not None
    assert remote.name == remote_name
    assert remote.url == remote_url
    
    # Test attempting to create same remote again
    remote = git_remote_create_once(git_repo, remote_name, remote_url)
    assert remote is None  # Should return None for existing remote
