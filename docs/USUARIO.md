# Guia de usuario

PfSchematic convierte exports XML de pfSense en un diagrama interactivo para revisar reglas, flujos, alias, puertos e interfaces.

## Inicio rapido

```bash
python instalar.py
python app.py
```

Abra:

```text
http://127.0.0.1:8765
```

## Carga de XML

- `Demo`: carga `muestra/demo-pfschematic.xml`, un XML sanitizado incluido para pruebas.
- `XML`: permite subir un export propio de pfSense.

El XML se procesa localmente. No se envia a servicios externos.

## Filtros

La pantalla permite filtrar por:

- texto libre: IP, alias, puerto, descripcion o miembros internos de alias;
- accion: `Pass`, `Block`, `Reject`, `Otro`;
- interfaz;
- protocolo.

Los contadores y la tabla de reglas se actualizan con cada filtro.

## Diagrama

Cada nodo representa un origen, destino, alias, interfaz o red. Cada arista representa una regla visible.

La etiqueta de arista usa este formato:

```text
#12 TCP:443
```

`#12` es el numero de regla segun el orden original del XML de pfSense.

## Exploracion de alias

Al seleccionar un nodo de tipo Alias, el panel derecho muestra:

- tipo de alias;
- cantidad de objetos;
- descripcion;
- IPs, redes, dominios o puertos internos;
- detalle asociado a cada objeto.

El buscador dentro del panel filtra solo los objetos del alias seleccionado.

## Exportacion

PfSchematic exporta:

- `JSON`: payload procesado con reglas, nodos, aristas, alias y estadisticas;
- `PNG`: imagen del diagrama visible con leyenda de filtros;
- `PDF`: vista imprimible del diagrama visible con la misma leyenda.

La leyenda incluye reglas visibles, ocultas por filtro, acciones incluidas/excluidas, interfaz, protocolo, busqueda y rango de reglas.

## CLI

Resumen:

```bash
python Diagramador.py muestra/demo-pfschematic.xml --summary
```

HTML estatico:

```bash
python Diagramador.py muestra/demo-pfschematic.xml -o pfsense_diagram.html
```
