# manbamm-converters

Convert proprietary scientific instrument file formats into open formats.

> **Status:** early development ("alpha").

Data files written by many scientific instruments (e.g. spectrometers) cannot be read directly by analysis software, because they use vendor-specific formats that are rarely documented. To keep open scientific data accessible in the long term, such files need to be converted to open formats (CSV, HDF5, TIFF, …).

Over the years we have developed several Python "file loaders" for instrument data. This package collects them, after careful checking and clean-up, so they can be used to read, or batch-convert, instrument files into plain Python / NumPy objects that are easy to save in an open format.


## Supported (and planned) formats

| Instrument / vendor | Format | Function | Status |
|---|---|---|---|
| OceanOptics (SpectraSuite) | `.ProcSpec` | [`read_procspec`](./src/manbamm_converters/read_procspec_consensus.py) | available |
| Avantes | `.RAW8`, `.RWD8` | – | future possibility |
| Shimadzu HPLC | – | – | future possibility |

## Installation

Requires Python ≥ 3.9. The only runtime dependency is NumPy.

Currently, install from a local copy of [MANBAMM-data-management](https://github.com/mhvwerts/MANBAMM-data-management), using a development (i.e., an "editable") installation:

```bash
# run from the root of the local repo
pip install -e ./file_conversion      # path to folder with pyproject.toml
```

or

```bash
# run from the the `./file_conversion` directory
pip install -e .
```




## Quick start

```python
from manbamm_converters import read_procspec

ds = read_procspec("example_data/nanoparticle_light_extinction_cy260403_630_1030nm.ProcSpec")

ds["wl"]          # wavelength axis (nm), numpy array
ds["processed"]   # processed spectrum, numpy array
ds["metadata"]    # dict: author, timestamp (ISO 8601, UTC), spectrometer model/serial,
                  #       integration time, number of averages, boxcar width, saturation flag
```

`read_procspec` returns a dictionary with the keys `wl`, `dark`, `bright`, `scope`, `processed`, `metadata` and `full_xml_metadata`. Spectra that are absent from the file are returned as empty arrays. See `help(read_procspec)` for the full description.

By default the integrity checksum stored in the file by the spectrometer is verified, and a `ValueError` is raised if the file was modified. Use `verify_checksum=False` to bypass this.

### Example: Converting to CSV

```python
import numpy as np
from manbamm_converters import read_procspec

ds = read_procspec("my_spectrum.ProcSpec")
np.savetxt(
    "my_spectrum.csv",
    np.column_stack([ds["wl"], ds["processed"]]),
    delimiter=",",
    header="wavelength_nm,processed",
    comments="",
)
```

### Example: Loading and plotting of ProcSpec files

A runnable example that plots the two files in `example_data/` is in [`examples/plot_procspec.py`](./examples/plot_procspec.py).



## Code origins

### ProcSpec reader

A ProcSpec file is a ZIP archive holding a `ps_<digits>.xml` data file and an `OOISignatures.xml` file with a hash of the data file. The reader is inspired by [`lightr`](https://github.com/ropensci/lightr)'s `lr_parse_oceanoptics_procspec` and by an older in-house Python loader of ProcSpec files. Consensus between the codes was established with the aid of LLMs and the result was tested on real ProcSpec files.


## License

Released under the [CeCILL-C](https://cecill.info/licences/Licence_CeCILL-C_V1-en.html) free software license; see [`LICENSE`](./LICENSE).
