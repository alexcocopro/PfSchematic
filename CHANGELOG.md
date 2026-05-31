# Cambios

## 0.1.1 - Endurecimiento y documentacion

- Se eliminaron scripts externos/CDN de la interfaz.
- Se agregaron cabeceras de seguridad HTTP.
- Se agrego validacion de `Host`.
- Se bloqueo la exposicion remota accidental.
- Se limito la ruta `/lib` con lista permitida.
- Se corrigio la carga de XML grandes manteniendo el limite de formulario alineado con el limite de subida.
- Se reinician los filtros al cargar un nuevo XML para evitar diagramas vacios por filtros anteriores.
- Se agregaron pruebas de seguridad.
- Se agrego Dependabot.
- Se amplio la documentacion operativa, tecnica y de publicacion.

## 0.1.0 - Primera version publica

- Parser seguro de exports XML de pfSense.
- Diagrama interactivo con filtros.
- Exploracion de alias.
- Exportacion JSON, PNG y PDF.
- Instalador multiplataforma.
- CI inicial en GitHub Actions.
