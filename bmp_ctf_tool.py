#!/usr/bin/env python3
"""
BMP CTF Repair Tool - by: D0V0
-------------------------------------------------
• Fixes malformed BMP headers often seen in CTFs:
    - Pixel offset
    - DIB header size
    - File size
    - Width / Height (deduced from pixel data)
• Keeps 8-bpp colour palettes intact.
• Optionally generates dimension variants.
"""

import struct
import argparse
from pathlib import Path

u16 = lambda b, o: struct.unpack_from('<H', b, o)[0]
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]
p32 = lambda b, o, v: struct.pack_into('<I', b, o, v)
row = lambda w, bpp: ((w * (bpp // 8) + 3) // 4) * 4


def header(buf: bytes) -> dict:
    return {
        "file_size": u32(buf, 2),
        "offset":    u32(buf, 10),
        "dib_size":  u32(buf, 14),
        "width":     u32(buf, 18),
        "height":    u32(buf, 22),
        "bpp":       u16(buf, 28)
    }


def print_header(h: dict, title: str) -> None:
    print(f"\n{title}")
    for k, v in h.items():
        print(f"  {k:9}: {v}")


def fix(path: str):
    buf = bytearray(Path(path).read_bytes())
    if buf[:2] != b'BM':
        raise ValueError("Not a BMP file")

    hdr = header(buf)
    original = hdr.copy()
    changed = False

    if hdr["bpp"] > 8 and hdr["offset"] != 54:          # True-color image
        p32(buf, 10, 54); hdr["offset"] = 54; changed = True
    if hdr["dib_size"] != 40:
        p32(buf, 14, 40); hdr["dib_size"] = 40; changed = True

    if hdr["file_size"] != len(buf):
        p32(buf, 2, len(buf)); hdr["file_size"] = len(buf); changed = True

    bytes_px = lambda: len(buf) - hdr["offset"]
    bpp_bytes = hdr["bpp"] // 8
    if bpp_bytes == 0:
        raise ValueError("Invalid bits-per-pixel value")

    if hdr["height"] and bytes_px() % hdr["height"] == 0:
        row_bytes = bytes_px() // hdr["height"]
        if row_bytes % 4 == 0:
            w = row_bytes // bpp_bytes
            if w and w != hdr["width"]:
                p32(buf, 18, w); hdr["width"] = w; changed = True

    rsize = row(hdr["width"], hdr["bpp"])
    if rsize and bytes_px() % rsize == 0:
        h = bytes_px() // rsize
        if h and h != hdr["height"]:
            p32(buf, 22, h); hdr["height"] = h; changed = True

    expected = hdr["offset"] + row(hdr["width"], hdr["bpp"]) * abs(hdr["height"])
    if len(buf) > expected:
        buf = buf[:expected]
        p32(buf, 2, len(buf))
        hdr["file_size"] = len(buf)
        changed = True
    elif len(buf) < expected:
        print("Warning: file appears truncated (missing pixel data)")

    out_path = f"{Path(path).stem}_fix.bmp"
    Path(out_path).write_bytes(buf)

    print_header(original,  "Original header")
    print_header(hdr,       "Fixed header")
    print(f"\nRepaired file: {out_path}\n")
    return out_path, hdr, bytes_px()


def brute_variants(fix_path: str, hdr: dict, px_bytes: int) -> None:
    """
    Generate width/height variants when the automatic fix
    still produces a distorted image.
    """
    variants = []
    var_dir = Path("variants")
    var_dir.mkdir(exist_ok=True)

    bpp_bytes = hdr["bpp"] // 8

    # Height variant
    row_bytes = row(hdr["width"], hdr["bpp"])
    if row_bytes and px_bytes % row_bytes == 0:
        h = px_bytes // row_bytes
        if h != hdr["height"]:
            nb = bytearray(Path(fix_path).read_bytes())
            p32(nb, 22, h)
            p32(nb, 2, len(nb))
            out = var_dir / f"{Path(fix_path).stem}_h{h}.bmp"
            out.write_bytes(nb)
            variants.append(out)

    # Width variant
    if hdr["height"] and px_bytes % hdr["height"] == 0:
        r = px_bytes // hdr["height"]
        if r % 4 == 0:
            w = r // bpp_bytes
            if w != hdr["width"]:
                nb = bytearray(Path(fix_path).read_bytes())
                p32(nb, 18, w)
                p32(nb, 2, len(nb))
                out = var_dir / f"{Path(fix_path).stem}_w{w}.bmp"
                out.write_bytes(nb)
                variants.append(out)

    if variants:
        print("Variants saved:")
        for v in variants:
            print(f"  {v}")
    else:
        print("No variants generated")


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair malformed BMP files used in CTF challenges")
    parser.add_argument("bmp", help="Path to BMP file")
    parser.add_argument("--brute", action="store_true", help="Generate dimension variants")
    parser.add_argument("--info",  action="store_true", help="Print header only, do not modify")
    args = parser.parse_args()

    buf = Path(args.bmp).read_bytes()
    print_header(header(buf), "BMP header")

    if args.info:
        return

    fixed_path, hdr_fixed, px = fix(args.bmp)
    if args.brute:
        brute_variants(fixed_path, hdr_fixed, px)


if __name__ == "__main__":
    main()
