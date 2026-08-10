#!/usr/bin/env bash
# Build jar MIDlet WIRA NUSA.
#
#   ./build.sh              -> pakai stub (cepat, tanpa WTK)
#   WTK=/path/WTK2.5.2 ./build.sh   -> pakai midpapi + preverify asli
#
# Hasil: dist/WiraNusa.jar dan dist/WiraNusa.jad
#
# Catatan jujur: jar ini dibangun di komputer kamu, bukan di tempat
# skrip ini ditulis. Kalau javac protes, baca pesan errornya -- semua
# kode sengaja dibatasi ke gaya CLDC 1.0 (tanpa float, generics,
# enum, foreach, StringBuilder) supaya lolos di JDK 8 dan preverify.

set -euo pipefail

AKAR="$(cd "$(dirname "$0")" && pwd)"
cd "$AKAR"

NAMA="WiraNusa"
VERSI="1.0.0"
MIDLET="Main"
ASET="../assets"
OUT="build"
DIST="dist"

rm -rf "$OUT" "$DIST"
mkdir -p "$OUT/kelas" "$OUT/stub" "$OUT/jar" "$DIST"

# --- pilih javac --------------------------------------------------------
if ! command -v javac >/dev/null 2>&1; then
  echo "javac tidak ditemukan. Pasang JDK 8 (atau JDK 17+ dengan --release 8)."
  exit 1
fi

VERSI_JAVAC="$(javac -version 2>&1 | sed -E 's/javac ([0-9]+).*/\1/')"
OPSI_TARGET=""
if [ "${VERSI_JAVAC}" = "1" ]; then
  OPSI_TARGET="-source 1.4 -target 1.4"          # JDK 8 lama: 1.4 masih ada
else
  OPSI_TARGET="--release 8"
  echo "catatan: memakai --release 8. Untuk HP asli, preverify tetap disarankan."
fi

# --- kompilasi ----------------------------------------------------------
if [ -n "${WTK:-}" ] && [ -f "$WTK/lib/midpapi20.jar" ]; then
  echo "pakai API asli dari $WTK"
  BOOT="$WTK/lib/cldcapi10.jar:$WTK/lib/midpapi20.jar"
  javac $OPSI_TARGET -bootclasspath "$BOOT" -d "$OUT/kelas" src/*.java
else
  echo "pakai stub javax.microedition (hanya untuk kompilasi)"
  javac $OPSI_TARGET -nowarn -d "$OUT/stub" \
      $(find stubs -name '*.java')
  javac $OPSI_TARGET -nowarn -cp "$OUT/stub" -d "$OUT/kelas" src/*.java
fi

# --- preverify (opsional tapi wajib untuk HP sungguhan) -----------------
ISI_JAR="$OUT/kelas"
if [ -n "${WTK:-}" ] && [ -x "$WTK/bin/preverify" ]; then
  echo "preverify..."
  mkdir -p "$OUT/verif"
  "$WTK/bin/preverify" -classpath "$WTK/lib/cldcapi10.jar:$WTK/lib/midpapi20.jar" \
      -d "$OUT/verif" "$OUT/kelas"
  ISI_JAR="$OUT/verif"
else
  echo "lewati preverify (tidak ada WTK). Emulator modern seperti FreeJ2ME,"
  echo "KEmulator, dan J2ME Loader umumnya tetap mau menjalankan jar ini."
fi

# --- susun isi jar ------------------------------------------------------
cp -r "$ISI_JAR"/*.class "$OUT/jar/"
if [ -d "$ASET" ]; then
  cp -r "$ASET"/* "$OUT/jar/"
else
  echo "PERINGATAN: folder aset tidak ada. Jalankan dulu:"
  echo "  python3 ../tools/gen_assets.py"
fi
mkdir -p "$OUT/jar/META-INF"
sed -e "s/@VERSI@/$VERSI/g" MANIFEST.MF > "$OUT/jar/META-INF/MANIFEST.MF"

# --- bungkus jar --------------------------------------------------------
if command -v jar >/dev/null 2>&1; then
  (cd "$OUT/jar" && jar cfm "../../$DIST/$NAMA.jar" META-INF/MANIFEST.MF .)
else
  (cd "$OUT/jar" && zip -qr "../../$DIST/$NAMA.jar" .)
fi

UKURAN=$(wc -c < "$DIST/$NAMA.jar")
sed -e "s/@VERSI@/$VERSI/g" -e "s/@UKURAN@/$UKURAN/g" \
    -e "s/@NAMAJAR@/$NAMA.jar/g" WiraNusa.jad.in > "$DIST/$NAMA.jad"

echo
echo "selesai: $DIST/$NAMA.jar ($UKURAN byte)"
echo "         $DIST/$NAMA.jad"
echo "BUILD_OK"
