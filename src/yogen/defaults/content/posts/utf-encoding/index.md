---
title: Decoding UTFs
author: Naza Gonella
date: 13/12/25
template: template
section: posts
---

---

As a small project I built a simple JSON parser in C. I first added support for all data types, except for Unicode escape characters (JSON accepts values such as `\u03C0` if you don't feel like manually copy-pasting the character `π` with code point `U+03C0`). I didn't find it urgent to add support for them right away, but when I finally got around to it, I realized encoding Unicode characters wasn't as simple as I had expected. You are not supposed to just put the raw code point value into the data structure.

So I decided to dive deep into Unicode and its encodings, and write about what I learned in the process. Hopefully you'll also pick something up along the way.

---

### Code Structure and Endianness

In each UTF encoding section, there will be a function named `CodepointToX` written in C that takes a code point and transforms it to its proper encoding, returning the size of the encoding in bytes.

I'm using a *big-endian* layout for writing sequential bytes: the most significant byte comes first. This also includes a big-endian implementation for the `CodepointToX` functions in [UTF-16](#utf-16-and-surrogate-pairs) and [UTF-32](#utf-32-the-naive-approach). You can find little-endian implementations in the [repository](https://github.com/NazaGonella/utf-encodings).

The [bonus](#bonus-combining-characters) section contains code written in Python.

---

### Unicode is not just ASCII++

You probably know ASCII, characters represented by numbers from 0 to 127; you may also know Unicode, same thing as ASCII but expanded, right?
There is a slight difference. ASCII and Unicode are both *coded character sets*, they map abstract symbols to numeric values called *code points*. The way they differ is on how they store these code points in memory, what is called *encoding*. ASCII is both a coded character set and an encoding format. Unicode itself is NOT an encoding format, in fact, it has multiple encodings.

---

### How ASCII does it

ASCII is straightforward. These are small values, we can assign a byte for each code point so the character with the code point `84` would be stored in a byte like `0101 0100`. We can extend this idea to Unicode with a naive approach, mapping the code point directly to bytes.


The problem arises from the number of characters in Unicode, over 150,000 characters that will need more than a single byte. This gets worse when you take into account the *codespace* of Unicode, the total set of possible codepoints Unicode defines for present and future use, which ranges from 0 to 1,114,111 code points[^1], or `U+0000` to `U+10FFFF` using Unicode notation with the `U+` prefix.

---

### UTF-32: The Naive Approach

The UTF-32 encoding solves this by assigning 4 bytes for each code point. Code point `84` (`54` in hexadecimal) would be stored as  `00 00 00 54`. A string like `Dog` would be encoded this way in binary:

- D: `0000 0000` `0000 0000` `0000 0000` `0100 0100`
- o: `0000 0000` `0000 0000` `0000 0000` `0110 1111`
- g: `0000 0000` `0000 0000` `0000 0000` `0110 0111`

You may notice the problem UTF-32 introduces. A lot of bytes go to waste when using the most common letters in the English alphabet. What in ASCII takes only 3 bytes to encode (dog), becomes 12 bytes with UTF-32. With this encoding, every character takes the same amount of bytes, so we call UTF-32 a *fixed-length* encoding.

Another thing to notice is the order of the bytes, in this case we are using big-endian. This version of UTF-32 is called **UTF-32-BE**. The little-endian version is called **UTF-32-LE**.

    int CodepointToUTF32BE(unsigned int codepoint, unsigned char *output) {

        if (codepoint >= 0x0 && codepoint <= 0x10FFFF) {
            output[0] = (codepoint >> 24) & 0xFF;
            output[1] = (codepoint >> 16) & 0xFF;
            output[2] = (codepoint >> 8) & 0xFF;
            output[3] = codepoint & 0xFF;
            return 4;
        }

        // invalid codepoint
        return 0;
    }

---

### UTF-16 and Surrogate Pairs

UTF-16 introduces *variable-width* encoding. Every code point is encoded as one or two 16-bit values, called *code units*.

Code points less than or equal to `U+FFFF`, outside the range `0xD800-0xDFFF` (you'll see why in a bit), correspond to characters in the *Basic Multilingual Plane* (BMP) and are directly encoded in a single 16-bit code unit.

For code points outside the BMP (greater than `U+FFFF`), UTF-16 uses *surrogate pairs*: each pair consists of two 16-bit code units, the first one being the *high surrogate* followed by the *low surrogate*.

Surrogate pairs follow a simple formula for encoding code points.

1. Subtract `0x10000` from the code point. The result is a 20-bit number in the range `0x00000-0xFFFFF`.
2. To make the **high surrogate**, take the *top* 10 bits of the 20-bit number and add the prefix `110110` (hex `0xD800`).
3. To make the **low surrogate**, take the *bottom* 10 bits of the 20-bit number and add the prefix `110111` (hex `0xDC00`).


So high surrogates have the form `1101` `10xx` `xxxx` `xxxx` and low surrogates `1101` `11xx` `xxxx` `xxxx`. The `x` bits are the data (or payload) bits carrying the code point value minus `0x10000`. This subtraction allows inserting values from 0 to 2^20 - 1, an additional 1,048,576 code points beyond the 65,536 code points of the BMP.

The high surrogate range is `0xD800-0xDBFF`. The low surrogate range is `0xDC00-0xDFFF`. The full surrogate block `0xD800-0xDFFF` is reserved exclusively in Unicode for surrogate code points. This means that no matter the UTF form, no character can have a code point in this range.

Like UTF-32, the order of the bytes determines the version of UTF-16, in this case we are describing **UTF-16BE** since it's big-endian. For little-endian it would be **UTF-16LE**.

    int CodepointToUTF16BE(unsigned int codepoint, unsigned char *output) {

        if (codepoint <= 0xFFFF) {
            if (codepoint >= 0xD800 && codepoint <= 0xDFFF) return 0; // values reserved for surrogate code points
            output[0] = (unsigned char)((codepoint >> 8) & 0xFF);
            output[1] = (unsigned char)(codepoint & 0xFF);
            return 2;
        }
        else if (codepoint <= 0x10FFFF) {
            unsigned int codepoint_u = codepoint - 0b10000;
            unsigned int high = (0b110110 << 10) | ((codepoint_u >> 10) & 0b1111111111);
            unsigned int low  = (0b110111 << 10) | (codepoint_u & 0b1111111111);

            output[0] = (high >> 8) & 0xFF;
            output[1] = high & 0xFF;
            output[2] = (low >> 8) & 0xFF;
            output[3] = low & 0xFF;
            return 4;
        }

        // invalid codepoint
        return 0;
    }

---

### UTF-8: The Standard Encoding

Now let's look into UTF-8, which also uses variable-width encoding.

In UTF-8, the number of bytes it takes to store a code point corresponds to the range of the value. Code points from `U+0000` to `U+007F` are stored in 1 byte, ranges from `U+0080` to `U+07FF` are stored in 2 bytes, and so on.

- `U+00000` - `U+00007F`: 1 Byte
- `U+00080` - `U+0007FF`: 2 Bytes
- `U+00800` - `U+00FFFF`: 3 Bytes
- `U+01000` - `U+10FFFF`: 4 Bytes

The Smiling Face with Sunglasses emoji 😎 corresponds to the Unicode code point `U+1F60E` which in UTF-8 uses 4 bytes. How would you encode this?

If we took the same plain encoding approach as UTF-32 there would be 4 bytes one next to the other, but nothing to indicate that those 4 bytes make a single character. How do we know if this isn't 4 characters each one taking 1 byte? Or 2 characters of 2 bytes? Let's say we want to index the third character in a string. How would we do that?

We need to define a more complex structure when working with variable-width encoding. An ideal encoding format will make it possible to identify where a character starts and where it ends in a string.

A document with UTF-8 encoding will have every byte either be a *leading byte*, which indicates the start of a character as well as how many bytes follow it, or a *continuation byte*, which allows validating the sequence.

`U+1F60E` (or `0001 1111 0110 0000 1110` in binary) encoded with UTF-8 looks like this:

- `(11110)000`
- `(10)011111`
- `(10)011000`
- `(10)001110`

Inside the parentheses are the header bits. Just by looking at the header bits we can determine if we are in a leading or continuation byte.

Continuation bytes start with `10`. We look at continuation bytes to validate UTF-8. If the number of continuation bytes do not correspond to those indicated by the leading byte, we know it's invalid UTF-8.

Leading bytes in multi-byte sequences consist of a series of ones followed by a zero. The number of ones indicates the total number of bytes used by the code point, including the leading byte. In our emoji example we see the leading byte has header bits `11110`, so we can read the code point as one character of 4 bytes. This rule applies to all code point lengths except for those of 1 byte, the ASCII characters.

1-byte characters have a leading byte that starts with zero, followed by the code point value. The letter `A` will be encoded in UTF-8 the same way as one would encode it in ASCII.[^2]

The rest of the bits are the data bits. These contain the code point value in binary, padded with leading zeros.

| First code point | Last code point | Byte 1 | Byte 2 | Byte 3 | Byte 4 |
|------------------|-----------------|--------|--------|--------|--------|
| U+0000   | U+007F   | 0xxxxxxx |-|-|-|
| U+0080   | U+07FF   | 110xxxxx | 10xxxxxx |-|-|
| U+0800   | U+FFFF   | 1110xxxx | 10xxxxxx | 10xxxxxx |-|
| U+010000 | U+10FFFF | 11110xxx | 10xxxxxx | 10xxxxxx | 10xxxxxx |

The table contains the bytes with the header bits set. The `x` bits correspond to the data bits holding code point values.

    int CodepointToUTF8(unsigned int codepoint, unsigned char *output) {

        if (codepoint <= 0x7F) {
            output[0] = (unsigned char)codepoint;
            return 1;
        } else if (codepoint <= 0x7FF) {
            output[0] = (unsigned char)(0b11000000 | ((codepoint >> 6) & 0x1F));    // (110)0 0000 | 000x xxxx
            output[1] = (unsigned char)(0b10000000 | (codepoint & 0x3F));           // (10)00 0000 | 00xx xxxx
            return 2;
        } else if (codepoint <= 0xFFFF) {
            output[0] = (unsigned char)(0b11100000 | ((codepoint >> 12) & 0x0F));   // (1110) 0000 | 0000 xxxx
            output[1] = (unsigned char)(0b10000000 | ((codepoint >> 6) & 0x3F));    // (10)00 0000 | 00xx xxxx
            output[2] = (unsigned char)(0b10000000 | (codepoint & 0x3F));           // (10)00 0000 | 00xx xxxx
            return 3;
        } else if (codepoint <= 0x10FFFF) {
            output[0] = (unsigned char)(0b11110000 | ((codepoint >> 18) & 0x07));   // (1111 0)000 | 0000 0xxx
            output[1] = (unsigned char)(0b10000000 | ((codepoint >> 12) & 0x3F));   // (10)00 0000 | 00xx xxxx
            output[2] = (unsigned char)(0b10000000 | ((codepoint >> 6) & 0x3F));    // (10)00 0000 | 00xx xxxx
            output[3] = (unsigned char)(0b10000000 | (codepoint & 0x3F));           // (10)00 0000 | 00xx xxxx
            return 4;
        }

        // invalid codepoint
        return 0;
    }

---

### Encoding Code Points

I will be using this wrapper to quickly print different code points.

    void PrintCodepointChar(int codepoint) {
        unsigned char encodedChar[5];   // a Unicode character doesn't take more than 4 bytes, the 5th byte is for the null terminator

        size_t len = CodepointToUTF8(codepoint, encodedChar);

        encodedChar[len] = '\0';
        printf("%s\n", encodedChar);
    }

If we run the code in a terminal with UTF-8 encoding we get the following when printing.

    PrintCodepointChar(0x0040);
        // OUTPUT: @
    PrintCodepointChar(0xE9);
        // OUTPUT: é
    PrintCodepointChar(0x03BB);
        // OUTPUT: λ
    PrintCodepointChar(0x266A);
        // OUTPUT: ♪
    PrintCodepointChar(0x1F60E);
        // OUTPUT: 😎
    PrintCodepointChar(0x1F40C);
        // OUTPUT: 🐌
    PrintCodepointChar(0x1F697);
        // OUTPUT: 🚗
    PrintCodepointChar(0x1F43B);
        // OUTPUT: 🐻

Let's change the wrapper function a little to showcase a cool Unicode feature.

    void PrintCodepointCombiningChar(int codepointBase, int codepointComb) {
        unsigned char encodedChars[9];

        unsigned char* p = encodedChars;
        p += CodepointToUTF8(codepointBase, encodedChars);
        p += CodepointToUTF8(codepointComb, p);

        *p = '\0';
        printf("%s\n", encodedChars);
    }

In this function we define `encodedChars` as a string containing the encoded code point `codepointBase` followed by the encoded code point `codepointComb`.

If we use this function with regular characters we get

    PrintCodepointCombiningChar(0x1F47D, 0x1F916);
        // OUTPUT: 👽🤖
    PrintCodepointCombiningChar(0x1F355, 0x1F62D);
        // OUTPUT: 🍕😭

That was to be expected, let's try with some other characters

    PrintCodepointChar(0x0065);                     
        // OUTPUT: e
    PrintCodepointChar(0xE9);                       
        // OUTPUT: é
    PrintCodepointCombiningChar(0x0065, 0x0301);    
        // OUTPUT: é

What exactly happened in the last line? Why was the string composed of the characters with code points `0x0065` and `0x0301` printed as a single character?

---

### Bonus! Combining characters

Not all characters have a direct visual representation (for example, control characters like the null terminator or line breaks), and not all characters have a single code point when encoded in Unicode. Believe it or not, the letters `é` and `é` don't share the same code point

    char1 = "é".encode("utf-8")
    char2 = "é".encode("utf-8")

    print("char 1 byte length:", len(char1))
    print("char 2 byte length", len(char2))
    print("char 1 bytes:", char1)
    print("char 2 bytes:", char2)

        # OUTPUT:
        # char 1 byte length: 2
        # char 2 byte length 3
        # char 1 bytes: b'\xc3\xa9'
        # char 2 bytes: b'e\xcc\x81'

What is going on? The answer to this is *combining characters*. These are special characters that modify preceding characters in order to create new variations.

In the first example, we are using a *precomposed character*, a character with a dedicated code point. In this case `é` has the code point `U+00E9`. In the next example, we are creating a combination of two characters for `é`, `U+0065` + `U+0301`, that is the letter `e` and the acute diacritic. This is called a *decomposed* character.

Most letters and symbols accept combining characters, and there is no limit to how many you can apply. This allows you to create some monstrous-looking characters that this site's font won't allow me to render properly, so I'm attaching an image

![[Zalgo text!](https://en.wikipedia.org/wiki/Zalgo_text)](https://upload.wikimedia.org/wikipedia/commons/4/4a/Zalgo_text_filter.png)

Now comes a new problem: how do we know if two strings are the same? They may look the same when printed but have totally different encodings. Luckily, Unicode defines *Unicode equivalence* to solve this issue.

Code point sequences are defined as **canonically equivalent** if they represent the same abstract character while also looking the same when displayed. In the last case `é` (precomposed) and `é` (decomposed) would be an example of this type of equivalence. When code point sequences are **compatibility equivalent**, they might look similar, but are used in different contexts, as they represent different abstract characters. It is the case of `A` and `𝔸`. You understand the meaning of the word `𝔸mbiguous`, but that is not how the character is usually used.

Based on these equivalences the standard also defines *Unicode normalization*, to make sure that equivalent text sequences have consistent encodings. You can read further on this topic in this [article](https://mcilloni.ovh/2023/07/23/unicode-is-hard/#unicode-normalization) by Marco Cilloni.

[^1]: This doesn't mean all code points are assigned.
[^2]: One of the major benefits of using UTF-8 is backwards compatibility with ASCII.
