import subprocess
from dataclasses import dataclass
import re

subvol_re = re.compile(r'ID (\d+) gen (\d+) parent (\d+) top level (\d+) received_uuid ([0-9a-f-]+) *uuid ([0-9a-f-]+) * path (.*)')

def subvolumes(volume):
    out = subprocess.check_output(['/usr/bin/btrfs', 'subvolume', 'list', '-puR', volume])
    subvols = [Subvolume(line) for line in out.decode('utf-8').splitlines()]
    
    by_id = {}
    for sv in subvols:
        by_id[sv.id] = sv
    for (id, sv) in by_id.items():
        if sv.parent_id in by_id:
            sv.parent = by_id[sv.parent_id]
            sv.parent.children.append(sv)
    for sv in subvols:
        print(sv, sv.parent, [str(c) for c in sv.children])

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
        self.uuid = m.group(6)
        self.path = m.group(7)
    
        self.parent = None
        self.children = []

    def __str__(self):
        return self.path
