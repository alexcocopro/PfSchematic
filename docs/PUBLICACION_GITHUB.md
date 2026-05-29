# Publicacion en GitHub

Repositorio:

```text
https://github.com/alexcocopro/PfSchematic
```

## Primer push

```bash
git init
git branch -M main
git remote add origin https://github.com/alexcocopro/PfSchematic.git
git add .
git commit -m "Primera version de PfSchematic"
git push -u origin main
```

## Cambios posteriores

```bash
git status
git add .
git commit -m "Describe el cambio"
git push
```

## Tags de version

```bash
git tag -a v0.1.0 -m "Primera version publica"
git push origin v0.1.0
```

## Error dubious ownership

Si Git muestra:

```text
detected dubious ownership
```

ejecute:

```bash
git config --global --add safe.directory G:/desarrollo_de_software/firewalls/diagrama_pfsence
```

## Antes de publicar

Revise:

```bash
git status --short --ignored
git ls-files samples
```

Solo deben versionarse:

```text
samples/demo-pfschematic.xml
samples/filter-demo-pfschematic.xml
```

No publique XML reales de pfSense. Deben quedar en `private/pfsense-backups/`, que aparece como ignorado en `git status --short --ignored`.
