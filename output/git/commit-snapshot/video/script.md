# A commit (a snapshot stamped with an id and linked to its parent) — narration script

## A commit (a snapshot stamped with an id and linked to its parent)

A commit (a snapshot stamped with an id and linked to its parent)

## A commit photographs your whole project.

A commit is a photo of your entire project at one instant. Here git captures every file — app.py, index.html, style.css — exactly as they are right now.

Git stamps that snapshot with a unique id, a1b3f7. That id is how you point back to this exact version later.

This isn't the first snapshot. The commit taken just before it, 9c2e0d, is still sitting there with its own copy of every file.

The new commit links back to that earlier one — its parent. Every commit knows the exact version that came right before it.

And the parent has a parent, and so on. Follow the chain back and you walk through the project's entire history, one snapshot at a time.
