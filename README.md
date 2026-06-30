# Waydroid Shared Folders

Bind mounts entre o host Linux e o Android (Waydroid) usando o método oficial da documentação.

## Mapeamento

| Host | Android |
|---|---|
| `~/Downloads` | `/sdcard/Download` |
| `~/Documentos` | `/sdcard/Documents` |
| `~/Imagens` | `/sdcard/Pictures` |
| `~/videos` | `/sdcard/Movies` |
| `~/Waydroid/WhatsApp` | `/sdcard/Android/media/com.whatsapp/WhatsApp/Media` |

## Requisitos

- [Waydroid](https://waydro.id/) instalado e funcionando
- `pkexec` ou `sudo` (para mounts como root)

## Uso

```bash
# Ativar binds (pede senha via pkexec)
pkexec ./setup-waydroid-binds.sh

# Reverter binds
pkexec ./revert-waydroid-binds.sh

# Copiar mídias existentes do WhatsApp para a pasta compartilhada
pkexec ./copy-existing-media.sh
```

Os binds são automaticamente restaurados toda vez que o container Waydroid inicia, via hook em `/usr/bin/waydroid-startup-scripts`.

## Scripts

| Script | Função |
|---|---|
| `setup-waydroid-binds.sh` | Aplica todos os bind mounts e adiciona persistência |
| `revert-waydroid-binds.sh` | Desmonta todos os binds e remove persistência |
| `copy-existing-media.sh` | Copia mídias já existentes no WhatsApp para a pasta compartilhada |

## Referência

- [Documentação oficial Waydroid - Shared Folder](https://docs.waydro.id/faq/setting-up-a-shared-folder)
- Comando base: `sudo mount --bind <source> ~/.local/share/waydroid/data/media/0/<target>`
