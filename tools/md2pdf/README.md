# md2pdf

Convert Markdown to PDF with Mermaid diagrams and blue links.

Requires Bash, Python 3, and Podman with network access for image pulls and
the first build.
Conversion containers run with networking disabled.

```sh
tools/md2pdf/md2pdf path/to/document.md [path/to/output.pdf]
```

Without an output argument, the PDF is written next to the input with the
same base name. An existing output is overwritten. Relative image paths
resolve from the input's directory.
The container setting stores temporary files under `${TMPDIR:-/var/tmp}`.

The default backend builds a local image tagged with the Containerfile SHA256.
Changing the Containerfile triggers a new build. The Containerfile pins Fedora 44
and the official Pandoc 3.7.0.2 tarballs with SHA256 checks. Supported build
architectures are amd64 (x86_64) and arm64 (aarch64).
Fedora supplies XeLaTeX (TeX Live 2026) and Liberation Sans 2.1.5; package
updates can change the rendering. Mermaid uses
`docker.io/minlag/mermaid-cli:11.4.2`, PNG scale 3, and a white background.
Diagrams occupy 90% of the text width.

For a distrobox environment, set its name:

```sh
MD2PDF_PANDOC=distrobox MD2PDF_DISTROBOX_NAME=my_box tools/md2pdf/md2pdf path/to/document.md
```

This setting requires distrobox and pandoc with XeLaTeX and Liberation Sans
inside the named distrobox. `MD2PDF_DISTROBOX_NAME` is required for this
backend. Podman still runs Mermaid and preprocessing.
Temporary files use `${XDG_CACHE_HOME:-$HOME/.cache}/md2pdf/`, which must
be shared with the distrobox. Both settings delete the work directory on exit.

Local Markdown image files are read and copied into the conversion container. Paths
with spaces and paths through parent directories are supported. Input, output,
and local image paths must not contain `:`. Missing local images cause an error.
Raw HTML `<img>` images are not copied. Raw LaTeX in untrusted Markdown can
read local files accessible to Pandoc, including host files in the distrobox backend.

PDFs use `markdown+autolink_bare_uris`, Liberation Sans at 11pt, one-inch
margins, blue links and URLs, and LaTeX `\frenchspacing`.

Build the example with:

```sh
tools/md2pdf/md2pdf tools/md2pdf/test/sample.md
```

Exit codes: 0 means success; 2 means invalid arguments, backend configuration,
or a rejected local path. Other failures return a nonzero status from the
failed command (for example, preprocessing, Podman, or Pandoc).
Standard output contains only the completed output path; diagnostics go to stderr.

Run the standard-library unit tests in the conversion image:

```sh
podman build -t localhost/md2pdf-test tools/md2pdf
podman run --rm --network=none --security-opt label=disable -v "$PWD:/src:ro" localhost/md2pdf-test \
  python3 -B -m unittest discover -s tools/md2pdf/test -v
```
