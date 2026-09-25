import logging
import subprocess
from dataclasses import dataclass
from enum import Enum

from vllm_stats import VllmActivity, parse_engine_log_line, summarize_samples

# The SSH key on each node is locked to a forced command, so the request itself carries no arguments.
METRICS_REQUEST = "epaper-metrics"
VLLM_SAMPLE_PREFIX = "vllm="
SSH_CONNECT_TIMEOUT_SECONDS = 5
SSH_COMMAND_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class GpuStatus:
    temperature_c: int
    utilization_pct: int


class GpuUnavailable(Enum):
    PENDING = "waiting..."
    OFFLINE = "offline"


@dataclass(frozen=True)
class NodeMetrics:
    gpu: object
    model: str = None
    vllm: VllmActivity = None


def parse_gpu_status(nvidia_smi_output):
    lines = nvidia_smi_output.strip().splitlines()
    if not lines:
        raise ValueError("nvidia-smi returned no GPU rows")
    temperature, utilization = (field.strip() for field in lines[0].split(","))
    return GpuStatus(temperature_c=int(temperature), utilization_pct=int(utilization))


def parse_node_metrics(metrics_output):
    lines = metrics_output.strip().splitlines()
    fields = _parse_fields(line for line in lines if not line.startswith(VLLM_SAMPLE_PREFIX))
    return NodeMetrics(gpu=_gpu_from_fields(fields), model=fields.get("model"), vllm=_vllm_from_lines(lines))


def query_node_metrics(host):
    try:
        return parse_node_metrics(_run_over_ssh(host, METRICS_REQUEST))
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        logging.warning(f"DGX Spark {host} query failed: {error}")
        return NodeMetrics(gpu=GpuUnavailable.OFFLINE)


def _parse_fields(lines):
    fields = {}
    for line in lines:
        key, separator, value = line.partition("=")
        if separator:
            fields[key.strip()] = value.strip()
    return fields


def _gpu_from_fields(fields):
    try:
        return GpuStatus(temperature_c=int(fields["temperature_c"]), utilization_pct=int(fields["utilization_pct"]))
    except KeyError as error:
        raise ValueError(f"node metrics are missing {error}") from error


def _vllm_from_lines(lines):
    samples = [parse_engine_log_line(line[len(VLLM_SAMPLE_PREFIX):])
               for line in lines if line.startswith(VLLM_SAMPLE_PREFIX)]
    return summarize_samples(samples) if samples else None


def _run_over_ssh(host, command):
    ssh_command = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT_SECONDS}", host, command]
    result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=SSH_COMMAND_TIMEOUT_SECONDS, check=True)
    return result.stdout
