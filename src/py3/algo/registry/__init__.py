"""Registry loaders: algorithms.yml and problems.yml -> lists of dicts (stdlib only).

The YAML files are parsed with tiny regex loaders, not PyYAML, so the workbench can ship in the
offline installer. Both the CLI (algo.cli.main) and the per-problem targets
(algo.leetcode.runnable) import from here, which keeps the two free of an import cycle.
File format: docs/API.md sections 3 and 4.
"""

from __future__ import annotations

import pathlib
from typing import Any

Item = dict[str, Any]

ROOT = pathlib.Path(__file__).resolve().parents[3]  # the install root (src/)
REGISTRY = ROOT / "registry" / "algorithms.yml"
PROBLEMS = ROOT / "registry" / "problems.yml"


def load_registry() -> list[Item]:
    """Parse algorithms.yml with a tiny regex parser (stdlib only, so it ships in the installer)."""
    import re

    text = REGISTRY.read_text()
    blocks = re.split(r"\n  - id: ", text)
    items = []
    for block in blocks[1:]:
        lines = block.splitlines()
        item = {"id": lines[0].strip()}
        for line in lines[1:]:
            s = line.strip()
            if s.startswith("name:"):
                item["name"] = s[5:].strip()
            elif s.startswith("leetcode:"):
                m = re.search(r"id:\s*(\d+),\s*title:\s*(.*?)\s*}", s)
                if m:
                    item["leetcode_id"] = int(m.group(1))
                    item["leetcode_title"] = m.group(2)
            elif s.startswith("category:"):
                item["category"] = s[9:].strip()
            elif s.startswith("data_structures:"):
                item["data_structures"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("identification:"):
                item["identification"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("disqualifiers:"):
                item["disqualifiers"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
            elif s.startswith("uses:"):
                item["uses"] = s.split("[", 1)[1].split("]", 1)[0].split(", ")
        for k in ("data_structures", "identification", "disqualifiers", "uses"):
            if k in item:
                item[k] = [x for x in item[k] if x]
        items.append(item)
    return items


def load_problems() -> list[Item]:
    """Parse problems.yml (one flow mapping per line) into dicts."""
    import re

    pat = re.compile(
        r"id:\s*(\d+),\s*title:\s*(.*?),\s*difficulty:\s*(\w+),"
        r"\s*algorithms:\s*\[(.*?)\],\s*keywords:\s*\[(.*?)\]"
    )
    out = []
    for line in PROBLEMS.read_text().splitlines():
        m = pat.search(line)
        if m:
            out.append(
                {
                    "id": int(m[1]),
                    "title": m[2],
                    "difficulty": m[3],
                    "algorithms": [x.strip() for x in m[4].split(",") if x.strip()],
                    "keywords": [x.strip() for x in m[5].split(",") if x.strip()],
                }
            )
            u = re.search(r"uses:\s*\[(.*?)\]", line)
            tag = re.search(r"list:\s*([\w-]+)", line)
            out[-1]["uses"] = [x.strip() for x in u[1].split(",") if x.strip()] if u else []
            out[-1]["list"] = tag[1] if tag else None
    return out


__all__ = ["PROBLEMS", "REGISTRY", "ROOT", "Item", "load_problems", "load_registry"]
