class _Reader:
    __slots__ = ("buf", "i")

    def __init__(self, buf: bytes):
        self.buf = buf
        self.i = 0

    def skip(self) -> None:
        b = self.buf[self.i]
        self.i += 1

        # positive fixint / negative fixint
        if b <= 0x7F or b >= 0xE0:
            return

        # fixmap
        if 0x80 <= b <= 0x8F:
            for _ in range(b & 0x0F):
                self.skip()
                self.skip()
            return

        # fixarray
        if 0x90 <= b <= 0x9F:
            for _ in range(b & 0x0F):
                self.skip()
            return

        # fixstr
        if 0xA0 <= b <= 0xBF:
            self.i += b & 0x1F
            return

        # nil / bool
        if b in (0xC0, 0xC2, 0xC3):
            return

        # bin8 / bin16 / bin32
        if b == 0xC4:
            n = self.buf[self.i]
            self.i += 1 + n
            return
        if b == 0xC5:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2 + n
            return
        if b == 0xC6:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4 + n
            return

        # ext8 / ext16 / ext32
        if b == 0xC7:
            n = self.buf[self.i]
            self.i += 2 + n
            return
        if b == 0xC8:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 3 + n
            return
        if b == 0xC9:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 5 + n
            return

        # float / uint / int / str
        sizes = {0xCA: 4, 0xCB: 8, 0xCC: 1, 0xCD: 2, 0xCE: 4, 0xCF: 8, 0xD0: 1, 0xD1: 2, 0xD2: 4, 0xD3: 8}
        n = sizes.get(b)
        if n is not None:
            self.i += n
            return

        # str8 / str16 / str32
        if b == 0xD9:
            n = self.buf[self.i]
            self.i += 1 + n
            return
        if b == 0xDA:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2 + n
            return
        if b == 0xDB:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4 + n
            return

        # array16 / array32
        if b == 0xDC:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2
            for _ in range(n):
                self.skip()
            return
        if b == 0xDD:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4
            for _ in range(n):
                self.skip()
            return

        # map16 / map32
        if b == 0xDE:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2
            for _ in range(n):
                self.skip()
                self.skip()
            return
        if b == 0xDF:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4
            for _ in range(n):
                self.skip()
                self.skip()
            return

        # fixext 1/2/4/8/16
        if b in (0xD4,):
            self.i += 2
            return
        if b == 0xD5:
            self.i += 3
            return
        if b == 0xD6:
            self.i += 5
            return
        if b == 0xD7:
            self.i += 9
            return
        if b == 0xD8:
            self.i += 17
            return

        raise ValueError(f"unsupported MessagePack byte: 0x{b:02x}")

    def read_str(self) -> str | None:
        b = self.buf[self.i]
        self.i += 1

        if b == 0xC0:
            return None

        if 0xA0 <= b <= 0xBF:
            n = b & 0x1F
        elif b == 0xD9:
            n = self.buf[self.i]
            self.i += 1
        elif b == 0xDA:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2
        elif b == 0xDB:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4
        else:
            raise ValueError(f"expected string, got 0x{b:02x}")

        end = self.i + n
        value = self.buf[self.i : end].decode("utf-8")
        self.i = end
        return value

    def read_map_len(self) -> int:
        b = self.buf[self.i]
        self.i += 1

        if 0x80 <= b <= 0x8F:
            return b & 0x0F
        if b == 0xDE:
            n = int.from_bytes(self.buf[self.i : self.i + 2], "big")
            self.i += 2
            return n
        if b == 0xDF:
            n = int.from_bytes(self.buf[self.i : self.i + 4], "big")
            self.i += 4
            return n

        raise ValueError(f"expected map, got 0x{b:02x}")
