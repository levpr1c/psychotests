# Maintainer: <your-email>
# Contributor: <your-name>

pkgname=psychotests-bin
pkgver=1.0.0
pkgrel=1
pkgdesc="TUI psychological testing application (9 tests)"
arch=('x86_64')
url="https://github.com/<user>/psychotests"
license=('custom:WTFPL')
depends=()
makedepends=('python' 'python-pip' 'python-pyinstaller')
source=("$pkgname-$pkgver.tar.gz::https://github.com/<user>/psychotests/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$srcdir/psychotests-$pkgver"
  python -m venv _build_venv
  source _build_venv/bin/activate
  pip install --no-input -r requirements.txt pyinstaller
  pyinstaller --onefile \
    --add-data "src/app.tcss:src/" \
    --add-data "src/data:src/data" \
    --name psychotests \
    run.py
  deactivate
}

package() {
  install -Dm755 "$srcdir/psychotests-$pkgver/dist/psychotests" \
    "$pkgdir/usr/bin/psychotests"
}
