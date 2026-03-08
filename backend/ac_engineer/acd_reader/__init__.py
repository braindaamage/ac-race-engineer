"""ACD reader — decrypt and extract Assetto Corsa data.acd archives."""

from .reader import AcdResult, read_acd

__all__ = ["read_acd", "AcdResult"]
