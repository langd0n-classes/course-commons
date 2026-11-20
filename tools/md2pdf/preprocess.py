#!/usr/bin/env python3
"""Extract Mermaid fences, or list local images from Pandoc's JSON AST."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def resources(source, ast):
    def walk(node):
        if isinstance(node, dict):
            if node.get('t') == 'Image':
                raw = node['c'][2][0]
                target = urlsplit(raw)
                if ':' in unquote(raw) and target.scheme not in ('http', 'https', 'data'):
                    print(f'md2pdf: local image path must not contain a colon (:): {raw}', file=sys.stderr)
                    sys.exit(2)
                if not target.scheme and not target.netloc:
                    path = Path(os.path.abspath(source.parent / unquote(target.path)))
                    sys.stdout.buffer.write(str(path).encode() + b'\0')
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(json.loads(ast.read_text(encoding='utf-8')))


def main():
    if sys.argv[1] == '--resources':
        resources(Path(sys.argv[2]), Path(sys.argv[3]))
        return
    source, destination, work = map(Path, sys.argv[1:])
    try:
        text = extract_mermaid(source.read_text(encoding='utf-8'), work)
    except ValueError as error:
        sys.exit(f'md2pdf: {error}')
    destination.write_text(text, encoding='utf-8')


def extract_mermaid(text, work):
    """Replace top-level Mermaid fences while preserving other fenced blocks."""
    output = []
    opened = None
    body = []
    count = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})([^\r\n]*)[\r\n]*$', line)
        if opened is None:
            if match and not (match[1][0] == '`' and '`' in match[2]):
                opened = (match[1][0], len(match[1]),
                          match[2].strip() == 'mermaid', line_number)
                if opened[2]:
                    body = []
                    continue
            output.append(line)
        else:
            char, length, mermaid, _ = opened
            closing = (match and match[1][0] == char
                       and len(match[1]) >= length and not match[2].strip())
            if closing:
                if mermaid:
                    count += 1
                    name = f'mermaid-{count}'
                    (work / f'{name}.mmd').write_text(''.join(body), encoding='utf-8')
                    ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
                    output.append(f'![](<{work / name}.png>){{width=90%}}{ending}')
                else:
                    output.append(line)
                opened = None
            elif mermaid:
                body.append(line)
            else:
                output.append(line)
    if opened and opened[2]:
        raise ValueError(f'unclosed Mermaid fence at line {opened[3]}')
    return ''.join(output)


if __name__ == '__main__':
    main()
