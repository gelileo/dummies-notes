# The commit history graph — narration script

## The commit history graph

The commit history graph

## It starts with one commit.

Every history begins with a single commit — one saved snapshot of your whole project, stamped with its own id. Go deeper: the commit figure shows what's inside one.

Make a change and you add another commit. It stores a link pointing back to the one before it — its parent.

Every new commit does the same, so the links chain together, each dot reaching back to the one before it.

Line them all up and you get a chain: oldest on the left, newest on the right. That chain is your project's entire history.

Want an old version back? Git starts at the newest commit and follows the links backward until it reaches the one you want, rebuilding it exactly. The past is fixed and always recoverable. Go deeper: the version figure explains what a saved snapshot is.
