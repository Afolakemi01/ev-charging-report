import json
import logging
from pathlib import Path

from ev_charging_report.cleaning import (
    build_summary,
    read_file,
    write_clean,
    write_rejects,
    write_summary,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s, %(levelname)s, %(message)s",
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    logger.info("run starting...")

    config = load_config(PROJECT_ROOT / "config.json")
    input_path = PROJECT_ROOT / config["input_path"]
    clean_path = PROJECT_ROOT / config["clean_output_path"]
    reject_path = PROJECT_ROOT / config["rejects_output_path"]
    summary_path = PROJECT_ROOT / config["summary_output_path"]

    cleaned, rejects, valid_rows, rejected_rows, rows_in = read_file(input_path)
    logger.info(
        "rows_in: %s, valid_rows: %s, rejected_rows: %s",
        rows_in,
        valid_rows,
        rejected_rows,
    )

    written = write_clean(cleaned, clean_path)
    logger.info("wrote %s rows to %s", written, clean_path)

    rejects_writter = write_rejects(rejects, reject_path)
    logger.info("wrote %s rejects to %s", rejects_writter, reject_path)

    summary = build_summary(cleaned, valid_rows, rejected_rows)
    write_summary(summary, summary_path)
    logger.info(
        "wrote summary to %s: %s valid rows, %s rejected rows",
        summary_path,
        valid_rows,
        rejected_rows,
    )

    logger.info("finished")


if __name__ == "__main__":
    main()
