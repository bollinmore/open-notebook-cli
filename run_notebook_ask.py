import subprocess
import sys

def run_notebook_ask(question):
    """
    Calls the ./notebook-cli.sh script with the 'ask' command and the provided question.
    Returns the stdout and stderr as a single string.
    """
    command = ["./notebook-cli.sh", "ask", question]
    try:
        # Execute the shell script and capture its output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"Error calling ./notebook-cli.sh with question: '{question}'
"
        error_message += f"Exit Code: {e.returncode}
"
        error_message += f"Stdout: {e.stdout.strip()}
"
        error_message += f"Stderr: {e.stderr.strip()}"
        print(error_message, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: The script './notebook-cli.sh' was not found. Please ensure it is in the current directory and is executable.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_notebook_ask.py "Your question here"", file=sys.stderr)
        sys.exit(1)

    question_to_ask = sys.argv[1]
    output = run_notebook_ask(question_to_ask)
    print(output)
