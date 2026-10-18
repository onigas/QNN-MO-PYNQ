"""Regression checks for the original C++ testbench's binary layout."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'raspberry_pi'))
from validate_native import reference_buffers


class ReferenceLayout(unittest.TestCase):
    def test_dorefanet_oversized_input_is_truncated_not_restrided(self):
        model = SimpleNamespace(
            model='dorefanet',
            network_json={'parameters': {'ACTIVATION_BITS': 2, 'MAX_IFM_CH': 384}},
            load_network=lambda: {
                'split1': {'input_dim': 54},
                'merge4': {'output_dim': 6, 'output_channels': 256}})
        source = (np.arange(393216) % 251).astype(np.uint8)
        golden = np.zeros((36, 96), dtype=np.uint8)
        golden[:, :64] = 17
        golden[:, 64:] = 231  # Padding is outside the original verification.
        inputs, output, expected, valid = reference_buffers(model, source, golden.ravel())
        self.assertEqual(inputs.size, 279936)
        np.testing.assert_array_equal(inputs, source[:279936])
        self.assertEqual(output.shape, (36, 96))
        self.assertEqual(valid, 64)
        np.testing.assert_array_equal(expected[:, :valid], np.full((36, 64), 17))
        self.assertTrue(np.all(expected[:, valid:] == 231))

    def test_yolo_smaller_padded_input_is_preserved(self):
        model = SimpleNamespace(
            model='tinier-yolo',
            network_json={'parameters': {'ACTIVATION_BITS': 3, 'MAX_IFM_CH': 512}},
            load_network=lambda: {'conv1': {'input': [16, 208, 208]},
                                  'conv7': {'output': [512, 13, 13]}})
        source = np.arange(346112, dtype=np.uint8)
        golden = np.zeros(32448, dtype=np.uint8)
        inputs, output, expected, valid = reference_buffers(model, source, golden)
        np.testing.assert_array_equal(inputs, source)
        self.assertEqual(output.shape, (169, 192))
        self.assertEqual(expected.shape, output.shape)
        self.assertEqual(valid, 192)


if __name__ == '__main__':
    unittest.main()
