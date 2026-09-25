#!/bin/sh
# Read-only metrics for the e-paper dashboard. Installed as the forced command
# of the dashboard's restricted SSH key, so it takes no arguments.
set -u

nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv,noheader,nounits |
    head -1 |
    awk -F'[[:space:]]*,[[:space:]]*' '{print "temperature_c=" $1; print "utilization_pct=" $2}'

container=$(docker ps --format '{{.Names}} {{.Image}}' 2>/dev/null | awk '$2 ~ /vllm/ {print $1; exit}')
[ -n "$container" ] || exit 0

model=$(curl -s --max-time 3 http://localhost:8000/v1/models 2>/dev/null |
    grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
[ -n "$model" ] && echo "model=$model"

# The dashboard averages this window: a single snapshot can land on a prefill
# step, where decoding momentarily drops to a few tokens per second.
SAMPLE_COUNT=5
docker logs --since 5m "$container" 2>&1 |
    grep 'Avg prompt throughput' |
    tail -"$SAMPLE_COUNT" |
    sed 's/^/vllm=/'
exit 0
