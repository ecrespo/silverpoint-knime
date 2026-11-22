"""Installs KNIME's Python extension API (``knime-extension``, from the ``knime`` conda channel, where
it is published) into the current environment for the tests: KNIME's own ``knime.extension.testing``
runs ``configure`` and ``execute`` without an Analytics Platform. The bundled extension gets the same
package from pixi (``pixi.toml``); this script is for ``uv`` development and CI only.
"""

from __future__ import annotations

import hashlib
import io
import sys
import sysconfig
import tarfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "5.9.0"
BUILD = "202511131730"
SHA256 = "497b3d9c943441b40bbaf6063dafa166a83c64ed7f9695aa272ba7bfc5813808"
URL = f"https://conda.anaconda.org/knime/noarch/knime-extension-{VERSION}-{BUILD}.conda"


def main() -> int:
    target = Path(sysconfig.get_paths()["purelib"])
    if (target / "knime" / "extension" / "testing.py").is_file() and "--force" not in sys.argv:
        print(f"knime-extension already in {target}")
        return 0
    data = urllib.request.urlopen(URL).read()  # noqa: S310 - a fixed https URL, checked below
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        print(f"digest {digest} is not the pinned {SHA256}")
        return 1
    import zstandard  # the .conda format holds zstd tarballs

    outer = zipfile.ZipFile(io.BytesIO(data))
    inner = next(n for n in outer.namelist() if n.startswith("pkg-") and n.endswith(".tar.zst"))
    raw = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(outer.read(inner))).read()
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for member in tar.getmembers():
            if member.name.startswith("site-packages/") and member.isfile():
                path = target / member.name.removeprefix("site-packages/")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(tar.extractfile(member).read())
    print(f"installed knime-extension {VERSION} into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
