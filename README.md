# icyhoty2k.github.io

The developer homepage for **[icyhoty2k](https://icyhoty2k.github.io/)** — Ivan Hristov
Yanev, Montana, Bulgaria.

It is the root of everything I publish. Individual products have their own sites and
repositories; this one sits above them and holds the things that belong to the person
rather than to any single product.

| Page | What it is |
|---|---|
| [`index.html`](index.html) | Landing page — what I make, and how to get it |
| [`about.html`](about.html) | The work: why hand-written, why no framework |
| [`cv.html`](cv.html) | The longer record — qualifications, languages, licences |
| [`support.html`](support.html) | Contact, per-app support and privacy policy links |

## Products

- **[QuickImageViewer](https://icyhoty2k.github.io/QuickImageViewer/)** — a fast, free
  image viewer for Windows 10 and 11. C++ against Win32 and Direct2D, no UI framework.
  [Source](https://github.com/icyhoty2k/QuickImageViewer).
- **[qIV Remote](https://icyhoty2k.github.io/QuickImageViewer/qiv-remote.html)** — the
  Android companion. In closed testing on Google Play and
  [looking for testers](https://groups.google.com/g/qiv-remote-testers).

## How it is built

Plain HTML and CSS. No framework, no build step, no JavaScript.

**No third parties, and that is meant literally.** The fonts are vendored in
`assets/fonts/` with their SIL Open Font License. There is no CDN, no analytics, no
tracking, no embedded anything. The site says so on the support page, so it has to be
true — opening the network tab should show requests to this domain and nowhere else.

Served by GitHub Pages as a user site: the repository name has to match the domain
exactly, and Pages enables itself for that name.

### Working on it

Nothing to install and nothing to run. Open `index.html` in a browser.

`assets/mark.svg` is the `i` monogram, drawn as geometry rather than set as type so it
renders identically everywhere. **The same shape is used as the Google Play developer
icon**, generated from the same numbers — if you change one, change both, or the
developer page and the developer's website stop matching.

## Licence

The site's code — the HTML, the CSS and the SVG — is MIT licensed; see
[LICENSE](LICENSE). Take any of it.

**The written content is not.** The biography, the product descriptions and the
photographs are mine, and the `icyhoty2k` name and mark identify me rather than being
free to reuse. Copy the markup, not the person.

Inter is licensed separately under the SIL Open Font License —
[`assets/fonts/OFL.txt`](assets/fonts/OFL.txt).
