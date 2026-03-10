# -*- coding: utf-8 -*-
"""Minimal smoke test for manual local verification.

This script demonstrates:
1. Context-managed sandbox lifecycle (create -> use -> teardown).
2. Running a simple IPython cell remotely in the sandbox.
"""

from alias_sandbox import AliasSandbox

with AliasSandbox() as sandbox:
    print(sandbox.sandbox_id)
    print(sandbox.run_ipython_cell("import time\ntime.sleep(1)"))
    input("Press Enter to continue...")
