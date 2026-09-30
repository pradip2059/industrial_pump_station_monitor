# Control Philosophy

## 1. Process Description

The simulated process contains:

- one storage tank,
- one discharge pump,
- a continuous incoming process flow,
- a tank-level transmitter represented as a percentage,
- manual operator controls,
- automatic level control,
- alarms and critical shutdown logic.

The tank level is constrained to 0-100%.

## 2. Operating Modes

### MANUAL

The operator can:

- start the pump,
- stop the pump,
- introduce a simulated inflow disturbance,
- introduce a simulated drain disturbance,
- place the system in standby.

Interlocks prevent contradictory process actions.

### AUTO

The pump is controlled from tank level.

| Condition | Command |
|---|---|
| Level ≥ 75% | Pump RUN |
| Level ≤ 25% | Pump STOP |
| 25% < Level < 75% | Maintain previous pump state |

This creates hysteresis and prevents rapid pump cycling.

## 3. Process Dynamics

The simulator uses simplified rates for demonstration:

- background inflow: +1 percentage point/second,
- pump discharge: -3 percentage points/second while running,
- net change while pump runs: approximately -2 percentage points/second.

The values are simulation parameters rather than specifications for a physical pump.

## 4. Alarm Philosophy

### Normal
20% < Level < 80%

### Low Warning
Level ≤ 20%

### High Warning
Level ≥ 80%

### Critical Low
Level reaches 0%.

Response:
- pump forced OFF,
- process simulation disabled,
- critical alarm annunciated.

### Critical High
Level reaches 100%.

Response:
- pump forced OFF,
- process simulation disabled,
- critical alarm annunciated.

## 5. Interlocks

### Pump Start Interlock
Manual pump start is rejected when:
- AUTO mode is selected, or
- tank level is already at the minimum process limit.

### Manual Fill Interlock
Manual fill simulation is blocked while the pump is running.

### Manual Drain Interlock
Manual drain simulation is blocked unless the pump is running.

### AUTO Mode Interlock
Manual process command buttons are disabled while AUTO mode is active.

## 6. HMI Information

The HMI displays:

- control mode,
- system state,
- pump state,
- tank level,
- alarm state,
- graphical tank-level bar,
- tank-level trend,
- timestamped event history.

## 7. PLC Mapping Concept

The same control philosophy can be represented in a PLC program using:

- BOOL tags for pump commands/status,
- REAL tags for tank level and thresholds,
- alarm bits for process conditions,
- mode-selection logic,
- permissives/interlocks,
- timers if required,
- HMI tags for commands, status, trends, and alarm displays.

The Python application is therefore useful as a software prototype for an industrial PLC/HMI implementation.
