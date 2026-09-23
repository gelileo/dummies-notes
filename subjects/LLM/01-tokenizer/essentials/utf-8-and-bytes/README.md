# Essential · UTF-8 and bytes

**Needed for:** *"ids 0–255 are the raw bytes"*, *"nothing is ever unrepresentable"*, and the
half-character streaming glitch in [chapter 01](../../README.md).

## A character is a number; UTF-8 is how the number is stored

```
    char  code point  bytes     UTF-8 bytes (hex)   bit pattern of the first byte
       A      U+0041      1                    41   01000001  0xxxxxxx  -> 1-byte char
       é      U+00E9      2                 c3 a9   11000011  110xxxxx  -> 2-byte char
       €      U+20AC      3              e2 82 ac   11100010  1110xxxx  -> 3-byte char
       你      U+4F60      3              e4 bd a0   11100100  1110xxxx  -> 3-byte char
       🙂     U+1F642      4           f0 9f 99 82   11110000  11110xxx  -> 4-byte char
   continuation bytes all start 10xxxxxx. the first byte's leading bits say how many follow.
   ASCII (0-127) is exactly one byte, unchanged -- which is why English is cheap in bytes.
```

Every character has a **code point** — a number. UTF-8 stores that number in one to four bytes,
and the first byte's leading bits announce how many follow. ASCII fits in one byte, unchanged,
which is why English is cheap in bytes and why every other script starts from a higher floor.

## Text is a sequence of 256 possible values

```
   'the 🙂 café': 10 characters -> 14 bytes: [116, 104, 101, 32, 240, 159, 153, 130, 32, 99, 97, 102, 195, 169]
   a byte-level tokenizer starts from these 256 values. any string in any language becomes
   some sequence of them, so ids 0-255 alone can represent every possible input.
```

That is the coverage guarantee behind byte-level tokenization: start the vocabulary with all 256
byte values and *any* string in *any* language is a sequence of things the table already
contains. There is never an unknown.

## Decoding needs whole characters

```
   first 1 byte(s) of b'\xf0\x9f\x99\x82': '�'
   first 2 byte(s) of b'\xf0\x9f\x99\x82': '�'
   first 3 byte(s) of b'\xf0\x9f\x99\x82': '�'
   first 4 byte(s) of b'\xf0\x9f\x99\x82': '🙂'
   a token boundary can fall inside a 4-byte character. until the next token arrives the
   partial bytes decode to the replacement character -- the '\ufffd' you see in bad streaming.
```

A token boundary can fall inside a four-byte character. Decode too early and you get the
replacement character until the rest arrives — the `\ufffd` glitch in naive streaming output.
Decoders buffer partial bytes for exactly this reason.

## Bytes, characters, tokens: three different counts

```
   'Hello'    5 chars  5 bytes
   '你好'       2 chars  6 bytes
   '🙂🙂'       2 chars  8 bytes
   'naïve'    5 chars  6 bytes
   tokens sit on top of bytes (chapter 01), so a script's byte cost is a floor on its token cost --
   and the tokenizer's merges, learned mostly from English, decide how far above that floor it lands.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **code point** | The number assigned to a character. `U+1F642` for 🙂. |
| **UTF-8** | The encoding that stores code points in 1–4 bytes; ASCII unchanged. |
| **byte** | A value 0–255. The unit tokenizers bottom out at. |
| **leading byte / continuation byte** | The first byte says how many bytes the character uses; the rest start `10…`. |
| **replacement character** `\ufffd` | What a decoder emits for an incomplete or invalid byte sequence. |
| **byte-level tokenizer** | One whose base vocabulary is the 256 byte values. Never fails on input. |
