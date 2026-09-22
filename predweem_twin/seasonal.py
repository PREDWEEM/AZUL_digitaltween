"""Referencia histórica exclusiva de los conteos locales de Azul 2026."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd


COUNTS_PATH = "data/calibration/azul_2026_counts.csv"
EXCLUDED_CAMPAIGNS = (
    "2008.xlsx", "2009.xlsx", "2010.xlsx", "2011.xlsx", "2012.xlsx",
    "2013.xlsx", "2014.xlsx", "2015.xlsx", "2023.xlsx", "2024.xlsx",
    "emererel2025 balcarce.xlsx", "emrel sp 2025 san pedro.xlsx",
    "test -emerel tresas 2025.xlsx",
)


class ReferenceUnavailable(ValueError):
    """No existe información local suficiente para expresar un porcentaje."""


def load_seasonal_reference(source: str | Path, as_of=None) -> pd.DataFrame:
    """Normaliza un CSV FECHA + PLM2 de Azul 2026 dentro de su ventana real.

    No lee el clasificador compartido ni usa su eje temporal. La fracción
    acumulada sólo está disponible desde el último conteo, cuando se conoce
    el total registrado. Las visitas son intervalos, no observaciones diarias.
    """
    path = Path(source)
    counts = pd.read_csv(path)
    if not {"FECHA", "PLM2"}.issubset(counts.columns) or len(counts) < 2:
        raise ValueError("La referencia Azul 2026 requiere FECHA, PLM2 y al menos dos visitas.")
    dates = pd.to_datetime(counts["FECHA"], errors="raise").dt.normalize()
    flows = pd.to_numeric(counts["PLM2"], errors="raise").to_numpy(float)
    if (dates.isna().any() or dates.duplicated().any()
            or not dates.is_monotonic_increasing or not dates.dt.year.eq(2026).all()
            or not np.isfinite(flows).all() or (flows < 0).any()
            or flows.sum() <= 0 or flows[0] != 0):
        raise ValueError("Conteos 2026 inválidos o sin cero inicial delimitador.")
    first, last = dates.iloc[0], dates.iloc[-1]
    cutoff = pd.Timestamp(as_of).tz_localize(None).normalize() if as_of is not None else None
    if cutoff is not None and pd.isna(cutoff):
        raise ValueError("Fecha de corte de la referencia inválida.")
    available = cutoff is None or cutoff >= last
    days = np.arange(first.dayofyear, last.dayofyear + 1, dtype=float)
    progress = (
        np.interp(days, dates.dt.dayofyear, np.cumsum(flows) / flows.sum())
        if available else np.full(len(days), np.nan)
    )
    excluded = ", ".join(EXCLUDED_CAMPAIGNS)
    if not available:
        excluded += f", azul_2026_counts.csv (disponible desde {last:%d/%m/%Y})"
    reference = pd.DataFrame({
        "Julian_days": days,
        "Progreso_P10": progress, "Progreso_Mediano": progress, "Progreso_P90": progress,
        "Progreso_2026": progress, "N_Campanas": int(available),
        "N_Campanas_Dia": int(available),
        "Campanas": "azul_2026_counts.csv" if available else "",
        "Campanas_Anos": "2026" if available else "",
        "Campanas_Excluidas": excluded,
        "Referencia_2026_Desde": last.date().isoformat(),
    })
    reference.attrs["source_2026"] = {
        "path": COUNTS_PATH, "sha256": sha256(path.read_bytes()).hexdigest(),
        "start": first.date().isoformat(), "end": last.date().isoformat(),
        "sample_count": len(counts), "window_total_plm2": float(flows.sum()),
        "used": available,
        "processing": "acumulado / total registrado; interpolación lineal entre visitas",
        "scope": "ventana registrada; no certifica el cierre biológico de la campaña",
    }
    return reference


def load_local_seasonal_reference(root: str | Path, as_of=None) -> pd.DataFrame:
    """Carga exclusivamente el archivo local de Azul; no admite otras campañas."""
    return load_seasonal_reference(Path(root) / COUNTS_PATH, as_of=as_of)


def reference_progress(reference: pd.DataFrame, julian_days):
    """Interpola dentro de la ventana; mantiene su total después como supuesto.

    Antes del primer conteo devuelve NaN: no hay evidencia de ausencia de
    nacimientos. La extensión posterior no se dibuja como historia observada.
    """
    days = np.asarray(julian_days, dtype=float)
    axis = reference["Julian_days"].to_numpy(float)
    return tuple(
        np.interp(days, axis, reference[column].to_numpy(float),
                  left=np.nan, right=float(reference[column].iloc[-1]))
        for column in ("Progreso_P10", "Progreso_Mediano", "Progreso_P90")
    )


def partial_season_normalization(trajectory: pd.DataFrame, as_of, reference: pd.DataFrame):
    """Ancla a Azul 2026 sin recurrir al total de una meteorología parcial.

    La única referencia no existía antes de su último conteo. Si no hay un
    ancla local conocida, se informa que el porcentaje no es estimable en vez
    de normalizar por el último día y convertirlo artificialmente en 100 %.
    """
    cutoff = pd.Timestamp(as_of).tz_localize(None).normalize()
    available_from = pd.Timestamp(reference["Referencia_2026_Desde"].iloc[0])
    if cutoff < available_from or not reference["N_Campanas"].eq(1).all():
        raise ReferenceUnavailable(
            f"No hay referencia histórica local anterior: Azul 2026 está disponible desde {available_from:%d/%m/%Y}."
        )
    candidates = trajectory.index[trajectory["Fecha"] <= cutoff].tolist()
    if not candidates:
        raise ReferenceUnavailable("No hay meteorología hasta la fecha consultada.")
    anchor_idx = candidates[-1]
    p10, median, p90 = reference_progress(reference, trajectory["Julian_days"].to_numpy(float))
    raw_cumulative = trajectory["EMERAC"].to_numpy(float)
    if not np.isfinite(median[anchor_idx]):
        raise ReferenceUnavailable(
            "La referencia Azul 2026 comienza el 1 de marzo. Antes de esa ventana no se "
            "puede estimar un porcentaje ni remanente con este único histórico."
        )
    if raw_cumulative[anchor_idx] <= 1e-12 or median[anchor_idx] <= .01:
        raise ReferenceUnavailable(
            "Aún no hay señal y progreso histórico suficientes para estimar el porcentaje "
            "estacional. No se normaliza por el final del pronóstico."
        )
    total = float(raw_cumulative[anchor_idx] / median[anchor_idx])
    if not np.isfinite(total) or total <= 1e-12:
        raise ReferenceUnavailable("No hay una escala estacional local válida.")
    return total, {
        "mode": "referencia estacional histórica",
        "anchor_date": trajectory.at[anchor_idx, "Fecha"],
        "reference_progress": float(median[anchor_idx]),
        "reference_p10": float(p10[anchor_idx]), "reference_p90": float(p90[anchor_idx]),
        "seasonal_signal_total": total,
    }
