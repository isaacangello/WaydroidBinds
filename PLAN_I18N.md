# Plano de Internacionalização (i18n) — Waydroid Binds

**Objetivo:** Implementar suporte a traduções com:
- Português (pt_BR) → traduz para Português
- Qualquer outro idioma → traduz para Inglês (fallback)
- AUR description sempre em Inglês

---

## 1. Análise de Strings a Traduzir

### GUI (main_window.py) - ~60 strings
| Categoria | Strings |
|-----------|---------|
| Window/Tab titles | "Waydroid Binds", "Pastas compartilhadas", "Rede / Firewall", "Mídia do WhatsApp" |
| Group boxes | "Pastas compartilhadas (Host → Android)", "Rede / Firewall do Waydroid", "Mídia do WhatsApp" |
| Botões | "Aplicar selecionados", "Reverter todos", "Atualizar", "Aplicar / Reparar", "Diagnóstico", "Reverter", "Copiar mídias existentes" |
| Labels firewall | "IP forwarding", "Firewall ativo", "Rede do container", "Interface de internet", "Política FORWARD", "Zona (firewalld)", "Container", "Conectividade (ping)" |
| Status | "MONTADO"/"não montado", "ON"/"OFF", "OK"/"FAIL", "ACCEPT", "trusted", "active" |
| Notas/tooltips | 5 textos explicativos |
| QMessageBox | 5 diálogos de confirmação |
| Log messages | "MODO DRY-RUN...", "[OK] tarefa concluída", "[ERRO] falha (código {code})" |

### Recursos Desktop/Metainfo
| Arquivo | Status |
|---------|--------|
| `.desktop` | ✅ Já tem `Name[pt_BR]` e `Comment[pt_BR]` |
| `.metainfo.xml` | ✅ Já tem `xml:lang="en"` para summary e description |

### Scripts Shell
| Arquivo | Strings |
|---------|---------|
| `setup-waydroid-binds.sh` | ~15 mensagens echo |
| `revert-waydroid-binds.sh` | ~5 mensagens |
| `copy-existing-media.sh` | ~8 mensagens |
| `setup-waydroid-firewall.sh` | ~30 mensagens |

---

## 2. Estratégia de Implementação

### 2.1 Framework: Qt Linguist (QTranslator + .ts/.qm)
- Nativo do PySide6/Qt
- Suporte a pluralização, contexto, comentários
- Ferramentas: `pyside6-lupdate`, `pyside6-lrelease`, Qt Linguist GUI

### 2.2 Estrutura de Arquivos
```
gui/
├── translations/
│   ├── waydroid-binds_pt.ts    # Português (fonte)
│   ├── waydroid-binds_en.ts    # Inglês (fallback)
│   └── waydroid-binds_pt.qm    # Compilado (runtime)
├── resources/
│   └── translations.qrc        # Resource file para embutir .qm
```

### 2.3 Regras de Idioma
```python
def get_translation_language() -> str:
    locale = QLocale.system().name()  # ex: "pt_BR", "en_US", "es_ES"
    if locale.startswith("pt"):
        return "pt"
    return "en"  # fallback para qualquer outro
```

### 2.4 AUR Description (PKGBUILD)
- `pkgdesc` em **Inglês** (requisito do AUR)
- Manter apenas: `pkgdesc="GUI and scripts for Waydroid shared folders and firewall"`

---

## 3. Passos de Implementação

### Fase 1: Preparação do Código Python (GUI)
1. **Envolver strings em `self.tr()` ou `QCoreApplication.translate()`**
   - Window title, tabs, group boxes, botões, labels, tooltips, QMessageBox, log messages
   - Usar contexto onde necessário: `self.tr("Aplicar", "button")`

2. **Criar `TranslationsManager` class**
   ```python
   class TranslationsManager:
       def __init__(self, app: QApplication):
           self.translator = QTranslator()
           self.load_translations(app)
       
       def load_translations(self, app: QApplication):
           lang = self.get_translation_language()
           qm_file = f":/translations/waydroid-binds_{lang}.qm"
           if self.translator.load(qm_file):
               app.installTranslator(self.translator)
   ```

3. **Atualizar `main.py` para inicializar traduções antes de criar MainWindow**

### Fase 2: Arquivos de Tradução
1. **Extrair strings:** `pyside6-lupdate gui/main_window.py gui/main.py -ts gui/translations/waydroid-binds_pt.ts`
2. **Criar fallback inglês:** Copiar `.ts` para `_en.ts` e traduzir para inglês
3. **Compilar:** `pyside6-lrelease gui/translations/*.ts`
4. **Criar `.qrc`** para embutir `.qm` no binário

### Fase 3: Recursos Desktop/Metainfo
- `.desktop`: Já OK (tem pt_BR e padrão)
- `.metainfo.xml`: Já OK (tem xml:lang="en")

### Fase 4: AUR (PKGBUILD)
- Alterar `pkgdesc` para inglês
- Manter descrição longa apenas em inglês

### Fase 4: Scripts Shell (Opcional/Simplificado)
- Usar `gettext` bash ou manter em inglês (CLI)
- Recomendação: Manter scripts em inglês (padrão CLI), apenas GUI traduzida

---

## 4. Arquivos a Criar/Modificar

### Novos Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `gui/translations/waydroid-binds_pt.ts` | Tradução português (fonte) |
| `gui/translations/waydroid-binds_en.ts` | Tradução inglês (fallback) |
| `gui/translations/translations.qrc` | Resource file |
| `gui/translations_manager.py` | Classe gerenciadora |

### Arquivos Modificados
| Arquivo | Mudanças |
|---------|----------|
| `gui/main.py` | Inicializar TranslationsManager |
| `gui/main_window.py` | Envolver strings em `tr()` |
| `gui/translations/waydroid-binds_pt.ts` | Gerado via lupdate |
| `gui/translations/waydroid-binds_en.ts` | Cópia traduzida para inglês |
| `packaging/arch/PKGBUILD` | `pkgdesc` em inglês |
| `gui/resources/translations.qrc` | Adicionar ao build |

---

## 5. Build System (GitHub Actions)
Adicionar no CI:
```yaml
- name: Atualizar traduções
  run: |
    pyside6-lupdate gui/main_window.py gui/main.py -ts gui/translations/waydroid-binds_pt.ts
    pyside6-lrelease gui/translations/*.ts
```

---

## 6. Perguntas para Decisão

1. **Scripts shell:** Traduzir mensagens de CLI ou manter em inglês?
   - Minha recomendação: Manter em inglês (padrão Unix/Linux)

2. **Ferramenta de tradução:** Usar Qt Linguist GUI ou editar `.ts` manualmente?
   - Qt Linguist é mais amigável para não-devs

3. **Contextos:** Usar contextos (ex: `tr("Aplicar", "button")`) para evitar ambiguidade?

4. **Teste:** Como validar? Rodar com `LANG=pt_BR` e `LANG=en_US`?

---

## 7. Cronograma Estimado
| Fase | Esforço |
|------|---------|
| Fase 1: Refatorar GUI para tr() | 2-3h |
| Fase 2: Gerar .ts, criar .en.ts, compilar .qm | 1-2h |
| Fase 3: Ajustar PKGBUILD e recursos | 30min |
| Fase 4: Testes (pt_BR, en_US, es_ES) | 1h |
| **Total** | **~5-6h** |

---

## 8. Exemplo de Uso do tr()

```python
# Antes
self.btn_bind_apply = QPushButton("Aplicar selecionados")

# Depois
self.btn_bind_apply = QPushButton(self.tr("Aplicar selecionados", "button"))

# Com contexto para desambiguar
label.setText(self.tr("ON", "status"))  # vs tr("ON", "switch")
```

---

**Próximo passo:** Aguardar confirmação para iniciar Fase 1.
