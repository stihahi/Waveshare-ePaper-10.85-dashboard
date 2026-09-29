#!/bin/sh
# Read-only metrics for the e-paper dashboard. Installed as the forced command
# of the dashboard's restricted SSH key, so it takes no arguments.
set -u

nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv,noheader,nounits |
    head -1 |
    awk -F'[[:space:]]*,[[:space:]]*' '{print "temperature_c=" $1; print "utilization_pct=" $2}'

# The dashboard averages this window: a single snapshot can land on a prefill
# step, where decoding momentarily drops to a few tokens per second.
SAMPLE_COUNT=5
ENGINE_LOG_MARKER='Avg prompt throughput'

# Serving containers are found by the statistics they log: image and container
# names vary per model recipe, and host networking hides the published port.
samples=''
for container in $(docker ps --format '{{.Names}}' 2>/dev/null); do
    samples=$(docker logs --since 5m "$container" 2>&1 | grep "$ENGINE_LOG_MARKER" | tail -"$SAMPLE_COUNT")
    [ -n "$samples" ] && break
done
[ -n "$samples" ] || exit 0

model=$(curl -s --max-time 3 http://localhost:8000/v1/models 2>/dev/null |
    grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
[ -n "$model" ] && echo "model=$model"

echo "$samples" | sed 's/^/vllm=/'
exit 0
