# QNN-MO-PYNQ — Choose your language

**Educational laboratory adaptation:** Prof. dr. ing. habil. Stefan Oniga  
**Original QNN-MO framework and technical assets:** [Xilinx/QNN-MO-PYNQ](https://github.com/Xilinx/QNN-MO-PYNQ). Original notices and the BSD-3-Clause license are retained.

| Language | Open the laboratories | Status |
| --- | --- | --- |
| **English** | [English — 11 labs](en/README.md) | All available |
| **Română** | [Română — 11 laboratoare](ro/README.md) | All translated |
| **Magyar** | [Magyar — 11 laboratórium](hu/README.md) | Mind lefordítva |

The original **English notebooks remain at the top level of `notebooks/`** so existing PYNQ installations and paths continue to work. The `en/` directory is a catalog, not a second copy. The `ro/` and `hu/` folders contain separate translated notebook files using the same shared models and reference resources from their parent directory.

**Validation:** The translations have not been executed or benchmarked on the target PYNQ-Z2 and Raspberry Pi hardware. They retain the English versions' executable algorithms; PYNQ translations include a minimal directory lookup adaptation. For verified teaching use, test each translated copy on its target board first.

**Rollback:** The exact English-only repository snapshot from before the multilingual restructuring is preserved in [`backup/english-only-2026-11-05`](https://github.com/onigas/QNN-MO-PYNQ/tree/backup/english-only-2026-11-05). Keep this branch unchanged; switching to it on GitHub is a non-destructive way to inspect the old layout. See [rollback instructions](../MULTILINGUAL_ROLLBACK.md).
