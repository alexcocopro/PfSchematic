# Operacion segura

PfSchematic esta pensado para ejecutarse localmente mientras se revisan backups o exports de pfSense. Un backup real puede contener informacion sensible.

## Recomendacion principal

Use siempre loopback salvo que tenga una razon concreta para exponer el servicio:

```bash
python app.py --host 127.0.0.1 --port 8765
```

No publique el puerto en Internet ni haga port-forward desde el router.

## Exposicion en LAN

Para compartir temporalmente en una red local:

```bash
python app.py --host 0.0.0.0 --port 8765 --allow-remote --trusted-host 192.168.1.50
```

Cambie `192.168.1.50` por la IP o DNS usado para acceder al servicio. Sin `--allow-remote` y `--trusted-host`, PfSchematic rechaza el arranque remoto.

## Datos sensibles

No suba backups reales de pfSense a repositorios publicos. Pueden contener:

- usuarios;
- hashes;
- certificados;
- claves privadas;
- gateways;
- VPN;
- reglas internas;
- dominios e IPs sensibles.

El `.gitignore` ignora `private/`, `exports/` y `runtime/`. Coloque los backups reales en `private/pfsense-backups/` y use `samples/` solo para XML demo sanitizados.

## Medidas implementadas

- XML local con `defusedxml`.
- Limite de carga por defecto: 64 MB.
- Validacion de cabecera `Host`.
- Cabeceras de seguridad HTTP.
- Cache deshabilitada para `/api/*`.
- Sin JavaScript externo/CDN.
- Librerias locales servidas por lista permitida.
- Waitress con limpieza de headers proxy no confiables.

## Variables utiles

```text
PFSCHEMATIC_HOST=127.0.0.1
PFSCHEMATIC_PORT=8765
PFSCHEMATIC_THREADS=4
PFSCHEMATIC_MAX_UPLOAD_MB=64
PFSCHEMATIC_MAX_FORM_MB=64
PFSCHEMATIC_ALLOW_REMOTE=false
PFSCHEMATIC_TRUSTED_HOSTS=localhost,127.0.0.1
```

## Firewall local

Si se usa en Windows, mantenga el perfil de red como privado/confiable solo si conoce esa red. Para uso local no necesita abrir reglas entrantes.

## Auditoria

GitHub Actions ejecuta pruebas en cada `push`. Dependabot revisa dependencias Python y GitHub Actions semanalmente.
