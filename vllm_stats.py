import re
from dataclasses import dataclass

ENGINE_LOG_PATTERN = re.compile(
    r"Avg prompt throughput:\s*(?P<prompt>[\d.]+) tokens/s.*?"
    r"Avg generation throughput:\s*(?P<generation>[\d.]+) tokens/s.*?"
    r"Running:\s*(?P<running>\d+) reqs.*?"
    r"Waiting:\s*(?P<waiting>\d+) reqs.*?"
    r"GPU KV cache usage:\s*(?P<kv_cache>[\d.]+)%"
)


@dataclass(frozen=True)
class VllmStats:
    prompt_throughput: float
    generation_throughput: float
    running: int
    waiting: int
    kv_cache_pct: float


def parse_engine_log_line(line):
    match = ENGINE_LOG_PATTERN.search(line)
    if not match:
        raise ValueError(f"not a vLLM engine statistics line: {line[:80]!r}")
    return VllmStats(
        prompt_throughput=float(match["prompt"]),
        generation_throughput=float(match["generation"]),
        running=int(match["running"]),
        waiting=int(match["waiting"]),
        kv_cache_pct=float(match["kv_cache"]),
    )
