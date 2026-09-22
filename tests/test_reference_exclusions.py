"""La referencia y su escala no dependen de ninguna curva compartida."""
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from predweem_twin.flows import historical_weekly_max
from predweem_twin.seasonal import load_local_seasonal_reference

ROOT = Path(__file__).parents[1]
COUNTS = Path("data/calibration/azul_2026_counts.csv")


@pytest.fixture
def local_files(tmp_path):
    (tmp_path / COUNTS).parent.mkdir(parents=True)
    shutil.copyfile(ROOT / COUNTS, tmp_path / COUNTS)
    return tmp_path


def test_reference_is_exactly_the_local_counts_on_their_calendar():
    counts = pd.read_csv(ROOT / COUNTS)
    dates = pd.to_datetime(counts.FECHA)
    ref = load_local_seasonal_reference(ROOT, "2027-05-05")
    assert ref.Julian_days.tolist() == list(range(60, 245))
    expected = np.interp(ref.Julian_days, dates.dt.dayofyear, counts.PLM2.cumsum()/counts.PLM2.sum())
    for col in ['Progreso_2026', 'Progreso_P10', 'Progreso_Mediano', 'Progreso_P90']:
        np.testing.assert_allclose(ref[col], expected)
    assert ref.N_Campanas.eq(1).all()
    assert ref.Campanas.eq('azul_2026_counts.csv').all()
    assert ref.Campanas_Anos.eq('2026').all()
    assert ref.attrs['source_2026']['window_total_plm2'] == 8224
    assert ref.attrs['source_2026']['sample_count'] == 11
    excluded = ref.Campanas_Excluidas.iloc[0].lower()
    for label in ('2008','2009','2010','2011','2012','2013','2014','2015','2023','2024','balcarce','san pedro','tresas'):
        assert label in excluded


def test_shared_pickle_is_never_read_and_cannot_change_the_pool(local_files):
    before = load_local_seasonal_reference(local_files, '2027-05-05')
    (local_files/'models').mkdir()
    (local_files/'models/modelo_clusters_k3.pkl').write_bytes(b'not a pickle: excluded in its entirety')
    after = load_local_seasonal_reference(local_files, '2027-05-05')
    pd.testing.assert_frame_equal(before, after)
    assert historical_weekly_max(before,'2027-05-05') == historical_weekly_max(after,'2027-05-05')


def test_density_scaling_does_not_change_relative_historical_flow(local_files):
    before = load_local_seasonal_reference(local_files)
    counts = pd.read_csv(local_files/COUNTS)
    counts.PLM2 *= 100
    counts.to_csv(local_files/COUNTS,index=False)
    after = load_local_seasonal_reference(local_files)
    np.testing.assert_allclose(before.Progreso_Mediano, after.Progreso_Mediano)


def test_future_2026_counts_cannot_supply_a_reference_before_closure(local_files):
    before = load_local_seasonal_reference(local_files,'2026-08-31')
    assert before.N_Campanas.eq(0).all()
    assert before.Progreso_Mediano.isna().all()
    assert not before.attrs['source_2026']['used']
    counts = pd.read_csv(local_files/COUNTS)
    counts.loc[len(counts)-1,'PLM2'] = 99999
    counts.to_csv(local_files/COUNTS,index=False)
    after = load_local_seasonal_reference(local_files,'2026-08-31')
    pd.testing.assert_series_equal(before.Progreso_Mediano,after.Progreso_Mediano)
    assert historical_weekly_max(after,'2026-08-31') is None
    assert load_local_seasonal_reference(local_files,'2026-09-01').N_Campanas.eq(1).all()


@pytest.mark.parametrize('fault',['duplicate','negative','nan','wrong_year','no_initial_zero','missing_column','unsorted'])
def test_invalid_counts_are_rejected(local_files,fault):
    counts=pd.read_csv(local_files/COUNTS)
    if fault=='duplicate':
        counts.loc[2,'FECHA']=counts.loc[1,'FECHA']
    elif fault=='wrong_year':
        counts.loc[0,'FECHA']='2025-03-01'
    elif fault=='missing_column':
        counts=counts.drop(columns='PLM2')
    elif fault=='unsorted':
        counts=counts.iloc[::-1]
    else:
        counts.loc[0 if fault=='no_initial_zero' else 2,'PLM2']={'negative':-1.,'nan':np.nan,'no_initial_zero':1.}[fault]
    counts.to_csv(local_files/COUNTS,index=False)
    with pytest.raises(ValueError):
        load_local_seasonal_reference(local_files)
