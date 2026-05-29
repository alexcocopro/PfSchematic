# Desarrollo y pruebas

## Requisitos

- Python 3.10 o superior.
- Node.js solo para validar sintaxis de `static/app.js`.

## Instalacion

```bash
python instalar.py
```

Instalacion manual:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

En Linux:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Pruebas

```bash
python -m unittest discover -s tests
python -m py_compile Diagramador.py app.py instalar.py
node --check static/app.js
```

## CI

`.github/workflows/ci.yml` ejecuta en cada `push` y `pull_request` hacia `main`:

- instalacion de dependencias;
- pruebas unitarias;
- compilacion Python;
- validacion JS.

## Dependencias

Dependencias de ejecucion:

```text
defusedxml
Flask
pyvis
waitress
```

Dependabot revisa semanalmente:

- `requirements.txt`;
- GitHub Actions.

## Convenciones

- Mantener XML reales fuera de Git.
- Usar demos sanitizados para pruebas.
- Mantener el servidor en `127.0.0.1` por defecto.
- Agregar pruebas cuando se cambie parser, payload, seguridad o exportaciones.
