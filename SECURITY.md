# Politica de seguridad

## Alcance

Esta politica aplica a PfSchematic y a los archivos incluidos en este repositorio.

## Reporte de vulnerabilidades

Reporte vulnerabilidades directamente al propietario del proyecto:

```text
Alex Cabello Leiva
Consultor de innovacion y ciberseguridad
```

No publique detalles explotables sin coordinacion previa.

## Modelo de uso esperado

PfSchematic debe ejecutarse localmente:

```bash
python app.py --host 127.0.0.1 --port 8765
```

La exposicion remota debe ser temporal, controlada y limitada a redes confiables.

## Datos sensibles

Los backups reales de pfSense no deben subirse al repositorio. El proyecto ignora XML reales en `muestra/` y solo permite demos sanitizados.

## Dependencias

Dependabot esta configurado para revisar dependencias Python y GitHub Actions semanalmente.
