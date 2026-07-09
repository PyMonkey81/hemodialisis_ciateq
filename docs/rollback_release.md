# Rollback y Release (Windows + Linux)

## Feature flags de plataforma

Archivo: `config/platform_features.json`

- `enable_linux_platform_layer`
- `enable_windows_legacy_prescale`
- `sanitize_linux_com_ports`

## Rollback rápido recomendado

1. Mantener binario Windows previo como artefacto estable.
2. Si hay regresión en Linux, desactivar flags nuevas (sin tocar lógica clínica):

```json
{
  "enable_linux_platform_layer": false,
  "enable_windows_legacy_prescale": true,
  "sanitize_linux_com_ports": false
}
```

3. Rehacer build y validar arranque/cierre.

## Checklist de release candidate

1. Smoke test de arranque/cierre exitoso en Windows y Linux.
2. Detección serial en 3 canales sin cambios de protocolo.
3. Build Windows (`build_exe.bat`) y Linux (`compile_linux.sh`) exitosos.
4. Registro en `build/build_history.csv` actualizado.
5. Confirmar que rutas legacy de Windows siguen activas.
