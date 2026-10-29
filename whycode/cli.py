"""WhyCode CLI: ask the graph a "why" question from the command line.

Usage:
  python3 -m whycode.cli --db data/whycode.db --question "Why does ...?"
"""
import argparse
import json

from whycode.graph import GraphStore
from whycode.qa import ask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/whycode.db")
    ap.add_argument("--question", required=True)
    args = ap.parse_args()
    result = ask(GraphStore(args.db), args.question)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
