# Arquitectura

PfSchematic esta dividido en parser, servidor local e interfaz web.

## Componentes

```text
Diagramador.py          Parser XML, estadisticas y payload del diagrama.
app.py                  Servidor local Flask/Waitress.
templates/index.html    Estructura de la interfaz.
static/app.js           Filtros, render de red, exportaciones y panel de alias.
static/styles.css       Diseno responsive.
lib/vis-9.1.2/          Libreria local para el grafo interactivo.
samples/                Demos sanitizados versionados.
private/                Respaldos reales locales ignorados por Git.
exports/                Salidas HTML/PNG/PDF y capturas ignoradas por Git.
runtime/                Logs y archivos temporales ignorados por Git.
tests/                  Pruebas de parser, payload y seguridad.
```

## Flujo de datos

1. El usuario carga un XML o usa el demo.
2. `app.py` recibe el archivo y aplica limites de formulario.
3. `Diagramador.py` parsea XML con `defusedxml`.
4. Se extraen interfaces, alias y reglas.
5. Se construye un payload JSON con reglas, nodos y aristas.
6. `static/app.js` filtra y renderiza el grafo con vis-network.
7. El usuario puede exportar JSON, PNG o PDF.

## Modelo de nodos y aristas

Los nodos contienen:

- `id`;
- `label`;
- `group`;
- `title`;
- `ruleNumbers`;
- `firstRule`;
- `lastRule`;
- metadatos de alias cuando aplica.

Las aristas contienen:

- `ruleId`;
- `ruleNumber`;
- origen y destino;
- accion;
- protocolo;
- puerto;
- estado;
- color y estilo visual.

## Alias

Los alias incluyen:

- nombre;
- tipo;
- descripcion;
- objetos internos;
- detalle por objeto;
- conteo.

Esto permite explorar puertos, IPs, redes y dominios sin volver al XML.

## Exportaciones

La exportacion PNG/PDF captura el canvas actual y lo compone en un lienzo nuevo con:

- encabezado de marca;
- diagrama visible;
- resumen de filtros;
- leyenda de colores;
- explicacion del numero de regla.
