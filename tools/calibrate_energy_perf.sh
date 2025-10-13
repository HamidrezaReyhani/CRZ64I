#!/usr/bin/env bash
set -euo pipefail
OP=$1        # "ADD" or "LOAD"
ITERS=$2
RUNS=${3:-7}
PIN=${4:-0}
SLEEP=${5:-1}

bench="./bench/micro_${OP,,}"
if [ ! -x "$bench" ]; then
  echo "bench not found: $bench" >&2
  exit 1
fi

rapl_path=$(find /sys/class/powercap -type f -name energy_uj 2>/dev/null | head -n1 || true)
echo "rapl_path: ${rapl_path:-<none>}"

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

measure_perf() {
  sudo perf stat -e power/energy-pkg/ -- taskset -c $PIN "$bench" "$ITERS" 2>&1 | \
    awk '/power\/energy-pkg/ { gsub(/,/,"",$1); print $1 }'
}

for i in $(seq 1 $RUNS); do
  echo "run $i / $RUNS ..."
  if [ -n "$rapl_path" ]; then
    before=$(sudo cat "$rapl_path" 2>/dev/null || echo "")
    taskset -c $PIN "$bench" "$ITERS" >/dev/null
    after=$(sudo cat "$rapl_path" 2>/dev/null || echo "")
    if [[ "$before" =~ ^[0-9]+$ && "$after" =~ ^[0-9]+$ ]]; then
      delta_j=$(python3 - <<PY
print((int($after) - int($before)) / 1e6)
PY
)
      echo "$delta_j" >> "$tmpfile"
      echo "  energy (J) = $delta_j"
    else
      v=$(measure_perf)
      echo "$v" >> "$tmpfile"
      echo "  perf energy (J) = $v"
    fi
  else
    v=$(measure_perf)
    echo "$v" >> "$tmpfile"
    echo "  perf energy (J) = $v"
  fi
  sleep $SLEEP
done

# compute median and energy per op
python3 - <<PY
import sys, statistics
vals = [float(x.strip()) for x in open("$tmpfile").read().splitlines() if x.strip()]
if not vals:
    print("NO_SAMPLES")
    sys.exit(1)
med = statistics.median(vals)
print("MEDIAN_J", med)
IT = $ITERS
print("ENERGY_PER_OP_J", med / IT)
print("SAMPLES:", vals)
PY
