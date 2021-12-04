import argparse
import btrfs
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src', type=str, help='source btrfs volume')
    parser.add_argument('dst', type=str, help='destination btrfs volume')
    parser.add_argument('--root', type=str, default='.snapshots', help='root subvolume to sync')
    args = parser.parse_args()

    src = btrfs.subvolumes(args.src)
    dst = btrfs.subvolumes(args.dst)

    read_write = []
    try:
        for src_sv in src.from_root(args.root):
            read_only = src_sv.is_read_only()
            if not read_only:
                src_sv.set_read_only(True)
                read_write.append(src_sv)

            if src_sv.uuid in dst.by_received_uuid:
                continue

            src_sv.send(dst)

            dst = btrfs.subvolumes(args.dst)
            if not src_sv.uuid in dst.by_received_uuid:
                print("sent from %s but wasn't received at %s" % (src_sv, dst))
                return 1
            dst_sv = dst.by_received_uuid[src_sv.uuid]
            if not read_only:
                dst_sv.set_read_only(False)
    finally:
        read_write.reverse()
        for src_sv in read_write:
            src_sv.set_read_only(False)

    return 0

if __name__ == '__main__':
    sys.exit(main())
