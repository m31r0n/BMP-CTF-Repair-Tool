# BMP CTF Repair Tool 🖼️🔧

A no‑frills, one‑command fixer for the **malformed BMP files** you meet in CTF
forensics challenges. It detects and patches the most common header mischief —
wrong pixel offset, fake DIB size, bogus dimensions, mismatched file length —
while **preserving palettes** in 8‑bpp images. Need more? Use `--brute` to try
extra width/height combos until the picture makes sense. Flag first, hex editor
later. 🚩

---

## Features

- **Pixel offset** → `54` bytes for true‑colour; untouched for 8‑bpp.
- **DIB header** forced to `40` bytes (Windows V3).
- `file_size` synchronised with the real file length.
- **Width / Height** inferred from pixel‑array size and 4‑byte padding.
- Strips hidden junk after the bitmap, but never your palette.
- `--brute` saves extra images with plausible dimensions in `variants/`.
- `--info` prints the header only (read‑only).

---

## A Bit of Theory 🤓

```text
| 14‑byte BMP header | 40‑byte DIB header | PALETTE (0–1024 B) | PIXELS |
          ↖ fields CTFs love to corrupt ↗          ↖ also targeted ↗
```

* **Pixel offset** (bytes 10–13) points to the pixel array; setting it huge
  can show a blank image.  
* **Width/Height** (bytes 18–25) define the raster grid; wrong values stretch,
  squash or crop the flag.  
* **file_size** (bytes 2–5) keeps things consistent for strict parsers.  
* **Padding**: each RGB row is 4‑byte aligned; miscount it and the picture
  shears diagonally.

This tool recalculates all of that from first principles, so you don’t have to.

---

## Usage

```bash
# Basic repair
python3 bmp_ctf_tool.py broken.bmp

# Repair + alternate dimensions (saved to ./variants/)
python3 bmp_ctf_tool.py broken.bmp --brute

# Header inspection only
python3 bmp_ctf_tool.py broken.bmp --info
```

Example output:

```text
BMP header
  file_size: 2893454
  offset   : 53434
  dib_size : 53434
  width    : 1134
  height   : 306
  bpp      : 24

Original header
  ...
Fixed header
  ...

Repaired file: broken_fix.bmp
```

With `--brute` you may get files like
`broken_fix_h850.bmp` or `broken_fix_w2634.bmp` inside **variants/**.

---

## Why Bother? 🎯

CTF authors love breaking headers: shifting pixel data, lying about sizes,
stuffing extra bytes after the bitmap. Most viewers choke and you’re left with
half a picture (literally). This script restores a **valid** BMP so you can see
what you’re meant to solve — a QR code, hidden text or the flag itself.

---

## License

MIT

