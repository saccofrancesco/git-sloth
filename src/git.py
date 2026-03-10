# Standard library imports
import subprocess

# Importing third-party librarie for CLI UX
from rich.console import Console

# Creating a global console to use in all the script
console: Console = Console()


def is_git_repository() -> bool:
    """
    Check whether the current directory is inside a Git repository.

    Returns:
        bool: True if inside a Git repository, otherwise False.
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,  # Raises CalledProcessError if command fails
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_staged_diff() -> str:
    """
    Retrieve the staged Git diff.

    This represents the changes currently added to the staging
    area via `git add`.

    Returns:
        str: The staged diff content.
        Returns an empty string if no changes are staged.
    """
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "diff", "--cached"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def create_commit(message: str) -> None:
    """
    Create a Git commit using the provided message.

    Args:
        message (str):
            The commit message to use.

    Raises:
        subprocess.CalledProcessError:
            If the `git commit` command fails.
    """
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "commit", "-m", message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If the commit failed, propagate the error
    if result.returncode != 0:
        console.print(f"Commit failed:\n{result.stderr.strip()}")
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd="git commit",
            output=result.stdout,
            stderr=result.stderr,
        )

    # Display Git's output on success
    console.print("Commit created successfully!")
    console.print(result.stdout.strip())
