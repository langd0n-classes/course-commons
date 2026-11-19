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
                target = urlsplit(node['c'][2][0])
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
    count = 0

    def replace(match):
        nonlocal count
        count += 1
        name = f'mermaid-{count}'
        (work / f'{name}.mmd').write_text(match.group(2), encoding='utf-8')
        return f'![]({work / name}.png){{width=90%}}'

    text = source.read_text(encoding='utf-8')
    text = re.sub(r'^(`{3,}|~{3,})mermaid[ \t]*\n(.*?)^\1[ \t]*$',
                  replace, text, flags=re.M | re.S)
    destination.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
