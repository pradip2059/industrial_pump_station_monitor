from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from alarms import AlarmSeverity, evaluate_level_alarm
from historian import Historian
from process import ControlMode, PumpStation


UPDATE_MS = 1000


class PumpStationHMI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Industrial Pump Station - SCADA Simulator")
        self.root.geometry("1180x720")
        self.root.minsize(1050, 650)

        self.station = PumpStation()
        self.historian = Historian(max_points=60)
        self.last_alarm_message = None
        self.update_job = None
        self.blink_job = None
        self.blink_on = True

        self._build_ui()
        self._log("HMI initialized")
        self._refresh_display()
        self._schedule_process_update()
        self._schedule_alarm_blink()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------------------------------------------------
    # UI BUILD
    # ---------------------------------------------------------
    def _build_ui(self) -> None:
        title = ttk.Label(
            self.root,
            text="INDUSTRIAL PUMP STATION CONTROL & MONITORING",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(12, 4))

        subtitle = ttk.Label(
            self.root,
            text="SCADA / HMI Process Simulator",
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 12))

        body = ttk.Frame(self.root, padding=12)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self.control_panel = ttk.LabelFrame(body, text="Process Control", padding=14)
        self.control_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.monitor_panel = ttk.LabelFrame(body, text="Monitoring & Historian", padding=14)
        self.monitor_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_control_panel()
        self._build_monitor_panel()

    def _build_control_panel(self) -> None:
        self.mode_var = tk.StringVar(value="MANUAL")
        self.state_var = tk.StringVar(value="SYSTEM IDLE")
        self.pump_var = tk.StringVar(value="PUMP STOPPED")
        self.level_var = tk.StringVar(value="Tank Level: 50.0%")
        self.alarm_var = tk.StringVar(value="PROCESS NORMAL")

        ttk.Label(
            self.control_panel,
            textvariable=self.mode_var,
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(5, 8))

        self.state_label = tk.Label(
            self.control_panel,
            textvariable=self.state_var,
            bg="#666666",
            fg="white",
            font=("Segoe UI", 13, "bold"),
            padx=10,
            pady=8,
        )
        self.state_label.pack(fill="x", pady=4)

        self.pump_label = tk.Label(
            self.control_panel,
            textvariable=self.pump_var,
            bg="#8b0000",
            fg="white",
            font=("Segoe UI", 13, "bold"),
            padx=10,
            pady=8,
        )
        self.pump_label.pack(fill="x", pady=4)

        ttk.Label(
            self.control_panel,
            textvariable=self.level_var,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(16, 4))

        self.level_canvas = tk.Canvas(
            self.control_panel,
            width=270,
            height=42,
            bg="white",
            highlightthickness=1,
            highlightbackground="black",
        )
        self.level_canvas.pack(pady=5)

        alarm_frame = ttk.LabelFrame(self.control_panel, text="Alarm Status", padding=8)
        alarm_frame.pack(fill="x", pady=(14, 8))

        self.alarm_lamp = tk.Canvas(alarm_frame, width=32, height=32, highlightthickness=0)
        self.alarm_lamp.pack(side="left", padx=(4, 10))

        self.alarm_label = tk.Label(
            alarm_frame,
            textvariable=self.alarm_var,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        self.alarm_label.pack(side="left", fill="x", expand=True)

        mode_frame = ttk.Frame(self.control_panel)
        mode_frame.pack(fill="x", pady=(14, 6))

        self.mode_button = ttk.Button(
            mode_frame,
            text="Switch to AUTO",
            command=self.toggle_mode,
        )
        self.mode_button.pack(fill="x")

        ttk.Separator(self.control_panel).pack(fill="x", pady=12)

        self.start_button = ttk.Button(
            self.control_panel,
            text="START PUMP",
            command=self.start_pump,
        )
        self.start_button.pack(fill="x", pady=4)

        self.stop_button = ttk.Button(
            self.control_panel,
            text="STOP PUMP",
            command=self.stop_pump,
        )
        self.stop_button.pack(fill="x", pady=4)

        self.fill_button = ttk.Button(
            self.control_panel,
            text="SIMULATE INFLOW +5%",
            command=self.manual_fill,
        )
        self.fill_button.pack(fill="x", pady=4)

        self.drain_button = ttk.Button(
            self.control_panel,
            text="SIMULATE DRAIN -5%",
            command=self.manual_drain,
        )
        self.drain_button.pack(fill="x", pady=4)

        ttk.Separator(self.control_panel).pack(fill="x", pady=12)

        self.standby_button = ttk.Button(
            self.control_panel,
            text="SYSTEM STANDBY",
            command=self.set_standby,
        )
        self.standby_button.pack(fill="x", pady=4)

        ttk.Label(
            self.control_panel,
            text=(
                "AUTO logic:\n"
                "Start pump at ≥ 75%\n"
                "Stop pump at ≤ 25%\n\n"
                "Warnings:\n"
                "High ≥ 80% | Low ≤ 20%"
            ),
            justify="left",
        ).pack(anchor="w", pady=(14, 0))

    def _build_monitor_panel(self) -> None:
        trend_frame = ttk.LabelFrame(self.monitor_panel, text="Tank Level Trend", padding=6)
        trend_frame.pack(fill="both", expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6.5, 3.3))
        (self.trend_line,) = self.ax.plot([], [])
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        self.ax.set_ylabel("Level (%)")
        self.ax.set_xlabel("Samples")
        self.ax.grid(True, alpha=0.25)

        self.trend_canvas = FigureCanvasTkAgg(self.fig, master=trend_frame)
        self.trend_canvas.get_tk_widget().pack(fill="both", expand=True)

        event_frame = ttk.LabelFrame(self.monitor_panel, text="Event Historian", padding=6)
        event_frame.pack(fill="both", expand=True, pady=(12, 0))

        list_container = ttk.Frame(event_frame)
        list_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.event_list = tk.Listbox(
            list_container,
            font=("Consolas", 10),
            yscrollcommand=scrollbar.set,
        )
        self.event_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.event_list.yview)

    # ---------------------------------------------------------
    # OPERATOR COMMANDS
    # ---------------------------------------------------------
    def toggle_mode(self) -> None:
        new_mode = (
            ControlMode.AUTO
            if self.station.mode is ControlMode.MANUAL
            else ControlMode.MANUAL
        )
        self.station.set_mode(new_mode)
        self._log(f"Control mode changed to {new_mode.value}")
        self._refresh_display()

    def start_pump(self) -> None:
        if self.station.start_pump():
            self._log("Manual command: pump START")
        else:
            self._log("START command rejected by mode/interlock", deduplicate=False)
        self._refresh_display()

    def stop_pump(self) -> None:
        if self.station.stop_pump():
            self._log("Manual command: pump STOP")
        else:
            self._log("STOP command rejected while AUTO mode is active", deduplicate=False)
        self._refresh_display()

    def manual_fill(self) -> None:
        if self.station.manual_fill(5.0):
            self._log("Operator simulation: tank inflow +5%")
        else:
            self._log("FILL command blocked by interlock", deduplicate=False)
        self._refresh_display()

    def manual_drain(self) -> None:
        if self.station.manual_drain(5.0):
            self._log("Operator simulation: tank drain -5%")
        else:
            self._log("DRAIN command blocked by interlock", deduplicate=False)
        self._refresh_display()

    def set_standby(self) -> None:
        self.station.disable()
        self._log("System placed in STANDBY")
        self._refresh_display()

    # ---------------------------------------------------------
    # PROCESS / ALARMS
    # ---------------------------------------------------------
    def _process_tick(self) -> None:
        previous_pump = self.station.pump_running
        previous_enabled = self.station.system_enabled

        self.station.update(1.0)

        if self.station.mode is ControlMode.AUTO:
            if previous_pump != self.station.pump_running:
                action = "STARTED" if self.station.pump_running else "STOPPED"
                self._log(f"AUTO control: pump {action}")

        if previous_enabled and not self.station.system_enabled:
            self._log("Critical process limit reached - automatic shutdown")

        self.historian.add_level(self.station.level)
        self._refresh_display()

    def _schedule_process_update(self) -> None:
        self._process_tick()
        self.update_job = self.root.after(UPDATE_MS, self._schedule_process_update)

    def _schedule_alarm_blink(self) -> None:
        alarm = self._current_alarm()
        if alarm.severity is AlarmSeverity.CRITICAL:
            self.blink_on = not self.blink_on
            self._draw_alarm_lamp("red" if self.blink_on else "white")
        self.blink_job = self.root.after(500, self._schedule_alarm_blink)

    def _current_alarm(self):
        cfg = self.station.config
        return evaluate_level_alarm(
            self.station.level,
            low_alarm=cfg.low_alarm_level,
            high_alarm=cfg.high_alarm_level,
            minimum=cfg.min_level,
            maximum=cfg.max_level,
        )

    # ---------------------------------------------------------
    # DISPLAY
    # ---------------------------------------------------------
    def _refresh_display(self) -> None:
        alarm = self._current_alarm()

        self.mode_var.set(f"CONTROL MODE: {self.station.mode.value}")
        self.level_var.set(f"Tank Level: {self.station.level:.1f}%")
        self.alarm_var.set(alarm.message)

        if self.station.system_enabled:
            self.state_var.set("SYSTEM RUNNING")
            self.state_label.config(bg="#2457a6")
        else:
            self.state_var.set("SYSTEM STANDBY")
            self.state_label.config(bg="#666666")

        if self.station.pump_running:
            self.pump_var.set("PUMP RUNNING")
            self.pump_label.config(bg="#157a37")
        else:
            self.pump_var.set("PUMP STOPPED")
            self.pump_label.config(bg="#8b0000")

        if self.station.mode is ControlMode.AUTO:
            self.mode_button.config(text="Switch to MANUAL")
            button_state = "disabled"
        else:
            self.mode_button.config(text="Switch to AUTO")
            button_state = "normal"

        for button in (
            self.start_button,
            self.stop_button,
            self.fill_button,
            self.drain_button,
        ):
            button.config(state=button_state)

        self._draw_level_bar(alarm.severity)

        if alarm.severity is AlarmSeverity.NORMAL:
            self._draw_alarm_lamp("green")
        elif alarm.severity is AlarmSeverity.WARNING:
            self._draw_alarm_lamp("orange")

        if alarm.message != self.last_alarm_message:
            self._log(f"Alarm state: {alarm.message}")
            self.last_alarm_message = alarm.message

        self._refresh_trend()
        self._refresh_event_list()

    def _draw_level_bar(self, severity: AlarmSeverity) -> None:
        self.level_canvas.delete("all")
        width = max(0, min(270, 270 * self.station.level / 100.0))

        if severity is AlarmSeverity.CRITICAL:
            fill = "red"
        elif severity is AlarmSeverity.WARNING:
            fill = "orange"
        else:
            fill = "green"

        self.level_canvas.create_rectangle(
            0, 0, width, 42, fill=fill, outline=""
        )
        self.level_canvas.create_text(
            135,
            21,
            text=f"{self.station.level:.1f}%",
            font=("Segoe UI", 11, "bold"),
        )

    def _draw_alarm_lamp(self, color: str) -> None:
        self.alarm_lamp.delete("all")
        self.alarm_lamp.create_oval(
            4, 4, 28, 28, fill=color, outline="black"
        )

    def _refresh_trend(self) -> None:
        values = list(self.historian.level_history)
        self.trend_line.set_data(range(len(values)), values)
        self.ax.set_xlim(0, max(20, len(values)))
        self.trend_canvas.draw_idle()

    def _refresh_event_list(self) -> None:
        self.event_list.delete(0, tk.END)
        for event in self.historian.events:
            self.event_list.insert(tk.END, event)

    def _log(self, message: str, deduplicate: bool = True) -> None:
        self.historian.log(message, deduplicate=deduplicate)

    def close(self) -> None:
        if self.update_job is not None:
            self.root.after_cancel(self.update_job)
        if self.blink_job is not None:
            self.root.after_cancel(self.blink_job)

        plt.close(self.fig)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    PumpStationHMI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
