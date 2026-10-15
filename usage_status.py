LIMIT_WINDOWS = ("five_hour", "seven_day")
FAILED_UTILIZATION = -1.0  # what codex.py writes when it could not fetch the limits


def claude_usage_failed(usage):
    return usage is None or ("error" in usage and "five_hour" not in usage)


def codex_usage_failed(usage):
    if usage is None or usage.get("error"):
        return True
    reported = [usage[name] for name in LIMIT_WINDOWS if usage.get(name) is not None]
    return not reported or any(window.get("utilization", FAILED_UTILIZATION) < 0 for window in reported)
