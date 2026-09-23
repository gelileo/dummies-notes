# Merging: joining two lines back together — narration script

## Merging: joining two lines back together

Merging: joining two lines back together

## Two lines that split from a shared commit

Here are two lines of history - blue main and teal feature - that split from the shared commit c9 and each added their own commits.

To join them back together, Git creates one brand-new commit, the purple dot g7, sitting between the two lines.

Give it a link back to d4, the tip of the main line: that is its first parent.

Give it a second link back to e5, the tip of the feature line: now g7 has two parents, both histories lead into it, and the two lines are one again.
