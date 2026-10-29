# -*- coding: utf-8 -*-
"""Framework adapter layer for phm_lite_check.

Each adapter lazily imports its host framework, so the base package
stays zero-dependency. Only import the adapter you need.
"""

__all__ = ["langchain_tool", "autogen_tool"]
