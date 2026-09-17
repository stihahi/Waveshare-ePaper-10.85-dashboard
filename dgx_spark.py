import logging
import subprocess
from dataclasses import dataclass
from enum import Enum

NVIDIA_SMI_QUERY = "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv,noheader,nounits"
SSH_CONNECT_TIMEOUT_SECONDS = 5
SSH_COMMAND_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class GpuStatus:
    temperature_c: int
    utilization_pct: int


class GpuUnavailable(Enum):
    PENDING = "waiting..."
    OFFLINE = "offline"


def parse_gpu_status(nvidia_smi_output):
    lines = nvidia_smi_output.strip().splitlines()
    if not lines:
        raise ValueError("nvidia-smi returned no GPU rows")
    temperature, utilization = (field.strip() for field in lines[0].split(","))
    return GpuStatus(temperature_c=int(temperature), utilization_pct=int(utilization))


def query_gpu_status(host):
    try:
        return parse_gpu_status(_run_over_ssh(host, NVIDIA_SMI_QUERY))
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        logging.warning(f"DGX Spark {host} query failed: {error}")
        return GpuUnavailable.OFFLINE


def _run_over_ssh(host, command):
    ssh_command = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT_SECONDS}", host, command]
    result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=SSH_COMMAND_TIMEOUT_SECONDS, check=True)
    return result.stdout
