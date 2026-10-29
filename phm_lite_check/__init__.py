# -*- coding: utf-8 -*-
"""phm_lite_check -- deterministic physics plausibility checking for
LLM outputs and robotics datasets. Offline subset of the PHM engine.

Public API:
    check_text(text)                    -> scan text for implausible quantities
    full_check(text, kinematics, conservation) -> text + kinematics + conservation
    check_quantity(value, unit)         -> one quantity against physical law
    check_robotics_record(record)       -> robotics/embodied-AI dataset record
    ENGINE_ID, __version__
"""

from .checker import (check_text, full_check, check_quantity,
                      check_probability, check_kinematics, check_conservation,
                      ENGINE_ID, __version__ as _checker_version)
from .robotics import check_robotics_record

__version__ = "1.0.0"
__all__ = [
    "check_text", "full_check", "check_quantity", "check_probability",
    "check_kinematics", "check_conservation", "check_robotics_record",
    "ENGINE_ID", "__version__",
]
