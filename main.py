# Importing libraries
import subprocess


# Checks whether the current working directory is inside a Git repository
def is_git_repository() -> bool:
    """
    Returns True if the current directory is inside a Git working tree,
    otherwise returns False.
    """
    try:
        # Run a Git command that succeeds only if we are inside a repository.
        # If the command fails, subprocess will raise CalledProcessError
        # because check=True is set.
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,  # Suppress standard output
            stderr=subprocess.PIPE,  # Suppress error output
        )
        return True

    except subprocess.CalledProcessError:
        # The command failed, meaning we are not inside a Git repository
        return False


# Main entry point of the application
def main() -> None:
    if not is_git_repository():
        print("Not inside a Git repository...")
    print("Git repository detected!")
