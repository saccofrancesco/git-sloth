"""
Gitsloth

A CLI tool that analyzes staged Git changes and generates
Conventional Commit messages using the OpenAI API.
"""

# Importing libraries
import argparse
import os
import sys
import subprocess
import questionary
from halo import Halo
import openai

# Store the current commit message template for commits generation
COMMIT_PROMPT_TEMPLATE: str = """
You are an expert software engineer that writes precise commit messages
following the Conventional Commits specification.

Generate {n} different commit messages for the following changes.

Rules:

1. Use the Conventional Commits format:
   <type>(optional scope): <short summary>

2. Allowed types:
   feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

3. The summary must:
   - Be lowercase
   - Use imperative mood (e.g., "add", "fix")
   - Not end with a period
   - Be concise (max 72 characters)

4. If the change is breaking:
   - Add an exclamation mark after the type/scope (e.g., feat!:)
   - Add a "BREAKING CHANGE:" footer

5. Include a body separated by a blank line if additional context is needed.

Return ONLY the commit messages as a numbered list.

Changes:
{diff}
"""


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.

    Returns:
        The parsed command-line arguments.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate AI-powered Git commit messages."
    )

    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser(
        "list", help="Generate multiple commit suggestions"
    )

    list_parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=5,
        help="Number of commit suggestions to generate",
    )

    return parser.parse_args()


def is_git_repository() -> bool:
    """
    Check whether the current directory is inside a Git repository.

    Returns:
        True if inside a Git repository, otherwise False.
    """
    try:
        # This command succeeds only when executed inside a git repo
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_staged_diff() -> str:
    """
    Retrieve the diff of staged changes.

    Returns:
        A string containing the staged diff.
        Returns an empty string if no changes are staged.
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["git", "diff", "--cached"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result.stdout.strip()


def estimate_token_count(text: str) -> int:
    """
    Roughly estimate the number of tokens in a string.

    This approximation assumes ~4 characters per token.

    Args:
        text: The input text.

    Returns:
        Estimated token count.
    """
    return len(text) // 4


def create_commit(message: str) -> None:
    """
    Create a Git commit with the provided message.

    Args:
        message: The commit message to use.

    Exits:
        Terminates the program if the commit fails.
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

    print("Commit created successfully!")
    print(result.stdout)

@Halo(text="Generating commit messages...", spinner="dots")
def generate_commit_messages(diff: str, n: int) -> list[str]:
    """
    Generate multiple Conventional Commit messages from a Git diff.

    The OpenAI API analyzes staged changes and proposes commit
    messages following the Conventional Commits specification.

    Args:
        diff: The staged git diff.
        n: Number of commit suggestions to generate.

    Returns:
        A list containing up to `n` commit message suggestions.

    Exits:
        Terminates the program if the OpenAI API key is not set.
    """
    api_key: str = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    client: openai.OpenAI = openai.OpenAI(api_key=api_key)

    prompt: str = COMMIT_PROMPT_TEMPLATE.format(diff=diff, n=n)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You generate high quality git commit messages.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    response_text: str = response.choices[0].message.content.replace("```", "").strip()

    commits: list[str] = []

    for line in response_text.split("\n"):
        line: str = line.strip()

        if not line:
            continue

        # Remove numeric prefixes like "1. feat: add feature"
        if "." in line:
            line: str = line.split(".", 1)[1].strip()

        commits.append(line)

    return commits[:n]


def choose_commit(commits: list[str]) -> str:
    """
    Prompt the user to select a commit message from a list.

    Args:
        commits: A list of commit message suggestions.

    Returns:
        The selected commit message.

    Exits:
        Terminates the program if the user quits.
    """
    return questionary.select("Proposed commit messages:", commits, qmark="").ask()


def main() -> None:
    """
    CLI entry point for the AI commit generator.

    Workflow:
        1. Ensure the current directory is a Git repository.
        2. Retrieve staged changes.
        3. Generate commit message suggestions using OpenAI.
        4. Allow the user to select or confirm a message.
        5. Create the Git commit.
    """
    args: argparse.Namespace = parse_args()

    if not is_git_repository():
        print("Error: Not inside a Git repository.")
        sys.exit(1)

    diff: str = get_staged_diff()

    if not diff:
        print("No staged changes found.")
        sys.exit(0)

    if estimate_token_count(diff) > 6000:
        print("Max tokens (6k) exceeded.")
        sys.exit(0)

    if args.command == "list":
        commits: list[str] = generate_commit_messages(diff, args.num)
        message: str = choose_commit(commits)
    else:
        commits: list[str] = generate_commit_messages(diff, 1)
        message: str = commits[0]
        print(message)

    confirm: str = input("\nCommit with this message? (y/n): ").strip().lower()

    if confirm != "y":
        print("Commit aborted.")
        sys.exit(0)

    create_commit(message)


if __name__ == "__main__":
    main()
