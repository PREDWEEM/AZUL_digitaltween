"""Normalización parcial sin otras localidades ni cierre artificial del pronóstico."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from predweem_twin.core import ModelParameters, PracticalANNModel, run_predweem
from predweem_twin.seasonal import load_local_seasonal_reference, ReferenceUnavailable

ROOT=Path(__file__).parents[1]


def run(cutoff, reference=None):
    cutoff=pd.Timestamp(cutoff)
    # Sólo para probar el calendario: la meteorología observada no es pronóstico 2027.
    weather=pd.read_csv(ROOT/'data/calibration/azul_2026_weather.csv')
    weather['Fecha']=pd.to_datetime(weather.Fecha)+pd.DateOffset(years=cutoff.year-2026)
    weather=weather[weather.Fecha.le(cutoff+pd.Timedelta(days=7))]
    return run_predweem(weather,PracticalANNModel.from_directory(ROOT/'models'),ModelParameters(),
                       normalization_as_of=cutoff,seasonal_reference=(
                           reference if reference is not None else load_local_seasonal_reference(ROOT,cutoff)))


def test_future_partial_run_anchors_to_azul_without_forcing_last_day_to_one():
    result=run('2027-03-30')
    row=result.loc[result.Fecha.eq('2027-03-30')].iloc[0]
    assert row.EMERAC_NORMALIZADA == pytest.approx(row.Progreso_Estacional_Referencia)
    assert result.EMERAC_NORMALIZADA.iloc[-1] < 1
    assert result.Normalizacion_Modo.eq('referencia estacional histórica').all()
    assert result.loc[result.Fecha.lt('2027-03-01'),'Progreso_Estacional_Referencia'].isna().all()


@pytest.mark.parametrize('cutoff',['2026-05-05','2026-08-31'])
def test_historical_normalization_rejects_future_reference_even_if_preloaded(cutoff):
    with pytest.raises(ReferenceUnavailable,match='disponible desde'):
        run(cutoff,load_local_seasonal_reference(ROOT))


def test_unknown_early_window_does_not_fall_back_to_total_available_weather():
    with pytest.raises(ReferenceUnavailable,match='comienza el 1 de marzo'):
        run('2027-02-20')
