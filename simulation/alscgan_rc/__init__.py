"""Composition-spread Al-Sc-Ga-N pads as physical reservoirs (simulation)."""

from . import arrays, benchmarks, device, materials, reservoir  # noqa: F401
from .arrays import PadArray  # noqa: F401
from .device import SegmentedFilm  # noqa: F401
from .materials import BOWED, DEFAULT, MaterialModel  # noqa: F401
from .reservoir import EchoStateNetwork, MultiplexedReservoir  # noqa: F401

__all__ = ["materials", "device", "reservoir", "benchmarks", "arrays",
           "SegmentedFilm", "MaterialModel", "DEFAULT", "BOWED",
           "MultiplexedReservoir", "EchoStateNetwork", "PadArray"]
