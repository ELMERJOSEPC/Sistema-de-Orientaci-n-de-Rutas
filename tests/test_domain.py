"""Pruebas unitarias del núcleo funcional."""

from __future__ import annotations

import unittest
from datetime import time

from rutas_puno.data import INCIDENCIAS, LINEAS
from rutas_puno.domain import (
    buscar_mejor_ruta,
    buscar_paradero,
    clasificar_turno,
    crear_incidencia,
    cubre_trayecto,
    cubre_trayecto_libre,
    debe_suspenderse,
    elegir_linea_mas_directa,
    entropia_shannon,
    esta_operativo,
    marcar_turno,
    paraderos_bloqueados,
    recomendar_linea,
    registrar_sancion,
    resolver_incidencia,
    resumen_dashboard,
    tramos_hasta,
)
from rutas_puno.models import Incidencia, Reporte, Turno


class TestDominioRutas(unittest.TestCase):
    """Casos de prueba para recomendación, incidencias, turnos y sanciones."""

    def test_01_entropia_sin_alternativas_es_cero(self) -> None:
        self.assertEqual(entropia_shannon(0), 0.0)

    def test_02_entropia_una_alternativa_es_cero(self) -> None:
        self.assertEqual(entropia_shannon(1), 0.0)

    def test_03_entropia_cuatro_alternativas_es_dos(self) -> None:
        self.assertEqual(entropia_shannon(4), 2.0)

    def test_04_buscar_paradero_es_insensible_a_mayusculas(self) -> None:
        self.assertEqual(buscar_paradero(LINEAS[0], "essalud salcedo"), 0)

    def test_05_cubre_trayecto_directo(self) -> None:
        self.assertTrue(cubre_trayecto(LINEAS[0], "EsSalud Salcedo", "Universidad"))

    def test_06_tramos_hasta_universidad_en_l50(self) -> None:
        self.assertEqual(tramos_hasta(LINEAS[0], "EsSalud Salcedo", "Universidad"), 4)

    def test_07_cubre_trayecto_libre_sin_bloqueo(self) -> None:
        self.assertTrue(
            cubre_trayecto_libre(
                LINEAS[0],
                "EsSalud Salcedo",
                "Universidad",
                bloqueados=frozenset(),
            )
        )

    def test_08_cubre_trayecto_libre_con_bloqueo(self) -> None:
        self.assertFalse(
            cubre_trayecto_libre(
                LINEAS[0],
                "EsSalud Salcedo",
                "Universidad",
                bloqueados=frozenset({"terminal terrestre"}),
            )
        )

    def test_09_recomendar_linea_directa_l50(self) -> None:
        recomendacion = recomendar_linea("EsSalud Salcedo", "Universidad", LINEAS, ())
        self.assertIsNotNone(recomendacion.recomendada)
        self.assertEqual(recomendacion.recomendada.numero, "L50")

    def test_10_recomendacion_calcula_cuatro_alternativas_y_entropia(self) -> None:
        recomendacion = recomendar_linea("EsSalud Salcedo", "Universidad", LINEAS, ())
        self.assertEqual(len(recomendacion.alternativas), 4)
        self.assertEqual(recomendacion.entropia, 2.0)

    def test_11_incidencia_terminal_recomienda_l15(self) -> None:
        incidencias = (
            Incidencia(1, "congestion", "Terminal Terrestre", "", "Hora punta", True),
        )
        recomendacion = recomendar_linea("EsSalud Salcedo", "Universidad", LINEAS, incidencias)
        self.assertEqual(recomendacion.recomendada.numero, "L15")

    def test_12_bfs_encuentra_ruta_con_transbordo(self) -> None:
        ruta = buscar_mejor_ruta("Chulluni", "Hospital Regional", LINEAS, bloqueados=frozenset())
        self.assertIsNotNone(ruta)
        self.assertEqual(ruta.transbordos, 1)

    def test_13_recomendacion_sin_directa_usa_transbordo(self) -> None:
        recomendacion = recomendar_linea("Chulluni", "Hospital Regional", LINEAS, ())
        self.assertTrue(recomendacion.requiere_transbordo)
        self.assertIsNotNone(recomendacion.ruta_transbordo)

    def test_14_paraderos_bloqueados_solo_activos(self) -> None:
        incidencias = (
            Incidencia(1, "congestion", "Terminal Terrestre", "", "A", True),
            Incidencia(2, "desvio", "Puerto Muelle", "", "B", False),
        )
        self.assertEqual(paraderos_bloqueados(incidencias), frozenset({"terminal terrestre"}))

    def test_15_crear_incidencia_incrementa_id(self) -> None:
        nuevas = crear_incidencia(INCIDENCIAS, "congestion", "Parque Pino", "Prueba")
        self.assertEqual(nuevas[-1].id, 2)
        self.assertTrue(nuevas[-1].activa)

    def test_16_resolver_incidencia_desactiva(self) -> None:
        incidencias = (Incidencia(1, "congestion", "Terminal", "", "A", True),)
        resueltas = resolver_incidencia(incidencias, 1)
        self.assertFalse(resueltas[0].activa)

    def test_17_clasificar_turno_en_tiempo(self) -> None:
        self.assertEqual(clasificar_turno("08:00", "08:04"), "en tiempo")

    def test_18_clasificar_turno_retrasado(self) -> None:
        self.assertEqual(clasificar_turno("08:00", "08:12"), "retrasado")

    def test_19_clasificar_turno_critico(self) -> None:
        self.assertEqual(clasificar_turno("08:00", "08:20"), "crítico")

    def test_20_marcar_turno_no_modifica_tupla_original(self) -> None:
        turnos: tuple[Turno, ...] = tuple()
        nuevos = marcar_turno(turnos, "L50", "VAA-501", "08:00", "08:20", "EsSalud")
        self.assertEqual(len(turnos), 0)
        self.assertEqual(len(nuevos), 1)
        self.assertEqual(nuevos[0].estado, "crítico")

    def test_21_suspension_tras_tres_sanciones(self) -> None:
        reportes: tuple[Reporte, ...] = tuple()
        reportes = registrar_sancion(reportes, "VAA-501", "L50", "Tardanza 1")
        reportes = registrar_sancion(reportes, "VAA-501", "L50", "Tardanza 2")
        reportes = registrar_sancion(reportes, "VAA-501", "L50", "Tardanza 3")
        self.assertTrue(debe_suspenderse(reportes, "VAA-501"))

    def test_22_dashboard_cuenta_incidencias_activas(self) -> None:
        incidencias = (
            Incidencia(1, "congestion", "Terminal", "", "A", True),
            Incidencia(2, "desvio", "Puerto", "", "B", False),
        )
        resumen = resumen_dashboard(LINEAS, incidencias, tuple())
        self.assertEqual(resumen["incidencias_activas"], 1)

    def test_23_esta_operativo_en_horario_de_atencion(self) -> None:
        self.assertTrue(esta_operativo(time(10, 30)))
        self.assertFalse(esta_operativo(time(22, 0)))


if __name__ == "__main__":
    unittest.main()
