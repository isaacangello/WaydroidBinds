# Flatpak / Flathub

Publicação do pacote Flatpak no Flathub.

- **App ID:** `org.waydroidbinds.WaydroidBinds`
- **Conta de desenvolvedor no Flathub (ID):** `50752`

## Publicar no Flathub

1. Build local (valida o manifesto):

   ```sh
   flatpak-builder --user --force-clean --repo=repo build \
     org.waydroidbinds.WaydroidBinds.yml
   flatpak build-bundle repo waydroid-binds.flatpak org.waydroidbinds.WaydroidBinds
   ```

2. Suba a fonte para o repositório oficial do Flathub
   (fork de `flathub/flathub`):
   - copie `org.waydroidbinds.WaydroidBinds.yml` para a raiz do fork;
   - adicione o `.desktop`, o ícone e a fonte (tarball versionado) como
     módulos `sources` (a CI do Flathub baixa a fonte, então use um tarball
     do GitHub Release, não `type: dir`).

3. Abra um PR no `flathub/flathub` com a conta de ID `50752` e siga o
   review automático (`flathub/flathub#Webbrowser` checks).

> Limitação: o Flatpak roda o GUI num sandbox. As ações privilegiadas
> (binds e firewall) dependem do pacote nativo instalado no host
> (`waydroid-binds` do pacman/deb/rpm), executado via `flatpak-spawn --host`.
