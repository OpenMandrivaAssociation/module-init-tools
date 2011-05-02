#TODO Take care of the conversion
%define _bindir /bin
%define _sbindir /sbin
%define _libdir /%_lib
%define _libexecdir /%_lib
%define major 0
%define libname %mklibname modprobe %major
%define devellibname %mklibname -d modprobe

# We must remove alternatives before new files are installed; otherwise
# they are wiped out by postun script of older version
%define toalternate insmod lsmod modprobe rmmod depmod modinfo

%define build_diet 1

Summary: Tools for managing Linux kernel modules
Name: module-init-tools
Version: 3.6
Release: 18
Source0: http://www.kernel.org/pub/linux/utils/kernel/module-init-tools/%name-%version.tar.bz2
Source1: blacklist-mdv
Source3: modprobe.default
Source4: modprobe.compat
Source5: modprobe.preload
Source6: ipw-no-associate.conf
# from Fedora package
Source20: blacklist-compat
Patch1: module-init-tools-3.6-libify.patch
Patch2: module-init-tools-3.2-pre8-dont-break-depend.patch
Patch3: module-init-tools-3.2-pre8-modprobe-default.patch
Patch4: module-init-tools-3.2.2-generate-modprobe.conf-no-defaults.patch
Patch5: module-init-tools-3.0-failed.unknown.symbol.patch
Patch6: module-init-tools-3.5-preferred.patch
# (proyvind): add support for xz compressed modules
Patch8: module-init-tools-3.6-xz-support.patch
License: GPL
Group: System/Kernel and hardware
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
Url: %{url}
Conflicts: modutils < 2.4.22-10mdk devfsd < 1.3.25-31mdk
Obsoletes: modutils
Requires: %libname = %{version}-%{release}
Conflicts: %libname < 3.6
BuildRequires: autoconf2.5
BuildRequires: glibc-static-devel
BuildRequires: libz-devel
BuildRequires:	liblzma-devel
BuildRequires: docbook-utils docbook-dtd41-sgml
%if %{build_diet}
BuildRequires:	dietlibc-devel
%endif

%description
This package contains a set of programs for loading, inserting, and
removing kernel modules for Linux (versions 2.5.47 and above). It
serves the same function that the "modutils" package serves for Linux
2.4.

%package -n %libname
Summary: Library for %{name}
Group: System/Libraries

%description -n %libname
Library for %{name}.


%package -n %devellibname
Summary: Development files for %{name}
Group: Development/C
Conflicts: module-init-tools-devel <= 3.3-pre11.14mdv
Obsoletes: module-init-tools-devel
Provides: modprobe-devel = %version-%release
Requires: %libname = %version
Obsoletes: %{_lib}modprobe0-devel < %version-%release

%description -n %devellibname
Development files for %{name}

%prep
%setup -q -n %name-%version
%patch1 -p1 -b .lib
%patch2 -p1 -b .dont-break-depend
%patch3 -p1 -b .modprobe-default
%patch4 -p1 -b .generate-modprobe.conf-no-defaults
%patch5 -p1 -b .failed-symb
%patch6 -p1 -b .preferred
%patch8 -p1 -b .xz~

autoreconf -fi
# XXX: Remove config.status, otherwise configure will get confused
rm -f config.status

%build
%serverbuild

%if %{build_diet}
mkdir -p objs-diet
pushd objs-diet
CONFIGURE_TOP=.. %configure2_5x --enable-zlib --enable-xz --disable-shared
make CFLAGS="-Os" CC="diet gcc"
popd
%endif

mkdir -p objs
pushd objs
CONFIGURE_TOP=.. %configure2_5x --enable-zlib --enable-xz
make  CFLAGS="%{optflags} -fPIC"
popd

%install
rm -rf $RPM_BUILD_ROOT

pushd objs
%makeinstall transform=
mv $RPM_BUILD_ROOT/bin/lsmod $RPM_BUILD_ROOT/sbin
popd

%if %{build_diet}
install -d $RPM_BUILD_ROOT%{_prefix}/lib/dietlibc/lib-%{_arch}
install objs-diet/.libs/libmodprobe.a $RPM_BUILD_ROOT%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
%endif

mkdir -p $RPM_BUILD_ROOT{%_libdir,%_includedir}
install -m644 modprobe.h list.h $RPM_BUILD_ROOT%_includedir

%ifarch %{ix86}
pushd $RPM_BUILD_ROOT/sbin && {
	rm -f insmod.static
} && popd
%endif

install -d -m755 $RPM_BUILD_ROOT/etc/
install -d -m755 $RPM_BUILD_ROOT/etc/depmod.d/
touch $RPM_BUILD_ROOT/etc/modprobe.conf
install -m 644 %{SOURCE5} $RPM_BUILD_ROOT/etc
install -d -m755 $RPM_BUILD_ROOT/etc/modprobe.d/
install -m 644 %{SOURCE1} %{SOURCE6} %{SOURCE20} $RPM_BUILD_ROOT/etc/modprobe.d

install -d -m755 $RPM_BUILD_ROOT/%{_libdir}/module-init-tools
install -m 644 %{SOURCE3} $RPM_BUILD_ROOT/%{_libdir}/module-init-tools
install -m 644 %{SOURCE4} $RPM_BUILD_ROOT/%{_libdir}/module-init-tools

# We have to remove alternatives before postun for old version runs,
# otherwise either dummy entries remain without any possibility to clean up
# or newly installed binaries are silentlty removed
%triggerprein -- module-init-tools < 3.3-pre11.10mdv2008.0
for i in %{toalternate}; do
	update-alternatives --remove $i /sbin/$i-25
	update-alternatives --remove $i /sbin/$i-24
	update-alternatives --remove man-$i %{_mandir}/man8/$i-25.8%{_extension}
	update-alternatives --remove man-$i %{_mandir}/man8/$i-24.8%{_extension}
done
exit 0

# libmodprobe.so.0 used to be in /lib for x86_64 before 3.6 which now ships them in /lib64
# and the ABI has been modified without bumping the major at the same time.
# The old files in /lib will be removed very late in the transaction, which will make scriptlets
# depending on libmodprobe fail (like depmod), because depmod will prefer the library from /lib
# with the old incompatible ABI.
# A workaround is to remove the old files from /lib earlier
%ifarch x86_64
%triggerin -- lib64modprobe0 >= 3.6
rm -f /lib/libmodprobe.so.0*
%endif

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

%clean
rm -rf $RPM_BUILD_ROOT

%if %mdkversion < 200900
%post   -n %libname -p /sbin/ldconfig
%endif
%if %mdkversion < 200900
%postun -n %libname -p /sbin/ldconfig
%endif

%files
%defattr(-,root,root)
%doc AUTHORS COPYING ChangeLog NEWS README 
%doc TODO stress_modules.sh
%dir /etc/depmod.d/
%config(noreplace) /etc/modprobe.conf
%config(noreplace) /etc/modprobe.preload
%dir /etc/modprobe.d/
%config(noreplace) /etc/modprobe.d/*
%dir %{_libdir}/module-init-tools
%{_libdir}/module-init-tools/*
/sbin/generate-modprobe.conf
/sbin/*
%{_mandir}/*/*


%files -n %devellibname
%defattr(-,root,root)
%_includedir/*.h
%{_libdir}/libmodprobe.a
%if %{build_diet}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libmodprobe.a
%endif
%{_libdir}/libmodprobe.la
%{_libdir}/libmodprobe.so


%files -n %libname
%defattr(-,root,root)
%{_libdir}/libmodprobe.so.*

