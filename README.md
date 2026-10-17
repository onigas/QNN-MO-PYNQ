# QNN-MO-PYNQ PIP INSTALL Package

This repo contains the pip install package for Quantized Neural Network (QNN) on PYNQ using a Multi-Layer Offload (MO) architecture.
Two different overlays are here included, namely W1A2 (1 bit weights, 2 bit activations) and W1A3 (1 bit weights, 3 bit activations), executing in the Programmable Logic 1 Convolutional layer and 1 (optional) Max Pool layer.

## Quick Start

In order to install it on your PYNQ board, connect to the board, open a terminal and type:

```shell
# (on PYNQ v2.3 and later versions, tested up to v2.5)
sudo pip3 install git+https://github.com/onigas/QNN-MO-PYNQ.git
```

NOTE: The board has to be connected to the internet.

**Installation may take more than 10 minutes, especially on memory-limited boards or when using swap, because dependencies, source builds, and model packaging must complete.**

This will install the QNN package to your board, and create a **QNN** directory in the Jupyter home area. You will find the Jupyter notebooks to test the QNN overlays in this directory.

In order to build the shared object during installation, the user should copy the include folder from VIVADO HLS on the PYNQ board (in windows in vivado-path/Vivado_HLS/201x.y/include, /vivado-path/Vidado_HLS/201x.y/include in unix) and set the environment variable *VIVADOHLS_INCLUDE_PATH* to the location in which the folder has been copied.
If the env variable is not set, the precompiled version will be used instead.

## Notebook execution order

The six notebooks are numbered in the recommended teaching order:

| Order | Notebook | Purpose |
| --- | --- | --- |
| 01 | [01_Machine_Learning_on_PYNQ.ipynb](notebooks/01_Machine_Learning_on_PYNQ.ipynb) | Introduction to quantization, dataflow, and multi-layer offload (reading). |
| 02 | [02_dorefanet-imagenet-samples.ipynb](notebooks/02_dorefanet-imagenet-samples.ipynb) | Classify a labelled ImageNet sample and inspect top-5 predictions and timing. |
| 03 | [03_dorefanet-classification.ipynb](notebooks/03_dorefanet-classification.ipynb) | Classify an image chosen by the user. |
| 04 | [04_dorefanet-imagenet-loop.ipynb](notebooks/04_dorefanet-imagenet-loop.ipynb) | Repeat ImageNet classification over sample image files. |
| 05 | [05_tiny-yolo-image.ipynb](notebooks/05_tiny-yolo-image.ipynb) | Detect objects in one image, with bounding boxes and CPU/FPGA execution stages. |
| 06 | [06_tiny-yolo-image-loop.ipynb](notebooks/06_tiny-yolo-image-loop.ipynb) | Repeat object detection over image files; this is not a video-input demo. |

For the object-detection track, read notebook 01 and then start with **05**, followed by **06**. Shut down the previous notebook kernel before loading another FPGA example. The loop demos stop after a configurable positive image limit (10 for **04**, 5 for **06**, with one pass through the folder by default). For an early stop, use **Kernel → Interrupt** and wait for the current native call to return. Their `finally` blocks release native resources; rerun the model-loading section before another loop run.

Notebooks **02–06** resolve parameters from the installed `qnn` package rather than a fixed Python 3.6 directory. Their revised flows check input files, filter image extensions, load legacy NumPy/pickle files explicitly, explain each CPU/FPGA stage, and release resources without global device resets or notebook-level `Xlnk` imports. **03** retains an optional software comparison of the same quantized layers; it is skipped by default. **05–06** explicitly declare the custom Darknet C signatures, pass contiguous float32 detection-head output, free native images/networks, and isolate output files in a unique folder per run. Detection scores are sorted numerically; no detections above threshold is handled normally.

Timing axes use **seconds** and explain the measured scope. Different CPU and FPGA stages must not be presented as a same-workload speedup; predictions/confidence are not dataset accuracy. The Python paths, original NumPy operations, repeated initialization, optional software comparison, loop error/interruption cleanup and empty-detection handling were checked **off-board with simulated accelerator/native interfaces**. This does not validate native-library execution, FPGA predictions or performance on the board.

To update an existing board installation, replace the numbered notebook files in `/home/xilinx/jupyter_notebooks/qnn/` using Jupyter upload and restart their kernels. Keep the existing data/image folders and installed model. **No package reinstallation is needed for these notebook updates.** The unused `Xlnk` imports in the installed Python package must already be removed as described below.

## Troubleshooting: unused Xlnk import on newer PYNQ

If importing `qnn` fails with `ImportError: cannot import name 'Xlnk' from 'pynq'`, the installed copy may still contain the legacy imports. The imports in `qnn/dorefanet.py` and `qnn/tinieryolo.py` are unused and have been removed in this fork.

For the Python 3.8 installation at the path below, update those two installed imports once, then restart the notebook kernel:

```bash
sudo sed -i.bak 's/from pynq import Overlay, Xlnk/from pynq import Overlay/' /usr/local/share/pynq-venv/lib/python3.8/site-packages/qnn/{dorefanet,tinieryolo}.py
```

Use the installed package path shown in the traceback if it differs. This fix has already been applied on the board used for these labs; do not repeat installation just to update notebook files.

## Troubleshooting: installation fails because of insufficient RAM

On a 512 MB PYNQ board, building the wheel can exhaust RAM while packaging the model parameters. The terminal may stop displaying progress and eventually report:

```text
ERROR: Failed building wheel for qnn-loopback
ERROR: Could not build wheels for qnn-loopback
```

These messages alone do not establish the cause. Check the kernel log:

```bash
dmesg | grep -i -E 'out of memory|oom|killed process' | tail -n 10
```

If it reports `Out of memory: Killed process ... (python3)` for the installation, use the temporary swap procedure below. This failure was observed during wheel packaging in a Python 3.8 PYNQ environment; adding 1 GiB of swap allowed the installation to complete successfully.

### 1. Check available resources

Close unused notebook kernels, then run:

```bash
free -h
df -h / /tmp
```

The procedure adds a 1 GiB file on the SD card. Allow space for that file as well as the installation's temporary files. Existing free disk space does not prevent a RAM shortage.

### 2. Create and enable temporary swap

Run these commands once. Use a new file at the path below; do not recreate or overwrite an already active swap file.

```bash
sudo dd if=/dev/zero of=/home/xilinx/qnn-install.swap bs=1M count=1024 status=progress
sudo chmod 600 /home/xilinx/qnn-install.swap
sudo mkswap /home/xilinx/qnn-install.swap
sudo swapon /home/xilinx/qnn-install.swap
free -h
```

Confirm that `free -h` now shows approximately 1 GiB of additional swap before retrying installation. If the swap file was already created and the board was restarted, enable that existing file with `sudo swapon /home/xilinx/qnn-install.swap` instead of recreating it.

### 3. Retry installation and keep a log

```bash
sudo pip3 install --log /home/xilinx/jupyter_notebooks/qnn-install.log git+https://github.com/onigas/QNN-MO-PYNQ.git
```

Installation can take longer with swap because SD-card access is slower than RAM. In a second terminal, inspect progress without interrupting the installation:

```bash
tail -n 30 /home/xilinx/jupyter_notebooks/qnn-install.log
```

The log file is accessible from the Jupyter home directory. If installation still fails, use the log to diagnose the new error rather than assuming that every wheel failure is caused by memory.

### 4. Optional cleanup after successful installation

The swap activation above is temporary: it is not added to `/etc/fstab` and will not automatically reactivate after reboot. The file remains on disk.

When memory permits, disable and remove it:

```bash
sudo swapoff /home/xilinx/qnn-install.swap && sudo rm /home/xilinx/qnn-install.swap
```

The file is removed only if `swapoff` succeeds. Close unused notebook kernels before cleanup if necessary.

## Repo organization

The repo is organized as follows:

-	qnn: contains the qnn class description as well as the classes for the test networks
	-	src: contains the sources of the 2 overlays and the libraries to rebuild them:
		- library: FINN library for HLS QNN-MO descriptions, host code, script to rebuilt and drivers for the PYNQ (please refer to README for more details)
		- network: overlay topologies (W1A2 and w1A3) HLS top functions, host code and make script for HW and SW built (please refer to README for more details)
	-	bitstreams: with the bitstream for the 2 overlays
	-	libraries: pre-compiled shared objects for low-level driver of the 2 overlays
	-	params: set of trained parameters for the 2 overlays:
		- A pruned version of [DoReFa-Net](https://arxiv.org/abs/1606.06160) network, trained on the [ImageNet](http://www.image-net.org/) dataset with 1 bit weights and 2 bit activations
		- A modified version of [Tiny Yolo](https://pjreddie.com/darknet/yolo/), namely Tinier-Yolo, trained on [PASCAL VOC](http://host.robots.ox.ac.uk/pascal/VOC/) dataset with 1 bit weights and 3 bit activations
-	notebooks: lists a set of python notebooks examples, that during installation will be moved in `/home/xilinx/jupyter_notebooks/qnn/` folder
-	tests: contains test scripts and test images

## Hardware design rebuilt

In order to rebuild the hardware designs, the repo should be cloned in a machine with installation of the Vivado Design Suite (tested with 2017.4).
Following the step-by-step instructions:

1.	Clone the repository on your linux machine: git clone https://github.com/Xilinx/QNN-MO-PYNQ.git;
2.	Move to `clone_path/QNN-MO-PYNQ/qnn/src/network/`
3.	Set the XILINX_QNN_ROOT environment variable to `clone_path/QNN-MO-PYNQ/qnn/src/`
4.	Launch the shell script make-hw.sh with parameters the target network, target platform and mode, with the command `./make-hw.sh {network} {platform} {mode}` where:
	- network can be W1A2 or W1A3;
	- platform can be pynqz1-z2 or ultra96;
	- mode can be `h` to launch Vivado HLS synthesis, `b` to launch the Vivado project (needs HLS synthesis results), `a` to launch both.
5.	The results will be visible in `clone_path/QNN-MO-PYNQ/qnn/src/network/output/` that is organized as follows:
	- bitstream: contains the generated bitstream(s);
	- hls-syn: contains the Vivado HLS generated RTL and IP (in the subfolder named as the target network);
	- report: contains the Vivado and Vivado HLS reports;
	- vivado: contains the Vivado project.
6.	Copy the generated bitstream and tcl script on the PYNQ board `pip_installation_path/qnn/bitstreams/`
