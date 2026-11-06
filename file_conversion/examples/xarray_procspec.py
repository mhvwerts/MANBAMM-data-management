"""Read the example ProcSpec files as xarray.DataArray.

Run from anywhere:  python examples/xarray_procspec.py
"""

from pathlib import Path

import matplotlib.pyplot as plt

from manbamm_converters import xrda_from_procspec_file

DATA_DIR = Path(__file__).resolve().parent.parent / "example_data"



ext_spec = xrda_from_procspec_file(Path(DATA_DIR, 
                                  'nanoparticle_light_extinction_cy260403_630_1030nm.ProcSpec'),
                             spectype='absorbance')
ext_spec = ext_spec.sel(wavelength = slice(540, 1000))
fig, ax = plt.subplots(num=1, clear=True)
ext_spec.plot(ax=ax)
ax.set_xlim()


sca_spec = xrda_from_procspec_file(Path(DATA_DIR, 
                                  'nanoparticle_light_scattering_cy260403_630_1030nm.ProcSpec'),
                             spectype='emission')
fig2, ax2 = plt.subplots(num=2, clear=True)
sca_spec.plot(ax=ax2)


plt.show()
