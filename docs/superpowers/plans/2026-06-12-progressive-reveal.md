# Progressive Reveal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make figure elements appear progressively, one narration beat at a time, on one canvas — smoothly in the HTML player and "popped" per beat in the MP4 — driven by `data-reveal`/`data-anim` tags on SVG groups plus a per-beat `beats` array in `figure.json`.

**Architecture:** Opt-in, backward-compatible additions to the existing Phase 6 video engine. `figure.json` frames gain `beats`; SVG `<g>` groups gain `data-reveal="k"` + optional `data-anim`. `build_video.py` expands each frame into one manifest slide per beat (carrying `reveal_to`); the MP4 path hides not-yet-revealed groups via a per-element `visibility:hidden` string transform (rasterizer-agnostic, "pop"); the HTML player inlines each frame SVG once and reveals groups with smooth entrance animation synced to narration. Untagged figures behave exactly as today.

**Tech Stack:** Python 3 stdlib + `unittest`; self-contained SVG; vanilla JS in the player template; `rsvg-convert`/`cairosvg` + `ffmpeg` + macOS `say` for the (already-validated) MP4 path.

**Spec:** `docs/superpowers/specs/2026-06-12-progressive-reveal-design.md`

---

## Reference: contracts (keep names/shapes identical across tasks)

Slide dict (existing keys + ONE new key `reveal_to`):
```python
{"kind": "title"|"section"|"frame"|"closing",
 "concept_slug": str|None, "image": str|None,
 "caption": str, "narration": str,
 "duration_s": float, "transition": "crossfade"|"cut"|"reveal",
 "reveal_to": int|None}     # NEW: 1-based beat index; None = show whole figure
```

`load_frames(figure_dir)` returns, per frame:
```python
{"file": str(abs), "caption": str, "commentary": str,
 "beats": list[{"caption": str, "narration": str}] | None}   # beats NEW
```

`figure.json` frame (additions are optional):
```json
{"file": "...", "caption": "...", "runbook": "...", "commentary": "...",
 "beats": [{"caption": "...", "narration": "..."}, ...]}
```
SVG `<g>` groups: optional `data-reveal="k"` (1-based) and `data-anim="rise|draw|fade"`.

Run tests from the repo root: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`. Never use `git commit --no-verify`; when a mapped code path changes (`scripts/build_video.py` → `video-engine.md`; `.claude/skills/concept-illustrator/**` → `illustration-engine.md`), update the mapped article in the SAME commit (keep article `status` ∈ {thin,mature,deprecated}) and ensure `python3 scripts/validate-articles` exits 0.

---

## Task 1: `load_frames` reads `beats`

**Files:**
- Modify: `scripts/build_video.py` (`load_frames`)
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Update the test fixture + add a test**

In `scripts/tests/test_build_video.py`, extend the `make_figure` helper so a caller can attach beats. Find the `make_figure(registry_root, slug, n_frames=2)` function and change its signature and the frame-dict construction to accept an optional `beats` list applied to the FIRST frame:

```python
def make_figure(registry_root, slug, n_frames=2, beats=None):
    """Register slug and attach a figure dir with n_frames SVG frames.
    If beats is given, attach it to the first frame's figure.json entry."""
    reg.register(registry_root, slug, slug.replace("-", " ").title(),
                 f"Plain definition of {slug}.")
    fig_dir = os.path.join(registry_root, slug, "figure")
    os.makedirs(fig_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        fname = f"frame-{i:02d}.svg"
        with open(os.path.join(fig_dir, fname), "w", encoding="utf-8") as fh:
            fh.write('<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" '
                     'width="100%" viewBox="0 0 680 220" role="img">'
                     f'<text>{slug} {i}</text></svg>')
        frame = {"file": fname, "caption": f"{slug} caption {i}",
                 "runbook": "rb", "commentary": f"This is narration for {slug} frame {i}."}
        if i == 1 and beats:
            frame["beats"] = beats
        frames.append(frame)
    with open(os.path.join(fig_dir, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": slug, "archetype": "illustrative",
                   "playback": "slideshow", "frames": frames}, fh)
    reg.attach_figure(registry_root, slug, fig_dir)
```

Then add this test class:

```python
class TestLoadFramesBeats(unittest.TestCase):
    def test_beats_read_when_present(self):
        with tempfile.TemporaryDirectory() as base:
            registry = os.path.join(base, "r")
            beats = [{"caption": "b1", "narration": "first beat"},
                     {"caption": "b2", "narration": "second beat"}]
            make_figure(registry, "tcp", 1, beats=beats)
            frames = bv.load_frames(os.path.join(registry, "tcp", "figure"))
            self.assertEqual(frames[0]["beats"], beats)

    def test_beats_none_when_absent(self):
        with tempfile.TemporaryDirectory() as base:
            registry = os.path.join(base, "r")
            make_figure(registry, "tcp", 2)
            frames = bv.load_frames(os.path.join(registry, "tcp", "figure"))
            self.assertIsNone(frames[0]["beats"])
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestLoadFramesBeats -v`
Expected: FAIL — `KeyError: 'beats'` (load_frames doesn't return that key yet).

- [ ] **Step 3: Implement**

In `scripts/build_video.py`, in `load_frames`, change the appended frame dict to include `beats`:

```python
        beats = frame.get("beats")
        if not isinstance(beats, list) or not beats:
            beats = None
        frames.append({"file": os.path.abspath(path),
                       "caption": frame.get("caption", ""),
                       "commentary": frame.get("commentary", ""),
                       "beats": beats})
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS (existing + new).

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(reveal): load_frames reads per-frame beats"
```
If the drift hook asks, append a one-line note to `knowledge/concepts/dummies-notes/video-engine.md` (keep `status: thin`), run `validate-articles`, then commit.

---

## Task 2: `_slide` gains `reveal_to`; `build_manifest` per-beat expansion

**Files:**
- Modify: `scripts/build_video.py` (`_slide`, `build_manifest`)
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add tests**

```python
class TestBeatExpansion(unittest.TestCase):
    def test_frame_with_beats_expands_to_one_slide_per_beat(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            beats = [{"caption": "c1", "narration": "n one"},
                     {"caption": "c2", "narration": "n two"},
                     {"caption": "c3", "narration": "n three"}]
            make_figure(registry, "tcp", 1, beats=beats)
            manifest, _ = bv.build_manifest(graph, registry)
            frames = [s for s in manifest["slides"] if s["kind"] == "frame"]
            self.assertEqual(len(frames), 3)
            self.assertEqual([s["reveal_to"] for s in frames], [1, 2, 3])
            self.assertEqual(frames[0]["caption"], "c1")
            self.assertEqual(frames[1]["narration"], "n two")
            # first beat of the frame is not a reveal; later beats are
            self.assertNotEqual(frames[0]["transition"], "reveal")
            self.assertEqual(frames[1]["transition"], "reveal")
            self.assertEqual(frames[2]["transition"], "reveal")
            # all beats share the same figure image
            self.assertEqual(len({s["image"] for s in frames}), 1)

    def test_frame_without_beats_is_single_slide_reveal_none(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 2)
            manifest, _ = bv.build_manifest(graph, registry)
            frames = [s for s in manifest["slides"] if s["kind"] == "frame"]
            self.assertEqual(len(frames), 2)
            self.assertTrue(all(s["reveal_to"] is None for s in frames))

    def test_title_slides_have_reveal_to_none(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 1)
            manifest, _ = bv.build_manifest(graph, registry)
            self.assertIsNone(manifest["slides"][0]["reveal_to"])  # title
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestBeatExpansion -v`
Expected: FAIL — `KeyError: 'reveal_to'`.

- [ ] **Step 3: Implement**

In `scripts/build_video.py`, change `_slide` to accept and store `reveal_to`:

```python
def _slide(kind, slug, image, caption, narration, wpm, transition, reveal_to=None):
    return {"kind": kind, "concept_slug": slug, "image": image,
            "caption": caption, "narration": narration,
            "duration_s": round(_duration_for(narration, wpm), 3),
            "transition": transition, "reveal_to": reveal_to}
```

In `build_manifest`, replace the frame loop (`for i, fr in enumerate(frames): ... slides.append(_slide("frame", ...))`) with beat-aware expansion:

```python
        for i, fr in enumerate(frames):
            frame_first = "crossfade" if i > 0 else "cut"
            if fr["beats"]:
                for bi, beat in enumerate(fr["beats"]):
                    slides.append(_slide(
                        "frame", slug, fr["file"], beat["caption"], beat["narration"],
                        wpm, "reveal" if bi > 0 else frame_first, reveal_to=bi + 1))
            else:
                slides.append(_slide(
                    "frame", slug, fr["file"], fr["caption"], fr["commentary"],
                    wpm, frame_first, reveal_to=None))
```

(The `title`, `section`, and `closing` `_slide(...)` calls already omit `reveal_to`, so they default to `None` — no change needed there.)

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(reveal): expand frames into per-beat slides with reveal_to"
```
Update `video-engine.md` + re-run validate-articles if the hook asks.

---

## Task 3: `_reveal_svg` + apply it in `stage_svg` (MP4 pop)

**Files:**
- Modify: `scripts/build_video.py` (`_reveal_svg` new, `stage_svg`)
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Add tests**

```python
import xml.etree.ElementTree as ET  # noqa: E402  (skip if already imported at top)

_REVEAL_SVG = (
    '<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" width="100%" '
    'viewBox="0 0 680 220" role="img">'
    '<g data-reveal="1"><rect x="1" y="1" width="10" height="10"/></g>'
    '<g data-reveal="2" data-anim="draw"><line x1="0" y1="0" x2="9" y2="0"/></g>'
    '<g data-reveal="3"><text>z</text></g>'
    '<g><text>backdrop</text></g>'
    '</svg>')


class TestRevealSvg(unittest.TestCase):
    def test_none_passes_through(self):
        self.assertEqual(bv._reveal_svg(_REVEAL_SVG, None), _REVEAL_SVG)

    def test_hides_groups_beyond_reveal_to(self):
        out = bv._reveal_svg(_REVEAL_SVG, 2)
        ET.fromstring(out)  # well-formed
        # group 3 hidden; groups 1,2 and the untagged backdrop NOT hidden
        self.assertEqual(out.count("visibility:hidden"), 1)
        self.assertIn('data-reveal="3"', out)
        # the hidden one is group 3
        g3 = out[out.index('data-reveal="3"') - 30: out.index('data-reveal="3"') + 30]
        self.assertIn("visibility:hidden", g3)

    def test_reveal_all_hides_nothing(self):
        out = bv._reveal_svg(_REVEAL_SVG, 3)
        self.assertNotIn("visibility:hidden", out)
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestRevealSvg -v`
Expected: FAIL — `AttributeError: ... '_reveal_svg'`.

- [ ] **Step 3: Implement**

In `scripts/build_video.py`, add near `_nest_figure` (the module already imports `re`):

```python
_REVEAL_G_RE = re.compile(r'<g\b[^>]*\bdata-reveal="(\d+)"[^>]*>')


def _reveal_svg(inner, reveal_to):
    """Return the figure markup with groups whose data-reveal index exceeds
    reveal_to marked visibility:hidden (layout preserved, simply not painted).
    Per-element inline style — no reliance on the rasterizer's CSS selector
    support. reveal_to=None returns the markup unchanged (show everything)."""
    if reveal_to is None:
        return inner

    def repl(m):
        tag = m.group(0)
        if int(m.group(1)) <= reveal_to:
            return tag
        if 'style="' in tag:
            return tag.replace('style="', 'style="visibility:hidden;', 1)
        return tag[:-1] + ' style="visibility:hidden">'

    return _REVEAL_G_RE.sub(repl, inner)
```

Then in `stage_svg`, change the frame branch so the nested figure is reveal-filtered. Replace:

```python
        parts.append(_nest_figure(_read_inner_svg(slide["image"]),
                                  pad, top_h, inner_w, inner_h))
```
with:
```python
        inner = _reveal_svg(_read_inner_svg(slide["image"]), slide.get("reveal_to"))
        parts.append(_nest_figure(inner, pad, top_h, inner_w, inner_h))
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(reveal): cumulative-state SVG for MP4 pop (_reveal_svg)"
```
Update `video-engine.md` if the hook asks.

---

## Task 4: figure-validator reveal lint (render.py)

**Files:**
- Modify: `.claude/skills/concept-illustrator/scripts/render.py` (`validate_figure`)
- Test: `.claude/skills/concept-illustrator/scripts/tests/test_render.py`

- [ ] **Step 1: Add tests**

Locate the render test module (`.claude/skills/concept-illustrator/scripts/tests/test_render.py`). Add a test class. It writes a minimal figure dir and calls `render.validate_figure(dir, style_path)` passing a **non-existent** style path (palette lint is skipped when the style file is absent, so only structural + reveal errors remain). The tests assert on reveal-specific error substrings, so any unrelated lint output doesn't interfere.

```python
class TestRevealLint(unittest.TestCase):
    def _figure(self, tmp, svg_body, beats):
        os.makedirs(tmp, exist_ok=True)
        with open(os.path.join(tmp, "frame-01.svg"), "w", encoding="utf-8") as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 220">'
                     + svg_body + '</svg>')
        frame = {"file": "frame-01.svg", "caption": "c", "runbook": "r",
                 "commentary": "c"}
        if beats is not None:
            frame["beats"] = beats
        with open(os.path.join(tmp, "figure.json"), "w", encoding="utf-8") as fh:
            json.dump({"concept_slug": "x", "archetype": "illustrative",
                       "playback": "static", "frames": [frame]}, fh)

    def _errors(self, tmp):
        issues = render.validate_figure(tmp, os.path.join(tmp, "nostyle.css"))
        return [m for lvl, m in issues if lvl == "ERROR"]

    def test_beats_match_max_reveal_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._figure(tmp, '<g data-reveal="1"><rect/></g><g data-reveal="2"><rect/></g>',
                         [{"caption": "a", "narration": "a"}, {"caption": "b", "narration": "b"}])
            self.assertFalse(any("reveal" in e or "beat" in e for e in self._errors(tmp)))

    def test_beats_count_mismatch_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._figure(tmp, '<g data-reveal="1"><rect/></g><g data-reveal="2"><rect/></g>',
                         [{"caption": "a", "narration": "a"}])  # 1 beat, max reveal 2
            self.assertTrue(any("beat" in e.lower() for e in self._errors(tmp)))

    def test_reveal_gap_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._figure(tmp, '<g data-reveal="1"><rect/></g><g data-reveal="3"><rect/></g>',
                         [{"caption": "a", "narration": "a"}, {"caption": "b", "narration": "b"},
                          {"caption": "c", "narration": "c"}])
            self.assertTrue(any("gap" in e.lower() or "consecutive" in e.lower()
                                for e in self._errors(tmp)))

    def test_tagged_without_beats_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._figure(tmp, '<g data-reveal="1"><rect/></g>', None)
            self.assertTrue(any("beat" in e.lower() for e in self._errors(tmp)))

    def test_beats_without_tags_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._figure(tmp, '<g><rect/></g>', [{"caption": "a", "narration": "a"}])
            self.assertTrue(any("data-reveal" in e for e in self._errors(tmp)))
```

If the test file imports differ, mirror the existing import block at the top of `test_render.py` (it already imports `render`, `os`, `json`, `tempfile`, `unittest`).

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py' -v -k Reveal`
Expected: FAIL (no reveal lint yet — mismatches not reported).

- [ ] **Step 3: Implement**

In `.claude/skills/concept-illustrator/scripts/render.py`, add a helper and call it from `validate_figure` inside the per-frame loop (where `root` is the parsed SVG and `name` is the file name). The parsed `root` is an `xml.etree.ElementTree.Element`. SVG elements are namespaced, so match by local tag name and read the `data-reveal` attribute (attributes are not namespaced here):

```python
def _lint_reveal(root, frame, name):
    """Beats <-> data-reveal consistency for one frame. Returns issues list."""
    issues = []
    reveals = []
    for el in root.iter():
        rv = el.get("data-reveal")
        if rv is None:
            continue
        try:
            reveals.append(int(rv))
        except ValueError:
            issues.append(("ERROR", f"{name}: data-reveal must be an integer (got {rv!r})"))
    beats = frame.get("beats") if isinstance(frame, dict) else None
    if not reveals and not beats:
        return issues
    if reveals and not beats:
        issues.append(("ERROR", f"{name}: has data-reveal groups but figure.json frame has no 'beats'"))
        return issues
    if beats and not reveals:
        issues.append(("ERROR", f"{name}: frame has 'beats' but the SVG has no data-reveal groups"))
        return issues
    mx = max(reveals)
    if sorted(set(reveals)) != list(range(1, mx + 1)):
        issues.append(("ERROR", f"{name}: data-reveal indices must be a gap-free 1..N (got {sorted(set(reveals))})"))
    if len(beats) != mx:
        issues.append(("ERROR", f"{name}: beats count ({len(beats)}) must equal the max data-reveal ({mx})"))
    return issues
```

Then, inside `validate_figure`'s per-frame loop, after the existing `issues += [(lvl, f"{name}: {m}") for lvl, m in lint_svg(root, palette)]` line, add:

```python
        issues += _lint_reveal(root, frame, name)
```

(`frame` and `name` and `root` are all in scope at that point.)

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py' -v`
Expected: PASS (all render tests incl. reveal lint).

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/scripts/render.py .claude/skills/concept-illustrator/scripts/tests/test_render.py
git commit -m "feat(reveal): figure validator lints beats <-> data-reveal consistency"
```
`render.py` (skill) maps to `illustration-engine.md` — update it (a sentence on the reveal lint) in the same commit and run `validate-articles`.

---

## Task 5: HTML player reveal engine

**Files:**
- Modify: `.claude/skills/concept-illustrator/assets/video.template.html`
- Modify: `scripts/build_video.py` (`_slide_html` replaced by container builder; `build_player`)
- Test: `scripts/tests/test_build_video.py`

- [ ] **Step 1: Replace the player template**

Overwrite `.claude/skills/concept-illustrator/assets/video.template.html` with:

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Video</title>
<style>
:root{color-scheme:light dark}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
     background:#0f1115;color:#e8e8e8;display:flex;flex-direction:column;align-items:center;min-height:100vh}
#stage{position:relative;width:min(96vw,1100px);aspect-ratio:16/9;background:#15181f;
       border-radius:10px;overflow:hidden;margin-top:1.2rem}
.slide{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
       justify-content:center;opacity:0;transition:opacity .5s ease;padding:2.2rem 2.2rem 3.4rem;box-sizing:border-box}
.slide.show{opacity:1} .slide.cut{transition:none}
.slide svg{max-width:100%;max-height:78%;height:auto}
.card{font-size:2.4rem;text-align:center;line-height:1.3}
#cap{position:absolute;bottom:1rem;left:0;right:0;text-align:center;font-size:1.05rem;color:#cfd2d8;padding:0 2rem;min-height:1.4em}
[data-reveal]{opacity:0;transition:opacity .55s ease,transform .55s ease}
[data-reveal]:not([data-anim="draw"]){transform:translateY(10px)}
[data-reveal].on{opacity:1;transform:none}
[data-reveal].dim{opacity:.32}
#bar{width:min(96vw,1100px);display:flex;gap:.8rem;align-items:center;margin:.8rem 0}
#prog{flex:1;height:5px;background:#2a2d36;border-radius:3px;overflow:hidden}
#prog>div{height:100%;width:0;background:#5DCAA5}
button{font:inherit;background:#23262e;color:#e8e8e8;border:1px solid #3a3d46;border-radius:6px;padding:.35rem .8rem;cursor:pointer}
label{font-size:.9rem;color:#aab;display:flex;gap:.35rem;align-items:center}
</style></head><body>
<div id="stage">{{SLIDES_HTML}}<div id="cap"></div></div>
<div id="bar">
  <button id="play">⏸ Pause</button>
  <button id="prev">←</button><button id="next">→</button>
  <div id="prog"><div></div></div>
  <span id="count"></span>
  <label><input type="checkbox" id="tts"> 🔊 narrate</label>
  <label><input type="checkbox" id="dim" checked> dim past</label>
</div>
<script>
var M=window.__MANIFEST__={{MANIFEST_JSON}};
var conts=[].slice.call(document.querySelectorAll('#stage > .slide'));
var cap=document.getElementById('cap'),count=document.getElementById('count');
var progEl=document.querySelector('#prog>div');
var tts=document.getElementById('tts'),dim=document.getElementById('dim');
var i=0,playing=true,timer=null,progRAF=null,start=0;
function speak(t){try{var u=new SpeechSynthesisUtterance(t);u.onend=function(){if(playing&&tts.checked)next();};speechSynthesis.cancel();speechSynthesis.speak(u);}catch(e){}}
function drawLines(g){
  var lines=g.tagName.toLowerCase()==='line'?[g]:[].slice.call(g.querySelectorAll('line'));
  lines.forEach(function(ln){
    var x1=+ln.getAttribute('x1'),y1=+ln.getAttribute('y1'),x2=+ln.getAttribute('x2'),y2=+ln.getAttribute('y2');
    var t0=null,D=650; ln.setAttribute('x2',x1); ln.setAttribute('y2',y1);
    function fr(ts){if(!t0)t0=ts;var p=Math.min(1,(ts-t0)/D),e=1-Math.pow(1-p,3);
      ln.setAttribute('x2',(x1+(x2-x1)*e).toFixed(1));ln.setAttribute('y2',(y1+(y2-y1)*e).toFixed(1));
      if(p<1)requestAnimationFrame(fr);}
    requestAnimationFrame(fr);
  });
}
function reveal(cont,level){
  [].slice.call(cont.querySelectorAll('[data-reveal]')).forEach(function(g){
    var k=+g.getAttribute('data-reveal'), shown=(level===null||k<=level);
    if(shown){
      if(!g.classList.contains('on')){g.classList.add('on'); if(g.getAttribute('data-anim')==='draw')drawLines(g);}
      g.classList.toggle('dim', dim.checked && level!==null && k<level);
    } else { g.classList.remove('on','dim'); }
  });
}
function show(n){
  i=(n+M.slides.length)%M.slides.length; var s=M.slides[i];
  conts.forEach(function(c,ci){c.classList.toggle('show',ci===s.container);c.classList.toggle('cut',s.transition!=='crossfade'&&s.transition!=='reveal');});
  var cont=conts[s.container];
  if(cont && cont.querySelector('[data-reveal]')) reveal(cont, s.reveal_to);
  cap.textContent = s.kind==='frame' ? (s.caption||'') : '';
  count.textContent=(i+1)+' / '+M.slides.length;
  clearTimeout(timer);start=performance.now();var dur=s.duration_s*1000;
  if(tts.checked)speak(s.narration); else if(playing)timer=setTimeout(next,dur);
  prog(dur);
}
function prog(dur){cancelAnimationFrame(progRAF);(function step(){var p=Math.min(1,(performance.now()-start)/dur);progEl.style.width=(p*100)+'%';if(p<1&&playing)progRAF=requestAnimationFrame(step);})();}
function next(){show(i+1);}function prev(){show(i-1);}
document.getElementById('next').onclick=next;document.getElementById('prev').onclick=prev;
document.getElementById('play').onclick=function(){playing=!playing;this.textContent=playing?'⏸ Pause':'▶ Play';if(playing)show(i);else{clearTimeout(timer);speechSynthesis.cancel();}};
show(0);
</script></body></html>
```

- [ ] **Step 2: Add the player test (and update the existing one)**

Replace the existing `TestPlayer.test_player_contains_manifest_and_controls` body so it reflects container-grouping (a 3-beat single-frame figure → ONE inlined figure SVG, not three), and keep `test_player_escapes_script_breakout_in_narration` unchanged:

```python
    def test_player_contains_manifest_and_controls(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            beats = [{"caption": "c1", "narration": "n1"},
                     {"caption": "c2", "narration": "n2"},
                     {"caption": "c3", "narration": "n3"}]
            make_figure(registry, "tcp", 1, beats=beats)
            manifest, _ = bv.build_manifest(graph, registry)
            out = os.path.join(base, "video.html")
            bv.build_player(manifest, bv.PLAYER_TEMPLATE, out)
            text = open(out, encoding="utf-8").read()
            self.assertIn("window.__MANIFEST__", text)
            self.assertIn('id="play"', text)
            self.assertNotIn("{{MANIFEST_JSON}}", text)
            self.assertNotIn("{{SLIDES_HTML}}", text)
            # the figure SVG (the fixture writes <text>tcp 1</text>) is inlined ONCE
            self.assertEqual(text.count("tcp 1"), 1)
            # the injected manifest carries reveal_to and container
            self.assertIn('"reveal_to"', text)
            self.assertIn('"container"', text)
```

Add a focused container test:

```python
class TestPlayerContainers(unittest.TestCase):
    def test_beats_share_one_container_cards_separate(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "g")
            registry = os.path.join(base, "r")
            write_decomp(graph, "tcp", True)
            make_figure(registry, "tcp", 1,
                        beats=[{"caption": "a", "narration": "a"},
                               {"caption": "b", "narration": "b"}])
            manifest, _ = bv.build_manifest(graph, registry)
            conts, idx = bv._containers(manifest["slides"])
            frame_slides = [j for j, s in enumerate(manifest["slides"]) if s["kind"] == "frame"]
            # both frame beats map to the same container
            self.assertEqual(idx[frame_slides[0]], idx[frame_slides[1]])
            # title/section/closing each get their own container
            self.assertEqual(len(set(idx)), len(conts))
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest scripts.tests.test_build_video.TestPlayerContainers -v`
Expected: FAIL — `AttributeError: ... '_containers'`.

- [ ] **Step 4: Implement the container builder + rewrite `build_player`/`_slide_html`**

In `scripts/build_video.py`, REPLACE `_slide_html` and `build_player` with a container model:

```python
def _containers(slides):
    """Assign each slide to a DOM container. Consecutive 'frame' slides sharing
    the same image collapse into one container (the figure SVG is inlined once);
    every non-frame slide is its own container.
    Returns (containers, idx) where containers is a list of
    {"kind","image"|None,"caption"} and idx[i] is slide i's container index."""
    containers, idx = [], []
    cur_img, cur = None, -1
    for s in slides:
        if s["kind"] == "frame" and s["image"] == cur_img and cur >= 0:
            idx.append(cur)
            continue
        if s["kind"] == "frame":
            containers.append({"kind": "frame", "image": s["image"], "caption": ""})
            cur, cur_img = len(containers) - 1, s["image"]
        else:
            containers.append({"kind": s["kind"], "image": None, "caption": s["caption"]})
            cur, cur_img = len(containers) - 1, None
        idx.append(cur)
    return containers, idx


def _container_html(c):
    if c["kind"] == "frame":
        return f'<div class="slide">{_read_inner_svg(c["image"])}</div>'
    return f'<div class="slide"><div class="card">{_esc(c["caption"])}</div></div>'


def build_player(manifest, template_path, out_path):
    """Render the self-contained HTML player from a manifest + template; returns out_path."""
    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    containers, idx = _containers(manifest["slides"])
    slides_html = "\n".join(_container_html(c) for c in containers)
    light = dict(manifest)
    light["slides"] = [{"kind": s["kind"], "concept_slug": s["concept_slug"],
                        "caption": s["caption"], "narration": s["narration"],
                        "duration_s": s["duration_s"], "transition": s["transition"],
                        "reveal_to": s["reveal_to"], "container": idx[j]}
                       for j, s in enumerate(manifest["slides"])]
    manifest_json = (json.dumps(light)
                     .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))
    html_out = (template.replace("{{SLIDES_HTML}}", slides_html)
                .replace("{{MANIFEST_JSON}}", manifest_json))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    return out_path
```

(Remove the now-unused `_slide_html`. The `_ROOT_DIM_RE`/`_nest_figure`/`stage_svg` functions are unaffected.)

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest scripts.tests.test_build_video -v`
Expected: PASS (all classes, incl. updated TestPlayer + TestPlayerContainers; MP4 smoke may skip).

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/concept-illustrator/assets/video.template.html scripts/build_video.py scripts/tests/test_build_video.py
git commit -m "feat(reveal): HTML player reveal engine (group beats per frame, animate entrance)"
```
`video.template.html` and `build_video.py` both map to `video-engine.md` — update it (a paragraph on the reveal engine + container grouping) in the same commit; run `validate-articles`.

---

## Task 6: golden reveal example — TCP handshake (additive proof)

**Files:**
- Create: `.claude/skills/concept-illustrator/examples/tcp-handshake-reveal/figure.json`
- Create: `.claude/skills/concept-illustrator/examples/tcp-handshake-reveal/frame-01.svg`

- [ ] **Step 1: Create the figure SVG**

Create `.claude/skills/concept-illustrator/examples/tcp-handshake-reveal/frame-01.svg` — one self-contained frame, design-system style, with six `data-reveal` groups:

```svg
<svg class="cd-svg" xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 680 300" role="img" font-family="sans-serif">
  <title>TCP three-way handshake — progressive reveal</title>
  <desc>Client and server open a connection with SYN, SYN-ACK, ACK, then the line is open.</desc>
  <defs>
    <style>text{font-family:-apple-system,"Segoe UI",Roboto,system-ui,"Helvetica Neue",Arial,sans-serif;}
text.t{font-size:14px;fill:#1c1c1a;} text.ts{font-size:12px;fill:#6b6a64;} text.th{font-size:15px;font-weight:500;fill:#111110;}
.box>rect{fill:#F1EFE8;stroke:#D3D1C7;}
.c-teal>rect{fill:#E1F5EE;stroke:#0F6E56;} .c-teal .th,.c-teal .t{fill:#085041;} .c-teal .ts{fill:#0F6E56;}
.c-coral>rect{fill:#FAECE7;stroke:#993C1D;} .c-coral .th,.c-coral .t{fill:#712B13;} .c-coral .ts{fill:#993C1D;}
.c-green>rect{fill:#EAF3DE;stroke:#3B6D11;} .c-green .th{fill:#27500A;}
.arr{stroke:#6b6a64;stroke-width:1.5;fill:none;stroke-linecap:round;}
.arr.coral{stroke:#993C1D;}
@media (prefers-color-scheme:dark){
text.t{fill:#d6d4ca;} text.ts{fill:#b6b4aa;} text.th{fill:#f2f0e9;}
.box>rect{fill:#2C2C2A;stroke:#5F5E5A;}
.c-teal>rect{fill:#085041;stroke:#5DCAA5;} .c-teal .th,.c-teal .t{fill:#9FE1CB;} .c-teal .ts{fill:#5DCAA5;}
.c-coral>rect{fill:#712B13;stroke:#F0997B;} .c-coral .th,.c-coral .t{fill:#F5C4B3;} .c-coral .ts{fill:#F0997B;}
.c-green>rect{fill:#27500A;stroke:#A7D977;} .c-green .th{fill:#DDF0C6;}
.arr{stroke:#b0aea4;} .arr.coral{stroke:#F0997B;}}</style>
    <marker id="arrow" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path class="arrow-head" d="M0,0 L7,3.5 L0,7 z" fill="#6b6a64"/></marker>
  </defs>

  <g class="node c-teal" data-reveal="1" data-anim="rise">
    <rect x="60" y="70" width="150" height="140" rx="8"/>
    <text class="th" x="135" y="132" text-anchor="middle">Client</text>
    <text class="ts" x="135" y="154" text-anchor="middle">your laptop</text>
  </g>
  <g class="node c-coral" data-reveal="2" data-anim="rise">
    <rect x="470" y="70" width="150" height="140" rx="8"/>
    <text class="th" x="545" y="132" text-anchor="middle">Server</text>
    <text class="ts" x="545" y="154" text-anchor="middle">the website</text>
  </g>

  <g data-reveal="3" data-anim="draw">
    <line class="arr" x1="210" y1="108" x2="468" y2="108" marker-end="url(#arrow)"/>
    <text class="ts" x="340" y="100" text-anchor="middle">SYN →</text>
  </g>
  <g data-reveal="4" data-anim="draw">
    <line class="arr coral" x1="470" y1="142" x2="212" y2="142" marker-end="url(#arrow)"/>
    <text class="ts" x="340" y="166" text-anchor="middle">← SYN-ACK</text>
  </g>
  <g data-reveal="5" data-anim="draw">
    <line class="arr" x1="210" y1="184" x2="468" y2="184" marker-end="url(#arrow)"/>
    <text class="ts" x="340" y="200" text-anchor="middle">ACK →</text>
  </g>

  <g class="c-green" data-reveal="6" data-anim="rise">
    <rect x="276" y="244" width="128" height="30" rx="15"/>
    <text class="th" x="340" y="264" text-anchor="middle">connection open</text>
  </g>
</svg>
```

- [ ] **Step 2: Create figure.json with six beats**

Create `.claude/skills/concept-illustrator/examples/tcp-handshake-reveal/figure.json`:

```json
{
  "concept_slug": "tcp-handshake-reveal",
  "archetype": "illustrative",
  "playback": "static",
  "frames": [
    {
      "file": "frame-01.svg",
      "caption": "The three-way handshake",
      "runbook": "One frame, six reveal steps. Client box (c-teal, data-reveal 1) and Server box (c-coral, 2) rise in. Three arrows draw in order: SYN client->server (3), SYN-ACK server->client (4, coral), ACK client->server (5). Finally a green 'connection open' badge (6) rises in. Arrows use data-anim=draw; boxes and badge use rise. Fixed 680x300 viewBox.",
      "commentary": "Before any data moves, the two computers shake hands: the client sends SYN, the server replies SYN-ACK, the client sends ACK, and the connection is open.",
      "beats": [
        {"caption": "Two computers want to talk.", "narration": "Two computers want to talk to each other."},
        {"caption": "Client and server", "narration": "Think of one as you — the client — and one as the website — the server."},
        {"caption": "SYN: the client waves", "narration": "First, your computer gives the server a little wave to get its attention. Engineers call it a SYN."},
        {"caption": "SYN-ACK: the server waves back", "narration": "The server waves back: I hear you, let's talk. That's the SYN-ACK."},
        {"caption": "ACK: the client confirms", "narration": "Your computer nods: great, I'm ready. The final ACK."},
        {"caption": "The line is open", "narration": "And just like that, the line is open — now they can actually start sending data."}
      ]
    }
  ]
}
```

- [ ] **Step 3: Validate the figure**

Run: `python3 .claude/skills/concept-illustrator/scripts/render.py .claude/skills/concept-illustrator/examples/tcp-handshake-reveal`
Expected: prints `OK ... clean` (the reveal lint passes: 6 beats == max data-reveal 6, gap-free).

- [ ] **Step 4: Build a viewer and eyeball it**

Run: `python3 .claude/skills/concept-illustrator/scripts/render.py .claude/skills/concept-illustrator/examples/tcp-handshake-reveal --viewer /tmp/tcp-reveal.html`
Expected: writes the viewer with no error. (Static viewer shows the full figure; the reveal animation is exercised by the video player in Task 8's end-to-end check.)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/concept-illustrator/examples/tcp-handshake-reveal
git commit -m "feat(reveal): golden TCP-handshake reveal example (6 beats)"
```
No mapped code path changed (it's an example asset), so this commit needs no article update — the pre-commit hook will pass. If it objects, add the example path to the relevant article's prose.

---

## Task 7: tag a quicksort frame (mutation-figure proof)

**Files:**
- Modify: `.claude/skills/concept-illustrator/examples/quicksort/frame-02.svg`
- Modify: `.claude/skills/concept-illustrator/examples/quicksort/figure.json`

- [ ] **Step 1: Read the frame and tag its pointer groups**

Read `.claude/skills/concept-illustrator/examples/quicksort/frame-02.svg`. It has `<g>` groups for the pointer/label annotations (the `j (scanning)`, `i (write slot)`, `pivot` markers above the row). Wrap the three pointer-annotation groups (or add `data-reveal` to the existing `<g>` that holds each) so they reveal in this order, leaving the array-cells backdrop untagged (always visible):
- the row of cells + their values = backdrop (NO data-reveal)
- `data-reveal="1" data-anim="rise"` on the group introducing the `j (scanning)` pointer over the teal cell
- `data-reveal="2" data-anim="rise"` on the `i (write slot)` pointer group
- `data-reveal="3" data-anim="rise"` on the `pivot` pointer group

If the pointers are not already in separate `<g>` wrappers, wrap each pointer (its arrow + label text) in a `<g data-reveal="k" data-anim="rise">…</g>`. Do not move or restyle anything — only group + tag. Keep the existing `viewBox` unchanged.

- [ ] **Step 2: Add beats to frame-02 in figure.json**

In `.claude/skills/concept-illustrator/examples/quicksort/figure.json`, add a `beats` array to the frame-02 entry (the object whose `"file"` is `frame-02.svg`), matching max data-reveal = 3:

```json
"beats": [
  {"caption": "Scan the next value", "narration": "Now we walk the array from left to right. The teal box is the value we are looking at right now."},
  {"caption": "Where small values land", "narration": "The little i marks the next open slot, waiting for a value smaller than the pivot."},
  {"caption": "The pivot is our yardstick", "narration": "Everything is compared against the pivot — the coral value on the right."}
]
```

(Leave the other frames untouched; they keep behaving as single-beat frames.)

- [ ] **Step 3: Validate**

Run: `python3 .claude/skills/concept-illustrator/scripts/render.py .claude/skills/concept-illustrator/examples/quicksort`
Expected: `OK ... clean` — the reveal lint passes for frame-02 (3 beats == max reveal 3), and the other frames (no data-reveal, no beats) are unaffected. If it errors about beats/reveal mismatch, fix the tagging so indices are gap-free 1..3 and exactly three groups are tagged.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/concept-illustrator/examples/quicksort
git commit -m "feat(reveal): tag quicksort frame-02 with reveal steps (mutation-figure proof)"
```

---

## Task 8: authoring docs, knowledge, and end-to-end check

**Files:**
- Modify: `.claude/skills/concept-illustrator/SKILL.md`
- Modify: `.claude/skills/concept-illustrator/references/figure-json.md`
- Modify: `.claude/skills/concept-illustrator/references/visual-vocabulary.md`
- Modify: `knowledge/concepts/dummies-notes/illustration-engine.md`
- Modify: `knowledge/concepts/dummies-notes/video-engine.md`
- Modify: `knowledge/log.md`

- [ ] **Step 1: Document the figure-format additions**

In `.claude/skills/concept-illustrator/references/figure-json.md`, add a "Progressive reveal (optional)" section documenting: SVG `<g>` groups may carry `data-reveal="k"` (1-based) and `data-anim="rise|draw|fade"` (default `rise`; `draw` for `<line>`/path arrows; untagged groups are the always-visible backdrop); and `figure.json` frames may carry `beats: [{caption, narration}]`, one per reveal index, in order, with `len(beats) == max(data-reveal)` and gap-free indices (enforced by `render.py`). A frame with neither behaves as a single beat (backward-compatible).

- [ ] **Step 2: Add authoring guidance to SKILL.md + visual-vocabulary**

In `.claude/skills/concept-illustrator/SKILL.md`, add a short "Progressive reveal" subsection: when a scene builds up additively, wrap each progressively-introduced element in `<g data-reveal="k" data-anim="…">` in explanation order (arrows → `draw`, shapes → `rise`), and write one short, human, plain-language narration beat per step into `beats`. Mutation between major states stays across frames. In `references/visual-vocabulary.md`, add a one-paragraph note on reveal order + entrance styles, pointing to the `tcp-handshake-reveal` example.

- [ ] **Step 3: Update the knowledge articles**

In `knowledge/concepts/dummies-notes/illustration-engine.md`, document the `data-reveal`/`data-anim`/`beats` format and the validator lint (bump `updated: 2026-06-12`; keep status valid). In `knowledge/concepts/dummies-notes/video-engine.md`, document per-beat manifest expansion (`reveal_to`), the `_reveal_svg` cumulative-state "pop" for MP4, and the HTML player reveal engine + per-frame container grouping (bump `updated: 2026-06-12`).

- [ ] **Step 4: Validate articles**

Run: `python3 scripts/validate-articles`
Expected: exit 0.

- [ ] **Step 5: End-to-end reveal build (HTML, on the real registry)**

Register + attach the new example so a video can be built from it, OR build directly from a graph that references an already-illustrated topic. Simplest end-to-end check using the existing TCP deliverable plus the new example is out of scope; instead assert the engine on the example via a tiny build:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
import build_video as bv, tempfile, os, json
d = tempfile.mkdtemp()
fig = ".claude/skills/concept-illustrator/examples/tcp-handshake-reveal"
frames = bv.load_frames(fig)
assert frames and frames[0]["beats"] and len(frames[0]["beats"]) == 6, "beats not read"
# fabricate a one-node manifest pointing at the example frame
slide_img = frames[0]["file"]
slides = [bv._slide("frame", "tcp-handshake-reveal", slide_img, b["caption"], b["narration"], 150,
                    "reveal" if k else "cut", reveal_to=k+1) for k, b in enumerate(frames[0]["beats"])]
manifest = {"topic":"x","title":"X","definition":"d","stage":dict(bv.STAGE),"reading_rate_wpm":150,"slides":slides}
out = os.path.join(d, "video.html"); bv.build_player(manifest, bv.PLAYER_TEMPLATE, out)
html = open(out, encoding="utf-8").read()
assert html.count("TCP three-way handshake") == 1, "figure inlined more than once"
assert '"reveal_to"' in html and '"container"' in html
# MP4 cumulative state: reveal_to=2 hides groups 3..6
svg2 = bv.stage_svg(slides[1], bv.STAGE)
assert svg2.count("visibility:hidden") == 4, svg2.count("visibility:hidden")
print("end-to-end reveal OK: 6 beats, 1 inlined SVG, MP4 pop hides later groups")
PY
```
Expected: prints `end-to-end reveal OK: ...`. (Confirms the figure flows through `load_frames` → per-beat slides → single-inline player → MP4 cumulative pop.)

- [ ] **Step 6: Append a log entry**

Append to the END of `knowledge/log.md`:
```markdown
- 2026-06-12 — Phase 7 (progressive reveal): data-reveal/data-anim on SVG groups + per-frame `beats` in figure.json. build_video expands frames into per-beat slides (reveal_to); MP4 pops via _reveal_svg (per-element visibility); HTML player groups beats per frame and animates entrance (rise / arrow-draw / fade) with optional dim-past. Validator lints beats↔reveal. Golden example: tcp-handshake-reveal (6 beats); quicksort frame-02 tagged. Backward-compatible.
```

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/concept-illustrator/SKILL.md .claude/skills/concept-illustrator/references/figure-json.md .claude/skills/concept-illustrator/references/visual-vocabulary.md knowledge/concepts/dummies-notes/illustration-engine.md knowledge/concepts/dummies-notes/video-engine.md knowledge/log.md
git commit -m "docs(reveal): figure-format + authoring guidance + knowledge for progressive reveal"
```

---

## Task 9: full regression + drift + real MP4 reveal smoke

**Files:** none (verification only)

- [ ] **Step 1: Run every suite**

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-illustrator/scripts/tests -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/concept-decompose/scripts/tests -p 'test_*.py'
```
Expected: all PASS (MP4 smoke skips only if ffmpeg/rasterizer absent — both are installed on this machine, so it should RUN).

- [ ] **Step 2: Validate knowledge + drift**

```bash
python3 scripts/validate-articles
python3 scripts/drift-check --warn-only
```
Expected: `validate-articles` exit 0; `drift-check` shows the touched mapped paths covered by their articles.

- [ ] **Step 3: Real MP4 reveal smoke (rasterizer is installed)**

Build an MP4 from the reveal example to confirm the "pop" renders end-to-end:
```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
import build_video as bv, tempfile, os
d = tempfile.mkdtemp()
fig = ".claude/skills/concept-illustrator/examples/tcp-handshake-reveal"
frames = bv.load_frames(fig); b = frames[0]["beats"]; img = frames[0]["file"]
slides = ([bv._slide("title", None, None, "TCP handshake", "Demo.", 150, "cut")]
          + [bv._slide("frame", "tcp-handshake-reveal", img, x["caption"], x["narration"], 150,
                       "reveal" if k else "cut", reveal_to=k+1) for k, x in enumerate(b)])
manifest = {"topic":"x","title":"X","definition":"d","stage":dict(bv.STAGE),"reading_rate_wpm":150,"slides":slides}
path, notes = bv.render_mp4(manifest, d, bv.STAGE)
print("notes:", notes); print("mp4:", path, os.path.getsize(path) if path and os.path.exists(path) else "MISSING")
PY
```
Expected: prints a real `video.mp4` path with non-zero size and no `rasterizer`/`ffmpeg` skip note. (Each beat is one held PNG showing cumulatively more of the figure.) Clean up `/tmp` afterward.

- [ ] **Step 4: Final commit if anything was adjusted**

If Steps 1–3 surfaced fixes, commit them; otherwise note "no changes — clean".

---

## Notes for the implementer

- **Drift discipline:** never `--no-verify`. `scripts/build_video.py` → `video-engine.md`; `.claude/skills/concept-illustrator/{SKILL.md,scripts/render.py,assets/**}` → `illustration-engine.md` (assets/template also mapped to `video-engine.md`). Update the mapped article in the same commit; keep article `status` ∈ {thin,mature,deprecated}; `validate-articles` must exit 0.
- **Backward compatibility is a hard requirement:** every test that uses a beat-less figure must still pass. A frame with no `data-reveal`/`beats` → one slide, `reveal_to=None`, whole figure shown — identical to today.
- **Zero new dependencies.** The reveal engine is vanilla JS in the template; the MP4 path reuses the existing rsvg/ffmpeg/say pipeline.
- **Run tests from the repo root** so `build_video` resolves `assemble`/`concept_registry`/`render`.
