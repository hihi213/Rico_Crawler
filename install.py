from __future__ import annotations

import logging
import platform
import shutil
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


def run_cmd(args: list[str], logger: logging.Logger) -> None:
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as exc:
        logger.error("명령 실패: %s", " ".join(args))
        if "playwright" in args:
            logger.info("브라우저 설치가 실패했습니다. 네트워크/권한 문제를 확인 후 다시 시도하세요.")
        if detect_os() == "windows":
            logger.info("Windows에서 실행 정책 문제가 있다면 PowerShell에서 실행 정책을 확인하세요.")
        sys.exit(exc.returncode or 1)


def python_available() -> bool:
    return shutil.which("python") is not None or shutil.which("python3") is not None


def print_python_install_guide(os_name: str, logger: logging.Logger) -> None:
    logger.error("Python이 설치되어 있지 않습니다.")
    if os_name == "macos":
        logger.info("macOS 설치 방법:")
        logger.info("  1) Homebrew 설치 후: brew install python@3.11")
        logger.info("  2) 또는 공식 설치 파일: https://www.python.org/downloads/")
        return
    if os_name == "windows":
        logger.info("Windows 설치 방법:")
        logger.info("  1) 공식 설치 파일: https://www.python.org/downloads/windows/")
        logger.info("  2) 설치 시 'Python을 PATH에 추가' 옵션 체크")
        logger.info("  3) 설치 후 새 터미널에서 재시도")
        return
    if os_name == "linux":
        logger.info("Linux 설치 방법(배포판별):")
        logger.info("  - Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv")
        logger.info("  - Fedora: sudo dnf install -y python3 python3-virtualenv")
        logger.info("  - Arch: sudo pacman -S python python-virtualenv")
        return
    logger.info("공식 다운로드: https://www.python.org/downloads/")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("install")

    project_root = Path(__file__).resolve().parent
    venv_dir = project_root / "venv"
    os_name = detect_os()

    if os_name == "unknown":
        logger.error("지원되지 않는 운영체제입니다. 수동 설치를 진행하세요.")
        sys.exit(1)

    if not python_available():
        print_python_install_guide(os_name, logger)
        sys.exit(1)

    logger.info("[1/3] 가상환경 생성")
    if not venv_dir.exists():
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)], logger)
    else:
        logger.info("가상환경이 이미 존재합니다: %s", venv_dir)

    python_path = venv_python_path(venv_dir, os_name)
    pip_path = venv_pip_path(venv_dir, os_name)
    if not python_path.exists() or not pip_path.exists():
        logger.error("가상환경 실행 파일을 찾을 수 없습니다: %s", venv_dir)
        sys.exit(1)

    logger.info("[2/3] 의존성 설치")
    run_cmd([str(pip_path), "install", "-r", "requirements.txt"], logger)

    logger.info("[3/3] Playwright 브라우저 설치")
    if os_name == "linux":
        run_cmd([str(python_path), "-m", "playwright", "install", "--with-deps"], logger)
    else:
        run_cmd([str(python_path), "-m", "playwright", "install"], logger)

    logger.info("설치 완료: %s", venv_dir)


if __name__ == "__main__":
    main()
