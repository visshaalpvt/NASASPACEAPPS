"""
Advisory Engine Module for KisanRadar.
Generates empirical, actionable adaptation advisories in 6 South Asian languages.
Evidence base: ICAR-NICRA, IRRI, IPCC AR6.
"""
from app.advisory.engine import generate_advisory

__all__ = ["generate_advisory"]
