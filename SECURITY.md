# Security policy

NVDA-retree runs inside NVDA, a screen reader that sits in the user's
local accessibility pipeline. The add-on does not open network
sockets, does not read or write files outside its own JSON state
(`semanticTree.json` under the NVDA user config), and does not alter
the accessibility tree of other applications.

If you believe you have found a vulnerability (for example: a way to
read or write files outside the NVDA config directory, to execute
arbitrary code through a crafted saved-state file, or to crash NVDA
from another process via this add-on) please **do not open a public
issue**. Instead, email the maintainer directly.

* Contact: Kyle Keane — kkeane@mit.edu
* Expected acknowledgement: within 7 days.
* Expected remediation for confirmed issues: within 30 days.

We will credit reporters in the release notes unless anonymity is
requested.
