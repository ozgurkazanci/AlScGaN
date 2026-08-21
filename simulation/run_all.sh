#!/usr/bin/env bash
# Production run, in dependency order. Each stage writes its own log.
set -u
cd "$(dirname "$0")"
for stage in exp3_device exp4_headline exp5_reproducibility exp6_robustness; do
  echo "=== START $stage $(date +%H:%M:%S)"
  python -u "${stage}.py" > "results/${stage}.log" 2>&1
  code=$?
  if [ $code -ne 0 ]; then
    echo "=== FAILED $stage (exit $code)"
    tail -20 "results/${stage}.log"
  else
    echo "=== DONE $stage $(date +%H:%M:%S)"
  fi
done
echo "=== ALL STAGES FINISHED"
