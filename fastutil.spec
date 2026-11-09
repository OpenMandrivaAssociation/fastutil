Name:		fastutil
Version:	8.5.19
Release:	1
Summary:	Type-specific Java collections
Group:		Development/Java
License:	ASL 2.0
URL:		https://fastutil.di.unimi.it/
Source0:	https://github.com/vigna/fastutil/archive/refs/tags/%{version}.tar.gz#/fastutil-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	make
BuildRequires:	clang
BuildRequires:	ant
BuildRequires:	sysjar

%description
fastutil provides type-specific maps, sets, lists and queues with a
small memory footprint. Gradle 8.11.1 calls ReferenceArrayList and
ReferenceOpenHashSet from it.unimi.dsi:fastutil.

%prep
%autosetup -n fastutil-%{version}

%build
# Drivers under drv/ expand through the C preprocessor. The Ant jar
# target compiles those sources. The OSGi targets need a vendored bnd
# jar, and this package does not run them.
make %{?_smp_mflags} sources
ant -noinput jar pom
python - <<'PY'
import xml.etree.ElementTree as ET

def local(tag):
    return tag.rsplit("}", 1)[-1]

tree = ET.parse("pom.xml")
root = tree.getroot()
for child in list(root):
    if local(child.tag) == "dependencies":
        root.remove(child)
tree.write("pom.xml", xml_declaration=True, encoding="unicode")
PY

%install
sysjar install --buildroot %{buildroot} \
	--artifact pom.xml:fastutil-%{version}.jar \
	--file-name fastutil \
	--filelist .mfiles

%files -f .mfiles
%doc LICENSE-2.0 README.md
