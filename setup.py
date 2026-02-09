from __future__ import annotations

import logging
import platform
import subprocess
import sys
from pathlib import Path


def detect_os() -> str:
    system = platform.system().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    if system.startswith("linux"):
        return "linux"
    return "unknown"


def venv_python_path(venv_dir: Path, os_name: str) -> Path:
    if os_name == "windows":
        return venv_dir / "Scripts" / "python"
    return venv_dir / "bin" / "python"


def venv_pip_path(venv_dir: Path, os_name: str) -> Path:
    if os_name == "windows":
        return venv_dir / "Scripts" / "pip"
    return venv_dir / "bin" / "pip"


def run_cmd(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("setup")

    project_root = Path(__file__).resolve().parent
    venv_dir = project_root / "venv"
    os_name = detect_os()

    if os_name == "unknown":
        logger.error("Unsupported OS. Please run setup manually.")
        sys.exit(1)

    logger.info("[1/3] Creating venv")
    if not venv_dir.exists():
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
    else:
        logger.info("venv already exists: %s", venv_dir)

    python_path = venv_python_path(venv_dir, os_name)
    pip_path = venv_pip_path(venv_dir, os_name)

    logger.info("[2/3] Installing dependencies")
    run_cmd([str(pip_path), "install", "-r", "requirements.txt"])

    logger.info("[3/3] Installing Playwright browsers")
    if os_name == "linux":
        run_cmd([str(python_path), "-m", "playwright", "install", "--with-deps"])
    else:
        run_cmd([str(python_path), "-m", "playwright", "install"])

    logger.info("Setup completed")


if __name__ == "__main__":
    main()
