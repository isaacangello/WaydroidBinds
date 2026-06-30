# Waydroid Shared Folders - Checkpoint

## Status Atual (2026-06-30)

### ✅ Binds Ativos

| Host | Android | Status |
|---|---|---|
| `~/Downloads` | `/sdcard/Download` | ✅ |
| `~/Documentos` | `/sdcard/Documents` | ✅ |
| `~/Imagens` | `/sdcard/Pictures` | ✅ |
| `~/videos` | `/sdcard/Movies` | ✅ |
| `~/Waydroid/WhatsApp` | `/sdcard/Android/media/com.whatsapp/WhatsApp/Media` | ✅ |

### ✅ Persistência
- Adicionado ao `/usr/bin/waydroid-startup-scripts`
- Binds restaurados automaticamente no startup do container

### ✅ Verificação
- Conteúdo visível dentro do Android via `waydroid shell ls`
- Mídias existentes do WhatsApp copiadas (15.570+ imagens)
- 14 subdiretórios de mídia do WhatsApp funcionando

### ⚠️ Corrigido (v1.1.0)
- Diretórios `~/Imagens` e `~/Documentos` tinham permissão 755
- Android Apps não conseguiam escrever (erro ao salvar foto)
- Agora o script aplica `chmod 777` antes de cada bind

### 📁 Estrutura
```
~/WaydroidBinds/
├── setup-waydroid-binds.sh
├── revert-waydroid-binds.sh
├── copy-existing-media.sh
├── README.md
├── CHANGELOG.md
└── checkpoint.md
```

### Método
`sudo mount --bind <source> ~/.local/share/waydroid/data/media/0/<target>`
