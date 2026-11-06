"""MANBAMM converters: read proprietary instrument file formats into open formats."""

from .read_procspec_consensus import read_procspec
from .xrda_dataloaders import xrda_from_procspec_file

__all__ = ["read_procspec",
           "xrda_from_procspec_file"]

__version__ = "0.1.1"
__author__ = "Martinus H. V. Werts"
__email__ = "martinus.werts@univ-angers.fr"
__copyright__ = "Copyright 2026, The Authors"
__license__ = "CECILL-C"
