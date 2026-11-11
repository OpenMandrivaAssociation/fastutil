Name:		fastutil
Version:	8.5.19
Release:	2
Summary:	Type-specific Java collections
Group:		Development/Java
License:	ASL 2.0
URL:		https://fastutil.di.unimi.it/
Source0:	https://github.com/vigna/fastutil/archive/refs/tags/%{version}.tar.gz#/fastutil-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 8.5.2. The junit, hamcrest, and bnd jars are
# not in this archive.
Source1:	https://github.com/vigna/fastutil/archive/refs/tags/8.5.2.tar.gz#/fastutil-8.5.2.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	make
BuildRequires:	clang
BuildRequires:	ant
BuildRequires:	sysjar

%description
fastutil provides type-specific maps, sets, lists and queues with a
small memory footprint. Gradle 8.11.1 calls ReferenceArrayList and
ReferenceOpenHashSet from it.unimi.dsi:fastutil. %{version} stays
the default jar. Gradle 9.9.1 strictly pins 8.5.2, so that jar is
installed beside it.

%prep
%autosetup -n fastutil-%{version}
%setup -q -T -D -a 1 -n fastutil-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

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
(
	cd fastutil-8.5.2
	make %{?_smp_mflags} sources
	ant -noinput jar
)
cat > fastutil-8.5.2/fastutil-8.5.2.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>it.unimi.dsi</groupId>
  <artifactId>fastutil</artifactId>
  <version>8.5.2</version>
  <name>fastutil</name>
  <description>Type-specific Java collections.</description>
  <url>https://fastutil.di.unimi.it/</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact fastutil-8.5.2/fastutil-8.5.2.pom:fastutil-8.5.2/fastutil-8.5.2.jar \
	--file-name fastutil-8.5.2 \
	--filelist .mfiles852
# %{version} owns fastutil.sysjar. 8.5.2 keeps a second index file.
/bin/mv %{buildroot}/usr/share/sysjar/index/it.unimi.dsi/fastutil.sysjar \
	%{buildroot}/usr/share/sysjar/index/it.unimi.dsi/fastutil-8.5.2.sysjar
sed -i 's|/usr/share/sysjar/index/it.unimi.dsi/fastutil\.sysjar|/usr/share/sysjar/index/it.unimi.dsi/fastutil-8.5.2.sysjar|' .mfiles852
sysjar install --buildroot %{buildroot} \
	--artifact pom.xml:fastutil-%{version}.jar \
	--file-name fastutil \
	--filelist .mfiles
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles852

%check
export JAVA_HOME="${JAVA_HOME:-%{_jvmdir}/java-openjdk}"
export PATH="$JAVA_HOME/bin:$PATH"
cat > FuSmoke.java << 'EOF'
import it.unimi.dsi.fastutil.objects.ReferenceArrayList;
import it.unimi.dsi.fastutil.objects.ReferenceOpenHashSet;
public class FuSmoke {
	public static void main(String[] args) {
		ReferenceArrayList<String> list = new ReferenceArrayList<String>();
		list.add("ok");
		ReferenceOpenHashSet<String> set = new ReferenceOpenHashSet<String>();
		set.add(list.get(0));
		if (list.size() != 1 || !set.contains("ok")) {
			throw new AssertionError(list.size());
		}
		System.out.println(args[0] + " " + list.get(0) + " " + set.size());
	}
}
EOF
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp fastutil-%{version}.jar -d . FuSmoke.java
java -cp ".:fastutil-%{version}.jar" FuSmoke fastutil819_ok > check819.log
cat check819.log
grep -F -q 'fastutil819_ok ok 1' check819.log
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp fastutil-8.5.2/fastutil-8.5.2.jar -d . FuSmoke.java
java -cp ".:fastutil-8.5.2/fastutil-8.5.2.jar" FuSmoke fastutil852_ok > check852.log
cat check852.log
grep -F -q 'fastutil852_ok ok 1' check852.log

%files -f .mfiles
%doc LICENSE-2.0 README.md
