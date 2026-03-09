# Importing libraries
import argparse
import os
import sys
import subprocess
import openai


def parse_args():
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")
    list_parser = subparser.add_parser(
        "list", help="Generate multiple commit suggestions"
    )
    list_parser.add_argument(
        "-n", "--num", type=int, default=5, help="Number of commit suggestions"
    )
    return parser.parse_args()


def is_git_repository() -> bool:
    """
    Check whether the current working directory is inside a Git repository.

    Returns:
        True if inside a Git repository, False otherwise.
    """
    try:
        # Git command succeeds only if we are inside a repository
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,  # Suppress stdout
            stderr=subprocess.PIPE,  # Suppress stderr
        )
        return True
    except subprocess.CalledProcessError:
        # Command failed → not a Git repository
        return False


def get_staged_diff() -> str:
    """
    Retrieve the diff of staged (cached) changes.

    Returns:
        A string containing the staged changes diff.
        Returns an empty string if no changes are staged.
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["git", "diff", "--cached"],
        stdout=subprocess.PIPE,  # Capture stdout (diff content)
        stderr=subprocess.PIPE,  # Capture stderr (errors)
        text=True,  # Return output as a string
    )

    return result.stdout.strip()


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def create_commit(message: str) -> None:
    """
    Commit staged changes with the provided commit message.

    Args:
        message: The commit message to use.

    Exits:
        Exits the program if the commit fails.
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["git", "commit", "-m", message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        print("Commit failed:")
        print(result.stderr)
        sys.exit(1)
    else:
        print("Commit created successfully!")
        print(result.stdout)


def generate_commit_message(diff: str, n: int) -> list[str]:
    """
    Generate a Conventional Commit formatted message based on a Git diff.

    Args:
        diff: The diff string of staged changes.

    Returns:
        A string containing the proposed commit message.

    Exits:
        Exits the program if the OpenAI API key is not set.
    """
    api_key: str = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not set.")
        sys.exit(1)

    client: openai.OpenAI = openai.OpenAI(api_key=api_key)

    prompt: str = f"""
        You are an expert software engineer that writes precise commit messages
        following the Conventional Commits specification. 

        Generate {n} different commit messages for the following changes.

        Follow these rules:

        1. Use the Conventional Commits format: <type>(optional scope): <short summary>
        2. Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, 
        chore, revert
        3. The summary must:
        - Be in lowercase
        - Not end with a period
        - Be concise (max 72 characters)
        - Use imperative mood (e.g., "add", "fix", not "added", "fixes")
        4. If the change is breaking, add:
        - An exclamation mark after the type/scope (e.g., feat!:)
        - A "BREAKING CHANGE:" section in the footer
        5. Include a body separated by a blank line if additional context is needed.
        6. Return ONLY the commit messages as a numbered list.

        {diff}
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cost-efficient and good quality
        messages=[
            {
                "role": "system",
                "content": "You generate high quality git commit messages.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    # Extract message text, remove extra newlines, strip whitespace
    text: str = response.choices[0].message.content.replace("```", "").strip()
    commits: list[str] = list()
    for line in text.split("\n"):
        line: str = line.strip()
        if not line:
            continue
        if "." in line:
            line: str = line.split(".", 1)[1].strip()
        commits.append(line)
    return commits[:n]


def choose_commit(commits: list[str]) -> str:
    print("\nProposed commit changes:\n")
    for i, commit in enumerate(commits, 1):
        print(f"{i}. {commit}")
    while True:
        choice: str = input("\nSelect commit number (or 'q' to quit): ").strip()
        if choice == "q":
            sys.exit(0)
        if choice.isdigit():
            idx: int = int(choice) - 1
            if 0 <= idx <= len(commits):
                return commits[idx]
        print("Invalid choice.")


def main() -> None:
    """
    Main entry point of the application.

    Steps:
        1. Verify the current directory is a Git repository.
        2. Retrieve staged changes.
        3. Generate a commit message using OpenAI.
        4. Ask for user confirmation before committing.
        5. Commit the changes if confirmed.
    """
    args = parse_args()

    if not is_git_repository():
        print("Error: Not inside a Git repository.")
        sys.exit(1)

    diff: str = get_staged_diff()
    if not diff:
        print("No staged changes found.")
        sys.exit(0)

    if estimate_tokens(diff) > 6000:
        print("Max tokens (6k) exceeded.")
        sys.exit(0)

    if args.command == "list":
        commits = generate_commit_message(diff, args.num)
        message = choose_commit(commits)
    else:
        message = generate_commit_message(diff)

    print("\nSelected commit message:\n")
    print(message)

    confirm: str = input("Commit with this message? (y/n): ").strip().lower()
    if confirm != "y":
        print("Commit aborted.")
        sys.exit(0)

    create_commit(message)


# Execute the application only when run directly
if __name__ == "__main__":
    main()
