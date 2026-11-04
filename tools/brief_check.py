#!/usr/bin/env python3
"""Check a scene (and optionally a build log) against the brief's machine-readable copy.
    python3 tools/brief_check.py brief.toml scene.toml [build.log]
parts: every entry must be contained in some [[view.label]] text (case-insensitive substring; '$' and '\\' ignored)
dims:  every entry must appear in a dim / dim3 draw item's text
views: every entry must be a [[view]] name
build log (if given): must contain no WARNING / CLASH / REALISM / ERROR lines
Exit 1 with one line per miss."""
import sys, tomllib, re


def norm(s):
    return re.sub(r"[\\$\s{}]", "", str(s)).lower()


def main(brief_path, scene_path, log_path=None):
    B = tomllib.load(open(brief_path, "rb")); S = tomllib.load(open(scene_path, "rb")); miss = []
    labels = [l.get("text", "") for v in S.get("view", []) for l in v.get("label", [])]
    key_extra = S.get("figure", {}).get("key_extra", [])
    for p in B.get("parts", []):
        if not any(norm(p) in norm(t) for t in labels + key_extra): miss.append("part %r has no balloon / key line in the scene" % p)
    dim_texts = [d[2] if d[0] == "dim3" else d[3] for v in S.get("view", []) for d in v.get("draw", []) if d[0] in ("dim", "dim3")]
    for d in B.get("dims", []):
        if not any(norm(d) in norm(t) for t in dim_texts): miss.append("dimension %r is not drawn in any view" % d)
    names = [v["name"] for v in S.get("view", [])]
    for v in B.get("views", []):
        if v not in names: miss.append("view %r is not in the scene (views: %s)" % (v, ", ".join(names)))
    if log_path:
        bad = [l.strip() for l in open(log_path, encoding="utf-8") if l.startswith(("overlay WARNING", "CLASH", "REALISM", "ERROR"))]
        miss += ["build log: " + l for l in bad]
    for m in miss: print("BRIEF MISS:", m)
    print("brief check: %d item(s) checked, %d miss" % (len(B.get("parts", [])) + len(B.get("dims", [])) + len(B.get("views", [])), len(miss)))
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
