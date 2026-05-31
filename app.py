from __future__ import annotations

import argparse
import ipaddress
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from Diagramador import APP_NAME, OWNER_TEXT, DiagramadorError, SAMPLE_XML, build_diagram_payload, load_pfsense_config


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_TRUSTED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
DEFAULT_MAX_UPLOAD_MB = 64
UPLOAD_LIMIT_MB = int(os.environ.get("PFSCHEMATIC_MAX_UPLOAD_MB", str(DEFAULT_MAX_UPLOAD_MB)))
FORM_MEMORY_LIMIT_MB = int(os.environ.get("PFSCHEMATIC_MAX_FORM_MB", str(UPLOAD_LIMIT_MB)))
ALLOWED_LIB_FILES = {
    "vis-9.1.2/vis-network.css",
    "vis-9.1.2/vis-network.min.js",
}
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_LIMIT_MB * 1024 * 1024
app.config["MAX_FORM_MEMORY_SIZE"] = FORM_MEMORY_LIMIT_MB * 1024 * 1024
app.config["MAX_FORM_PARTS"] = 8
app.config["TRUSTED_HOSTS"] = DEFAULT_TRUSTED_HOSTS


def _payload_from_path(path: Path):
    config = load_pfsense_config(path)
    return build_diagram_payload(config)


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


def _json_error(message: str, status_code: int):
    return jsonify({"error": message, "status": status_code}), status_code


@app.get("/")
def index():
    return render_template("index.html", app_name=APP_NAME, owner_text=OWNER_TEXT)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "app": APP_NAME, "owner": OWNER_TEXT, "sample": SAMPLE_XML.name})


@app.get("/favicon.ico")
def favicon():
    return "", 204


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(exc):
    if _is_api_request():
        upload_limit_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        form_limit_mb = app.config["MAX_FORM_MEMORY_SIZE"] // (1024 * 1024)
        return _json_error(
            "El XML supera los limites configurados "
            f"(subida {upload_limit_mb} MB, formulario {form_limit_mb} MB). "
            "Ajuste PFSCHEMATIC_MAX_UPLOAD_MB y PFSCHEMATIC_MAX_FORM_MB si necesita procesar respaldos mas grandes.",
            413,
        )
    return exc


@app.errorhandler(HTTPException)
def handle_http_exception(exc):
    if _is_api_request():
        message = exc.description or exc.name or "Solicitud no valida."
        return _json_error(message, exc.code or 500)
    return exc


@app.errorhandler(Exception)
def handle_unexpected_exception(exc):
    if _is_api_request():
        app.logger.exception("Error inesperado procesando una solicitud de API")
        return _json_error("No se pudo procesar el XML. Revise que sea un backup/export XML valido de pfSense.", 500)
    raise exc


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/sample")
def sample():
    try:
        return jsonify(_payload_from_path(SAMPLE_XML))
    except DiagramadorError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/upload")
def upload():
    upload_file = request.files.get("xml")
    if upload_file is None or not upload_file.filename:
        return jsonify({"error": "Seleccione un archivo XML."}), 400
    if not upload_file.filename.lower().endswith(".xml"):
        return jsonify({"error": "El archivo debe tener extension .xml."}), 400

    try:
        config = load_pfsense_config(upload_file.stream, display_name=upload_file.filename)
        return jsonify(build_diagram_payload(config))
    except DiagramadorError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/lib/<path:filename>")
def local_lib(filename):
    normalized = filename.replace("\\", "/")
    if normalized not in ALLOWED_LIB_FILES:
        return jsonify({"error": "Recurso no permitido."}), 404
    return send_from_directory(ROOT_DIR / "lib", filename)


def create_app():
    return app


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _is_loopback_bind(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_wildcard_bind(host: str) -> bool:
    return host in {"0.0.0.0", "::", ""}


def _trusted_hosts_from_env() -> list[str]:
    raw = os.environ.get("PFSCHEMATIC_TRUSTED_HOSTS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Servidor local de PfSchematic.")
    parser.add_argument("--host", default=os.environ.get("PFSCHEMATIC_HOST", os.environ.get("DIAGRAMADOR_HOST", "127.0.0.1")))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PFSCHEMATIC_PORT", os.environ.get("DIAGRAMADOR_PORT", "8765"))))
    parser.add_argument("--threads", type=int, default=int(os.environ.get("PFSCHEMATIC_THREADS", os.environ.get("DIAGRAMADOR_THREADS", "4"))))
    parser.add_argument("--allow-remote", action="store_true", default=_bool_env("PFSCHEMATIC_ALLOW_REMOTE"), help="Permite enlazar el servicio fuera de loopback.")
    parser.add_argument("--trusted-host", action="append", default=[], help="Host/IP permitido en la cabecera Host. Requerido con --host 0.0.0.0.")
    parser.add_argument("--dev", action="store_true", help="Usa el servidor de desarrollo de Flask.")
    args = parser.parse_args()

    if not _is_loopback_bind(args.host) and not args.allow_remote:
        raise SystemExit(
            "Por seguridad PfSchematic solo inicia en 127.0.0.1 por defecto. "
            "Use --allow-remote y --trusted-host si realmente necesita exponerlo en la red."
        )

    trusted_hosts = list(dict.fromkeys(DEFAULT_TRUSTED_HOSTS + _trusted_hosts_from_env() + args.trusted_host))
    if args.allow_remote and not _is_wildcard_bind(args.host):
        trusted_hosts.append(args.host)
    if args.allow_remote and _is_wildcard_bind(args.host) and not (args.trusted_host or _trusted_hosts_from_env()):
        raise SystemExit("Use --trusted-host con el nombre o IP por el que accedera al servicio remoto.")
    app.config["TRUSTED_HOSTS"] = list(dict.fromkeys(trusted_hosts))

    if args.dev:
        app.run(host=args.host, port=args.port, debug=False)
        return

    from waitress import serve

    shown_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"{APP_NAME} disponible en http://{shown_host}:{args.port}")
    serve(app, host=args.host, port=args.port, threads=args.threads, clear_untrusted_proxy_headers=True)


if __name__ == "__main__":
    main()
