"""Read the example ProcSpec files and plot their processed spectra.

Run from anywhere:  python examples/plot_procspec.py
Requires matplotlib
"""

from pathlib import Path

import matplotlib.pyplot as plt

from manbamm_converters import read_procspec

DATA_DIR = Path(__file__).resolve().parent.parent / "example_data"

for path in sorted(DATA_DIR.glob("*.ProcSpec")):
    ds = read_procspec(path)
    print(f"\n{path.name}\n{ds['metadata']}")

    plt.figure()
    plt.plot(ds["wl"], ds["processed"])
    plt.xlim(630, 1030)
    plt.ylim(bottom=0)
    plt.xlabel("wavelength / nm")
    plt.title(path.name, fontsize=8)

plt.show()
