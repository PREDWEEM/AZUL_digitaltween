"""Preparación de 2027; las series desplazadas aquí son sólo fixtures de prueba."""

from datetime import date, datetime
from pathlib import Path
import shutil

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import actualizar_clima as clima
from campaign import campaign_weather_path, default_campaign_year
from predweem_twin.seasonal import load_local_seasonal_reference
from predweem_twin.storage import TwinStore
from predweem_twin.weather import fetch_open_meteo, read_weather_file

ROOT = Path(__file__).parents[1]


def test_default_waits_for_2027_and_keeps_separate_files():
    assert default_campaign_year(date(2026, 12, 31)) == 2026
    assert default_campaign_year(date(2027, 1, 1)) == 2027
    assert campaign_weather_path(2026) == Path("meteo_daily.csv")
    assert campaign_weather_path(2027) == Path("data/meteo_2027.csv")
    reference = load_local_seasonal_reference(ROOT, as_of="2027-05-05")
    assert reference.N_Campanas.eq(1).all()
    assert reference.Campanas.eq("azul_2026_counts.csv").all()


def test_upload_filters_selected_campaign_without_relabeling_dates(tmp_path):
    path = tmp_path / "both_years.csv"
    pd.DataFrame({"Fecha": ["2026-05-05", "2027-05-05", "2027-10-02"],
                  "Prec": [100., 2., 300.]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="varios años"):
        read_weather_file(path)
    selected = read_weather_file(path, campaign_year=2027)
    assert selected.Fecha.tolist() == ["2027-05-05"]
    assert selected.Prec.tolist() == [2.]
    with pytest.raises(ValueError, match="No hay datos"):
        read_weather_file(ROOT / "meteo_daily.csv", campaign_year=2027)


def test_no_downloads_or_files_before_campaign_begins(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in ("FECHA_INICIO", "FECHA_FIN", "ARCHIVO_CSV"):
        monkeypatch.setattr(clima, name, getattr(clima, name))
    clima.configure_campaign(2027)
    monkeypatch.setattr(clima, "_ahora_local", lambda: datetime(2026, 10, 1, 12))

    def forbidden(*args, **kwargs):
        raise AssertionError("No debe descargar datos de una campaña futura")

    monkeypatch.setattr(clima, "_resolver_corte_reanalisis", forbidden)
    with pytest.raises(ValueError, match="aún no comenzó"):
        clima.actualizar_meteorologia()
    assert not (tmp_path / "data/meteo_2027.csv").exists()
    import predweem_twin.weather as weather
    monkeypatch.setattr(weather, "_today_argentina", lambda: date(2026, 10, 1))
    monkeypatch.setattr(weather.requests, "get", forbidden)
    with pytest.raises(ValueError, match="aún no comenzó"):
        fetch_open_meteo(-36.87, -59.89, "2027-01-01")


@pytest.mark.parametrize("today", [date(2027, 1, 1), date(2027, 9, 28), date(2027, 10, 2)])
def test_updater_writes_2027_only_and_respects_october_cutoff(monkeypatch, tmp_path, today):
    from test_actualizar_clima import bloque
    from datetime import timedelta
    monkeypatch.chdir(tmp_path)
    original = b"2026 archived meteorology\n"
    (tmp_path / "meteo_daily.csv").write_bytes(original)
    for name in ("FECHA_INICIO", "FECHA_FIN", "ARCHIVO_CSV"):
        monkeypatch.setattr(clima, name, getattr(clima, name))
    clima.configure_campaign(2027)
    monkeypatch.setattr(clima, "_ahora_local", lambda: datetime.combine(today, datetime.min.time()))
    # Exercise the real resolver at campaign start, when no reanalysis exists yet.
    monkeypatch.setattr(clima, "_ultimo_dia_completo_modelo", lambda model, target: target)
    monkeypatch.setattr(clima, "_descargar_historico_modelo",
                        lambda first, last, **kw: bloque(first, last, kw["tipo"]))
    monkeypatch.setattr(clima, "_consultar_diario",
                        lambda *args, **kw: bloque(today, today + timedelta(days=7), "PRONOSTICO"))
    result = clima.actualizar_meteorologia()
    final = min(today + timedelta(days=7), date(2027, 10, 1))
    assert result.Fecha.tolist() == pd.date_range("2027-01-01", final).strftime("%Y-%m-%d").tolist()
    assert (tmp_path / "data/meteo_2027.csv").exists()
    assert (tmp_path / "meteo_daily.csv").read_bytes() == original


def test_app_requires_new_weather_and_keeps_2026_as_history(tmp_path):
    for name in ("app.py", "campaign.py", "meteo_daily.csv"):
        shutil.copy2(ROOT / name, tmp_path / name)
    for directory in ("models", "predweem_twin", "data"):
        shutil.copytree(ROOT / directory, tmp_path / directory,
                        ignore=shutil.ignore_patterns("*.db*", "__pycache__"))
    historical = tmp_path / "data/calibration/azul_2026_counts.csv"
    original_counts = historical.read_bytes()
    original_weather = (tmp_path / "meteo_daily.csv").read_bytes()
    app = AppTest.from_file(str(tmp_path / "app.py"), default_timeout=45)
    app.session_state["campaign_year"] = 2026
    app.run()
    assert not app.exception
    app.selectbox(key="campaign_year").set_value(2027).run()
    assert not app.exception and not app.error
    assert any("Todavía no hay meteorología de 2027" in item.value for item in app.info)
    assert len(app.metric) == 0

    # Test fixture only: never persisted to the repository or used as a forecast.
    fixture = pd.read_csv(ROOT / "data/calibration/azul_2026_weather.csv", parse_dates=["Fecha"])
    fixture["Fecha"] += pd.DateOffset(years=1)
    fixture.to_csv(tmp_path / "data/meteo_2027.csv", index=False)
    store = TwinStore(tmp_path / "data/twin_state.db")
    store.upsert_observation("Azul-01", "2026-03-20", .9, .1)
    store.upsert_coverage_observations("Azul-01", pd.DataFrame({
        "Fecha": pd.to_datetime(["2026-03-20"]), "Cobertura_PCT": [90.]}))
    app.run()
    assert not app.exception and not app.error
    app.date_input[0].set_value(date(2027, 3, 30)).run()
    assert not app.exception and not app.error
    next(item for item in app.radio if item.label == "Cobertura de rastrojo").set_value("Serie observada").run()
    assert not app.exception and not app.error
    assert any("Referencia local Azul 2026" in item.value and "1 campaña" in item.value
               for item in app.caption)
    audit = next(item.value for item in app.dataframe if "Variable" in item.value.columns)
    values = audit.set_index("Variable")["Valor"]
    assert values["Corte meteorológico"] == "30/03/2027"
    assert values["Observaciones asimiladas"] == "0"
    assert values["Cobertura"] == "Constante 10 %"
    metrics = {item.label: item.value for item in app.metric}
    assert metrics["Emergencia estimada"] != "Aún no estimable"
    assert historical.read_bytes() == original_counts
    assert (tmp_path / "meteo_daily.csv").read_bytes() == original_weather
    app.selectbox(key="campaign_year").set_value(2026).run()
    assert not app.exception and app.date_input[0].value.year == 2026
