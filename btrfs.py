import subprocess
from dataclasses import dataclass
import re

subvol_re = re.compile(r'ID (\d+) gen (\d+) parent (\d+) top level (\d+) received_uuid ([0-9a-f-]+) *uuid ([0-9a-f-]+) * path (.*)')

@dataclass
class Subvolume:
    id: int
    gen: int
    parent: int
    top_level: int
    received_uuid: str
    uuid: str
    path: str

    def __init__(self, line):
        m = subvol_re.fullmatch(line)
        if not m:
            raise Exception("can't parse subvolume line", line)
        self.id = int(m.group(1))
        self.gen = int(m.group(2))
        self.parent = int(m.group(3))
        self.top_level = int(m.group(4))
        self.received_uuid = m.group(5)
        self.uuid = m.group(6)
        self.path = m.group(7)

def subvolumes(volume):
    out = subprocess.check_output(['/usr/bin/btrfs', 'subvolume', 'list', '-puR', volume])
    return [Subvolume(line) for line in out.decode('utf-8').splitlines()]
