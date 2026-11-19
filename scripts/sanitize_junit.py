#!/usr/bin/env python3
"""Remove detailed test output from a JUnit report before artifact upload."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("airflow/junit.xml")
    destination = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("junit-sanitized.xml")

    tree = ET.parse(source)
    for node in tree.iter():
        if node.tag in {"system-out", "system-err", "properties"}:
            node.clear()
        elif node.tag in {"failure", "error"}:
            node.attrib.pop("message", None)
            node.attrib.pop("type", None)
            node.text = "[details removed from public artifact]"
    tree.write(destination, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
