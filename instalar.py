#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
REQUIREMENTS = ROOT_DIR / "requirements.txt"
VENV_DIR = ROOT_DIR / ".venv"
PYTHON_MIN = (3, 10)


def _run(command: list[str], cwd: Path = ROOT_DIR) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.check_call(command, cwd=cwd)


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _ensure_supported_python() -> None:
    if sys.version_info < PYTHON_MIN:
        version = ".".join(str(part) for part in PYTHON_MIN)
        raise SystemExit(f"Se requiere Python {version} o superior.")


def _create_venv(venv_dir: Path) -> Path:
    python_path = _venv_python(venv_dir)
    if not python_path.exists():
        _run([sys.executable, "-m", "venv", str(venv_dir)])
    return python_path


def _install_requirements(python_path: Path) -> None:
    if not REQUIREMENTS.exists():
        raise SystemExit("No se encontro requirements.txt.")
    _run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def _write_launchers(python_path: Path) -> None:
    windows_launcher = ROOT_DIR / "iniciar_pfschematic.bat"
    linux_launcher = ROOT_DIR / "iniciar_pfschematic.sh"
    app_path = ROOT_DIR / "app.py"

    windows_launcher.write_text(
        f'@echo off\r\n"{python_path}" "{app_path}" %*\r\n',
        encoding="utf-8",
    )
    linux_launcher.write_text(
        f'#!/usr/bin/env sh\nexec "{python_path}" "{app_path}" "$@"\n',
        encoding="utf-8",
        newline="\n",
    )
    try:
        linux_launcher.chmod(0o755)
    except OSError:
        pass


def _run_tests(python_path: Path) -> None:
    _run([str(python_path), "-m", "unittest", "discover", "-s", "tests"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Instala PfSchematic en Windows o Linux.")
    parser.add_argument("--no-venv", action="store_true", help="Instala dependencias en el Python actual.")
    parser.add_argument("--skip-tests", action="store_true", help="No ejecuta pruebas al terminar.")
    parser.add_argument("--start", action="store_true", help="Inicia la aplicacion al finalizar.")
    parser.add_argument("--host", default="127.0.0.1", help="Host usado si se inicia la aplicacion.")
    parser.add_argument("--port", default="8765", help="Puerto usado si se inicia la aplicacion.")
    args = parser.parse_args()

    _ensure_supported_python()
    print(f"Sistema: {platform.system()} {platform.release()}", flush=True)

    python_path = Path(sys.executable) if args.no_venv else _create_venv(VENV_DIR)
    _install_requirements(python_path)
    _write_launchers(python_path)

    if not args.skip_tests:
        _run_tests(python_path)

    print("")
    print("Instalacion lista.")
    print(f"Ejecute: {python_path} {ROOT_DIR / 'app.py'}")
    print(f"URL local: http://{args.host}:{args.port}")
    print("Tambien puede usar iniciar_pfschematic.bat o iniciar_pfschematic.sh.")

    if args.start:
        subprocess.check_call([str(python_path), str(ROOT_DIR / "app.py"), "--host", args.host, "--port", args.port])


if __name__ == "__main__":
    main()
