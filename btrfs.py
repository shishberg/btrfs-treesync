import subprocess
from dataclasses import dataclass
import re

subvol_re = re.compile(r'ID (\d+) gen (\d+) parent (\d+) top level (\d+) received_uuid ([0-9a-f-]+) *uuid ([0-9a-f-]+) * path (.*)')

def subvolumes(volume):
    out = subprocess.check_output(['/usr/bin/btrfs', 'subvolume', 'list', '-puR', volume])
    subvols = [Subvolume(line) for line in out.decode('utf-8').splitlines()]
    return Subvolumes(subvols)

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

    def __init__(self, line: str):
        m = subvol_re.fullmatch(line)
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

    def __str__(self):
        return self.path

class Subvolumes(object):
    def __init__(self, subvols: list[Subvolume]):
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
