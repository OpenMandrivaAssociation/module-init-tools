%define	major	1
%define	libname	%mklibname modprobe %{major}
%define	devname	%mklibname -d modprobe

%bcond_without	diet

Summary:	Tools for managing Linux kernel modules
Name:		module-init-tools
Version:	3.16
Release:	3
Source0:	http://www.kernel.org/pub/linux/utils/kernel/module-init-tools/%name-%version.tar.bz2
Source1:	blacklist-mdv.conf
Source3:	modprobe.default
Source5:	modprobe.preload
Source6:	ipw-no-associate.conf
# from Fedora package
Source20:	blacklist-compat.conf
Patch0:		module-init-tools-3.16-new-api.diff
# split:
Patch1:		module-init-tools-3.16-libify.patch
Patch2:		module-init-tools-3.16-dont-break-depend.patch
# add --use-modprobe-c to ./generate-modprobe.conf:
# ./generate-modprobe.conf is no more used by the package and it's
# probably time to not ship it anymore.
Patch4:		module-init-tools-3.16-generate-modprobe.conf-no-defaults.patch
# fail on unknown symbol:
Patch5:		module-init-tools-3.16-failed.unknown.symbol.patch
# (blino) /lib/module-init-tools/ldetect-lst-modules.alias needs to be
# parsed in its own group, so that modprobe.d/*.conf files are
# preferred over it
#
# If ldetect-lst-modules.alias was in modprobe.d, both aliases from
# this file and other .conf files would be loaded, while we want to be
# able to completely override or disable ldetect-lst aliases from
# modprobe.d/*.conf files
Patch6:		module-init-tools-3.16-preferred.patch
# build fix:
Patch7:		module-init-tools-3.16-fix-build.patch
# exit() is not a user-friendly user managment method in a library:
Patch8:		module-init-tools-3.16-libify-2.patch
# rename warn() -> mod_warn() (mga#3309):
Patch9:		module-init-tools-3.16-libify-4.patch
# quiet API:
Patch10:	module-init-tools-3.16-libify-7.patch
Patch20:	module-init-tools-3.16-xz-support.patch
License:	GPLv2+
Group:		System/Kernel and hardware
Url:		http://www.kernel.org/pub/linux/utils/kernel/module-init-tools/
BuildRequires:	autoconf2.5
BuildRequires:	glibc-static-devel
BuildRequires:	libz-devel
BuildRequires:	liblzma-devel
BuildRequires:	docbook-utils docbook-dtd41-sgml
%if %{with diet}
BuildRequires:	dietlibc-devel
%endif

%description
This package contains a set of programs for loading, inserting, and
removing kernel modules for Linux (versions 2.5.47 and above). It
serves the same function that the "modutils" package serves for Linux
2.4.

%package -n	%{libname}
Summary:	Library for %{name}
Group:		System/Libraries

%description -n	%{libname}
Library for %{name}.

%package -n	%{devname}
Summary:	Development files for %{name}
Group:		Development/C
%rename		module-init-tools-devel
Provides:	modprobe-devel = %{EVRD}
Requires:	%{libname} = %{version}

%description -n %{devname}
Development files for %{name}

%prep
%setup -q
%patch0 -p1 -b .new-api
%patch1 -p1 -b .lib
%patch2 -p1 -b .dont-break-depend
%patch4 -p1 -b .generate-modprobe.conf-no-defaults
%patch5 -p1 -b .failed-symb
%patch6 -p1 -b .preferred
%patch7 -p1 -b .fixbuild
%patch8 -p1 -b .lib2
%patch9 -p1 -b .lib4
%patch10 -p1 -b .quiet_api
%patch20 -p1 -b .xz~

autoreconf -fi
# XXX: Remove config.status, otherwise configure will get confused
rm -f config.status

%build
%serverbuild

%if %{with diet}
mkdir -p objs-diet
pushd objs-diet
CONFIGURE_TOP=.. \
%configure2_5x	--enable-zlib \
		--enable-liblzma \
		--disable-shared \
		--bindir=/bin \
		--sbindir=/sbin \
		--libdir=/%{_lib} \
		--libexecdir=/%{_lib}

# (tv) fix static build:
perl -pi -e 'warn "TOTO", s/$/ -Wl,-Bstatic -lz -Wl,-Bdynamic/ if /LDADD.*libmodtools.a$/' Makefile 
make CFLAGS="-Os" CC="diet gcc"
popd
%endif

mkdir -p objs
pushd objs
CONFIGURE_TOP=.. \
%configure2_5x	--enable-zlib \
		--enable-liblzma \
		--bindir=/bin \
		--sbindir=/sbin \
		--libdir=/%{_lib} \
		--libexecdir=/%{_lib}

make  CFLAGS="%{optflags} -fPIC"
popd

%install
pushd objs
%makeinstall_std transform=
mv %{buildroot}/bin/lsmod %{buildroot}/sbin
popd

%if %{with diet}
install objs-diet/.libs/libmodprobe.a -D %{buildroot}%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
install objs-diet/insmod.static -D %{buildroot}/sbin/insmod.static
install objs-diet/modprobe -D %{buildroot}/sbin/modprobe-static
%endif

mkdir -p %{buildroot}{%{_libdir},%{_includedir}}
install -m644 modprobe.h list.h %{buildroot}%{_includedir}

install -d -m755 %{buildroot}%{_sysconfdir}
install -d -m755 %{buildroot}%{_sysconfdir}/depmod.d/
install -m644 %{SOURCE5} %{buildroot}%{_sysconfdir}
install -d -m755 %{buildroot}%{_sysconfdir}/modprobe.d/
install -m644 %{SOURCE1} %{SOURCE6} %{SOURCE20} %{buildroot}%{_sysconfdir}/modprobe.d

install -d -m755 %{buildroot}/lib/module-init-tools
install -m644 %{SOURCE3} -D %{buildroot}%{_sysconfdir}/modprobe.d/00_modprobe.conf

install -m755 generate-modprobe.conf %{buildroot}/sbin/generate-modprobe.conf

%pre
# /etc/modprobe.conf is deprecated. All config files should be put in
# /etc/modprobe.d/ directory now.
if [ -e /etc/modprobe.conf ]; then
	if [ ! -s /etc/modprobe.conf ]; then
		rm -f /etc/modprobe.conf
	elif [ ! -e /etc/modprobe.d/modprobe.conf ]; then
		mv /etc/modprobe.conf /etc/modprobe.d/
	fi
fi

%files
%doc AUTHORS ChangeLog NEWS README
%doc TODO stress_modules.sh
%dir %{_sysconfdir}/depmod.d/
%config(noreplace) %{_sysconfdir}/modprobe.preload
%dir %{_sysconfdir}/modprobe.d/
%config(noreplace) %{_sysconfdir}/modprobe.d/*
%dir /lib/module-init-tools
/sbin/*
%{_mandir}/*/*

%files -n %{devname}
%{_includedir}/*.h
/%{_lib}/libmodprobe.a
%if %{with diet}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
%endif
/%{_lib}/libmodprobe.la
/%{_lib}/libmodprobe.so

%files -n %{libname}
/%{_lib}/libmodprobe.so.*
