#TODO Take care of the conversion
%define name module-init-tools
%define version 3.3
%define priority 20
%define mdkrelease %mkrel 9
%define url http://www.kerneltools.org/pub/downloads/module-init-tools/
%define _bindir /bin
%define _sbindir /sbin
%define _libdir /lib
%define _libexecdir /lib

%define pre 11

%if %pre
%define release pre%{pre}.%mdkrelease
%define tarname %name-%version-pre%{pre}
%else
%define release %mdkrelease
%define tarname %name-%version
%endif

%define toalternate insmod lsmod modprobe rmmod depmod modinfo

Summary: Tools for managing Linux kernel modules
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{url}/%{tarname}.tar.bz2
Source3: modprobe.default
Source4: modprobe.compat
Source5: modprobe.preload
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
Requires(post): /usr/sbin/update-alternatives
Requires(postun): /usr/sbin/update-alternatives
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

%prep
%setup -q -n %{tarname}
%patch2 -p1 -b .dont-break-depend
%patch3 -p1 -b .all-defaults
%patch7 -p1 -b .modprobe-default
%patch8 -p1 -b .generate-modprobe.conf-no-defaults
%patch9 -p1 -b .failed-symb
%patch10 -p1 -b .fix_insmod_strrchr

%build
%serverbuild
%configure2_5x --enable-zlib
%make

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall transform=

mv $RPM_BUILD_ROOT/bin/lsmod $RPM_BUILD_ROOT/sbin

pushd $RPM_BUILD_ROOT/sbin && {
for i in %{toalternate};do
	mv $i $i-25
done
} && popd

rm -rf $RPM_BUILD_ROOT/%{_mandir}
for n in 5 8;do
	install -d $RPM_BUILD_ROOT/%{_mandir}/man$n/
	for i in *.$n;do
		[[ $n == 8 ]] && ext="-25" || ext=""
		install -m644 $i $RPM_BUILD_ROOT/%{_mandir}/man${n}/${i%%.*}${ext}.$n
	done
done

pushd $RPM_BUILD_ROOT/sbin && {
%ifnarch %{ix86}
	mv insmod.static insmod.static-25
%else
	rm -f insmod.static
%endif
} && popd

install -d -m755 $RPM_BUILD_ROOT/etc/
touch $RPM_BUILD_ROOT/etc/modprobe.conf
install -m 644 %{SOURCE5} $RPM_BUILD_ROOT/etc
install -d -m755 $RPM_BUILD_ROOT/etc/modprobe.d/

install -d -m755 $RPM_BUILD_ROOT/lib/module-init-tools
install -m 644 %{SOURCE3} $RPM_BUILD_ROOT/lib/module-init-tools
install -m 644 %{SOURCE4} $RPM_BUILD_ROOT/lib/module-init-tools

%post
for i in %{toalternate};do
	update-alternatives --install /sbin/$i $i /sbin/$i-25 %{priority}
	update-alternatives --install \
	%{_mandir}/man8/$i.8%{_extension} man-$i %{_mandir}/man8/$i-25.8%{_extension} %{priority}
	[ -e /sbin/$i ] || update-alternatives --auto $i
	[ -e %{_mandir}/$i.8%{_extension} ] || update-alternatives --auto man-$i
done

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

%postun
for i in %{toalternate};do
	if [ ! -f /sbin/$i-25 ]; then
	  update-alternatives --remove $i /sbin/$i
	fi
	[ -e /sbin/$i ] || update-alternatives --auto $i

	if [ ! -f %{_mandir}/man8/$i-25.8%{_extension} ]; then
	  update-alternatives --remove man-$i %{_mandir}/man8/$i.8%{_extension}
	fi
	[ -e %{_mandir}/man8/$i.8%{_extension} ] || update-alternatives --auto man-$i
done

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS COPYING ChangeLog NEWS README 
%doc TODO stress_modules.sh
%config(noreplace) /etc/modprobe.conf
%config(noreplace) /etc/modprobe.preload
%dir /etc/modprobe.d/
%dir /lib/module-init-tools
/lib/module-init-tools/*
/sbin/generate-modprobe.conf
/sbin/*25
%{_mandir}/*/*


