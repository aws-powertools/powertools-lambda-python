from __future__ import annotations

is_cold_start = True


def reset_cold_start_flag():
    global is_cold_start
    if not is_cold_start:
        is_cold_start = True
