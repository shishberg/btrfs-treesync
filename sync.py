import argparse
import btrfs
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src', type=str, help='source btrfs volume')
    parser.add_argument('dst', type=str, help='destination btrfs volume')
    parser.add_argument('--root', type=str, default='.snapshots', help='root subvolume to sync')
    args = parser.parse_args()

    src_subvols = btrfs.subvolumes(args.src)
    dst_subvols = btrfs.subvolumes(args.dst)

    for sv in src_subvols.from_root(args.root):
        print(sv)

    return 0

if __name__ == '__main__':
    sys.exit(main())
