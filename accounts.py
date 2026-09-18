import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ACCOUNT_NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]+")


def account_file(prefix, account):
    if not ACCOUNT_NAME_PATTERN.fullmatch(account):
        raise ValueError(f"account name must match {ACCOUNT_NAME_PATTERN.pattern}: {account!r}")
    return SCRIPT_DIR / f"{prefix}_{account}.json"


def account_from_argv(argv):
    value_index = argv.index("--account") + 1 if "--account" in argv else len(argv)
    if value_index >= len(argv):
        raise ValueError("--account <name> is required")
    return argv[value_index]
