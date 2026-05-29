from __future__ import annotations

import argparse
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from Diagramador import APP_NAME, OWNER_TEXT, DiagramadorError, SAMPLE_XML, build_diagram_payload, load_pfsense_config


ROOT_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024


def _payload_from_path(path: Path):
    config = load_pfsense_config(path)
    return build_diagram_payload(config)


@app.get("/")
def index():
    return render_template("index.html", app_name=APP_NAME, owner_text=OWNER_TEXT)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "app": APP_NAME, "owner": OWNER_TEXT, "sample": SAMPLE_XML.name})


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
    return send_from_directory(ROOT_DIR / "lib", filename)


def create_app():
    return app


def main():
    parser = argparse.ArgumentParser(description="Servidor local de PfSchematic.")
    parser.add_argument("--host", default=os.environ.get("DIAGRAMADOR_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DIAGRAMADOR_PORT", "8765")))
    parser.add_argument("--threads", type=int, default=int(os.environ.get("DIAGRAMADOR_THREADS", "8")))
    parser.add_argument("--dev", action="store_true", help="Usa el servidor de desarrollo de Flask.")
    args = parser.parse_args()

    if args.dev:
        app.run(host=args.host, port=args.port, debug=False)
        return

    from waitress import serve

    shown_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"{APP_NAME} disponible en http://{shown_host}:{args.port}")
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == "__main__":
    main()
