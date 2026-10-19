# Publish the profile

## Ready-to-upload files

The rendered GIFs and PNGs are already included. You do not need Python,
GitHub Actions, an API key, a CDN, or an image-generation service to use them.

1. Create a **public** GitHub repository named exactly **v1rtu3x**, owned by
   the **v1rtu3x** account. For an existing profile repository, work on a branch
   and review the diff instead of overwriting unrelated files.
2. Extract the archive. Upload the **contents** of its `v1rtu3x` folder,
   not the outer folder and not the ZIP itself.
3. Confirm the repository root contains `README.md`, `README-static.md`,
   and `assets/`. Commit the files, then visit your GitHub profile.

GitHub displays a profile README when a public repository matching the
username contains a nonempty root `README.md`:
https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme

## Quick checks after upload

- The banner loads rather than displaying a broken-image icon.
- It starts with a readable name and role, even when GIF autoplay is disabled.
- The name rolls into place and the terminal text types out during the loop.
- The four AES transformations animate; there is no extra project showcase.
- Every contribution and publication link resolves.
- The compact header loads on a narrow viewport.
- The static version link works.

The `<picture>` element selects desktop/mobile and dark/light assets using
browser media preferences. Exact selection can depend on GitHub and browser
settings; the fallback is the dark desktop GIF. The static version is provided
independently of animation preferences. A local preview is not a substitute
for checking the final GitHub-rendered profile.

GitHub lets visitors control GIF autoplay:
https://docs.github.com/en/account-and-profile/how-tos/account-settings/managing-accessibility-settings

## Local preview

From this folder:

```bash
python -m http.server 8765
```

Open `http://localhost:8765/preview.html`. This page is a local visual preview,
not a replica of every GitHub layout detail. It is not needed on your profile.

## Customize or rebuild

```bash
python -m venv .venv
# Linux / macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python source/render.py
```

Install DejaVu Sans Mono locally. Font files are intentionally not bundled.
Alternatively, provide paths to your own regular and bold monospaced fonts:

```bash
python source/render.py --font /path/to/regular.ttf --bold-font /path/to/bold.ttf
```

To regenerate only the main animation:

```bash
python source/render.py --theme dark --layout desktop
```

Source: `source/render.py`. Lossless GIF compression: `source/optimize_gif.py`. AES values: `source/aes_trace.py`.
Palette rationale and animation behavior: `docs/DESIGN.md`.

No remote repository has been created or modified by this package.
