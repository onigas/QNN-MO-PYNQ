# Restoring the English-only QNN-MO-PYNQ repository

The multilingual organization was added **after** the English-only repository snapshot at commit:

`7ba3bc571bb24a4b05384be466389a229efdd2ba`

A dedicated branch points to that exact snapshot:

[`backup/english-only-2026-11-05`](https://github.com/onigas/QNN-MO-PYNQ/tree/backup/english-only-2026-11-05)

**Preserve this branch unchanged.** It includes the English laboratory notebooks, technical sources and assets, the English README, and the original Xilinx license and notices, exactly as they were before the multilingual folders were introduced.

## Option 1 — Inspect or use the old English version (no changes)

On GitHub, open the backup branch link above, or select `backup/english-only-2026-11-05` from the branch dropdown. You can browse and download the English-only version without changing `master`.

For a local checkout of the archived layout:

```bash
git clone --branch backup/english-only-2026-11-05 --single-branch \
  https://github.com/onigas/QNN-MO-PYNQ.git QNN-MO-PYNQ-english-only
```

This is a separate checkout; it does not change the public `master` branch.

## Option 2 — Make English-only the current main layout again (reviewable)

If the multilingual structure is no longer wanted, restore the **content of the snapshot** through a separate branch and a pull request rather than rewriting Git history.

From a clean local checkout (no uncommitted work):

```bash
git fetch origin master backup/english-only-2026-11-05
git switch -c restore-english-only origin/master
git restore --source=origin/backup/english-only-2026-11-05 --staged --worktree -- .
git commit -m "Restore English-only QNN laboratory layout"
git push -u origin restore-english-only
```

Then create a GitHub pull request **from `restore-english-only` into `master`**, review the changed-file list, and merge when appropriate. This makes the current files match the snapshot while retaining the commit history and the multilingual development history.

**Important:** This full content restoration also discards later work on `master` *from the resulting file tree* if it was not present in the English-only snapshot, although the commits remain accessible in Git history. Review new technical changes before merging; prefer selective removal of multilingual folders if those later improvements should be retained. Do not use a force push or delete the backup branch.

## What remains unchanged during multilingual development

- The English notebooks remain in their original `notebooks/` paths.
- The original Xilinx framework, model parameters, overlays, files and BSD-3-Clause copyright notice are retained.
- Romanian and Hungarian notebook copies are under `notebooks/ro/` and `notebooks/hu/`.
- `notebooks/en/` is a link catalog pointing to the original English files.
- Hardware validation is still required for translated copies.

[Main repository](README.md) · [Language selection](notebooks/README.md)
