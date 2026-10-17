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
