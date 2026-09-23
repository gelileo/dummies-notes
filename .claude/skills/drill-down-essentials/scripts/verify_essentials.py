#!/usr/bin/env python3
"""Verify a chapter's essentials/ folder.

  python3 verify_essentials.py <chapter-dir> [--no-mermaid]

Checks, in order of how often they actually break:
  1. every concept folder has README.md and demo.py
  2. every demo.py runs cleanly from inside its own folder
  3. every relative markdown link in the chapter resolves
  4. every mermaid block parses (needs npx; skipped if unavailable)
  5. articles carry the pieces that make them usable on their own

Exit code 0 if everything passes, 1 otherwise.
"""
import os, re, subprocess, sys, shutil

LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
MERMAID = re.compile(r'```mermaid\n(.*?)```', re.S)


def md_files(root):
    for d, _, fs in os.walk(root):
        if '__pycache__' in d:
            continue
        for f in fs:
            if f.endswith('.md'):
                yield os.path.join(d, f)


def check_structure(ess, fail):
    concepts = sorted(d for d in os.listdir(ess)
                      if os.path.isdir(os.path.join(ess, d)) and not d.startswith(('.', '_')))
    if not os.path.exists(os.path.join(ess, 'README.md')):
        fail("essentials/README.md is missing — readers need an index to land on")
    if not concepts:
        fail("no concept folders found under essentials/")
    for c in concepts:
        for required in ('README.md', 'demo.py'):
            p = os.path.join(ess, c, required)
            if not os.path.exists(p):
                # a concept with no runnable evidence is the main thing to catch
                fail(f"{c}/{required} is missing")
    # stray files at the top level usually mean a half-finished reorganisation
    for f in os.listdir(ess):
        p = os.path.join(ess, f)
        if os.path.isfile(p) and f != 'README.md':
            fail(f"essentials/{f} sits outside a concept folder")
    return concepts


def check_demos(ess, concepts, fail):
    for c in concepts:
        d = os.path.join(ess, c)
        script = os.path.join(d, 'demo.py')
        if not os.path.exists(script):
            continue
        r = subprocess.run([sys.executable, 'demo.py'], cwd=d,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            fail(f"{c}/demo.py exited {r.returncode}: "
                 f"{(r.stderr.strip().splitlines() or ['no stderr'])[-1]}")
        elif not r.stdout.strip():
            fail(f"{c}/demo.py printed nothing — the article has no evidence to quote")


def check_links(chapter, fail, warn):
    """Links inside the chapter are the author's responsibility and always fail.
    Links that point outside it (a sibling chapter, the curriculum root) may simply
    target something not written yet, so they warn instead -- otherwise a chapter
    reviewed in isolation drowns in noise about its neighbours."""
    n = outside = 0
    for f in md_files(chapter):
        base = os.path.dirname(f)
        for m in LINK.finditer(open(f, encoding='utf-8').read()):
            t = m.group(1).split('#')[0].strip()
            if not t or t.startswith(('http://', 'https://', 'mailto:')):
                continue
            n += 1
            target = os.path.normpath(os.path.join(base, t))
            if os.path.exists(target):
                continue
            inside = os.path.commonpath([chapter, os.path.abspath(target)]) == chapter
            if inside:
                fail(f"broken link in {os.path.relpath(f, chapter)} -> {t}")
            else:
                outside += 1
                warn(f"link leaves the chapter and does not resolve: "
                     f"{os.path.relpath(f, chapter)} -> {t}")
    return n, outside


def check_mermaid(chapter, fail, enabled):
    blocks = [(f, b) for f in md_files(chapter)
              for b in MERMAID.findall(open(f, encoding='utf-8').read())]
    if not blocks:
        return 0, False
    if not enabled or not shutil.which('npx'):
        return len(blocks), False
    import tempfile
    for f, b in blocks:
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, 'd.mmd')
            open(src, 'w').write(b)
            r = subprocess.run(['npx', '-y', '@mermaid-js/mermaid-cli',
                                '-i', src, '-o', os.path.join(td, 'd.svg')],
                               capture_output=True, text=True)
            if not os.path.exists(os.path.join(td, 'd.svg')):
                fail(f"mermaid block in {os.path.relpath(f, chapter)} does not parse: "
                     f"{r.stderr.strip()[:200]}")
    return len(blocks), True


def check_articles(ess, concepts, warn):
    for c in concepts:
        p = os.path.join(ess, c, 'README.md')
        if not os.path.exists(p):
            continue
        s = open(p, encoding='utf-8').read()
        if 'Needed for' not in s:
            warn(f"{c}/README.md has no '**Needed for:**' line — a reader arriving "
                 f"from a link cannot tell what it unblocks")
        if not re.search(r'^\|.*\|.*\|', s, re.M):
            warn(f"{c}/README.md has no terminology table")
        if 'demo.py' not in s:
            warn(f"{c}/README.md never tells the reader to run demo.py")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    chapter = os.path.abspath(args[0])
    ess = os.path.join(chapter, 'essentials')
    if not os.path.isdir(ess):
        print(f"FAIL  no essentials/ folder in {chapter}")
        return 1

    problems, warnings = [], []
    fail = problems.append
    warn = warnings.append

    concepts = check_structure(ess, fail)
    check_demos(ess, concepts, fail)
    nlinks, noutside = check_links(chapter, fail, warn)
    nmermaid, ran_mermaid = check_mermaid(chapter, fail, '--no-mermaid' not in sys.argv)
    check_articles(ess, concepts, warn)

    print(f"chapter   {os.path.basename(chapter)}")
    print(f"concepts  {len(concepts)}: {', '.join(concepts)}")
    print(f"links     {nlinks} checked" +
          (f", {noutside} point outside the chapter and did not resolve" if noutside else ""))
    print(f"mermaid   {nmermaid} block(s) " +
          ("validated" if ran_mermaid else "found, not validated (npx unavailable or --no-mermaid)"))
    for w in warnings:
        print(f"WARN  {w}")
    for p in problems:
        print(f"FAIL  {p}")
    print("PASS" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
