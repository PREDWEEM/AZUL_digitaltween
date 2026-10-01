"""Cierre inclusivo de la campaña en el gemelo."""
import pandas as pd
import pytest
from predweem_twin.weather import operational_weather_window

@pytest.mark.parametrize("year", [2026, 2027])
@pytest.mark.parametrize("cutoff,expected", [("09-28", 3), ("10-01", 0), ("10-10", 0)])
def test_twin_horizon_stops_at_campaign_end(year, cutoff, expected):
    frame = pd.DataFrame({"Fecha": pd.date_range(f"{year}-09-25", f"{year}-10-10")})
    window, meta = operational_weather_window(frame, as_of=f"{year}-{cutoff}")
    assert window.Fecha.max() == pd.Timestamp(f"{year}-10-01")
    assert meta["campaign_year"] == year
    assert meta["forecast_days_expected"] == expected
    assert meta["forecast_days_available"] == expected
    assert meta["complete"]
