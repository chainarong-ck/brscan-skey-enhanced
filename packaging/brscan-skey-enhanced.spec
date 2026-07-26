%{!?package_version:%global package_version 0.1.0}

Name:           brscan-skey-enhanced
Version:        %{package_version}
Release:        1%{?dist}
Summary:        Enhanced Brother scanner button actions and settings GUI
License:        LicenseRef-Unknown
URL:            https://github.com/chainarong-ck/brscan-skey-enhanced
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  bash
BuildRequires:  coreutils
BuildRequires:  python3 >= 3.9
Requires:       bash
Requires:       coreutils
Requires:       python3 >= 3.9
Requires:       python3-gobject
Requires:       gtk3
Recommends:     ImageMagick
Recommends:     xdg-utils

%description
Configure per-user Scan to File, Scan to Image, and Scan to Email actions
for Brother brscan-skey without modifying files from the Brother driver.

%prep
%setup -q

%build

%install
bash packaging/install-files.sh "%{buildroot}" "%{_prefix}" gtk

%check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
bash -n \
    install.sh \
    uninstall.sh \
    bin/* \
    script/*.sh \
    packaging/*.sh \
    packaging/debian/postrm \
    *.config

%postun
if [ "$1" -eq 0 ]; then
    rm -rf -- "%{_prefix}/lib/%{name}/configurator/__pycache__"
    rmdir "%{_prefix}/lib/%{name}/configurator" >/dev/null 2>&1 || :
    rmdir "%{_prefix}/lib/%{name}" >/dev/null 2>&1 || :
fi

%files
%{_bindir}/brscan-skey-config
%{_bindir}/brscan-skey-read-settings
%{_datadir}/applications/brscan-skey-config.desktop
%{_datadir}/doc/%{name}/
%{_prefix}/lib/%{name}/
