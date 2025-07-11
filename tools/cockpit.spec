#
# Copyright (C) 2014-2020 Red Hat, Inc.
#
# Cockpit is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# Cockpit is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Cockpit; If not, see <https://www.gnu.org/licenses/>.
#

# This file is maintained at the following location:
# https://github.com/cockpit-project/cockpit/blob/main/tools/cockpit.spec
#
# If you are editing this file in another location, changes will likely
# be clobbered the next time an automated release is done.
#
# Check first cockpit-devel@lists.fedorahosted.org
#

# earliest base that the subpackages work on; this is still required as long as
# we maintain the basic/optional split, then it can be replaced with just %{version}.
%define required_base 266

# we generally want CentOS packages to be like RHEL; special cases need to check %{centos} explicitly
%if 0%{?centos}
%define rhel %{centos}
%endif

%define _hardened_build 1

%define __lib lib

%if 0%{?suse_version} > 1500
%define pamconfdir %{_pam_vendordir}
%define pamconfig tools/cockpit.suse.pam
%else
%define pamconfdir %{_sysconfdir}/pam.d
%define pamconfig tools/cockpit.pam
%endif

%if %{defined _pamdir}
%define pamdir %{_pamdir}
%else
%define pamdir %{_libdir}/security
%endif

Name:           cockpit
Summary:        Web Console for Linux servers

License:        LGPL-2.1-or-later
URL:            https://cockpit-project.org/

Version:        0
Release:        1%{?dist}
Source0:        https://github.com/cockpit-project/cockpit/releases/download/%{version}/cockpit-%{version}.tar.xz

%if 0%{?fedora} >= 41 || 0%{?rhel}
ExcludeArch: %{ix86}
%endif

%define enable_multihost 1
%if 0%{?fedora} >= 41 || 0%{?rhel} >= 10
%define enable_multihost 0
%endif

# Ship custom SELinux policy
%define selinuxtype targeted
%define selinux_configure_arg --enable-selinux-policy=%{selinuxtype}

BuildRequires: gcc
BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(json-glib-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= 0.105
BuildRequires: pam-devel

BuildRequires: autoconf automake
BuildRequires: make
BuildRequires: python3-devel
BuildRequires: gettext >= 0.21
BuildRequires: openssl-devel
BuildRequires: gnutls-devel >= 3.4.3
BuildRequires: zlib-devel
BuildRequires: krb5-devel >= 1.11
BuildRequires: libxslt-devel
BuildRequires: glib-networking
BuildRequires: sed

BuildRequires: glib2-devel >= 2.50.0
# this is for runtimedir in the tls proxy ace21c8879
BuildRequires: systemd-devel >= 235
%if 0%{?suse_version}
BuildRequires: distribution-release
BuildRequires: openssh
BuildRequires: distribution-logos
BuildRequires: wallpaper-branding
%else
BuildRequires: openssh-clients
BuildRequires: docbook-style-xsl
%endif
BuildRequires: krb5-server
BuildRequires: gdb

# For documentation
BuildRequires: xmlto

BuildRequires:  selinux-policy
BuildRequires:  selinux-policy-devel

# This is the "cockpit" metapackage. It should only
# Require, Suggest or Recommend other cockpit-xxx subpackages

Requires: cockpit-bridge
Requires: cockpit-ws
Requires: cockpit-system

# Optional components
Recommends: (cockpit-storaged if udisks2)
Recommends: (cockpit-packagekit if dnf)
Suggests: python3-pcp

%if 0%{?rhel} == 0
Recommends: (cockpit-networkmanager if NetworkManager)
# c-ostree is not in RHEL 8/9
Recommends: (cockpit-ostree if rpm-ostree)
Suggests: cockpit-selinux
%endif
%if 0%{?rhel} && 0%{?centos} == 0
Requires: subscription-manager-cockpit
%endif

BuildRequires:  python3-devel
BuildRequires:  python3-pip
%if 0%{?rhel} == 0 && !0%{?suse_version}
# All of these are only required for running pytest (which we only do on Fedora)
BuildRequires:  procps-ng
BuildRequires:  python3-pytest-asyncio
BuildRequires:  python3-pytest-timeout
%endif

%prep
%setup -q -n cockpit-%{version}

%build
%configure \
    %{?selinux_configure_arg} \
%if 0%{?suse_version}
    --docdir=%_defaultdocdir/%{name} \
%endif
    --with-pamdir='%{pamdir}' \
%if %{enable_multihost}
    --enable-multihost \
%endif

%make_build

%check
make -j$(nproc) check

%if 0%{?rhel} == 0 && 0%{?suse_version} == 0
export NO_QUNIT=1
%pytest
%endif

%install
%if 0%{?suse_version}
export NO_BRP_STALE_LINK_ERROR="yes"
%endif
%make_install

mkdir -p $RPM_BUILD_ROOT%{pamconfdir}
install -p -m 644 %{pamconfig} $RPM_BUILD_ROOT%{pamconfdir}/cockpit

rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -D -p -m 644 AUTHORS COPYING README.md %{buildroot}%{_docdir}/cockpit/

# Build the package lists for resource packages
# cockpit-bridge is the basic dependency for all cockpit-* packages, so centrally own the page directory
echo '%dir %{_datadir}/cockpit' > base.list
echo '%dir %{_datadir}/cockpit/base1' >> base.list
find %{buildroot}%{_datadir}/cockpit/base1 -type f -o -type l >> base.list
echo '%{_sysconfdir}/cockpit/machines.d' >> base.list
echo %{buildroot}%{_datadir}/polkit-1/actions/org.cockpit-project.cockpit-bridge.policy >> base.list

echo '%dir %{_datadir}/cockpit/shell' >> system.list
find %{buildroot}%{_datadir}/cockpit/shell -type f >> system.list

echo '%dir %{_datadir}/cockpit/systemd' >> system.list
find %{buildroot}%{_datadir}/cockpit/systemd -type f >> system.list

echo '%dir %{_datadir}/cockpit/users' >> system.list
find %{buildroot}%{_datadir}/cockpit/users -type f >> system.list

echo '%dir %{_datadir}/cockpit/metrics' >> system.list
find %{buildroot}%{_datadir}/cockpit/metrics -type f >> system.list

echo '%dir %{_datadir}/cockpit/kdump' > kdump.list
find %{buildroot}%{_datadir}/cockpit/kdump -type f >> kdump.list

echo '%dir %{_datadir}/cockpit/sosreport' > sosreport.list
find %{buildroot}%{_datadir}/cockpit/sosreport -type f >> sosreport.list

echo '%dir %{_datadir}/cockpit/storaged' > storaged.list
find %{buildroot}%{_datadir}/cockpit/storaged -type f >> storaged.list

echo '%dir %{_datadir}/cockpit/networkmanager' > networkmanager.list
find %{buildroot}%{_datadir}/cockpit/networkmanager -type f >> networkmanager.list

echo '%dir %{_datadir}/cockpit/packagekit' > packagekit.list
find %{buildroot}%{_datadir}/cockpit/packagekit -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/apps' >> packagekit.list
find %{buildroot}%{_datadir}/cockpit/apps -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/selinux' > selinux.list
find %{buildroot}%{_datadir}/cockpit/selinux -type f >> selinux.list

echo '%dir %{_datadir}/cockpit/static' > static.list
echo '%dir %{_datadir}/cockpit/static/fonts' >> static.list
find %{buildroot}%{_datadir}/cockpit/static -type f >> static.list

sed -i "s|%{buildroot}||" *.list

%if 0%{?suse_version}
# remove files of not installable packages
rm -r %{buildroot}%{_datadir}/cockpit/sosreport
rm -f %{buildroot}/%{_prefix}/share/metainfo/org.cockpit_project.cockpit_sosreport.metainfo.xml
rm -f %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/cockpit-sosreport.png
%else
%global _debugsource_packages 1
%global _debuginfo_subpackages 0

%define find_debug_info %{_rpmconfigdir}/find-debuginfo.sh %{?_missing_build_ids_terminate_build:--strict-build-id} %{?_include_minidebuginfo:-m} %{?_find_debuginfo_dwz_opts} %{?_find_debuginfo_opts} %{?_debugsource_packages:-S debugsourcefiles.list} "%{_builddir}/%{?buildsubdir}"

%endif
# /suse_version
rm -rf %{buildroot}/usr/src/debug

# On RHEL kdump, networkmanager, selinux, and sosreport are part of the system package
%if 0%{?rhel}
cat kdump.list sosreport.list networkmanager.list selinux.list >> system.list
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit_project.cockpit_sosreport.metainfo.xml
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit_project.cockpit_kdump.metainfo.xml
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit_project.cockpit_selinux.metainfo.xml
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit_project.cockpit_networkmanager.metainfo.xml
rm -f %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/cockpit-sosreport.png
%endif

# -------------------------------------------------------------------------------
# Sub-packages

%description
The Cockpit Web Console enables users to administer GNU/Linux servers using a
web browser.

It offers network configuration, log inspection, diagnostic reports, SELinux
troubleshooting, interactive command-line sessions, and more.

%files
%license COPYING
%{_docdir}/cockpit/AUTHORS
%{_docdir}/cockpit/COPYING
%{_docdir}/cockpit/README.md
%{_datadir}/metainfo/org.cockpit_project.cockpit.appdata.xml
%{_datadir}/icons/hicolor/128x128/apps/cockpit.png
%doc %{_mandir}/man1/cockpit.1.gz


%package bridge
Summary: Cockpit bridge server-side component
BuildArch: noarch

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%files bridge -f base.list
%license COPYING
%doc %{_mandir}/man1/cockpit-bridge.1.gz
%{_bindir}/cockpit-bridge
%{_libexecdir}/cockpit-askpass
%{python3_sitelib}/%{name}*

%package doc
Summary: Cockpit deployment and developer guide
BuildArch: noarch

%description doc
The Cockpit Deployment and Developer Guide shows sysadmins how to
deploy Cockpit on their machines as well as helps developers who want to
embed or extend Cockpit.

%files doc
%license COPYING
%exclude %{_docdir}/cockpit/AUTHORS
%exclude %{_docdir}/cockpit/COPYING
%exclude %{_docdir}/cockpit/README.md
%{_docdir}/cockpit

%package system
Summary: Cockpit admin interface package for configuring and troubleshooting a system
BuildArch: noarch
Requires: cockpit-bridge >= %{version}-%{release}
%if !0%{?suse_version}
Requires: shadow-utils
%endif
Requires: grep
Requires: /usr/bin/pwscore
Requires: /usr/bin/date
Provides: cockpit-shell = %{version}-%{release}
Provides: cockpit-systemd = %{version}-%{release}
Provides: cockpit-tuned = %{version}-%{release}
Provides: cockpit-users = %{version}-%{release}
%if 0%{?rhel}
Requires: NetworkManager >= 1.6
Requires: sos
Requires: sudo
Recommends: PackageKit
Recommends: setroubleshoot-server >= 3.3.3
Recommends: /usr/bin/kdumpctl
Suggests: NetworkManager-team
Suggests: python3-pcp
Provides: cockpit-kdump = %{version}-%{release}
Provides: cockpit-networkmanager = %{version}-%{release}
Provides: cockpit-selinux = %{version}-%{release}
Provides: cockpit-sosreport = %{version}-%{release}
%endif

#NPM_PROVIDES

%description system
This package contains the Cockpit shell and system configuration interfaces.

%files system -f system.list
%license COPYING
%dir %{_datadir}/cockpit/shell/images

%package ws
Summary: Cockpit Web Service
Requires: glib-networking
Requires: openssl
Requires: glib2 >= 2.50.0
Requires: (%{name}-ws-selinux = %{version}-%{release} if selinux-policy-base)
Recommends: sscg >= 2.3
Recommends: system-logos
Suggests: sssd-dbus >= 2.6.2
# for cockpit-desktop
Suggests: python3
Obsoletes: cockpit-tests < 331

# prevent hard python3 dependency for cockpit-desktop, it falls back to other browsers
%global __requires_exclude_from ^%{_libexecdir}/cockpit-client$

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

If sssd-dbus is installed, you can enable client certificate/smart card
authentication via sssd/FreeIPA.

%files ws -f static.list
%license COPYING
%doc %{_mandir}/man1/cockpit-desktop.1.gz
%doc %{_mandir}/man5/cockpit.conf.5.gz
%doc %{_mandir}/man8/cockpit-ws.8.gz
%doc %{_mandir}/man8/cockpit-tls.8.gz
%doc %{_mandir}/man8/pam_ssh_add.8.gz
%dir %{_sysconfdir}/cockpit
%config(noreplace) %{_sysconfdir}/cockpit/ws-certs.d
%config(noreplace) %{pamconfdir}/cockpit

# created in %post, so that users can rm the files
%ghost %{_sysconfdir}/issue.d/cockpit.issue
%ghost %{_sysconfdir}/motd.d/cockpit
%ghost %attr(0644, root, root) %{_sysconfdir}/cockpit/disallowed-users
%dir %{_datadir}/cockpit/issue
%{_datadir}/cockpit/issue/update-issue
%{_datadir}/cockpit/issue/inactive.issue
%{_unitdir}/cockpit.service
%{_unitdir}/cockpit-issue.service
%{_unitdir}/cockpit.socket
%{_unitdir}/cockpit-session-socket-user.service
%{_unitdir}/cockpit-session.socket
%{_unitdir}/cockpit-session@.service
%{_unitdir}/cockpit-wsinstance-http.socket
%{_unitdir}/cockpit-wsinstance-http.service
%{_unitdir}/cockpit-wsinstance-https-factory.socket
%{_unitdir}/cockpit-wsinstance-https-factory@.service
%{_unitdir}/cockpit-wsinstance-https@.socket
%{_unitdir}/cockpit-wsinstance-https@.service
%{_unitdir}/cockpit-wsinstance-socket-user.service
%{_unitdir}/system-cockpithttps.slice
%{_prefix}/%{__lib}/tmpfiles.d/cockpit-ws.conf
%{pamdir}/pam_ssh_add.so
%{pamdir}/pam_cockpit_cert.so
%{_libexecdir}/cockpit-ws
%{_libexecdir}/cockpit-wsinstance-factory
%{_libexecdir}/cockpit-tls
%{_libexecdir}/cockpit-client
%{_libexecdir}/cockpit-client.ui
%{_libexecdir}/cockpit-desktop
%{_libexecdir}/cockpit-certificate-ensure
%{_libexecdir}/cockpit-certificate-helper
%{_libexecdir}/cockpit-session
%{_datadir}/cockpit/branding

%post ws
# set up dynamic motd/issue symlinks on first-time install; don't bring them back on upgrades if admin removed them
# disable root login on first-time install; so existing installations aren't changed
if [ "$1" = 1 ]; then
    mkdir -p /etc/motd.d /etc/issue.d
    ln -s ../../run/cockpit/issue /etc/motd.d/cockpit
    ln -s ../../run/cockpit/issue /etc/issue.d/cockpit.issue
    printf "# List of users which are not allowed to login to Cockpit\n" > /etc/cockpit/disallowed-users
    printf "root\n" >> /etc/cockpit/disallowed-users
    chmod 644 /etc/cockpit/disallowed-users
fi

# on upgrades, adjust motd/issue links to changed target if they still exist (changed in 331)
if [ "$1" = 2 ]; then
    if [ "$(readlink /etc/motd.d/cockpit 2>/dev/null)" = "../../run/cockpit/motd" ]; then
        ln -sfn ../../run/cockpit/issue /etc/motd.d/cockpit
    fi
    if [ "$(readlink /etc/issue.d/cockpit.issue 2>/dev/null)" = "../../run/cockpit/motd" ]; then
        ln -sfn ../../run/cockpit/issue /etc/issue.d/cockpit.issue
    fi
fi

%tmpfiles_create cockpit-ws.conf
%systemd_post cockpit.socket cockpit.service
# firewalld only partially picks up changes to its services files without this
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

# check for deprecated PAM config
if test -f %{_sysconfdir}/pam.d/cockpit &&  grep -q pam_cockpit_cert %{_sysconfdir}/pam.d/cockpit; then
    echo '**** WARNING:'
    echo '**** WARNING: pam_cockpit_cert is a no-op and will be removed in a'
    echo '**** WARNING: future release; remove it from your /etc/pam.d/cockpit.'
    echo '**** WARNING:'
fi

# remove obsolete system user on upgrade (replaced with DynamicUser in version 330)
if getent passwd cockpit-wsinstance >/dev/null; then
    userdel cockpit-wsinstance
fi

%preun ws
%systemd_preun cockpit.socket cockpit.service

%postun ws
%systemd_postun_with_restart cockpit.socket cockpit.service

%package ws-selinux
Summary: SELinux security policy for cockpit-ws
# older -ws contained the SELinux policy, now split out
Conflicts: %{name}-ws < 337-1.2025
Requires(post): selinux-policy-%{selinuxtype} >= %{_selinux_policy_version}
Requires(post): libselinux-utils
Requires(post): policycoreutils

%description ws-selinux
SELinux policy module for the cockpit-ws package.

%files ws-selinux
%license COPYING
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%{_mandir}/man8/%{name}_session_selinux.8cockpit.*
%{_mandir}/man8/%{name}_ws_selinux.8cockpit.*
%ghost %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}

%pre ws-selinux
%selinux_relabel_pre -s %{selinuxtype}

%post ws-selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%selinux_relabel_post -s %{selinuxtype}

%postun ws-selinux
%selinux_modules_uninstall -s %{selinuxtype} %{name}
%selinux_relabel_post -s %{selinuxtype}

# -------------------------------------------------------------------------------
# Sub-packages that are part of cockpit-system in RHEL/CentOS, but separate in Fedora

%if 0%{?rhel} == 0

%package kdump
Summary: Cockpit user interface for kernel crash dumping
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
%if 0%{?suse_version}
Requires: kexec-tools
%else
Requires: /usr/bin/kdumpctl
%endif
BuildArch: noarch

%description kdump
The Cockpit component for configuring kernel crash dumping.

%files kdump -f kdump.list
%license COPYING
%{_datadir}/metainfo/org.cockpit_project.cockpit_kdump.metainfo.xml

# sosreport is not supported on opensuse yet
%if !0%{?suse_version}
%package sosreport
Summary: Cockpit user interface for diagnostic reports
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: sos
BuildArch: noarch

%description sosreport
The Cockpit component for creating diagnostic reports with the
sosreport tool.

%files sosreport -f sosreport.list
%license COPYING
%{_datadir}/metainfo/org.cockpit_project.cockpit_sosreport.metainfo.xml
%{_datadir}/icons/hicolor/64x64/apps/cockpit-sosreport.png
%endif

%package networkmanager
Summary: Cockpit user interface for networking, using NetworkManager
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: NetworkManager >= 1.6
# Optional components
Recommends: NetworkManager-team
BuildArch: noarch

%description networkmanager
The Cockpit component for managing networking.  This package uses NetworkManager.

%files networkmanager -f networkmanager.list
%license COPYING
%{_datadir}/metainfo/org.cockpit_project.cockpit_networkmanager.metainfo.xml

%endif

%if 0%{?rhel} == 0

%package selinux
Summary: Cockpit SELinux package
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
# setroubleshoot is available on SLE Micro starting with 5.5
%if !0%{?is_smo} || ( 0%{?is_smo} && 0%{?sle_version} >= 150500 )
Requires:       setroubleshoot-server >= 3.3.3
%endif
BuildArch: noarch

%description selinux
This package contains the Cockpit user interface integration with the
utility setroubleshoot to diagnose and resolve SELinux issues.

%files selinux -f selinux.list
%license COPYING
%{_datadir}/metainfo/org.cockpit_project.cockpit_selinux.metainfo.xml

%endif

%package -n cockpit-storaged
Summary: Cockpit user interface for storage, using udisks
Requires: cockpit-shell >= %{required_base}
Requires: udisks2 >= 2.9
Recommends: udisks2-lvm2 >= 2.9
Recommends: udisks2-iscsi >= 2.9
%if ! 0%{?rhel}
Recommends: udisks2-btrfs >= 2.9
%endif
Recommends: device-mapper-multipath
Recommends: clevis-luks
Requires: %{__python3}
%if 0%{?suse_version}
Requires: python3-dbus-python
%else
Requires: python3-dbus
%endif
BuildArch: noarch

%description -n cockpit-storaged
The Cockpit component for managing storage.  This package uses udisks.

%files -n cockpit-storaged -f storaged.list
%license COPYING
%{_datadir}/metainfo/org.cockpit_project.cockpit_storaged.metainfo.xml

%post storaged

# version 332 moved the btrfs temp mounts db to /run
if [ "$1" = 2 ] && [ -d /var/lib/cockpit/btrfs ]; then
    rm -rf --one-file-system  /var/lib/cockpit/btrfs || true
fi

%package -n cockpit-packagekit
Summary: Cockpit user interface for packages
BuildArch: noarch
Requires: cockpit-bridge >= %{required_base}
Requires: PackageKit
Recommends: python3-tracer
# HACK: https://bugzilla.redhat.com/show_bug.cgi?id=1800468
Requires: polkit

%description -n cockpit-packagekit
The Cockpit components for installing OS updates and Cockpit add-ons,
via PackageKit.

%files -n cockpit-packagekit -f packagekit.list
%license COPYING

# The changelog is automatically generated and merged
%changelog
