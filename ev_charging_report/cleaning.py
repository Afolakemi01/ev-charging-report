import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pyarrow as pa
import pyarrow.parquet as pq

EXPECTED = {"session_id", "station_id", "start_time", "end_time", "kwh"}
SCHEMA = pa.schema(
    [
        ("session_id", pa.string()),
        ("station_id", pa.string()),
        ("start_time", pa.timestamp("us")),
        ("end_time", pa.timestamp("us")),
        ("kwh", pa.decimal128(10, 2)),
    ]
)


def field_check(record):
    keys = set(record)
    missing = EXPECTED - keys

    if missing:
        return (record, "missing_field")

    for field in sorted(EXPECTED):
        if record[field] is None:
            return (record, f"missing_{field}")

    return (record, None)


def blank_check(record):
    cleaned = {key: value.strip() for key, value in record.items()}

    for field in sorted(EXPECTED):
        if cleaned[field] == "":
            return (record, f"blank_{field}")

    return (cleaned, None)


def parse_session(record):
    try:
        start_time = datetime.fromisoformat(record["start_time"])
    except ValueError:
        raise ValueError("unparsable_time")

    try:
        end_time = datetime.fromisoformat(record["end_time"])
    except ValueError:
        raise ValueError("unparsable_time")

    if end_time <= start_time:
        raise ValueError("end_not_after_start")

    try:
        kwh = Decimal(record["kwh"])
    except InvalidOperation:
        raise ValueError("kwh_is_invalid")

    if not kwh.is_finite():
        raise ValueError("kwh_is_invalid")

    if kwh <= 0 or kwh > 150:
        raise ValueError("kwh_is_invalid")

    cleaned = {
        "session_id": record["session_id"],
        "station_id": record["station_id"],
        "start_time": start_time,
        "end_time": end_time,
        "kwh": kwh,
    }
    return cleaned


def validate_rows(row, seen):

    record, reason = field_check(row)
    if reason is not None:
        return (row, reason)

    record, reason = blank_check(record)
    if reason is not None:
        return (row, reason)

    try:
        record = parse_session(record)
    except ValueError as e:
        return (row, str(e))

    if row["session_id"] in seen:
            return (row, "duplicate_session")

    seen.add(row["session_id"])
    return (record, None)


def read_file(path):
    rows_in = 0
    rejected_rows = 0
    valid_rows = 0
    cleaned = []
    rejects = []
    seen = set()

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for line_no, row in enumerate(reader, start=2):
            rows_in += 1

            record, reason = validate_rows(row, seen)

            if reason is not None:
                rejected_rows += 1
                rejects.append(
                    {
                        "line_number": line_no,
                        "session_id": row["session_id"],
                        "reason": reason,
                    }
                )

            else:
                cleaned.append(record)
                valid_rows += 1

    assert rows_in == valid_rows + rejected_rows, (
        f"assertion failed, count do not match: rows_in:{rows_in}, valid_rows:{valid_rows}, rejected_rows:{rejected_rows}"
    )
    return cleaned, rejects, valid_rows, rejected_rows, rows_in


def write_clean(cleaned, path):
    table = pa.Table.from_pylist(cleaned, schema=SCHEMA)
    pq.write_table(table, path)
    return len(cleaned)


def write_rejects(rejects, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        field_names = ["line_number", "session_id", "reason"]
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for item in rejects:
            writer.writerow(
                {
                    "line_number": item["line_number"],
                    "reason": item["reason"],
                    "session_id": item["session_id"],
                }
            )
    return len(rejects)


def build_summary(cleaned, valid_rows, rejected_rows):
    stations = {}
    for record in cleaned:
        station = record["station_id"]
        if station not in stations:
            stations[station] = {"sessions": 0, "kwh": Decimal(0)}
        stations[station]["sessions"] += 1
        stations[station]["kwh"] += record["kwh"]

    summary = {
        "stations": stations,
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
    }
    return summary


def write_summary(summary, path):

    for station in summary["stations"]:
        summary["stations"][station]["kwh"] = float(summary["stations"][station]["kwh"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    print("cleaning.py is a module; run pipeline.py instead")
