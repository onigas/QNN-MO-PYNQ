#!/usr/bin/env bash
set -euo pipefail
lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -m)" != aarch64 ]]; then
  echo 'Requires 64-bit ARM64 Linux (uname -m must report aarch64).' >&2
  exit 1
fi
cd "$lab_root"
python3 -m venv --system-site-packages raspberry_pi/.venv
raspberry_pi/.venv/bin/python -c 'import numpy, cv2, matplotlib, PIL, notebook, ipykernel, threadpoolctl'
raspberry_pi/.venv/bin/python raspberry_pi/prepare.py
lab_darknet="$lab_root/raspberry_pi/.deps/darknet"
if [[ ! -d "$lab_darknet/.git" ]]; then
  git clone https://github.com/giuliogamba/darknet.git "$lab_darknet"
fi
if [[ -n "$(git -C "$lab_darknet" status --porcelain --untracked-files=no)" ]]; then
  echo "Local Darknet source changes detected; preserve or commit them before rebuilding." >&2
  exit 1
fi
git -C "$lab_darknet" checkout --detach 3bbbe379de1ecd8d8e533b73795f105f650da8e5
make -C "$lab_darknet" clean
mkdir -p "$lab_darknet/obj"
make -C "$lab_darknet" -j2 libdarknet.so GPU=0 CUDNN=0 OPENCV=0 OPENMP=0 \
  CFLAGS="-O3 -fPIC -fcommon -std=gnu11 -Wno-unknown-pragmas -Werror=implicit-function-declaration -Werror=int-conversion -include $lab_root/raspberry_pi/darknet_compat.h"
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --load-only
printf '%s\n' 'Dependencies loaded. Next run both reference tests in raspberry_pi/README.md.'
