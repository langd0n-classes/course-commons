# md2pdf

Convert Markdown to PDF with Mermaid diagrams and blue links.

Requires Bash, Python 3, and Podman with network access for the first build.

```sh
tools/md2pdf/md2pdf path/to/document.md [path/to/output.pdf]
```

Without an output argument, the PDF is written next to the input with the
same base name. Relative image paths resolve from the input's directory.
The container setting stores temporary files under `${TMPDIR:-/var/tmp}`.

The default backend builds `localhost/md2pdf-pandoc:3.7.0.2` on first use.
The Containerfile pins Fedora 44 and the Ubuntu variant of pandoc 3.7.0.2.
Fedora supplies XeLaTeX (TeX Live 2026) and Liberation Sans 2.1.5; package
updates can change the rendering. Mermaid uses
`docker.io/minlag/mermaid-cli:11.4.2`, PNG scale 3, and a white background.
Diagrams occupy 90% of the text width.

For the existing `langdon_distrobox` environment, run:

```sh
MD2PDF_PANDOC=distrobox tools/md2pdf/md2pdf path/to/document.md
```

This setting requires distrobox and pandoc with XeLaTeX and Liberation Sans
inside `langdon_distrobox`. Podman still runs Mermaid and preprocessing.
Temporary files use `${XDG_CACHE_HOME:-$HOME/.cache}/md2pdf/`, which must
be shared with the distrobox. Both settings delete the work directory on exit.

Local Markdown image files are copied into the conversion container. Paths
with spaces and paths through parent directories are supported.

PDFs use `markdown+autolink_bare_uris`, Liberation Sans at 11pt, one-inch
margins, blue links and URLs, and LaTeX `\frenchspacing`.

Build the example with:

```sh
tools/md2pdf/md2pdf tools/md2pdf/test/sample.md
```
