#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
uv tool install . --force

echo -ne "\n\n\nThanks for installing\n----------------------------------------------\n\n\n"
ascii-bg