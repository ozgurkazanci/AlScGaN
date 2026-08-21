#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
for stage in exp7_ternary exp6_robustness exp5_reproducibility; do
  echo "=== START $stage $(date +%H:%M:%S)"
  python -u "${stage}.py" > "results/${stage}.log" 2>&1
  if [ $? -ne 0 ]; then echo "=== FAILED $stage"; tail -15 "results/${stage}.log"
  else echo "=== DONE $stage $(date +%H:%M:%S)"; fi
done
echo "=== FINAL RUN FINISHED"
