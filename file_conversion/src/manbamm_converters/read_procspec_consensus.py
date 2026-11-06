"""Read OceanOptics ProcSpec files

A ProcSpec file is a ZIP archive containing one ``ps_<digits>.xml`` data file
and an ``OOISignatures.xml`` file holding a hash of the data file (plus one
more auxiliary file; the archive normally holds exactly 3 files).


- Inspired by lightr's `lr_parse_oceanoptics_procspec`
  (https://github.com/ropensci/lightr)
  and an older home-grown ProcSpec loader in Python.
- Consensus between the different codes was established.
- Coding assisted by LLM
- Tweaked and tested using real ProcSpec files
"""

import copy
import hashlib
import re
import warnings
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta, timezone

import numpy as np

ROOT_TAG = "com.oceanoptics.spectrasuite.processors.ProcessedSpectrum"
EXPECTED_N_FILES = 3

# Characters that are illegal in XML 1.0: all C0 control characters except
# tab (\x09), line feed (\x0a) and carriage return (\x0d). The OceanOptics
# software is known to leave such stray characters in its XML (e.g. \x01 and
# \x10), which make the file unparseable.
_XML_ILLEGAL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _doubles(nodes):
    """Collect all <double> descendants of the given nodes as a float array."""
    return np.array(
        [float(d.text) for n in nodes for d in n.iterfind(".//double")],
        dtype=float,
    )


def _texts(nodes, tag):
    """Text of the first <tag> descendant of each node (None if absent)."""
    out = []
    for n in nodes:
        el = n.find(f".//{tag}")
        out.append(el.text.strip() if el is not None and el.text else None)
    return out


def _real_nodes(nodes):
    """Drop XStream back-reference nodes (``<x reference="../.."/>``).

    These are empty pointers to an earlier node and carry no data.
    """
    return [n for n in nodes if "reference" not in n.attrib]


def _first_text(root, tag):
    el = root.find(f".//{tag}")
    return el.text.strip() if el is not None and el.text else None


def _scope_saturated(root):
    """Saturation flag of the scope spectrum, as True / False.

    The search is restricted to the ``sourceSpectra`` node, because the dark
    and reference spectra carry their own ``saturated`` flags. Returns None
    if the flag is absent or has an unrecognised value.
    """
    src = root.find(".//sourceSpectra")
    text = _first_text(src, "saturated") if src is not None else None
    return {"true": True, "false": False}.get(text.lower()) if text else None


def _get_wavelengths(root, expected_n):
    """Get the wavelength axis, checking that it has ``expected_n`` points.

    Primary method: concatenate the doubles of all
    ``channelWavelengths`` nodes.
    Fallback: use only the last non-empty ``channelWavelengths``
    node. Raises ``ValueError`` if neither gives the expected length.
    """
    nodes = root.findall(".//channelWavelengths")
    wl = _doubles(nodes)
    if wl.size == expected_n:
        return wl

    nonempty = [n for n in nodes if n.find(".//double") is not None]
    if nonempty:
        wl_fallback = _doubles([nonempty[-1]])
        if wl_fallback.size == expected_n:
            warnings.warn(
                f"Concatenating all channelWavelengths nodes gave {wl.size} "
                f"points instead of {expected_n}; using the last non-empty "
                "channelWavelengths node instead."
            )
            return wl_fallback
        raise ValueError(
            f"Cannot determine wavelengths: expected {expected_n} points, "
            f"but got {wl.size} (all nodes) and {wl_fallback.size} "
            "(last non-empty node)."
        )
    raise ValueError(
        f"Cannot determine wavelengths: expected {expected_n} points, "
        "but no non-empty channelWavelengths node was found."
    )


def _acquisition_millitime(root):
    """milliTime of the first ``acquisitionTime`` element.

    The first acquisitionTime in the file holds the actual spectrum
    acquisition time; later ones belong to the dark and reference spectra.
    """
    acq = root.find(".//acquisitionTime")
    if acq is None:
        raise ValueError("No acquisitionTime element found in ProcSpec file.")
    text = _first_text(acq, "milliTime")
    if text is None:
        raise ValueError("No milliTime found in first acquisitionTime element.")
    return int(float(text))


def _xml_metadata(root):
    """Return the XML as a string with all numerical data removed.

    All ``<double>`` elements are dropped, keeping only the file structure and
    the non-numeric metadata tags (a safety net in case relevant metadata was
    not decoded explicitly). The input tree is not modified.
    """
    root = copy.deepcopy(root)
    for elem in list(root.iter()):
        for child in elem.findall("double"):
            elem.remove(child)
    return ET.tostring(root, encoding="unicode")


def read_procspec(filename, verify_checksum=True,
                               full_xml_metadata=False):
    """Read an OceanOptics ProcSpec file.

    Parameters
    ----------
    filename : str or path-like
        Path to the ``.ProcSpec`` file.
    verify_checksum : bool, default True
        Check whether the file was modified since its creation by the
        spectrometer. Raises ``ValueError`` if the check fails.
    full_xml_metadata : bool, default False
        If True, also return the full XML with all numerical data removed
        (a safety net in case relevant metadata was not decoded explicitly).

    Returns
    -------
    dict with keys

    wl, dark, bright, scope, processed : numpy.ndarray
        Wavelength axis (nm) and the dark, bright (reference), scope and
        processed spectra.
        Spectra that are absent from the file are empty arrays.
    metadata : dict
        Author, timestamp (ISO 8601, UTC) and its raw value in Java
        milliseconds (``millitime_stamp``), spectrometer model / serial
        number, and, for the dark, bright (reference) and scope spectra, the
        integration time (``*_inttime_ms``), number of scans averaged
        (``*_Navg``) and boxcar width in pixels (``*_boxcar_Npx``).
        In addition, ``scope_saturated`` is the spectrometer's own saturation
        flag for the scope spectrum (True / False; None if absent). Values
        are ``None`` for absent spectra, or lists if the file holds several
        nodes of a kind.
    full_xml_metadata : str or None
        The XML with all numerical data removed if ``full_xml_metadata=True``
        was requested, otherwise ``None``.

    Raises
    ------
    ValueError
        If the archive does not contain exactly 3 files, the data file is
        missing, the root XML node is unexpected, the checksum fails, or the
        wavelength axis cannot be matched to the spectra.

    Notes
    -----
    The text of the data file is cleaned before XML parsing: it is decoded as
    cp1252 and all control characters that are illegal in XML are removed.
    """
    with zipfile.ZipFile(filename) as zf:
        names = zf.namelist()

        if len(names) != EXPECTED_N_FILES:
            raise ValueError(
                f"Unexpected ProcSpec container: {len(names)} files "
                f"instead of {EXPECTED_N_FILES}: {names}"
            )

        # Each ProcSpec archive contains a single data file named ps_<digits>.xml
        data_name = next((n for n in names if re.search(r"ps_\d+\.xml", n)), None)
        if data_name is None:
            raise ValueError(f"No ps_<digits>.xml data file found in {names}")
        raw = zf.read(data_name)

        if verify_checksum:
            sig_name = next(
                (n for n in names if n.endswith("OOISignatures.xml")), None
            )
            if sig_name is None:
                warnings.warn("No OOISignatures.xml found. Skipping integrity check.")
            else:
                sig = ET.fromstring(zf.read(sig_name))
                saved_hash = _first_text(sig, "hashValue").replace(" ", "")
                algo = _first_text(sig, "hashAlgorithm")
                if algo == "SHA-512":
                    actual_hash = hashlib.sha512(raw).hexdigest()
                else:
                    warnings.warn(
                        f"Unsupported hash algorithm ({algo}) in signature. "
                        "Skipping integrity check."
                    )
                    actual_hash = saved_hash
                if actual_hash.lower() != saved_hash.lower():
                    raise ValueError(
                        "The file integrity check failed and the data may be "
                        "corrupted\nTo bypass this error, use "
                        "`verify_checksum=False`."
                    )

    # OceanOptics software writes cp1252-encoded text (e.g. micro or degree
    # signs in text fields), so decode as cp1252. Bytes undefined in cp1252
    # are replaced rather than raising. The software also leaves stray control
    # characters (seen: \x01, \x10), which are illegal in XML: remove all
    # XML-illegal control characters before parsing.
    text = _XML_ILLEGAL_CHARS.sub("", raw.decode("cp1252", errors="replace"))
    root = ET.fromstring(text)

    if root.tag != ROOT_TAG:
        raise ValueError(
            f"Unexpected root node '{root.tag}' (expected '{ROOT_TAG}')."
        )

    # Scope spectrum (first match only, which is probably the only one)
    scope_node = root.find(".//pixelValues")
    scope = _doubles([scope_node]) if scope_node is not None else np.array([])
    # The raw integration time is in microseconds; store it in milliseconds.
    scope_inttime = float(_first_text(root, "integrationTime")) / 1000
    scope_average = _first_text(root, "scansToAverage")
    scope_boxcar = _first_text(root, "boxcarWidth")

    # Bright reference spectrum
    bright_nodes = _real_nodes(root.findall(".//referenceSpectrum"))
    bright = _doubles(bright_nodes)
    bright_inttime = [
        float(x) / 1000 for x in _texts(bright_nodes, "integrationTime") if x
    ]
    bright_average = _texts(bright_nodes, "scansToAverage")
    bright_boxcar = _texts(bright_nodes, "boxcarWidth")

    # Dark spectrum
    dark_nodes = _real_nodes(root.findall(".//darkSpectrum"))
    dark = _doubles(dark_nodes)
    dark_inttime = [
        float(x) / 1000 for x in _texts(dark_nodes, "integrationTime") if x
    ]
    dark_average = _texts(dark_nodes, "scansToAverage")
    dark_boxcar = _texts(dark_nodes, "boxcarWidth")

    # Processed spectrum
    processed = _doubles(root.findall(".//processedPixels"))

    # Wavelengths, checked against the processed spectrum (or the scope
    # spectrum for files lacking a processed one)
    expected_n = processed.size if processed.size else scope.size
    if expected_n == 0:
        raise ValueError("No processed or scope spectrum found in file.")
    wl = _get_wavelengths(root, expected_n)

    # Metadata
    author = _first_text(root, "userName")
    millitime = _acquisition_millitime(root)
    # Add whole milliseconds to the epoch (avoids float rounding noise from
    # dividing by 1000). The source resolution is 1 ms.
    timestamp = (
        datetime(1970, 1, 1, tzinfo=timezone.utc)
        + timedelta(milliseconds=millitime)
    ).isoformat(timespec="milliseconds")
    specclass = _first_text(root, "spectrometerClass")
    m = re.search(r"\.([A-Za-z0-9]+)$", specclass or "")
    specmodel = m.group(1) if m else specclass
    spec_id = _first_text(root, "spectrometerSerialNumber")

    def one(x):  # unwrap single-element lists; None if elements are absent
        if len(x) == 0:
            return None
        return x[0] if len(x) == 1 else x

    def one_int(x):  # like one(), but convert the values to ints
        v = one(x)
        if v is None:
            return None
        if isinstance(v, list):
            return [int(i) if i is not None else None for i in v]
        return int(v)

    metadata = {
        "author": author,
        "timestamp": timestamp,
        "millitime_stamp": millitime,
        "spectrometer_model": specmodel,
        "spectrometer_serial": spec_id,
        "dark_inttime_ms": one(dark_inttime),
        "bright_inttime_ms": one(bright_inttime),
        "scope_inttime_ms": scope_inttime,
        "scope_saturated": _scope_saturated(root),
        "dark_Navg": one_int(dark_average),
        "bright_Navg": one_int(bright_average),
        "scope_Navg": one_int([scope_average]) if scope_average else None,
        "dark_boxcar_Npx": one_int(dark_boxcar),
        "bright_boxcar_Npx": one_int(bright_boxcar),
        "scope_boxcar_Npx": one_int([scope_boxcar]) if scope_boxcar else None,
    }

    return {
        "wl": wl,
        "dark": dark,
        "bright": bright,
        "scope": scope,
        "processed": processed,
        "metadata": metadata,
        "full_xml_metadata": _xml_metadata(root) if full_xml_metadata else None
    }
