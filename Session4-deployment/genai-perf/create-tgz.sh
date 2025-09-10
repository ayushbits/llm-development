#!/usr/bin/env bash
tar -cvzf customer-tco-computation.tgz \
  analyze_latencies.ipynb \
  requirements.txt \
  common_env.sh \
  README.md \
  nim-docker-launch.sh \
  genai-perf-docker-launch.sh \
  sweep-genai-perf.sh