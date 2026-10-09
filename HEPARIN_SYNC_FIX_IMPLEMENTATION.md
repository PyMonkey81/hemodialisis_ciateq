# Fix: Synchronization of Clamped Heparin Time with Firmware

## Problem Summary
When heparin auto-stop time is clamped due to therapy duration changes, the value is updated locally (JSON and UI) but **NOT sent to the firmware**. This causes:
1. `_validate_and_clamp_heparin_auto_stop_time()` writes 00:30 locally
2. The warning is shown
3. But `heparineAutoStopHours` and `heparineAutoStopMinutes` remain 01:00 in the firmware
4. When the heparin screen opens, the old firmware reading (01:00) overwrites the local value (00:30)
5. The dosage sent is wrong (1.0 instead of 0.5)

## Root Cause
- Tags `heparineAutoStopHours`, `heparineAutoStopMinutes`, and `heparineTherapyDosage` are **not in `LOCAL_SETPOINT_TAGS`**
- When `update_value()` receives a serial read, it's not blocked by the LOCAL_SETPOINT_TAGS check
- The old firmware value overwrites the clamped value

## Solution Implemented

### 1. Add Ignore Mechanism (`ignore_tags_until`)
**File:** `gui/appMainHemodialysis.py`

Added a dictionary in `__init__` to track which tags should be ignored until a certain timestamp:
```python
self.ignore_tags_until = {}  # {tag: expiration_time_in_seconds_since_epoch}
```

### 2. Modify `update_value()` to Check Ignore List
**File:** `gui/appMainHemodialysis.py`, line ~2487

After the LOCAL_SETPOINT_TAGS check, verify if the tag is in the ignore list:
```python
if tag in self.ignore_tags_until:
    if time.time() < self.ignore_tags_until[tag]:
        logger.debug(f"[HEPARIN-SYNC] Ignorando lectura de {tag}={value}")
        return
    else:
        del self.ignore_tags_until[tag]
```

### 3. Modify `_validate_and_clamp_heparin_auto_stop_time()` - 4 Steps

#### Step 1: Write to current_values (Already Done)
```python
self.current_values["heparineAutoStopHours"] = float(clamped_h)
self.current_values["heparineAutoStopMinutes"] = float(clamped_m)
self._persist_therapy_config_tag(...)
```

#### Step 2: Send to Firmware via `_write_setpoint()`
Use the same path as the Heparin Time numpad:
```python
self._write_setpoint("heparineAutoStopHours", float(clamped_h))
self._write_setpoint("heparineAutoStopMinutes", float(clamped_m))
self._write_setpoint("heparineTherapyDosage", dosage_ml)
```

**Why this works:** Since these tags are NOT in `LOCAL_SETPOINT_TAGS`, `_write_setpoint()` sends them to the firmware via `serial_comm.write_double()`.

#### Step 3: Block Old Firmware Reads for 3 Seconds
```python
ignore_until = time.time() + 3.0
self.ignore_tags_until["heparineAutoStopHours"] = ignore_until
self.ignore_tags_until["heparineAutoStopMinutes"] = ignore_until
self.ignore_tags_until["heparineTherapyDosage"] = ignore_until
```

This prevents the old 01:00 value from overwriting the 00:30 that was just sent.

#### Step 4: Update UI Widget
```python
if (hasattr(self, 'heparin_config_screen') and self.heparin_config_screen is not None):
    self.heparin_config_screen.input_heparin_auto_stop.setText(f"{clamped_h:02d}:{clamped_m:02d}")
    self.heparin_config_screen.current_values["heparineAutoStopHours"] = float(clamped_h)
    self.heparin_config_screen.current_values["heparineAutoStopMinutes"] = float(clamped_m)
    self.heparin_config_screen.current_values["heparineTherapyDosage"] = dosage_ml
```

## Expected Behavior After Fix

**Test Case:** Therapy 3:00 → Therapy 1:00 with Heparin at 1:00

1. ✓ Warning is shown: "Tiempo de heparina limitado a 00:30"
2. ✓ Widget shows: 00:30
3. ✓ Firmware receives: heparineAutoStopHours=0, heparineAutoStopMinutes=30
4. ✓ Dosage sent: 0.5 ml (not 1.0)
5. ✓ When opening heparin screen later, value remains 00:30 (old firmware read is blocked)
6. ✓ No inconsistency errors in logs

## Changes Made

### File: `gui/appMainHemodialysis.py`

1. **Line ~283:** Added `self.ignore_tags_until = {}` in `__init__`
2. **Line ~2487:** Added ignore check in `update_value()` 
3. **Line ~1145:** Modified `_validate_and_clamp_heparin_auto_stop_time()` to:
   - Call `_write_setpoint()` for the 3 tags
   - Mark tags as ignored for 3 seconds
   - Improved logging with [HEPARIN-SYNC] prefix

## Testing

- All existing tests pass (18/18 in `tests/test_heparin_time.py`)
- No syntax errors
- Code compiles successfully

## Notes

- The 3-second blocking window is conservative and accounts for:
  - Serial communication latency
  - Firmware processing time
  - Potential retransmissions
- Tags are automatically unblocked from the dictionary once the time expires
- Logging includes [HEPARIN-SYNC] prefix for easy tracking

