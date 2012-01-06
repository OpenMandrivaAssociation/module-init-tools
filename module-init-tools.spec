%define major 1
%define libname %mklibname modprobe %{major}
%define devellibname %mklibname -d modprobe

# We must remove alternatives before new files are installed; otherwise
# they are wiped out by postun script of older version
%define toalternate insmod lsmod modprobe rmmod depmod modinfo

%define build_diet 1

Summary:	Tools for managing Linux kernel modules
Name:		module-init-tools
Version:	3.16
Release:	1
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
License:	GPL
Group:		System/Kernel and hardware
Url:		http://www.kernel.org/pub/linux/utils/kernel/module-init-tools/
Conflicts:	modutils < 2.4.22-10mdk devfsd < 1.3.25-31mdk
Obsoletes:	modutils
Requires:	%{libname} = %{version}-%{release}
Conflicts:	%{libname} < 3.6
BuildRequires:	autoconf2.5
BuildRequires:	glibc-static-devel
BuildRequires:	libz-devel
BuildRequires:	liblzma-devel
BuildRequires:	docbook-utils docbook-dtd41-sgml
%if %{build_diet}
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


%package -n	%{devellibname}
Summary:	Development files for %{name}
Group:		Development/C
Conflicts:	module-init-tools-devel <= 3.3-pre11.14mdv
Obsoletes:	module-init-tools-devel
Provides:	modprobe-devel = %{version}-%{release}
Requires:	%{libname} = %{version}
Obsoletes:	%{_lib}modprobe0-devel < %{version}-%{release}

%description -n %{devellibname}
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

%if %{build_diet}
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

%if %{build_diet}
install objs-diet/.libs/libmodprobe.a -D %{buildroot}%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
install objs-diet/insmod.static -D %{buildroot}/sbin/insmod.static
install objs-diet/modprobe -D %{buildroot}/sbin/modprobe-static
%endif

mkdir -p %{buildroot}{%{_libdir},%{_includedir}}
install -m644 modprobe.h list.h %{buildroot}%{_includedir}

%ifarch %{ix86}
pushd %{buildroot}/sbin && {
	rm -f insmod.static
} && popd
%endif

install -d -m755 %{buildroot}%{_sysconfdir}
install -d -m755 %{buildroot}%{_sysconfdir}/depmod.d/
touch %{buildroot}%{_sysconfdir}/modprobe.conf
install -m644 %{SOURCE5} %{buildroot}%{_sysconfdir}
install -d -m755 %{buildroot}%{_sysconfdir}/modprobe.d/
install -m644 %{SOURCE1} %{SOURCE6} %{SOURCE20} %{buildroot}%{_sysconfdir}/modprobe.d

install -d -m755 %{buildroot}/lib/module-init-tools
install -m644 %{SOURCE3} -D %{buildroot}%{_sysconfdir}/modprobe.d/00_modprobe.conf

install -m755 generate-modprobe.conf %{buildroot}/sbin/generate-modprobe.conf

%pre
if [ -e /etc/modprobe.d/blacklist-mdv ]; then
	mv /etc/modprobe.d/blacklist-mdv{,.conf}
fi
if [ -e /etc/modprobe.d/blacklist-compat ]; then
	mv /etc/modprobe.d/blacklist-compat{,.conf}
fi

%post
if [ ! -s /etc/modprobe.conf ]; then
	MODPROBE_CONF=/etc/modprobe.conf
elif [ -e /etc/modprobe.conf.rpmnew ]; then
	MODPROBE_CONF=/etc/modprobe.conf.rpmnew
fi

if [ -s /etc/modules.conf -a -n "$MODPROBE_CONF" ]; then
	echo '# This file is autogenerated from /etc/modules.conf using generate-modprobe.conf command' >> $MODPROBE_CONF
	echo >> $MODPROBE_CONF
	/sbin/generate-modprobe.conf >> $MODPROBE_CONF 2> /dev/null
fi

if [ -s /etc/modprobe.conf ]; then
	perl -pi -e 's/(^\s*include\s.*modprobe\.(default|compat).*)/# This file is now included automatically by modprobe\n# $1/' /etc/modprobe.conf
fi

exit 0

%files
%doc AUTHORS COPYING ChangeLog NEWS README 
%doc TODO stress_modules.sh
%dir /etc/depmod.d/
%config(noreplace) /etc/modprobe.conf
%config(noreplace) /etc/modprobe.preload
%dir /etc/modprobe.d/
%config(noreplace) /etc/modprobe.d/*
%dir /lib/module-init-tools
/sbin/*
%{_mandir}/*/*

%files -n %devellibname
%{_includedir}/*.h
/%{_lib}/libmodprobe.a
%if %{build_diet}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
%endif
/%{_lib}/libmodprobe.la
/%{_lib}/libmodprobe.so

%files -n %libname
/%{_lib}/libmodprobe.so.*
