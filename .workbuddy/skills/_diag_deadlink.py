import os, re
SKILLS_ROOT = os.path.abspath(".")
REF_RE = re.compile(r"(?:\(|\s|`)(references/[A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)")
LINK_RE = re.compile(r"\]\((references/[^)]+)\)")
root_refs = os.path.join(SKILLS_ROOT, "references")
dead = []
checked = 0
for r, _, files in os.walk(SKILLS_ROOT):
    if "SKILL.md" not in files:
        continue
    sk = os.path.join(r, "SKILL.md")
    md = open(sk, encoding="utf-8").read()
    refs = set()
    for m in LINK_RE.finditer(md):
        refs.add(m.group(1))
    for m in REF_RE.finditer(md):
        refs.add(m.group(1))
    for rel in refs:
        checked += 1
        local = os.path.normpath(os.path.join(r, rel))
        shared = os.path.normpath(os.path.join(root_refs, os.path.basename(rel)))
        if os.path.isfile(local) or os.path.isfile(shared):
            continue
        dead.append((os.path.relpath(sk, SKILLS_ROOT), rel))
for r, _, files in os.walk(SKILLS_ROOT):
    refdir = os.path.join(r, "references")
    if not os.path.isdir(refdir):
        continue
    for fn in files:
        if not fn.endswith(".md"):
            continue
        rp = os.path.join(refdir, fn)
        try:
            rmd = open(rp, encoding="utf-8").read()
        except Exception:
            continue
        refs = set()
        for m in LINK_RE.finditer(rmd):
            refs.add(m.group(1))
        for m in REF_RE.finditer(rmd):
            refs.add(m.group(1))
        for rel in refs:
            checked += 1
            local = os.path.normpath(os.path.join(r, rel))
            nested = os.path.normpath(os.path.join(refdir, rel))
            shared = os.path.normpath(os.path.join(root_refs, os.path.basename(rel)))
            if os.path.isfile(local) or os.path.isfile(nested) or os.path.isfile(shared):
                continue
            dead.append((os.path.relpath(rp, SKILLS_ROOT), rel))
print("=== CHECKED %d references, DEAD %d ===" % (checked, len(dead)))
by_skill = {}
for s, rel in dead:
    by_skill.setdefault(s, []).append(rel)
for s in sorted(by_skill):
    print("\n[%s]" % s)
    for rel in sorted(set(by_skill[s])):
        print("   ", rel)
