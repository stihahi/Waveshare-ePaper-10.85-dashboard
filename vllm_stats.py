import re
from dataclasses import dataclass
from statistics import fmean

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

    def served_requests(self):
        return self.running > 0


@dataclass(frozen=True)
class VllmActivity:
    mean_prompt_throughput: float
    mean_generation_throughput: float
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


def summarize_samples(samples):
    if not samples:
        raise ValueError("no vLLM engine statistics samples to summarize")
    serving = [sample for sample in samples if sample.served_requests()]
    newest = samples[-1]
    return VllmActivity(
        mean_prompt_throughput=_mean(sample.prompt_throughput for sample in serving),
        mean_generation_throughput=_mean(sample.generation_throughput for sample in serving),
        running=newest.running,
        waiting=newest.waiting,
        kv_cache_pct=newest.kv_cache_pct,
    )


def _mean(values):
    collected = list(values)
    return fmean(collected) if collected else 0.0
