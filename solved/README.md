# solved/ — automatic session archive

Every Claude Code session in this repo is captured here automatically as a clean
markdown file (`YYYY-MM-DD_<session>.md`) by the **Stop hook**
(`.claude/hooks/capture_session.py`). Each file holds the question/solution pairs
from that session; `../USAGE_LOG.md` indexes them.

This is the raw material for the **learning loop** — see
[docs/09](../docs/09-how-this-repo-learns.md). You don't edit these by hand; you
*review* them periodically and promote recurring lessons into `CLAUDE.md` or new
worked examples.

> These files may contain the full text of your questions and answers. The repo
> is **private** — keep it that way if your sessions include anything sensitive.
