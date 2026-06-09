"""Pruebas de persistencia JSON."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rutas_puno.data import LINEAS
from rutas_puno.storage import cargar_lineas, guardar_lineas


class TestStorage(unittest.TestCase):
    def test_guardar_y_cargar_lineas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lineas.json"
            guardar_lineas(path, LINEAS)
            cargadas = cargar_lineas(path)
            self.assertEqual(cargadas[0].numero, "L50")
            self.assertEqual(cargadas[0].vehiculos[0].placa, "VAA-501")


if __name__ == "__main__":
    unittest.main()
