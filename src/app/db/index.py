import os
from typing import Optional

from sortedcontainers import SortedDict


class TableIndex:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = SortedDict()
        self.file = None
        self.open_file()
        self.is_closed = False
        self.load()

    def __del__(self):
        self.close()

    def close(self) -> None:
        self.dump()
        self.is_closed = True
        self.file.close()

    def open_file(self) -> None:
        if not os.path.exists(self.filepath):
            open(self.filepath, "w").close()
        self.file = open(self.filepath, "a+b")

    def load(self) -> None:
        assert not self.is_closed

        self.file.seek(0)
        while self.file.tell() != os.path.getsize(self.filepath):
            id_bytes = self.file.read(4)
            pos_bytes = self.file.read(8)
            if not id_bytes or not pos_bytes:
                break
            id_ = int.from_bytes(id_bytes, byteorder="little", signed=True)
            pos = int.from_bytes(pos_bytes, byteorder="little", signed=False)
            self.tree[id_] = pos

    def dump(self) -> None:
        if self.is_closed:
            return

        self.file.seek(0)
        self.file.truncate()
        for id_, pos in self.tree.items():
            self.file.write(id_.to_bytes(4, byteorder="little", signed=True))
            self.file.write(pos.to_bytes(8, byteorder="little", signed=False))
        self.file.flush()

    def exists(self, id_: int) -> bool:
        return id_ in self.tree.keys()

    def get(self, id_: int) -> Optional[int]:
        return self.tree.get(id_)

    def get_next_id(self) -> int:
        if len(self.tree) == 0:
            return 0

        # TODO: optimize
        return max(self.tree.keys()) + 1

    def set(self, id_: int, pos: int) -> None:
        self.tree[id_] = pos
        self.dump()

    def delete(self, id_: int) -> Optional[int]:
        result = self.tree.pop(id_, None)
        self.dump()
        return result

    def clear(self) -> None:
        self.tree.clear()
        self.dump()
