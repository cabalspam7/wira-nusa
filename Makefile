# Wira Nusa — Makefile
# Butuh: Python 3.9+, JDK 8+ (untuk target jar)

.PHONY: all assets stubs test server jar clean

all: assets test

## Generate aset PNG orisinal (paperdoll, mob, latar, tile, UI)
assets:
	python3 tools/gen_assets.py

## Generate stub javax.microedition.* untuk compile tanpa WTK
stubs:
	python3 tools/gen_stubs.py

## Jalankan selftest server (271 cek)
test:
	python3 server/selftest.py

## Jalankan server
server:
	python3 server/app.py --host 0.0.0.0 --port 7777 --db data/wira.db

## Build client jar (perlu JDK + stubs + assets)
jar: stubs assets
	cd client && ./build.sh

## Hapus file generate (assets/, client/stubs/, client/dist/)
clean:
	rm -rf assets/bg assets/c assets/mob assets/tile assets/ui assets/weapon
	rm -f assets/icon.png assets/manifest.txt
	rm -rf client/stubs client/dist
