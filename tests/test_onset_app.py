"""La alerta de Azul sigue disponible cuando no existe una escala histórica."""

from datetime import date
import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_alert_arrow_toggle_and_early_monitoring_without_future_reference():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()

    def checked():
        assert not app.exception, [error.message for error in app.exception]

    def chart():
        return json.loads(app.get("plotly_chart")[0].proto.spec)

    def arrows():
        return [item for item in chart()["layout"].get("annotations", [])
                if item.get("name") == "initial_monitoring_alert"]

    checked()
    assert app.toggle(key="onset_alert_enabled").value is True
    # Septiembre: referencia 2026 conocida, gráfico retrospectivo disponible.
    app.date_input[0].set_value(date(2026, 9, 1)).run()
    checked()
    arrow = arrows()[0]
    expected_date = pd.Timestamp("2026-03-10").timestamp() * 1000
    assert arrow["x"] == expected_date and arrow["ax"] == 0 and arrow["ay"] < 0
    assert "10/03/2026 · estimada" in arrow["text"]
    weekly_data = chart()["data"]
    cumulative = app.get("plotly_chart")[1].proto.spec
    thermal = next(m.value for m in app.metric if m.label == "TT desde primer pico")
    app.radio(key="flow_frequency").set_value("Diario").run()
    checked()
    assert arrows()[0]["x"] == expected_date
    assert app.get("plotly_chart")[1].proto.spec == cumulative
    app.radio(key="flow_frequency").set_value("Semanal").run()
    app.toggle(key="onset_alert_enabled").set_value(False).run()
    checked()
    assert not arrows() and chart()["data"] == weekly_data
    assert app.get("plotly_chart")[1].proto.spec == cumulative
    assert next(m.value for m in app.metric if m.label == "TT desde primer pico") == thermal

    # Marzo: la referencia anual aún no se conoce. El inicio fisiológico sí
    # puede consultarse, sin publicar porcentajes calculados con el total futuro.
    app.toggle(key="onset_alert_enabled").set_value(True).run()
    app.date_input[0].set_value(date(2026, 3, 9)).run()
    checked()
    assert any("Sin inicio previsto" in element.value for element in app.info)
    app.date_input[0].set_value(date(2026, 3, 10)).run()
    checked()
    assert any("Alerta preventiva" in element.value and "17/03/2026" in element.value
               for element in app.warning)
    assert any("Revisión retrospectiva" in element.value for element in app.caption)
    assert any("no hay una campaña" in element.value for element in app.info)
    assert len(app.get("plotly_chart")) >= 2
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Emergencia estimada"] == "Aún no estimable"
    assert metrics["Emergencia remanente"] == "Aún no estimable"
    assert "Aún no estimable" in metrics["Intensidad de emergencia · 7 días"]
    assert "nan" not in str(metrics).lower()
    app.toggle(key="onset_alert_enabled").set_value(False).run()
    checked()
    assert not any("Alerta preventiva" in element.value for element in app.warning)
    assert len(app.get("plotly_chart")) >= 2
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Emergencia estimada"] == "Aún no estimable"
    assert metrics["Emergencia remanente"] == "Aún no estimable"
    assert "Aún no estimable" in metrics["Intensidad de emergencia · 7 días"]
    assert "nan" not in str(metrics).lower()
