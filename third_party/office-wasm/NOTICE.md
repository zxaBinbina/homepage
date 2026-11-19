# Notices

The office-wasm viewer is licensed under the GNU Affero General Public License, version 3 or later (see `LICENSE`).
It is a modified version of, and is distributed together with, the following works.

## Office engine (AGPL-3.0)

This software is modified office applications that are based on Euro-Office, itself based on the original ONLYOFFICE
work. Modified versions must preserve notices sufficient to allow users to identify the original developer and the
source of the original work. (Text of the `ATTRIBUTION` file of cryptpad/onlyoffice-x2t-wasm.)

| Part | Origin | Licence |
|---|---|---|
| `artifacts/onlyoffice-editor/` (sdkjs, web-apps, dictionaries) | CryptPad build of https://github.com/cryptpad/onlyoffice-editor (sha512 in `artifacts/onlyoffice-editor.zip.sha512`) | AGPL-3.0 |
| `artifacts/x2t/` | CryptPad prebuilt x2t.wasm, https://github.com/cryptpad/onlyoffice-x2t-wasm | AGPL-3.0 |
| `artifacts/x2t-st/`, `artifacts/x2t-mt/` | built by `build/x2t/build.mjs` from cryptpad/onlyoffice-x2t-wasm (core 9.3.2) with the patch in `build/x2t/ctx/patches/` | AGPL-3.0 |
| `x2t/`, `viewer.mjs`, `index.html`, `tools/`, `build/`, `fonts/*.mjs`, `fonts/*.cjs` | this project | AGPL-3.0-or-later |

Upstream sources: https://github.com/Euro-Office/core, https://github.com/Euro-Office/sdkjs,
https://github.com/Euro-Office/web-apps, https://github.com/ONLYOFFICE/core, https://github.com/ONLYOFFICE/sdkjs,
https://github.com/ONLYOFFICE/web-apps.

"ONLYOFFICE" is a trademark of Ascensio System SIA. This project is not affiliated with or endorsed by Ascensio
System SIA, Euro-Office or XWiki SAS (CryptPad).

## Math fonts (SIL Open Font License 1.1)

`fonts/math/WasmMath*.{ttf,woff2}` are derived from STIX Two Math 2.13 b171, https://github.com/stipub/stixfonts,
Copyright 2001-2021 The STIX Fonts Project Authors, with Reserved Font Name "TM Math". The derived fonts use other
names (Wasm Math Extra / Symbol / Blackboard / Script / Fraktur), as the licence requires. Licence text: `fonts/math/OFL.txt`.
"STIX Fonts" is a trademark of the IEEE.

`fonts/math-src/afm/Symbol.afm` is Adobe's font metrics file for Symbol, used only for its glyph order and metrics;
its notice is in `fonts/math-src/afm/README-Adobe-AFM.txt`.

The fonts are substitutes for "MT Extra", "Symbol", "Euclid Math One", "Euclid Math Two" and "Euclid Fraktur", which
are not included and not redistributed. `fonts/math-src/encodings/design-science.json` records the byte-code tables
published by Design Science (facts about the encodings, no font data). MathType is a trademark of WIRIS / Design Science.

## Document fonts

`artifacts/onlyoffice-editor/fonts/` is the font pack of the CryptPad build. Most files are open licences (Apache-2.0,
OFL, GPL with font exception, ...). The upstream pack also held `arial*.ttf` (Monotype, Arial 2.82) and `calibri*.ttf`
(Microsoft, Calibri 1.02), which are not under an open licence (upstream has them only as test fixtures, commit c2d8d703).
`node tools/font-pack.cjs` removes them from the pack and from `sdkjs/common/AllFonts.js`; Arial then answers to
Arimo and Calibri to Carlito (metric-compatible, `fonts/font-aliases.cjs`), Times New Roman to Tinos. Run it after every
rebuild of the pack. Details: `docs/analysis.md` sections 13 and 14.

### Metric-compatible fonts (`fonts/metric/`, 11/11/2026)

Open fonts with the metrics of common Word fonts, built by `fonts/metric-src/build-metric-fonts.py` (inputs, URLs, checksums:
`fonts/metric/SOURCE.md`; licence texts next to the fonts). Word name -> pack family: Georgia -> Gelasio (OFL); Garamond -> EB Garamond (OFL);
Palatino Linotype, Book Antiqua -> WasmPagella (TeX Gyre Pagella, GUST Font Licence); Century Gothic -> WasmAdventor (TeX Gyre Adventor);
Segoe UI (+Light, +Semibold) -> WasmUI (Selawik, Microsoft, OFL); Arial Narrow -> WasmNarrow (Liberation Sans Narrow 1.07.4, GPL-2 with font
exception); Comic Sans MS -> WasmComic (Comic Relief, OFL); Cambria -> WasmCaladea (Caladea, OFL); Tahoma -> WasmTahoma (Roboto, Apache-2.0);
Verdana -> WasmVerdana (DejaVu Sans, Bitstream Vera licence). Fonts with a Reserved Font Name, and the GUST fonts, are modified (renamed, vertical
metrics, Vietnamese letters copied from Roboto / Arimo / Tinos) and therefore published under the `Wasm...` names. The pack's Selawik, Liberation Sans
Narrow and Comic Relief files (no Vietnamese) are replaced by these. Facts taken from Windows fonts (advance widths, line heights) are measurements, no font data.

The Vietnamese legacy fonts `.VnTime` and `.VnTimeH` (TCVN3 / ABC code layout) are added by the same tool, in one of two sets:

- `--vn original` (default): the original ABC files (`fonts/vn-orig/`, provenance and checksums in
  `fonts/vn-orig/SOURCE.md`), installed as patched copies from `fonts/vn-orig/patched/` made by
  `fonts/vn-src/patch-vn-originals.py`: a second cmap entry (U+F0AD) for the u-with-horn glyph and the few glyphs the
  originals lack (some TCVN3 letters, typographic punctuation) copied from the open rebuild (Tinos, OFL). The pristine files stay in `fonts/vn-orig/`.
  **Decision of the owner (10/11/2026):** the TCVN3 fonts `.VnTime` / `.VnTimeH` were issued by the Vietnamese government
  for general use, so they are used as they are and no licence work is planned. (No licence text ships with the files:
  none in the archives, none in the font files; this records the owner's call, not a licence grant.)
  The open set would be chosen only if it were at least as good; the 10/11 comparison says it is not (see below).
- `--vn open`: fonts of the same names and code layout built from Tinos (OFL 1.1, `fonts/vn/`, script `fonts/vn-src/`).
  Clear licence; the glyph shapes are Tinos, not the originals. Not the default: its line metrics differ from the
  originals (ascent 1825 / descent 443 per 2048 against about 1397 / 464 in `VnTime`, so single line spacing is roughly
  20% taller and documents paginate differently) and some glyph widths differ by up to 7%. The patched originals keep
  the original metrics and are complete.
