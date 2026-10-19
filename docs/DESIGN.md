# Design and motion specification

## Layout

The desktop header follows the approved arrangement: thin terminal title bar,
large identity panel on the left, AES panel on the right, three aligned cards
beneath, and a bottom command strip. Typography, borders, and accents are
rendered from source rather than blurred or warped from a screenshot.

The mobile variant stacks the identity and AES panels while retaining the
three-card row. All informative text is repeated as real text in the README;
the banner is not the only accessible source of profile information.

## Motion

14-second loop, 25 rendered frames per second (40 ms each):

- At the beginning, the name and role are readable. A paused GIF is useful.
- From approximately 1.2 to 5.1 seconds, the name's letters scroll vertically
  in independent, eased character rolls and resolve to MARK-PAUL TAMAS.
- The role types in at approximately 4.75-6.2 seconds.
- The subtitle types in at approximately 6.3-8.2 seconds.
- The resolved identity remains visible for several seconds before the loop.
- AES operations are staged at 1.5, 4.0, 6.5, and 9.0 seconds.
- Name/footer carets pulse softly. Borders, cards, and primary layout stay still.

A shared palette is used across GIF frames to avoid color-palette flicker.
The static assets always show the resolved identity.

## Cryptographic accuracy and limits

The name's [decrypted] label is a visual identity-reveal metaphor. Rotating
characters is NOT how AES decryption works and does not represent breaking
AES. The name is not the plaintext for the adjacent AES calculation.

The panel demonstrates the FIRST FORWARD ROUND of AES-128, beginning after
its initial AddRoundKey. SubBytes uses the actual AES S-box; ShiftRows moves
rows left by 0,1,2,3 bytes; MixColumns uses arithmetic in GF(2^8); AddRoundKey
uses the expanded round-one key and displays byte-level XOR examples.
The loop is not presented as a full ten-round encryption or decryption.

This is an illustration, not a production cryptographic implementation.
The calculation is tested with the public AES known-answer vector:

- Input: 00112233445566778899aabbccddeeff
- Key: 000102030405060708090a0b0c0d0e0f
- Full AES-128 output: 69c4e0d86a7b0430d8cdb78070b4c55a

The rendered state is column-major as in FIPS 197. Intermediate values and
key expansion are tested in `tests/test_aes_trace.py`.

Reference: https://csrc.nist.gov/pubs/fips/197/final

## Palette

A digital adaptation of Sanzo Wada's Yellow Orange / Dark Tyrian Blue pairing
(combination 2), with added neutral tones for readable interface text.
Digital reference values: Yellow Orange #F99D1B; Dark Tyrian Blue #12354E.
The dark animation uses a softer #E7B26B accent and darker blue-black panels;
the light animation uses deep blue text and a darker amber accent for contrast.
These are interface adaptations, not claims of exact historic print colors.

Digital palette reference: https://colors.elwyn.co/
Concrete render colors: `source/palette.json` and `PALETTES` in the renderer.

No moving waveform, decorative metrics, external stats, or unmerged work
is included. The displayed project names identify accepted upstream work,
not claims of ownership of those projects.
