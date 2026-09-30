from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControlMode(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class PumpState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"


@dataclass
class PumpStationConfig:
    initial_level: float = 50.0
    min_level: float = 0.0
    max_level: float = 100.0

    # Simulation rates, percentage points per second.
    inflow_rate: float = 1.0
    pump_outflow_rate: float = 3.0

    # Automatic-control setpoints.
    auto_start_level: float = 75.0
    auto_stop_level: float = 25.0

    # Alarm thresholds.
    low_alarm_level: float = 20.0
    high_alarm_level: float = 80.0


class PumpStation:
    """Simple tank + discharge-pump process model."""

    def __init__(self, config: PumpStationConfig | None = None) -> None:
        self.config = config or PumpStationConfig()
        self.level = self.config.initial_level
        self.mode = ControlMode.MANUAL
        self.pump_state = PumpState.STOPPED
        self.system_enabled = False

    @property
    def pump_running(self) -> bool:
        return self.pump_state is PumpState.RUNNING

    def enable(self) -> None:
        self.system_enabled = True

    def disable(self) -> None:
        self.system_enabled = False
        self.stop_pump()

    def set_mode(self, mode: ControlMode) -> None:
        self.mode = mode
        self.system_enabled = True

    def start_pump(self) -> bool:
        if self.mode is not ControlMode.MANUAL:
            return False
        if self.level <= self.config.min_level:
            return False
        self.system_enabled = True
        self.pump_state = PumpState.RUNNING
        return True

    def stop_pump(self) -> bool:
        if self.mode is not ControlMode.MANUAL and self.system_enabled:
            return False
        self.pump_state = PumpState.STOPPED
        return True

    def force_stop_pump(self) -> None:
        self.pump_state = PumpState.STOPPED

    def manual_fill(self, amount: float = 5.0) -> bool:
        """Operator test function. Interlocked while pump is running."""
        if self.mode is not ControlMode.MANUAL or self.pump_running:
            return False
        self.level = min(self.config.max_level, self.level + amount)
        return True

    def manual_drain(self, amount: float = 5.0) -> bool:
        """Operator test function. Interlocked unless pump is running."""
        if self.mode is not ControlMode.MANUAL or not self.pump_running:
            return False
        self.level = max(self.config.min_level, self.level - amount)
        return True

    def _apply_auto_control(self) -> None:
        if self.level >= self.config.auto_start_level:
            self.pump_state = PumpState.RUNNING
        elif self.level <= self.config.auto_stop_level:
            self.pump_state = PumpState.STOPPED

    def update(self, dt_seconds: float = 1.0) -> None:
        if not self.system_enabled:
            return

        if self.mode is ControlMode.AUTO:
            self._apply_auto_control()

        # Tank always receives simulated inflow.
        delta = self.config.inflow_rate * dt_seconds

        # Pump removes fluid while running.
        if self.pump_running:
            delta -= self.config.pump_outflow_rate * dt_seconds

        self.level += delta
        self.level = max(self.config.min_level, min(self.config.max_level, self.level))

        # Critical process protection.
        if self.level <= self.config.min_level:
            self.force_stop_pump()
            self.system_enabled = False

        if self.level >= self.config.max_level:
            self.force_stop_pump()
            self.system_enabled = False
