# PfSchematic

PfSchematic es una herramienta local para convertir exports XML de pfSense en un diagrama interactivo, visual y filtrable. Permite revisar reglas de firewall, interfaces, alias, puertos, protocolos y flujos sin navegar manualmente por el XML.

Propiedad de Alex Cabello Leiva, consultor de innovacion y ciberseguridad.

Repositorio sugerido: [alexcocopro/PfSchematic](https://github.com/alexcocopro/PfSchematic)

## Funciones

- Carga de backups XML completos de pfSense.
- Soporte para exports parciales con raiz `filter`.
- Diagrama interactivo con zoom, arrastre, busqueda y filtros.
- Filtros por accion, interfaz, protocolo y texto libre.
- Tabla lateral de reglas visibles.
- Exploracion de nodos Alias para ver IPs, redes, dominios, puertos y detalles internos.
- Exportacion del diagrama filtrado a PNG con leyenda de filtros.
- Exportacion a PDF mediante una vista imprimible con la misma leyenda.
- Exportacion del payload procesado a JSON.
- Parser XML seguro con `defusedxml`.
- Servidor local WSGI con Waitress.
- Instalador multiplataforma para Windows y Linux.

## Documentacion

- [Guia de usuario](docs/USUARIO.md)
- [Operacion segura](docs/OPERACION_SEGURA.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Estructura de directorios](docs/ESTRUCTURA_DIRECTORIOS.md)
- [Desarrollo y pruebas](docs/DESARROLLO.md)
- [Publicacion en GitHub](docs/PUBLICACION_GITHUB.md)
- [Politica de seguridad](SECURITY.md)
- [Cambios](CHANGELOG.md)

## Instalacion Rapida

```bash
python instalar.py
```

El instalador crea `.venv`, instala dependencias, genera lanzadores y ejecuta las pruebas.

Para instalar en el Python actual:

```bash
python instalar.py --no-venv
```

Para instalar e iniciar al finalizar:

```bash
python instalar.py --start
```

## Ejecutar

Windows:

```powershell
iniciar_pfschematic.bat
```

Linux:

```bash
./iniciar_pfschematic.sh
```

Tambien puede ejecutarse directamente:

```bash
python app.py
```

Abra la aplicacion en:

```text
http://127.0.0.1:8765
```

Para cambiar el puerto:

```bash
python app.py --port 9000
```

Para exponerlo en la red local:

```bash
python app.py --host 0.0.0.0 --port 8765 --allow-remote --trusted-host 192.168.1.50
```

Reemplace `192.168.1.50` por la IP o nombre DNS desde donde abrira la herramienta. PfSchematic no permite enlazarse a `0.0.0.0` sin esa confirmacion explicita.

## Uso

1. Abra PfSchematic en el navegador.
2. Use `Demo` para cargar el XML sanitizado incluido.
3. Use `Subir XML` para analizar un backup/export propio de pfSense.
4. Aplique filtros por texto, accion, interfaz o protocolo.
5. Seleccione un nodo de tipo Alias para explorar sus objetos internos.
6. Use los botones de exportacion para guardar JSON, PNG o PDF.

## Orden de reglas

Las aristas del diagrama muestran el numero de regla con el formato `#n` antes del protocolo y puerto. Ese numero respeta el orden original en el XML exportado desde pfSense. Los nodos tambien guardan en el tooltip la primera regla, ultima regla y una lista resumida de reglas asociadas.

## Exportacion PNG/PDF

El PNG se descarga directamente con el diagrama visible y una leyenda que resume:

- reglas visibles y ocultas por filtros;
- acciones incluidas y acciones filtradas fuera;
- interfaz, protocolo y busqueda aplicados;
- rango visible de reglas segun el orden de pfSense;
- colores de acciones y nota sobre el significado de `#n`.

El PDF abre una vista imprimible del mismo contenido. Desde el dialogo del navegador seleccione `Guardar como PDF`.

## Uso CLI

Generar un HTML estatico:

```bash
python Diagramador.py samples/demo-pfschematic.xml -o exports/html/pfsense_diagram.html
```

Ver solo resumen:

```bash
python Diagramador.py samples/demo-pfschematic.xml --summary
```

## Muestra Incluida

La app carga por defecto:

```text
samples/demo-pfschematic.xml
```

Resultado esperado con la muestra completa:

```text
5 reglas de firewall
2 reglas pass
1 regla reject
1 regla block
1 regla sin tipo explicito
4 alias
3 interfaces definidas
```

Tambien se incluye un export parcial:

```text
samples/filter-demo-pfschematic.xml
```

Ese archivo tiene raiz `filter` y 2 reglas directas.

## Estructura

```text
app.py                    Servidor local WSGI/Flask.
Diagramador.py            Parser, estadisticas y generador HTML.
instalar.py               Instalador Windows/Linux.
requirements.txt          Dependencias de ejecucion.
requirements-dev.txt      Dependencias opcionales de verificacion visual.
samples/                  XML demo sanitizados versionados.
private/                  Respaldos reales locales ignorados por Git.
exports/                  PNG/PDF/HTML/capturas generadas ignoradas por Git.
runtime/                  Logs y archivos temporales ignorados por Git.
templates/index.html      Interfaz web.
static/styles.css         Estilos responsive.
static/app.js             Filtros, diagrama, alias y exportacion.
tests/test_diagramador.py Pruebas de parser y payload.
```

## Verificacion

```bash
python -m unittest discover -s tests
```

Verificacion de sintaxis:

```bash
python -m py_compile Diagramador.py app.py instalar.py
```

## Seguridad

PfSchematic procesa los XML localmente. El servidor se inicia en `127.0.0.1` por defecto y el parser usa `defusedxml` para reducir riesgos de XXE y ataques XML comunes.

Un backup completo de pfSense puede contener hashes, certificados, usuarios, configuraciones sensibles y secretos. No publique ni comparta XML reales sin sanitizarlos.

Los XML reales deben ubicarse en `private/pfsense-backups/`, carpeta ignorada por Git. Solo se versionan los demos sanitizados en `samples/`.

Medidas activas de endurecimiento:

- enlace local por defecto, sin exposicion remota accidental;
- `--allow-remote` y `--trusted-host` requeridos para publicar en LAN;
- validacion de cabecera `Host` con `TRUSTED_HOSTS`;
- limite de carga XML de 64 MB por defecto, configurable con `PFSCHEMATIC_MAX_UPLOAD_MB`;
- limite de formulario configurable con `PFSCHEMATIC_MAX_FORM_MB`; si no se define, sigue `PFSCHEMATIC_MAX_UPLOAD_MB`;
- cabeceras `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` y `Permissions-Policy`;
- respuestas `/api/*` con `Cache-Control: no-store`;
- librerias servidas desde `/lib` con lista permitida;
- sin JavaScript externo/CDN en la interfaz.

Para levantarlo en un equipo de trabajo, use preferiblemente:

```bash
python app.py --host 127.0.0.1 --port 8765
```

## Propiedad

PfSchematic es propiedad de Alex Cabello Leiva, consultor de innovacion y ciberseguridad. Todo uso, distribucion o modificacion debe respetar la autorizacion del propietario.
