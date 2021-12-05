import subprocess
from dataclasses import dataclass
import re
import os

SUBVOL_RE = re.compile(r'ID (\d+) gen (\d+) parent (\d+) top level (\d+) received_uuid ([0-9a-f-]+) *uuid ([0-9a-f-]+) * path (.*)')
BTRFS_BIN = '/usr/bin/btrfs'

def subvolumes(volume):
    out = subprocess.check_output([BTRFS_BIN, 'subvolume', 'list', '-puR', volume])
    subvols = [Subvolume(line, volume) for line in out.decode('utf-8').splitlines()]
    return Subvolumes(subvols, volume)

class Subvolume(object):
    id: int
    gen: int
    parent_id: int
    top_level: int
    received_uuid: str
    uuid: str
    path: str

    # parent
    # children

    def __init__(self, line: str, volume: str):
        m = SUBVOL_RE.fullmatch(line)
        if not m:
            raise Exception("can't parse subvolume line", line)
        self.id = int(m.group(1))
        self.gen = int(m.group(2))
        self.parent_id = int(m.group(3))
        self.top_level = int(m.group(4))
        self.received_uuid = m.group(5)
        if self.received_uuid == '-':
            self.received_uuid = None
        self.uuid = m.group(6)
        self.path = m.group(7)
    
        self.parent = None
        self.children = []

        self.full_path = os.path.join(volume, self.path)

    def __str__(self):
        return self.full_path

    def send(self, dst):
        send_cmd = [BTRFS_BIN, 'send']
        if self.parent:
            prev_sibling = None
            for sibling in self.parent.children:
                if sibling is self:
                    break
                if sibling.uuid in dst.by_received_uuid:
                    prev_sibling = sibling
            if prev_sibling:
                send_cmd += ['-p', prev_sibling.full_path]
        send_cmd.append(self.full_path)
        recv_cmd = [BTRFS_BIN, 'receive', os.path.dirname(os.path.join(dst.volume, self.path))]
        
        print(' '.join(send_cmd), '\\')
        print('|', ' '.join(recv_cmd))

        ps = subprocess.Popen(send_cmd, stdout=subprocess.PIPE)
        output = subprocess.check_output(recv_cmd, stdin=ps.stdout)
        ps.wait()

    def is_read_only(self) -> bool:
        out = subprocess.check_output([BTRFS_BIN, 'property', 'get', '-ts', self.full_path, 'ro'])
        return 'true' in out.decode('utf-8').lower()

    def set_read_only(self, ro: bool):
        cmd = [BTRFS_BIN, 'property', 'set', '-ts', self.full_path, 'ro', str(ro).lower()]
        print(' '.join(cmd))
        subprocess.check_output(cmd)

class Subvolumes(object):
    def __init__(self, subvols: list[Subvolume], volume: str):
        self.volume = volume

        self.roots = []
        self.by_id = {}
        self.by_uuid = {}
        self.by_received_uuid = {}

        for sv in subvols:
            self.by_id[sv.id] = sv
            self.by_uuid[sv.uuid] = sv
            if sv.received_uuid:
                self.by_received_uuid[sv.received_uuid] = sv

        for sv in subvols:
            if sv.parent_id in self.by_id:
                sv.parent = self.by_id[sv.parent_id]
                sv.parent.children.append(sv)
            else:
                self.roots.append(sv)
        
        sort_by_path(self.roots)

    def from_root(self, root):
        yield from enumerate_from_root(self.roots, root)

    def __str__(self) -> str:
        return self.volume

def sort_by_path(subvols: list[Subvolume]):
    subvols.sort(key=lambda sv: sv.path)
    for sv in subvols:
        sort_by_path(sv.children)

def enumerate_from_root(subvols: list[Subvolume], root, under_root=False):
    for sv in subvols:
        sv_under_root = under_root or sv.path == root
        if sv_under_root:
            yield sv
        yield from enumerate_from_root(sv.children, root, sv_under_root)
