"""Configuración común de pruebas."""

import os

# La suite abre la app sin ingreso con Google; ver acceso._modo_pruebas.
os.environ.setdefault("PREDWEEM_ACCESO_PRUEBAS", "1")
