from pathlib import Path

import numpy as np
import pytest

from manbamm_converters import read_procspec

DATA_DIR = Path(__file__).resolve().parent.parent / "example_data"
FILES = sorted(DATA_DIR.glob("*.ProcSpec"))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_read_example_files(path):
    ds = read_procspec(path)
    assert ds["wl"].size > 0
    assert ds["processed"].size == ds["wl"].size
    assert np.all(np.diff(ds["wl"]) > 0)  # wavelength axis increases
    assert ds["metadata"]["timestamp"].endswith("+00:00")
    assert ds["full_xml_metadata"] is None


def test_full_xml_metadata():
    ds = read_procspec(FILES[0], full_xml_metadata=True)
    assert isinstance(ds["full_xml_metadata"], str)


# tests carried out one, inactive for now

# def test_corrupted_file_fails_checksum(tmp_path):
#     import zipfile

#     bad = tmp_path / "bad.ProcSpec"
#     with zipfile.ZipFile(FILES[0]) as src, zipfile.ZipFile(bad, "w") as dst:
#         for info in src.infolist():
#             data = src.read(info.filename)
#             if info.filename.startswith("ps_"):
#                 data = data.replace(b"<double>", b"<double> ", 1)  # tamper
#             dst.writestr(info, data)
#     with pytest.raises(ValueError, match="integrity"):
#         read_procspec(bad)
#     read_procspec(bad, verify_checksum=False)  # bypass works


# def test_not_a_zip(tmp_path):
#     p = tmp_path / "x.ProcSpec"
#     p.write_text("nope")
#     with pytest.raises(Exception):
#         read_procspec(p)
