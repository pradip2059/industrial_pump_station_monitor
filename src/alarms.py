from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AlarmSeverity(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AlarmState:
    severity: AlarmSeverity
    message: str


def evaluate_level_alarm(
    level: float,
    low_alarm: float = 20.0,
    high_alarm: float = 80.0,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> AlarmState:
    if level <= minimum:
        return AlarmState(AlarmSeverity.CRITICAL, "CRITICAL LOW LEVEL - SYSTEM STOPPED")
    if level >= maximum:
        return AlarmState(AlarmSeverity.CRITICAL, "CRITICAL HIGH LEVEL - SYSTEM STOPPED")
    if level <= low_alarm:
        return AlarmState(AlarmSeverity.WARNING, "LOW LEVEL ALARM")
    if level >= high_alarm:
        return AlarmState(AlarmSeverity.WARNING, "HIGH LEVEL ALARM")
    return AlarmState(AlarmSeverity.NORMAL, "PROCESS NORMAL")
