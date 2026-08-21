#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
for stage in exp3_device exp7_ternary exp5_reproducibility; do
  echo "=== START $stage $(date +%H:%M:%S)"
  python -u "${stage}.py" > "results/${stage}.log" 2>&1
  if [ $? -ne 0 ]; then
    echo "=== FAILED $stage"; tail -20 "results/${stage}.log"
  else
    echo "=== DONE $stage $(date +%H:%M:%S)"
  fi
done
echo "=== FIXES FINISHED"
python -u exp6_robustness.py > results/exp6_robustness.log 2>&1 && echo "=== DONE exp6_robustness $(date +%H:%M:%S)"
