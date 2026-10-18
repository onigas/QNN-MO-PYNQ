"""Run on the Pi before comparing inference timings."""
import argparse
import time
import numpy as np
from qnn_cpu import ROOT, CPUBackend, DarknetCPU, load_cpu_library


def reference_buffers(model, inputs, expected):
    """Match main.cpp input loading and OffloadUtils::verifyBuffers."""
    net = model.load_network()
    params = model.network_json['parameters']
    bits = params['ACTIVATION_BITS']
    stride = params['MAX_IFM_CH'] * bits // 8
    if model.model == 'dorefanet':
        in_dim = net['split1']['input_dim']
        out_dim = net['merge4']['output_dim']
        out_channels = net['merge4']['output_channels']
    else:
        in_dim = net['conv1']['input'][1]
        out_channels, out_dim, _ = net['conv7']['output']
    in_bytes = in_dim * in_dim * stride
    out_bytes = out_dim * out_dim * stride
    valid_bytes = out_channels * bits // 8
    if out_channels * bits % 8 or valid_bytes > stride:
        raise ValueError('Unsupported reference layout.')
    # The original executable truncates oversized input files; singleInference
    # instead interprets their size as a different per-pixel stride. Truncate
    # here before passing the buffer. Smaller inputs retain native padding.
    if inputs.size >= in_bytes:
        inputs = np.ascontiguousarray(inputs[:in_bytes])
    elif inputs.size * 8 % (in_dim * in_dim):
        raise ValueError('Reference input has an invalid per-pixel size.')
    if expected.size < out_bytes:
        raise ValueError('Reference output is shorter than the native layout.')
    expected = expected[:out_bytes].reshape(out_dim * out_dim, stride)
    output = np.zeros((out_dim * out_dim, stride), dtype=np.uint8)
    print('Reference input: {} bytes; output: {} pixels, {} valid bytes/pixel (stride {}).'.format(
        inputs.size, out_dim * out_dim, valid_bytes, stride))
    return inputs, output, expected, valid_bytes

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--load-only', action='store_true')
    group.add_argument('--model', choices=['dorefanet', 'tinier-yolo'])
    args = parser.parse_args()
    if args.load_only:
        handles = [load_cpu_library(kind) for kind in ('W1A2', 'W1A3')]
        darknet = DarknetCPU()
        darknet.close()
        print('PASS: native libraries load. This does NOT validate inference.')
        return
    folder = ROOT / 'tests/Test_image' / args.model
    inputs = np.fromfile(folder / 'input.bin', dtype=np.uint8)
    expected = np.fromfile(folder / 'verification.bin', dtype=np.uint8)
    model = CPUBackend(args.model)
    inputs, output, expected, valid_bytes = reference_buffers(model, inputs, expected)
    try:
        model.init_accelerator()
        start = time.perf_counter()
        model.inference(inputs, output)
        duration = time.perf_counter() - start
    finally:
        model.deinit_accelerator()
    differences = output[:, :valid_bytes] != expected[:, :valid_bytes]
    if np.any(differences):
        raise SystemExit('FAIL: {} valid packed bytes differ in {} pixels. Stop before benchmarking.'.format(
            np.count_nonzero(differences), np.count_nonzero(np.any(differences, axis=1))))
    print('PASS: exact valid packed reference output (padding excluded); {:.3f} s'.format(duration))

if __name__ == '__main__':
    main()
