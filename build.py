import argparse
import subprocess
import sys

nuitka_args = [
    '--standalone',
    '--assume-yes-for-downloads',
    # '--plugin-enable=numpy',
    '--include-data-dir=data=data',
    '--output-dir=Release',
    '--user-plugin=nuitka_plugins/MediapipePlugin.py'
]


def build():
    parser = argparse.ArgumentParser(description='Build motion input with Nuitka.')
    parser.add_argument('--lto', action='store_true',
                        help='Use link time optimisation. Default: False')
    parser.add_argument('--console', action='store_true',
                        help='Show console when running the built executable. Default: False')
    parser.add_argument('target_file', type=str,
                        help='Target file to build.')
    args = parser.parse_args()
    print(args)
    nuitka_args.append('--lto=yes')
    nuitka_args.append('--windows-disable-console')
    subprocess.call([sys.executable, "-m", "nuitka"] + nuitka_args + [args.target_file])


if __name__ == "__main__":
    build()
