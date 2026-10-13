import pytest

from ev_charging_report.cleaning import blank_check, field_check, parse_session


def test_check_field_rejects_missing_field():
    record = {
        "session_id": "S1",
        "station_id": "A",
        "end_time": "2026-09-01T09:00:00",
        "kwh": "12.5",
    }

    record, reason = field_check(record)
    assert reason == "missing_field"


def test_check_blank_rejects_invalid():
    record = {
        "session_id": "S1",
        "station_id": "A",
        "start_time": " ",
        "end_time": "2026-09-01T09:00:00",
        "kwh": "12.5",
    }

    record, reason = blank_check(record)
    assert reason == "blank_start_time"
    assert record["start_time"] == " "


def test_check_parse_session_raises_error():
    record = {
        "session_id": "S1",
        "station_id": "A",
        "start_time": "09/03/2026/01T10:15:00",
        "end_time": "2026-09-01T09:00:00",
        "kwh": "12.5",
    }
    with pytest.raises(ValueError):
        parse_session(record)
