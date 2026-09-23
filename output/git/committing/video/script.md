# Committing: adding a dot to the history line — narration script

## Committing: adding a dot to the history line

Committing: adding a dot to the history line

## A label marking the commit you are on now

A label marking the commit you are on now

Git keeps your project as a chain of commits — dots on a line, each one a full snapshot linked back to its parent, oldest on the left, newest on the right. Go deeper: the commit figure shows what a single snapshot holds, and the history-graph figure shows how the dots link into one chain.

One dot is special: it's the commit whose files you actually have open right now. A small movable label points at exactly that dot — a 'you are here' pin on your history. Here it sits on the newest commit, e7.

The label isn't stuck. Slide it from e7 back to an earlier dot, 3f, and 'where you are' moves with it — the dashed arrow shows the slide, and the pin now points at 3f.

The label always points at exactly one dot, and the files in your project are that dot's snapshot. Landing on 3f means your files are now 3f's version — move the label and your files follow. Go deeper: the commit figure explains what that snapshot contains.

## Committing: adding a dot to the history line

Committing: adding a dot to the history line

Think of a repo's history as a row of beads on a string. Each bead is a commit, one saved snapshot of your work, and every commit carries an arrow pointing back to the one before it. The teal label sitting on the last bead, c7e, marks exactly where you are right now.

Now you make a commit. A fresh bead, 2b8, pops onto the end of the line, one brand-new snapshot of your work.

That new bead doesn't float free. An arrow links 2b8 back to c7e, the commit you were just on. That backward link is its parent, and it's what threads the whole history together into one chain.

Last, the label slides forward onto 2b8. That's now where you are, and the line is one snapshot longer than before. Go deeper: the snapshot in each bead is 'a commit'; the whole row of linked beads is 'the commit history graph'; the sliding teal tag is 'the label marking the commit you are on now'.
