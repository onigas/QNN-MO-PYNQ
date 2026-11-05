# Raspberry Pi 4 — CPU comparison with PYNQ

Separate notebooks using the original models and weights:

- [02.1 — DoReFaNet ImageNet](../notebooks/02.1_dorefanet-imagenet-rpi.ipynb)
- [05.1 — Tinier-YOLO, image file or Logitech camera](../notebooks/05.1_tiny-yolo-image-rpi.ipynb)

Target platform: **Raspberry Pi 4 Model B, 4 GB, Debian 13 Trixie ARM64**.
`uname -m` must report `aarch64`. Do not install the PYNQ package or run
`pip install .` for this port. PYNQ notebooks 01–08 remain separate.

**Status:** adapters and notebooks prepared for on-device validation.
All five local tests passed, including the Darknet adapter compiled on x86_64.
Both notebooks' cells were executed locally with the ARM64 kernel output replaced
by reference data. This verifies the Python workflow, not inference correctness on
the Pi. Run the two native reference checks below before using the notebooks.
No Raspberry Pi performance results were published at this stage.

## 1. Installation on Raspberry Pi

Keep uStreamer and Home Assistant running; the camera does not need reconfiguration.
From a terminal on the Raspberry Pi:

```bash
sudo apt update
sudo apt install -y git build-essential python3-venv python3-numpy python3-opencv python3-matplotlib python3-pil python3-notebook python3-ipykernel python3-threadpoolctl libbz2-1.0 libssl3t64 zlib1g
cd ~
git clone --depth=1 https://github.com/onigas/QNN-MO-PYNQ.git
cd QNN-MO-PYNQ
bash raspberry_pi/setup_rpi.sh
```

If you already have a checkout without local modifications, run `git pull --ff-only`
there and then rerun the setup command. Do not overwrite modified notebooks. Use a
short directory path without spaces (for example `~/QNN-MO-PYNQ`), as Darknet is a
legacy C project. Installation downloads source code and decompresses large weights;
sufficient free storage space and internet access are required.
On a Pi with 4 GB RAM, close other inference notebooks before running DoReFaNet.

The setup script creates a local `.venv` using Debian Python packages,
downloads and SHA256-verifies the Debian ARM64 `libzip4` package, extracts it only to
`.deps/libzip4`, and compiles CPU Darknet with two parallel jobs.
It does not replace system libzip or link the incompatible libzip5 and libzip4 ABIs.
The original software libraries `qnn/libraries/ultra96/lib_sw_W1A2.so` and `lib_sw_W1A3.so`
are ARM64 binaries; the adapters check SHA256 before loading. They do not use an FPGA.

Darknet is obtained from `giuliogamba/darknet`, pinned to commit
`3bbbe379de1ecd8d8e533b73795f105f650da8e5`, with GPU/CUDNN/OpenCV/OpenMP disabled.
`darknet_compat.h` declares the `load_alphabet_path` function missing from the original
header to avoid truncated pointers on 64-bit targets. `-fcommon` permits legacy
global definitions. External sources are kept under `.deps`, not installed globally.

## 2. Verification before benchmarking

From the repository root:

```bash
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --load-only
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --model dorefanet
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --model tinier-yolo
```

The first test checks only library loading. The next two actually execute the CPU
kernels with binary inputs from `tests/Test_image` and compare bytes in the valid
channels against `verification.bin`, excluding padding as in
`OffloadUtils::verifyBuffers`.
For DoReFaNet, the input file buffer contains 393216 bytes but the effective input
is 279936 bytes. The first 279936 are used, as in the original C++ executable.
The initial version of the validator passed the entire file and compared padding
as well. Update the repository and rerun the test if you used that version.
Proceed to a notebook only after receiving `PASS` for its model. On `FAIL`,
stop comparisons and retain the full diagnostic output.

The C++/HLS reference is not an optimized AI runtime for the Pi. Inference can
take minutes. Elapsed time is displayed every 15 seconds without estimating
progress. A Jupyter interrupt may not take effect until the native call returns.
Do not start another inference concurrently.

## 3. Starting Jupyter

```bash
bash raspberry_pi/start_jupyter.sh
```

Open the local token-authenticated URL displayed by Jupyter. To access it from
another computer, use an SSH tunnel to the reported port (example for port 8888):

```bash
ssh -L 8888:127.0.0.1:8888 USER@RPI_ADDRESS
```

Then open `127.0.0.1:8888` in your browser with the token from the Pi's Jupyter server.
The script limits BLAS/OpenMP to one thread; the notebooks also use `threadpoolctl`.
Run cells in order and execute the memory-cleanup cell at the end.

## 4. Sharing the Logitech camera with Home Assistant

uStreamer remains the sole process accessing the USB camera and continues
streaming to Home Assistant. Notebook 05.1 requests a single still image
from the existing server:

```python
SOURCE = 'snapshot'
SNAPSHOT_URL = 'http://127.0.0.1:8080/snapshot'
```

It does not use `VideoCapture`, open `/dev/video0`, or stop any services.
The URL must return JPEG/PNG, not the multipart stream at `/stream`.
If uStreamer uses a different port, change the URL. Resolve timeouts and HTTP
errors by checking the existing server, rather than starting a second camera process.
Notebook 05.1 processes one frame per invocation; it is not a real-time video detector.

The snapshot stays in memory. Darknet requires file paths, so input PNG files and
its temporary outputs are created in `/dev/shm` and removed when their context
ends, including on Python exceptions. There is no SD-card fallback and no automatic
saving of captures or JSON files. Forced process termination can leave temporary
files in RAM until cleanup or restart.
Jupyter may embed displayed images in the saved notebook; clear cell outputs
before saving if you do not want the images retained.

## 5. Fair comparison methodology

Initially use `SOURCE = 'file'` and exactly the same input file on both platforms.
Notebook 02.1 defaults to `n01484850_0.jpg` and 05.1 to `dog.jpg`.
Each notebook displays SHA256 hashes of its input and quantized output.
A fresh camera frame is not identical to a previously acquired frame on PYNQ.

| Measurement | Scope |
| --- | --- |
| `quantized_core_s` | Only the `classifier.inference` call, corresponding to the PYNQ offload boundary |
| `first_cpu_s`, `last_cpu_s` | Initial convolution and final FC/convolution on the CPU |
| `packing_s`, `unpacking_s` | Buffer conversion for the quantized kernel |
| `preprocess_s` | Image loading and transformation for the model |
| `decode_draw_ram_io_s` (05.1) | Decoding, drawing and RAM temporary-file I/O |
| Snapshot acquisition | Reported separately, outside inference |

The sum of the new notebooks' measured stages does not have the same boundaries
as the PYNQ 02/05 plot sums, which exclude preprocessing and buffers.
Model loading, plot display and hash calculation are outside the timed stages.
The CPU/FPGA ratio characterizes this software reference, not the maximum
potential performance of a Raspberry Pi with an optimized runtime.

Run one warm-up followed by multiple measurements and report the median.
Record temperature, power supply, OS/NumPy/BLAS versions, thread limits and
the fact that uStreamer remains active. BLAS differences may slightly affect
floating-point stages; verify the quantized outputs first.
No thresholds or weights were adjusted to produce more favorable results.

## Development tests

```bash
raspberry_pi/.venv/bin/python -m unittest discover -s tests -p 'test_rpi*.py' -v
```

These tests cover bit packing, HTTP snapshots, RAM temporary-file cleanup,
notebook structure and the Darknet adapter if its library is available.
They do not replace ARM64 inference verification in Section 2.

## 02.2 — MobileNet with OpenCV DNN

[Notebook 02.2](../notebooks/02.2_mobilenet-opencv-imagenet-rpi.ipynb) uses
MobileNet v1 ImageNet via OpenCV 4.x CPU in the **QNN Raspberry Pi** kernel.
Open it from the repository directory and run the cells in order.
Do not install Caffe/TensorFlow or upgrade OpenCV with pip: the already installed
Debian 4.10 package is sufficient. The first run downloads approximately 17 MB
of SHA256-verified model, configuration and label files into
`raspberry_pi/.deps/mobilenet`.

The notebook contains Top-5 results, warm-up, and five measurements with
one and four threads, median/min/max, and an automatically generated table
and chart using the user's historical measurements:
66.6034 s for the three DoReFaNet stages on RPi and 1.296 s for the same
stages on PYNQ.
The historic predictions used different images; the comparison concerns
the order of magnitude of execution time, not classification accuracy.
MobileNet is a different model, not a DoReFaNet conversion.
Its full-model time is compared against full DoReFaNet computation,
not the 0.057 s FPGA core time.
Result files and captures are not saved automatically.

Validation: notebook 02.2 cells were tested with actual MobileNet inference on
x86_64/OpenCV 4.10; MobileNet execution times on Raspberry Pi must be measured
on that device. Native QNN tests on Pi passed on 18 October 2026:
DoReFaNet 67.017 s and Tinier-YOLO 274.349 s for the quantized kernels.
