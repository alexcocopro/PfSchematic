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
python app.py --host 0.0.0.0 --port 8765
```

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
python Diagramador.py muestra/demo-pfschematic.xml -o pfsense_diagram.html
```

Ver solo resumen:

```bash
python Diagramador.py muestra/demo-pfschematic.xml --summary
```

## Muestra Incluida

La app carga por defecto:

```text
muestra/demo-pfschematic.xml
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
muestra/filter-demo-pfschematic.xml
```

Ese archivo tiene raiz `filter` y 2 reglas directas.

## Estructura

```text
app.py                    Servidor local WSGI/Flask.
Diagramador.py            Parser, estadisticas y generador HTML.
instalar.py               Instalador Windows/Linux.
requirements.txt          Dependencias de ejecucion.
requirements-dev.txt      Dependencias opcionales de verificacion visual.
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

Los XML reales ubicados en `muestra/` quedan ignorados por Git. Solo se versionan los demos sanitizados `demo-pfschematic.xml` y `filter-demo-pfschematic.xml`.

## Propiedad

PfSchematic es propiedad de Alex Cabello Leiva, consultor de innovacion y ciberseguridad. Todo uso, distribucion o modificacion debe respetar la autorizacion del propietario.
