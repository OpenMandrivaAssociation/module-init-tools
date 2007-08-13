#TODO Take care of the conversion
%define name module-init-tools
%define version 3.3
%define priority 20
%define mdkrelease %mkrel 15
%define url http://www.kerneltools.org/pub/downloads/module-init-tools/
%define _bindir /bin
%define _sbindir /sbin
%define _libdir /lib
%define _libexecdir /lib
%define major 0
%define libname %mklibname modprobe %major
%define devellibname %mklibname -d modprobe %major

%define pre 11

%if %pre
%define release pre%{pre}.%mdkrelease
%define tarname %name-%version-pre%{pre}
%else
%define release %mdkrelease
%define tarname %name-%version
%endif

# We must remove alternatives before new files are installed; otherwise
# they are wiped out by postun script of older version
%define toalternate insmod lsmod modprobe rmmod depmod modinfo

Summary: Tools for managing Linux kernel modules
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{url}/%{tarname}.tar.bz2
Source1: blacklist-mdv
Source3: modprobe.default
Source4: modprobe.compat
Source5: modprobe.preload
# from Fedora package
Source6: blacklist-compat
Patch1:  module-init-tools-libify.patch
Patch2:  module-init-tools-3.2-pre8-dont-break-depend.patch
Patch3:  module-init-tools-3.2-pre8-all-defaults.patch
Patch7:  module-init-tools-3.2-pre8-modprobe-default.patch
Patch8:  module-init-tools-3.2.2-generate-modprobe.conf-no-defaults.patch
Patch9:  module-init-tools-3.0-failed.unknown.symbol.patch
Patch10: module-init-tools-3.3-pre11-insmod-strrchr.patch
License: GPL
Group: System/Kernel and hardware
BuildRoot: %{_tmppath}/%{name}-buildroot
Url: %{url}
Conflicts: modutils < 2.4.22-10mdk devfsd < 1.3.25-31mdk
BuildRequires: autoconf2.5
BuildRequires: glibc-static-devel
BuildRequires: libz-devel
BuildRequires: docbook-utils docbook-dtd41-sgml

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

%description -n %devellibname
Development files for %{name}


%prep
%setup -q -n %{tarname}
%patch1 -p1 -b .lib
%patch2 -p1 -b .dont-break-depend
%patch3 -p1 -b .all-defaults
%patch7 -p1 -b .modprobe-default
%patch8 -p1 -b .generate-modprobe.conf-no-defaults
%patch9 -p1 -b .failed-symb
%patch10 -p1 -b .fix_insmod_strrchr

%build
%serverbuild
rm -f Makefile{,.in}
libtoolize -c
aclocal --force
automake -c -f
autoconf
%configure2_5x --enable-zlib
%make  CFLAGS="%{optflags} -fPIC"

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall transform=

mv $RPM_BUILD_ROOT/bin/lsmod $RPM_BUILD_ROOT/sbin

rm -rf $RPM_BUILD_ROOT/%{_mandir}
for n in 5 8;do
	install -d $RPM_BUILD_ROOT/%{_mandir}/man$n/
	for i in *.$n;do
		install -m644 $i $RPM_BUILD_ROOT/%{_mandir}/man${n}/$i
	done
done
mkdir -p $RPM_BUILD_ROOT{%_libdir,%_includedir}
install -m644 modprobe.h list.h $RPM_BUILD_ROOT%_includedir

%ifarch %{ix86}
pushd $RPM_BUILD_ROOT/sbin && {
	rm -f insmod.static
} && popd
%endif

install -d -m755 $RPM_BUILD_ROOT/etc/
touch $RPM_BUILD_ROOT/etc/modprobe.conf
install -m 644 %{SOURCE5} $RPM_BUILD_ROOT/etc
install -d -m755 $RPM_BUILD_ROOT/etc/modprobe.d/
install -m 644 %{SOURCE1} %{SOURCE6} $RPM_BUILD_ROOT/etc/modprobe.d

install -d -m755 $RPM_BUILD_ROOT/lib/module-init-tools
install -m 644 %{SOURCE3} $RPM_BUILD_ROOT/lib/module-init-tools
install -m 644 %{SOURCE4} $RPM_BUILD_ROOT/lib/module-init-tools

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

%post   -n %libname -p /sbin/ldconfig
%postun -n %libname -p /sbin/ldconfig

%files
%defattr(-,root,root)
%doc AUTHORS COPYING ChangeLog NEWS README 
%doc TODO stress_modules.sh
%config(noreplace) /etc/modprobe.conf
%config(noreplace) /etc/modprobe.preload
%dir /etc/modprobe.d/
/etc/modprobe.d/*
%dir /lib/module-init-tools
/lib/module-init-tools/*
/sbin/generate-modprobe.conf
/sbin/*
%{_mandir}/*/*


%files -n %devellibname
%defattr(-,root,root)
%_includedir/*.h
%{_libdir}/libmodprobe.a
%{_libdir}/libmodprobe.la
%{_libdir}/libmodprobe.so


%files -n %libname
%defattr(-,root,root)
%{_libdir}/libmodprobe.so.*

