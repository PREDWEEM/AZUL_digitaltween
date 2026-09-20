"""Una actualización puede conservar el módulo anterior en el proceso Cloud."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from predweem_twin import seasonal
from tests.test_reference_reload import app_reference_loader


ROOT = Path(__file__).parents[1]


def test_app_uses_current_filters_when_imported_module_is_stale(monkeypatch):
    # Reproduce la tabla antigua: once curvas y sin Campanas_Excluidas.
    current = seasonal.load_seasonal_reference(ROOT / "models/modelo_clusters_k3.pkl")
    legacy = current.drop(columns="Campanas_Excluidas").copy()
    legacy["N_Campanas"] = 11
    legacy["Campanas"] += ", emererel2025 balcarce.xlsx, emrel sp 2025 san pedro.xlsx"
    legacy[["Progreso_P10", "Progreso_Mediano", "Progreso_P90"]] = .25

    def stale_loader(*args, **kwargs):
        return legacy.copy()

    monkeypatch.setattr(seasonal, "load_seasonal_reference", stale_loader)
    # No basta con evitar la excepción: los percentiles también deben ser
    # los de la selección nueva, no los de las once curvas antiguas.
    import pandas as pd
    pd.testing.assert_frame_equal(app_reference_loader(ROOT)(), current)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception, [error.message for error in app.exception]
    for _ in range(2):
        used = next(str(x.value) for x in app.markdown if str(x.value).startswith("Campañas utilizadas:"))
        assert "balcarce" not in used.lower() and "san pedro" not in used.lower()
        assert any("9 campañas" in str(x.value) for x in app.caption)
        app.run()
        assert not app.exception, [error.message for error in app.exception]
