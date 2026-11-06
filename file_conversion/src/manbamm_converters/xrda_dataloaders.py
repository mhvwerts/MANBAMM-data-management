import numpy as np
import xarray as xr
from pathlib import Path

from .read_procspec_consensus import read_procspec

SPECATTRS = {
    "absorbance": {"name": "OD", "long_name": "optical density", "units": ""},
    "emission":   {"name": "intensity", "long_name": "intensity", "units": "a.u."},
}


def xrda_from_procspec_file(fn, spectype="absorbance", verify_checksum=True):
    if spectype not in SPECATTRS:
        raise ValueError(f"spectype must be one of {list(SPECATTRS)}, got {spectype!r}")

    dat = read_procspec(fn, verify_checksum=verify_checksum)

    if not dat["processed"].size:
        raise ValueError(
            f"{fn}: file is missing a processed spectrum, which is required"\
            " for good spectroscopic practice."
        )
    values = dat["processed"]

    spec = dict(SPECATTRS[spectype])
    name = spec.pop("name")

    # drop None values for netCDF compatibility
    meta = {k: v for k, v in dat["metadata"].items() if v is not None}

    da = xr.DataArray(
        data=values,
        dims=["wavelength"],
        coords={
            "wavelength": ("wavelength", dat["wl"],
                           {"units": "nm", "long_name": "wavelength"}),
            # scalar coordinate: becomes a real dimension when concatenating
            "time": np.datetime64(meta["millitime_stamp"], "ms"), 
        },
        name=name,
        attrs={**spec, **meta, "source_file": Path(fn).name},
    )
    return da

