"""Cambios en los datos y formato durante una actualización de Streamlit."""

import ast
from pathlib import Path
from runpy import run_path
import shutil

import numpy as np
import pytest


ROOT = Path(__file__).parents[1]


def app_reference_loader(root):
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "load_progress_reference")
    namespace = {"BASE": root, "run_path": run_path}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(ROOT / "app.py"), "exec"), namespace)
    return namespace["load_progress_reference"]


def test_app_reloads_reference_after_data_changes(tmp_path):
    (tmp_path / "predweem_twin").mkdir()
    shutil.copyfile(ROOT / "predweem_twin/seasonal.py", tmp_path / "predweem_twin/seasonal.py")
    (tmp_path / "data/calibration").mkdir(parents=True)
    data = tmp_path / "data/calibration/azul_2026_counts.csv"
    shutil.copyfile(ROOT / "data/calibration/azul_2026_counts.csv", data)
    loader = app_reference_loader(tmp_path)
    before = loader()
    import pandas as pd
    counts = pd.read_csv(data)
    counts.loc[len(counts)-1, "PLM2"] = 50000.
    counts.to_csv(data, index=False)
    after = loader()
    assert not np.allclose(before.Progreso_Mediano, after.Progreso_Mediano)
    assert after.N_Campanas.eq(1).all()
    assert not after.Campanas.str.contains("balcarce|san pedro", case=False).any()


@pytest.mark.parametrize("defect", ["missing_metadata", "excluded_campaign"])
def test_inconsistent_reference_is_rejected_before_simulation(defect):
    loader = app_reference_loader(ROOT)
    invalid = loader()
    if defect == "missing_metadata":
        invalid = invalid.drop(columns="Campanas_Excluidas")
    else:
        invalid["Campanas"] += ", emrel sp 2025 san pedro.xlsx"
    loader.__globals__["run_path"] = lambda path: {
        "load_local_seasonal_reference": lambda *args, **kwargs: invalid
    }
    with pytest.raises(ValueError, match="referencia estacional"):
        loader()
