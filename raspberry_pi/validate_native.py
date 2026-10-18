"""Run on the Pi before comparing inference timings."""
import argparse
import time
import numpy as np
from qnn_cpu import ROOT, CPUBackend, DarknetCPU, load_cpu_library

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
    output = np.zeros_like(expected)
    model = CPUBackend(args.model)
    try:
        model.init_accelerator()
        start = time.perf_counter()
        model.inference(inputs, output)
        duration = time.perf_counter() - start
    finally:
        model.deinit_accelerator()
    if not np.array_equal(output, expected):
        raise SystemExit('FAIL: {} packed bytes differ. Stop before benchmarking.'.format(np.count_nonzero(output != expected)))
    print('PASS: exact packed reference output; {:.3f} s'.format(duration))

if __name__ == '__main__':
    main()
