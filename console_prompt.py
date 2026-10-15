# Login prompts at startup. Under systemd nobody is at the console, so an
# unanswerable prompt counts as "press Enter to disable" instead of crashing
# the whole dashboard.


def ask(question):
    try:
        return input(question).strip()
    except EOFError:
        print("(no console attached, skipped)")
        return ""
