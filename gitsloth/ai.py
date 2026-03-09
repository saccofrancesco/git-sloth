# Importing libraries
import os
import openai

# Creating the commit propmt template to then format with 2 variables and an f-string
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


# Estimate the number of tokens based on the input text's length
def estimate_token_count(text: str) -> int:
    """
    Roughly estimate the number of tokens in a string.
    This approximation assumes ~4 characters per token.

    Args:
        text: The input text.

    Returns:
        Estimated token count.
    """

    # Computing a rough approximation of 4 chars per token
    return len(text) // 4


# Based on a diff change output generate an n-number of commits related to the context's
# changes
def generate_commit_messages(diff: str, n: int) -> list[str]:
    """
    Generate multiple Conventional Commit messages from a Git diff.

    Args:
        diff: The staged git diff.
        n: Number of commit suggestions to generate.

    Returns:
        A list containing up to `n` commit message suggestions.

    Raises:
        EnvironmentError: If the OPENAI_API_KEY is not set.
    """

    # Get the api key from the env variable of the user
    api_key: str = os.getenv("OPENAI_API_KEY")

    # Checking if it has founded something; if not raising a missing error
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")

    # Create the OpenAI client to do the request of the following formatted prompt f-string
    client: openai.OpenAI = openai.OpenAI(api_key=api_key)
    prompt: str = COMMIT_PROMPT_TEMPLATE.format(diff=diff, n=n)

    # Generating a response with the specified payload
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

    # Sanitize the response output for the single commit generation case (where n = 1)
    response_text: str = response.choices[0].message.content.replace("```", "").strip()

    # Extract generated commits from the model and store them in a list for better use
    commits: list[str] = list()
    for line in response_text.split("\n"):
        line: str = line.strip()
        if not line:
            continue
        if "." in line:
            line: str = line.split(".", 1)[1].strip()
        commits.append(line)

    # After filling the commits, return the computed list
    return commits
