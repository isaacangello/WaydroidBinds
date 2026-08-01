Name:           waydroid-binds
Version:        1.3.0
Release:        1%{?dist}
Summary:        Waydroid shared folders and firewall manager

License:        GPL-3.0-or-later
URL:            https://github.com/isaacangello/WaydroidBinds
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3

Requires:       python3-pyside6

%description
GUI and scripts to set up Waydroid shared folders (bind mounts) and
persistent internet access (firewall auto-config: IP forwarding, NAT and
firewalld zone).

%prep
%setup -q -n %{name}-%{version}

%build
# nothing to build

%install
rm -rf %{buildroot}
install -dm 0755 %{buildroot}%{_bindir}
install -dm 0755 %{buildroot}%{_datadir}/waydroid-binds
install -m 0755 waydroid-binds-gui %{buildroot}%{_bindir}/waydroid-binds-gui
for s in setup-waydroid-binds.sh setup-waydroid-firewall.sh \
         revert-waydroid-binds.sh copy-existing-media.sh; do
    install -m 0755 "$s" %{buildroot}%{_datadir}/waydroid-binds/
done
cp -a gui %{buildroot}%{_datadir}/waydroid-binds/
install -dm 0755 %{buildroot}%{_datadir}/applications
install -m 0644 gui/resources/waydroid-binds.desktop %{buildroot}%{_datadir}/applications/
install -dm 0755 %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 0644 gui/resources/waydroid-binds.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%{_bindir}/waydroid-binds-gui
%{_datadir}/waydroid-binds/
%{_datadir}/applications/waydroid-binds.desktop
%{_datadir}/icons/hicolor/scalable/apps/waydroid-binds.svg

%changelog
* Sat Aug 01 2026 Isaac Angello <isaac.angello@gmail.com> - 1.3.0-1
- GUI PySide6 (painel completo).
* Sat Aug 01 2026 Isaac Angello <isaac.angello@gmail.com> - 1.2.0-1
- Firewall auto-config e correção do hook de persistência.
