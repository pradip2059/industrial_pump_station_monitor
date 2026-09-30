# Suggested I/O and PLC Tag Map

The Python simulator is software-only, but its variables can be mapped to an industrial PLC/SCADA tag structure.

## Analog Tags

| Tag | Type | Description |
|---|---|---|
| `Tank_Level_PV` | REAL | Tank level process value, 0-100% |
| `Tank_Level_High_SP` | REAL | High warning setpoint |
| `Tank_Level_Low_SP` | REAL | Low warning setpoint |
| `Auto_Start_Level_SP` | REAL | Pump auto-start setpoint |
| `Auto_Stop_Level_SP` | REAL | Pump auto-stop setpoint |

## Digital Commands

| Tag | Type | Description |
|---|---|---|
| `Pump_Start_Cmd` | BOOL | Manual pump start command |
| `Pump_Stop_Cmd` | BOOL | Manual pump stop command |
| `System_Standby_Cmd` | BOOL | Place system in standby |
| `Mode_Auto_Cmd` | BOOL | Select automatic operation |
| `Mode_Manual_Cmd` | BOOL | Select manual operation |

## Equipment Status

| Tag | Type | Description |
|---|---|---|
| `Pump_Run_Sts` | BOOL | Pump running status |
| `System_Enabled_Sts` | BOOL | Process enabled |
| `Mode_Auto_Sts` | BOOL | Automatic mode active |
| `Mode_Manual_Sts` | BOOL | Manual mode active |

## Alarm Tags

| Tag | Type | Description |
|---|---|---|
| `Alm_Level_High` | BOOL | High-level warning |
| `Alm_Level_Low` | BOOL | Low-level warning |
| `Alm_Level_HighHigh` | BOOL | Critical high-level alarm |
| `Alm_Level_LowLow` | BOOL | Critical low-level alarm |

## Example Physical I/O Mapping

A real pump-station implementation could map the logic to field I/O such as:

| Signal | Typical Type | Example Function |
|---|---|---|
| Tank level transmitter | 4-20 mA analog input | Tank level feedback |
| Pump starter/VFD run command | Digital output | Start pump |
| Pump running auxiliary contact | Digital input | Running feedback |
| Pump fault contact | Digital input | Equipment fault |
| Emergency stop | Digital input | Safety shutdown |
| High-high level switch | Digital input | Independent overflow protection |
| Low-low level switch | Digital input | Dry-run protection |

Actual addresses depend on the selected PLC and I/O hardware.
