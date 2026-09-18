def claude_usage_failed(usage):
    return usage is None or ("error" in usage and "five_hour" not in usage)


def codex_usage_failed(usage):
    # codex.py signals failure with utilization = -1.0 rather than an "error" key.
    if usage is None or usage.get("error") or "seven_day" not in usage:
        return True
    return usage["seven_day"].get("utilization", -1) < 0
