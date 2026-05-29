# Estructura de directorios

Esta organizacion separa el codigo versionable de los respaldos reales de pfSense y de las salidas generadas.

```text
PfSchematic/
  app.py                         Servidor local Flask/Waitress.
  Diagramador.py                 Parser, estadisticas y generador HTML.
  instalar.py                    Instalador Windows/Linux.
  requirements.txt               Dependencias de ejecucion.
  requirements-dev.txt           Dependencias opcionales de verificacion visual.
  README.md                      Presentacion del proyecto.
  SECURITY.md                    Politica de seguridad.
  CHANGELOG.md                   Cambios publicados.
  LICENSE                        Licencia del proyecto.

  samples/                       XML demo sanitizados y versionados.
    demo-pfschematic.xml
    filter-demo-pfschematic.xml

  private/                       Datos reales locales. Ignorado por Git.
    pfsense-backups/             Backups/exports reales de pfSense.

  exports/                       Salidas generadas. Ignorado por Git.
    html/                        HTML estatico generado por CLI.
    png/                         Exportaciones PNG.
    pdf/                         Exportaciones PDF.
    evidencias/                  Capturas y pruebas visuales.

  runtime/                       Archivos de ejecucion. Ignorado por Git.
    logs/                        Logs del servidor local.

  static/                        JavaScript y CSS de la interfaz.
  templates/                     Plantillas HTML.
  lib/                           Librerias locales permitidas.
  tests/                         Pruebas automatizadas.
  docs/                          Documentacion tecnica y operativa.
  .github/                       CI y automatizaciones de GitHub.
```

## Que se sube a GitHub

Suba el codigo, la documentacion, las pruebas, las librerias locales necesarias y los XML demo sanitizados de `samples/`.

## Que no se sube

No suba backups reales, capturas con informacion sensible, logs ni salidas generadas. Esos archivos deben vivir en:

- `private/pfsense-backups/`
- `exports/`
- `runtime/`

Estas rutas estan incluidas en `.gitignore`.
