#!/usr/bin/env python3
"""Create a fallback JUnit report when the test runner produced none."""

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path to the JUnit XML report")
    parser.add_argument("exit_code", type=int, help="Test runner exit code")
    args = parser.parse_args()

    if args.output.exists():
        return

    message = (
        "System test runner exited with code "
        f"{args.exit_code} before JUnit report was generated."
    )
    suites = ET.Element("testsuites")
    suite = ET.SubElement(
        suites,
        "testsuite",
        {
            "name": "pytest",
            "errors": "1",
            "failures": "0",
            "skipped": "0",
            "tests": "1",
            "time": "0.0",
        },
    )
    testcase = ET.SubElement(
        suite,
        "testcase",
        {"classname": "breeze.system_tests", "name": "bootstrap_execution", "time": "0.0"},
    )
    ET.SubElement(testcase, "error", {"message": message})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suites).write(args.output, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
