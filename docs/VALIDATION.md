# Validation record - 2026-10-19

- 13 automated tests passed: 11 AES/reference tests and 2 GIF-writer tests.
- The four animations are 14 seconds long with infinite looping.
- All decoded frames after transparent-delta compression were compared with
  their pre-compression RGB frames: no pixel differences and no timing loss.
- Main desktop assets: 1600 x 548. Compact assets: 800 x 792.
- Animated frames were sampled from the complete timeline for visual review.
- The complete README was rendered locally in Chromium using in-memory HTML
  and embedded copies of the assets. Eight combinations of dark/light,
  desktop/mobile, and reduced/normal motion selected the intended image.
- No horizontal overflow or JavaScript error was found in those local checks.
- The repository's relative asset and documentation paths were checked.
- No font files, keys, tokens, external image dependencies, or build caches
  are included in the distributable archive.

This is not a live GitHub deployment test. Check the final uploaded profile
as described in PUBLISHING.md. The animated GIFs have no JavaScript dependency;
JavaScript is used only by the optional local preview's static-preview button.
