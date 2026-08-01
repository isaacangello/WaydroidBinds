# Flatpak / Flathub

Publicação do pacote Flatpak no Flathub.

- **App ID:** `io.github.isaacangello.waydroidbinds`
- **Runtime:** `org.kde.Platform`/`org.kde.Sdk` 6.8 + BaseApp `io.qt.PySide.BaseApp` 6.8
- **Conta de desenvolvedor no Flathub (ID):** `50752`

## Estrutura de manifests

- `io.github.isaacangello.waydroidbinds.yml` — manifest de **desenvolvimento/CI**:
  fonte local (`type: dir`). Usado no `release.yml` para gerar o bundle `.flatpak`.
- `io.github.isaacangello.waydroidbinds.flathub.yml` — manifest de **submissão**:
  fonte = tarball do GitHub Release (`v1.3.0.tar.gz`) com `sha256` + `x-checker-data`
  (atualização automática de versão pelo flathubbot).

## Build local (valida o manifesto de dev)

```sh
flatpak-builder --user --force-clean --repo=repo build \
  packaging/flatpak/io.github.isaacangello.waydroidbinds.yml \
  --install-deps-from flathub
flatpak build-bundle repo waydroid-binds.flatpak io.github.isaacangello.waydroidbinds
```

## Submeter no Flathub (executar após criar o release v1.3.0)

> **Atenção:** a política do Flathub proíbe PR de submissão gerado/automatizado
> por IA. O PR e os comentários de review devem ser **seus**. Também desative o
> review automático de Copilot para o repositório `flathub` na sua conta.

1. **Release no GitHub:**
   ```sh
   git push origin main
   git tag v1.3.0 && git push origin v1.3.0
   gh release create v1.3.0 --title "Waydroid Binds 1.3.0" --generate-notes
   ```
2. **Preencher o sha256** no `io.github.isaacangello.waydroidbinds.flathub.yml`
   (substituir `REPLACE_ME`):
   ```sh
   curl -L https://github.com/isaacangello/WaydroidBinds/archive/refs/tags/v1.3.0.tar.gz | sha256sum
   ```
3. **Validar** (metainfo/desktop devem passar):
   ```sh
   flatpak-builder-lint manifest io.github.isaacangello.waydroidbinds.flathub.yml
   appstreamcli validate gui/resources/io.github.isaacangello.waydroidbinds.metainfo.xml
   desktop-file-validate gui/resources/io.github.isaacangello.waydroidbinds.desktop
   ```
4. **Fork do flathub** (copiar todas as branches) e branch a partir de `new-pr`:
   ```sh
   gh repo fork flathub/flathub --clone
   cd flathub && git checkout new-pr && git checkout -b io.github.isaacangello.waydroidbinds
   cp /caminho/io.github.isaacangello.waydroidbinds.flathub.yml .
   git add . && git commit -m "Add io.github.isaacangello.waydroidbinds" && git push
   ```
5. **PR contra `new-pr`** (web), título `Add io.github.isaacangello.waydroidbinds`,
   e na descrição (com suas palavras) explique:
   - arquitetura host-dependent: binds/firewall exigem `pkexec` no host →
     `flatpak-spawn --host pkexec ...`; justifica `--filesystem=host`,
     `--talk-name=org.freedesktop.Flatpak`, `--socket=session-bus`.
   - `--share=network`: diagnóstico de conectividade (ping).
6. **Review:** responder comentários; quando pedirem, comentar `bot, build`.
7. **Aprovação:** aceitar o convite de colaborador do repo do app em
   `flathub/io.github.isaacangello.waydroidbinds` (≤ 1 semana; exige 2FA no
   GitHub). Atualizações futuras são feitas lá — o `x-checker-data` abre PRs de
   bump de versão automaticamente.
8. **Opcional (badge "verified"):** requer domínio próprio (verificação por DNS)
   ou vínculo com org/account no GitHub.

> **Limitação:** o Flatpak roda o GUI num sandbox. As ações privilegiadas
> (binds e firewall) dependem do pacote nativo instalado no host
> (`waydroid-binds` do pacman/deb/rpm), executado via `flatpak-spawn --host`.
> O status dos binds também é lido do host (`flatpak-spawn --host mount`).
