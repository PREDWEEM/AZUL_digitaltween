"""Campañas operativas de Azul; la referencia histórica sigue siendo 2026."""

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CAMPAIGN_YEARS = (2026, 2027)


def campaign_bounds(year: int) -> tuple[date, date]:
    if year not in CAMPAIGN_YEARS:
        raise ValueError(f"Campaña {year} no habilitada. Seleccione 2026 o 2027.")
    return date(year, 1, 1), date(year, 10, 1)


def default_campaign_year(today: date | None = None) -> int:
    today = today or datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    return min(max(today.year, CAMPAIGN_YEARS[0]), CAMPAIGN_YEARS[-1])


def campaign_weather_path(year: int) -> Path:
    campaign_bounds(year)
    return Path("meteo_daily.csv") if year == 2026 else Path("data/meteo_2027.csv")
