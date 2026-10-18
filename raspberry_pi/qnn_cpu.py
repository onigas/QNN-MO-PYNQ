#!/usr/bin/env python
#   Copyright (c) 2018, Xilinx, Inc.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""ARM64 CPU reference adapters. No PYNQ import and no camera-device access."""
import ctypes as C
import hashlib
import importlib.util
import io
import json
import os
import platform
import tempfile
import threading
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / 'qnn/params'
DEPS = ROOT / 'raspberry_pi/.deps'
_spec = importlib.util.spec_from_file_location('qnn_portable_utils', ROOT / 'qnn/utils.py')
utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(utils)
ILSVRC_PIXEL_MEAN_FILE = str(PARAMS / 'ilsvrc_pp_mean.npy')
_active = None
_zip_handle = None
LIB_HASHES = {
    'W1A2': 'bbe268e41c17bc30186605072c58e3e0c9c26df6f028ec9dcccab9f6656fec9e',
    'W1A3': 'e38f472b2d66303414ff37efa43a5add3d6f436435654857e0efb7ac4f1514f7',
}


def load_cpu_library(kind):
    global _zip_handle
    if platform.machine() != 'aarch64':
        raise RuntimeError('This CPU reference needs ARM64/aarch64 Linux, not a 32-bit OS.')
    path = ROOT / 'qnn/libraries/ultra96' / ('lib_sw_' + kind + '.so')
    if hashlib.sha256(path.read_bytes()).hexdigest() != LIB_HASHES[kind]:
        raise RuntimeError('Unexpected CPU library checksum: ' + str(path))
    zip_path = DEPS / 'libzip4/usr/lib/aarch64-linux-gnu/libzip.so.4'
    if _zip_handle is None:
        _zip_handle = C.CDLL(str(zip_path), mode=C.RTLD_GLOBAL)
    lib = C.CDLL(str(path), mode=C.RTLD_LOCAL)
    for name, args in {
        'initParameters': [C.c_uint, C.c_uint],
        'initAccelerator': [C.c_char_p, C.c_char_p],
        'singleInference': [C.c_void_p, C.c_size_t, C.c_void_p, C.c_size_t],
        'deinitAccelerator': [],
    }.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, None
    return lib


class CPUBackend:
    def __init__(self, model='dorefanet'):
        if model not in ('dorefanet', 'tinier-yolo'):
            raise ValueError(model)
        self.model = model
        self.kind = 'W1A2' if model == 'dorefanet' else 'W1A3'
        self.lib = load_cpu_library(self.kind)
        self.init = False
        self.json_network = ROOT / 'qnn/bitstreams/ultra96' / (self.kind + '-overlay.json')
        self.json_layer = PARAMS / (model + '-layers.json')
        self.network_json = json.loads(self.json_network.read_text())
        self.layer_json = json.loads(self.json_layer.read_text())

    def load_network(self):
        return {layer['name']: {k: v for k, v in layer.items() if k != 'name'}
                for layer in self.layer_json['layers']}

    def init_accelerator(self):
        global _active
        if self.init:
            return
        if _active is not None:
            raise RuntimeError('Release the other CPU model before initializing this one.')
        self.lib.initParameters(1, 0)
        self.lib.initAccelerator(os.fsencode(self.json_network), os.fsencode(self.json_layer))
        self.init = True
        _active = self

    def inference(self, img, out):
        if not self.init:
            raise RuntimeError('Initialize the CPU model first.')
        for arr in (img, out):
            if arr.dtype != np.uint8 or not arr.flags.c_contiguous:
                raise ValueError('Native buffers must be contiguous uint8 arrays.')
        if not out.flags.writeable:
            raise ValueError('Output must be writable.')
        with elapsed_notice('CPU quantized reference'):
            self.lib.singleInference(img.ctypes.data, img.nbytes, out.ctypes.data, out.nbytes)

    def deinit_accelerator(self):
        global _active
        if self.init:
            self.lib.deinitAccelerator()
            self.init = False
            if _active is self:
                _active = None

    def get_accel_buffer(self, channels, dim):
        if not self.init:
            raise RuntimeError('Initialize the CPU model first.')
        return np.zeros((dim, dim, channels), dtype=np.uint8)

    def prepare_buffer(self, values):
        if not self.init:
            raise RuntimeError('Initialize the CPU model first.')
        bits = self.network_json['parameters']['ACTIVATION_BITS']
        values = np.moveaxis(values.astype(np.uint8), 0, -1)
        shifts = np.arange(bits, dtype=np.uint8)
        unpacked = ((values[..., None] >> shifts) & 1).reshape(*values.shape[:2], -1)
        return np.packbits(unpacked, axis=-1, bitorder='little')

    def postprocess_buffer(self, buffer):
        if not self.init:
            raise RuntimeError('Initialize the CPU model first.')
        bits = self.network_json['parameters']['ACTIVATION_BITS']
        h, w, channels = buffer.shape
        unpacked = np.unpackbits(buffer, axis=-1, bitorder='little')[..., :channels * bits]
        values = unpacked.reshape(h, w, channels, bits)
        return (values * (1 << np.arange(bits))).sum(-1).astype(np.float32).ravel()


class DorefanetCPU(CPUBackend):
    def __init__(self):
        super().__init__('dorefanet')


    def load_image(self, imgfile):
        """ Load image from file and apply transformation. """

        imgfile = os.path.abspath(imgfile)
        if not os.path.exists(imgfile) or not os.path.isfile(imgfile):
            raise IOError("Image file does not exist")

        img = cv2.imread(imgfile).astype('float32')
        img = self.transform(img)

        img_class = os.path.basename(imgfile).split('_')[0]

        return img, img_class

    def center_crop(self, img, shape):
        """ Crop image to specified shape. """

        orig_shape = img.shape
        h = int((orig_shape[0] - shape[0]) * 0.5)
        w = int((orig_shape[1] - shape[1]) * 0.5)

        return img[h : h + shape[0], w : w + shape[1]]

    def resize(self, img, shape):
        """ Resize image to specified shape. """

        orig_shape = img.shape[:2]
        scale = 256.0 / min(orig_shape)
        h = int(max(shape[0], min(orig_shape[1], scale * orig_shape[1])))
        w = int(max(shape[1], min(orig_shape[0], scale * orig_shape[0])))
        img = cv2.resize(img, (h, w), interpolation=cv2.INTER_CUBIC)

        return img

    def transform(self, img, shape=(224, 224)):
        """ Transform image with ILSVRC dataset metadata. """

        if shape != (224, 224):
            raise NotImplementedError("To be implemented")

        # Get ILSVRC metadata
        pp_mean = np.load(ILSVRC_PIXEL_MEAN_FILE, allow_pickle=True)
        pp_mean_224 = pp_mean[16:-16, 16:-16, :]

        # Crop and rescale image to 224x224
        img = self.resize(img, shape)
        img = self.center_crop(img, shape)
        img = img - pp_mean_224
        img = img[np.newaxis, :, :, :]

        # Normalize pixel values in range [0, 1.0]
        img = img / 255.0


        # Trasform [0, 1] floating point values into integer values (8-bit)
        # img = img * (2**7 - 1)
        # img[img < 0] = img[img < 0] + 255
        # img = np.floor(img)
        # img = img.astype(np.uint8)

        return img

class TinierYoloCPU(CPUBackend):
    def __init__(self):
        super().__init__('tinier-yolo')


@contextmanager
def elapsed_notice(label):
    stop = threading.Event()
    start = time.perf_counter()
    def report():
        while not stop.wait(15):
            print('{}: {:.0f} s elapsed (not an ETA)'.format(label, time.perf_counter()-start), flush=True)
    thread = threading.Thread(target=report, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1)


def snapshot(url='http://127.0.0.1:8080/snapshot'):
    request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.headers.get_content_type() not in ('image/jpeg', 'image/png'):
            raise ValueError('Use the still-image /snapshot URL, not the /stream URL.')
        data = response.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError('Snapshot exceeds 8 MiB.')
    with Image.open(io.BytesIO(data)) as opened:
        if opened.width * opened.height > 16_000_000:
            raise ValueError('Snapshot exceeds 16 megapixels.')
        return opened.convert('RGB')


@contextmanager
def temporary_image(image):
    if not Path('/dev/shm').is_dir():
        raise RuntimeError('RAM-backed /dev/shm is required.')
    with tempfile.TemporaryDirectory(prefix='qnn-rpi-', dir='/dev/shm') as folder:
        path = Path(folder) / 'input.png'
        image.save(path)
        yield path


class NativeImage(C.Structure):
    _fields_ = [('w', C.c_int), ('h', C.c_int), ('c', C.c_int), ('data', C.POINTER(C.c_float))]


class DarknetCPU:
    def __init__(self):
        self.root = DEPS / 'darknet'
        self.lib = C.CDLL(str(self.root / 'libdarknet.so'), mode=C.RTLD_LOCAL)
        signatures = {
            'load_image_color': ([C.c_char_p, C.c_int, C.c_int], NativeImage),
            'letterbox_image': ([NativeImage, C.c_int, C.c_int], NativeImage),
            'free_image': ([NativeImage], None),
            'parse_network_cfg': ([C.c_char_p], C.c_void_p),
            'free_network': ([C.c_void_p], None),
            'forward_region_layer_pointer_nolayer': ([C.c_void_p, C.POINTER(C.c_float)], None),
            'draw_detection_python': ([C.c_void_p, C.c_char_p, C.c_float, C.c_float,
                                       C.c_char_p, C.c_char_p, C.c_char_p, C.c_char_p], None),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.lib, name)
            fn.argtypes, fn.restype = args, result
        self.net = self.lib.parse_network_cfg(os.fsencode(PARAMS / 'tinier-yolo-bwn-3bit-relu-nomaxpool.cfg'))
        if not self.net:
            raise RuntimeError('Darknet configuration load failed.')

    def close(self):
        if self.net:
            self.lib.free_network(self.net)
            self.net = None

    def load_image(self, path):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        original = letterboxed = None
        try:
            original = self.lib.load_image_color(os.fsencode(path), 0, 0)
            if not original.data:
                raise RuntimeError('Image load failed.')
            letterboxed = self.lib.letterbox_image(original, 416, 416)
            if not letterboxed.data:
                raise RuntimeError('Letterboxing failed.')
            pixels = np.ctypeslib.as_array(letterboxed.data, (3, 416, 416)).copy()
            return np.swapaxes(pixels, 0, 2)[np.newaxis]
        finally:
            if letterboxed is not None and letterboxed.data:
                self.lib.free_image(letterboxed)
            if original is not None and original.data:
                self.lib.free_image(original)

    def draw(self, path, values, threshold=0.3):
        if not self.net:
            raise RuntimeError('Darknet model was released.')
        if not 0 < threshold < 1:
            raise ValueError('Threshold must be between 0 and 1.')
        if (values.shape != (125, 13, 13) or values.dtype != np.float32
                or not values.flags.c_contiguous or not np.all(np.isfinite(values))):
            raise ValueError('Expected finite contiguous float32 head (125, 13, 13).')
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        with tempfile.TemporaryDirectory(prefix='qnn-rpi-', dir='/dev/shm') as folder:
            prefix = Path(folder) / 'result'
            scores = Path(folder) / 'scores.txt'
            paths = [str(path), str(self.root / 'data/voc.names'), str(self.root) + '/', str(prefix), str(scores)]
            if any(len(p.encode()) > 200 for p in paths):
                raise ValueError('Use shorter paths for the legacy Darknet C helper.')
            self.lib.forward_region_layer_pointer_nolayer(self.net, values.ctypes.data_as(C.POINTER(C.c_float)))
            self.lib.draw_detection_python(self.net, paths[0].encode(), threshold, 0.5,
                                           *(p.encode() for p in paths[1:]))
            with Image.open(str(prefix) + '.png') as opened:
                preview = opened.convert('RGB')
            detections = []
            for line in scores.read_text().splitlines():
                if line.strip():
                    name, score = line.rsplit(':', 1)
                    detections.append((name.strip(), float(score.strip().rstrip('%')) / 100))
            return preview, sorted(detections, key=lambda item: item[1], reverse=True)


def machine_info():
    model = Path('/proc/device-tree/model')
    return {'model': model.read_text().rstrip('\0') if model.exists() else platform.machine(),
            'platform': platform.platform(), 'python': platform.python_version(),
            'numpy': np.__version__, 'opencv': cv2.__version__}
