from enum import Enum

LIMIT_WINDOWS = ("five_hour", "seven_day")
REJECTED_REFRESH_STATUSES = (400, 401)


class UsageProblem(Enum):
    LOGIN_EXPIRED = "login_expired"
    FETCH_FAILED = "fetch_failed"


class LoginExpired(Exception):
    """The auth server rejected the stored refresh token; only a new login fixes it."""


def error_payload(problem):
    return {"error": problem.value}


def usage_problem(usage):
    if usage is None:
        return UsageProblem.FETCH_FAILED
    if "error" in usage:
        return _problem_named(usage["error"])
    if all(usage.get(name) is None for name in LIMIT_WINDOWS):
        return UsageProblem.FETCH_FAILED
    return None


def _problem_named(error):
    if error == UsageProblem.LOGIN_EXPIRED.value:
        return UsageProblem.LOGIN_EXPIRED
    return UsageProblem.FETCH_FAILED
