#!/usr/bin/env python3
"""How characters become bytes, and why 256 base tokens cover every possible input.
Run: python3 demo.py"""

print("=== a character is a number (its code point); UTF-8 is how that number is stored as bytes ===")
print(f"   {'char':>5}{'code point':>12}{'bytes':>7}{'UTF-8 bytes (hex)':>22}   bit pattern of the first byte")
for ch in ("A", "é", "€", "你", "🙂"):
    b = ch.encode("utf-8")
    lead = format(b[0], "08b")
    kind = {1: "0xxxxxxx  -> 1-byte char", 2: "110xxxxx  -> 2-byte char", 3: "1110xxxx  -> 3-byte char", 4: "11110xxx  -> 4-byte char"}[len(b)]
    print(f"   {ch:>5}{f'U+{ord(ch):04X}':>12}{len(b):>7}{' '.join(f'{x:02x}' for x in b):>22}   {lead}  {kind}")
print("   continuation bytes all start 10xxxxxx. the first byte's leading bits say how many follow.")
print("   ASCII (0-127) is exactly one byte, unchanged -- which is why English is cheap in bytes.")

print("\n=== so every byte is one of 256 values, and text is a sequence of them ===")
s = "the 🙂 café"
b = s.encode()
print(f"   {s!r}: {len(s)} characters -> {len(b)} bytes: {list(b)}")
print("   a byte-level tokenizer starts from these 256 values. any string in any language becomes")
print("   some sequence of them, so ids 0-255 alone can represent every possible input.")

print("\n=== decoding must see whole characters: the streaming glitch ===")
b = "🙂".encode()
for cut in (1, 2, 3, 4):
    print(f"   first {cut} byte(s) of {b!r}: {b[:cut].decode('utf-8', 'replace')!r}")
print("   a token boundary can fall inside a 4-byte character. until the next token arrives the")
print("   partial bytes decode to the replacement character -- the '\\ufffd' you see in bad streaming.")

print("\n=== byte count is not character count is not token count ===")
for s in ("Hello", "你好", "🙂🙂", "naïve"):
    print(f"   {s!r:<10} {len(s)} chars  {len(s.encode())} bytes")
print("   tokens sit on top of bytes (chapter 01), so a script's byte cost is a floor on its token cost --")
print("   and the tokenizer's merges, learned mostly from English, decide how far above that floor it lands.")
