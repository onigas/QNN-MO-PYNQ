"""Prepare local dependencies without replacing system libzip or PYNQ files."""
import bz2
import hashlib
import platform
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'raspberry_pi/.deps'
URL = 'https://deb.debian.org/debian/pool/main/libz/libzip/libzip4_1.7.3-1+b1_arm64.deb'
SHA256 = 'e6dd28155c1aa8b797304622af9cc1099663c4171f858c63fe975ba85c27d9a8'

def main():
    if platform.machine() != 'aarch64':
        raise SystemExit('Install 64-bit ARM64 Linux on the Raspberry Pi first.')
    DEPS.mkdir(parents=True, exist_ok=True)
    for archive in (ROOT / 'qnn/params').rglob('*.bz2'):
        target = archive.with_suffix('')
        if target.exists():
            continue
        partial = target.with_name(target.name + '.partial')
        print('Decompressing', archive.name, flush=True)
        try:
            with bz2.open(archive, 'rb') as src, partial.open('wb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    lib = DEPS / 'libzip4/usr/lib/aarch64-linux-gnu/libzip.so.4'
    if not lib.exists():
        with tempfile.TemporaryDirectory(dir=DEPS) as folder:
            package = Path(folder) / 'libzip4.deb'
            with urllib.request.urlopen(URL, timeout=60) as src, package.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            if hashlib.sha256(package.read_bytes()).hexdigest() != SHA256:
                raise RuntimeError('libzip4 download checksum mismatch.')
            subprocess.run(['dpkg-deb', '-x', str(package), str(DEPS / 'libzip4')], check=True)
    print('Local libzip4 and model parameters ready.')

if __name__ == '__main__':
    main()
