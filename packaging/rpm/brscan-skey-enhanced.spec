%{!?pkg_version:%global pkg_version 0.1.0}

Name:           brscan-skey-enhanced
Version:        %{pkg_version}
Release:        1%{?dist}
Summary:        Easier Brother brscan-skey button configuration
License:        LicenseRef-Project
URL:            https://github.com/chainarong-ck/brscan-skey-enhanced
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       bash
Requires:       python3
Requires:       python3-gobject
Requires:       gtk3
Requires:       ImageMagick
Requires:       xdg-utils

%description
Configurable Scan to File, Scan to Image, and Scan to Email handlers for
Brother scanners on Linux, with a GTK settings application. The proprietary
Brother scanner driver and brscan-skey must be installed separately.

%prep
%setup -q

%build

%install
install -d \
    %{buildroot}%{_prefix}/lib/brscan-skey-enhanced/configurator \
    %{buildroot}%{_prefix}/lib/brscan-skey-enhanced/script \
    %{buildroot}%{_datadir}/brscan-skey-enhanced/brother-config \
    %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir}/applications \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

install -m 0644 configurator/*.py \
    %{buildroot}%{_prefix}/lib/brscan-skey-enhanced/configurator/
install -m 0755 script/*.sh \
    %{buildroot}%{_prefix}/lib/brscan-skey-enhanced/script/
install -m 0644 *.config \
    %{buildroot}%{_datadir}/brscan-skey-enhanced/brother-config/
install -m 0755 bin/* %{buildroot}%{_bindir}/
install -m 0644 assets/brscan-skey-enhanced.desktop \
    %{buildroot}%{_datadir}/applications/
install -m 0644 assets/brscan-skey-enhanced.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%post
brother_dir="/opt/brother/scanner/brscan-skey/script"
if [ -d "$brother_dir" ]; then
    BRSCAN_SHARE_DIR="%{_datadir}/brscan-skey-enhanced" \
    BRSCAN_BROTHER_SCRIPT_DIR="$brother_dir" \
        %{_bindir}/brscan-skey-enhanced-integrate install || :
else
    echo "Install Brother brscan-skey, then run:"
    echo "  sudo brscan-skey-enhanced-integrate install"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database %{_datadir}/applications || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q %{_datadir}/icons/hicolor || :
fi

%preun
if [ "$1" -eq 0 ]; then
    BRSCAN_SHARE_DIR="%{_datadir}/brscan-skey-enhanced" \
    BRSCAN_BROTHER_SCRIPT_DIR="/opt/brother/scanner/brscan-skey/script" \
        %{_bindir}/brscan-skey-enhanced-integrate remove || :
fi

%files
%{_bindir}/brscan-skey-settings
%{_bindir}/brscan-skey-enhanced-check
%{_bindir}/brscan-skey-enhanced-integrate
%{_prefix}/lib/brscan-skey-enhanced/
%{_datadir}/brscan-skey-enhanced/
%{_datadir}/applications/brscan-skey-enhanced.desktop
%{_datadir}/icons/hicolor/scalable/apps/brscan-skey-enhanced.svg

%changelog
* Sat Jul 25 2026 Brother Scan Enhanced maintainers <noreply@github.com> - 0.1.0-1
- Initial package
