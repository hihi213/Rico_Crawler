from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def run_main(args: list[str]) -> None:
    main_path = Path(__file__).resolve().parent / "main.py"
    cmd = [sys.executable, str(main_path), *args]
    subprocess.run(cmd, check=True)


def usage(logger: logging.Logger) -> None:
    logger.info("Usage:")
    logger.info("  python run.py                     # 2 pages (default)")
    logger.info("  python run.py page <N>             # N pages")
    logger.info("  python run.py interval <SEC> [N]   # interval mode, optional pages")
    logger.info("  python run.py reset                # reset checkpoint then run")
    logger.info("  python run.py set <KEY> <VALUE>    # update config.yaml")
    logger.info("  python run.py set-keys             # show configurable keys")
    logger.info("  python run.py filter               # quick filter run")
    logger.info("Examples:")
    logger.info("  python run.py page 5")
    logger.info("  python run.py interval 3600 2")
    logger.info("  python run.py set crawl.max_pages 10")
    logger.info("  python run.py filter")


def collect_keys(data: dict[str, Any], prefix: str = "") -> list[str]:
    keys: list[str] = []
    for k, v in data.items():
        path = f"{prefix}{k}" if not prefix else f\"{prefix}.{k}\"
        if isinstance(v, dict):
            keys.extend(collect_keys(v, path))
        else:
            keys.append(path)
    return keys


def parse_value(value: str) -> Any:
    return yaml.safe_load(value)


def key_exists(data: dict[str, Any], key_path: str) -> bool:
    keys = key_path.split(".")
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    return True


def set_config_value(config_path: Path, key_path: str, value: Any) -> None:
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    keys = key_path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value

    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("run")
    argv = sys.argv[1:]

    if not argv:
        run_main(["--max-pages", "2"])
        return

    if argv[0] == "page" and len(argv) == 2 and argv[1].isdigit():
        run_main(["--max-pages", argv[1]])
        return

    if argv[0] == "interval" and len(argv) in (2, 3) and argv[1].isdigit():
        args = ["--mode", "interval", "--interval-sec", argv[1]]
        if len(argv) == 3 and argv[2].isdigit():
            args.extend(["--max-pages", argv[2]])
        run_main(args)
        return

    if argv[0] == "reset" and len(argv) == 1:
        run_main(["--reset-checkpoint"])
        return

    if argv[0] == "set" and len(argv) == 3:
        config_path = Path(__file__).resolve().parent / "config.yaml"
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not key_exists(data, argv[1]):
            logger.warning("Unknown key: %s", argv[1])
            logger.info("Use `python run.py set-keys` to list available keys.")
            sys.exit(2)
        value = parse_value(argv[2])
        set_config_value(config_path, argv[1], value)
        logger.info("Updated %s in config.yaml", argv[1])
        return

    if argv[0] in ("set-keys", "keys") and len(argv) == 1:
        config_path = Path(__file__).resolve().parent / "config.yaml"
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for key in collect_keys(data):
            logger.info(key)
        return

    if argv[0] == "filter" and len(argv) == 1:
        run_main(
            [
                "--max-pages",
                "2",
                "--filter-pbanc-knd-cd",
                "공440002",
                "--filter-pbanc-stts-cd",
                "공400001",
                "--filter-bid-pgst-cd",
                "입160003",
            ]
        )
        return

    usage(logger)
    sys.exit(1)


if __name__ == "__main__":
    main()
