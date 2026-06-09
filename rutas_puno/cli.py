"""Interfaz de consola para el Sistema de Orientación de Rutas - Puno."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Sequence

from . import data
from .domain import (
    crear_incidencia,
    marcar_turno,
    recomendar_linea,
    resolver_incidencia,
    resumen_dashboard,
)
from .logging_config import configurar_logging
from .maps import mapa_linea, mapa_ruta
from .models import Cuenta, Incidencia, Linea, Turno
from .security import verificar_login
from .storage import (
    cargar_cuentas,
    cargar_incidencias,
    cargar_lineas,
    cargar_turnos,
    guardar_incidencias,
    guardar_lineas,
    guardar_turnos,
)

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LINEAS_PATH = DATA_DIR / "lineas.json"
INCIDENCIAS_PATH = DATA_DIR / "incidencias.json"
CUENTAS_PATH = DATA_DIR / "usuarios.json"
TURNOS_PATH = DATA_DIR / "turnos.json"


def cargar_datos() -> tuple[tuple[Linea, ...], tuple[Incidencia, ...], tuple[Cuenta, ...], tuple[Turno, ...]]:
    """Carga datos desde JSON; si no existen, usa datos de prueba."""

    lineas = cargar_lineas(LINEAS_PATH) or data.LINEAS
    incidencias = cargar_incidencias(INCIDENCIAS_PATH) or data.INCIDENCIAS
    cuentas = cargar_cuentas(CUENTAS_PATH) or data.CUENTAS
    turnos = cargar_turnos(TURNOS_PATH) or data.TURNOS
    return lineas, incidencias, cuentas, turnos


def guardar_datos_operacion(incidencias: Sequence[Incidencia], turnos: Sequence[Turno]) -> None:
    """Guarda cambios operativos en JSON."""

    guardar_incidencias(INCIDENCIAS_PATH, incidencias)
    guardar_turnos(TURNOS_PATH, turnos)


def mostrar_lineas(lineas: Sequence[Linea]) -> None:
    print("\nLÍNEAS DISPONIBLES")
    print("-" * 60)
    for linea in lineas:
        print(
            f"{linea.numero:<4} | Color: {linea.color:<8} | "
            f"Costo: S/ {linea.costo:.2f} | Frec.: {linea.frecuencia_min} min"
        )


def mostrar_paraderos(lineas: Sequence[Linea]) -> None:
    paraderos = sorted({p for linea in lineas for p in linea.paraderos})
    print("\nPARADEROS REGISTRADOS")
    print("-" * 60)
    for indice, paradero in enumerate(paraderos, start=1):
        print(f"{indice:02d}. {paradero}")


def menu_pasajero(lineas: Sequence[Linea], incidencias: Sequence[Incidencia]) -> None:
    """Menú de consulta para el usuario pasajero."""

    mostrar_paraderos(lineas)
    origen = input("\nOrigen: ").strip()
    destino = input("Destino: ").strip()

    try:
        recomendacion = recomendar_linea(origen, destino, lineas, incidencias)
    except ValueError as exc:
        print(f"\nError: {exc}")
        return

    print("\nRESULTADO DE RECOMENDACIÓN")
    print("-" * 60)
    print(recomendacion.alerta)

    if recomendacion.recomendada:
        linea = recomendacion.recomendada
        alternativas = ", ".join(l.numero for l in recomendacion.alternativas)
        print(f"Línea recomendada: {linea.numero} ({linea.color})")
        print(f"Tramos aproximados: {recomendacion.tramos}")
        print(f"Costo: S/ {linea.costo:.2f}")
        print(f"Frecuencia: cada {linea.frecuencia_min} min")
        print(f"Alternativas evaluadas: {alternativas}")
        print(f"Entropía de Shannon: {recomendacion.entropia} bits")
        try:
            print(f"Mapa: {mapa_linea(linea, origen, destino)}")
        except Exception as exc:  # noqa: BLE001 - Se muestra el error sin detener el menú.
            LOGGER.debug("No se pudo generar mapa: %s", exc)
    elif recomendacion.ruta_transbordo:
        ruta = recomendacion.ruta_transbordo
        print(f"Ruta con transbordos: {ruta.transbordos}")
        print(f"Costo total: S/ {ruta.costo_total:.2f}")
        for i, segmento in enumerate(ruta.segmentos, start=1):
            print(
                f"  {i}. Tomar {segmento.linea} desde {segmento.subir} "
                f"hasta {segmento.bajar} | S/ {segmento.costo:.2f}"
            )
        try:
            print(f"Mapa: {mapa_ruta(ruta)}")
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("No se pudo generar mapa de transbordo: %s", exc)
    else:
        print("No se encontró ruta disponible con los datos actuales.")


def pedir_login(cuentas: Sequence[Cuenta], rol: str) -> Cuenta | None:
    """Solicita usuario y contraseña para un rol."""

    usuario = input("Usuario: ").strip()
    password = input("Contraseña: ").strip()
    cuenta = verificar_login(cuentas, usuario, password, rol=rol)
    if cuenta is None:
        print("Acceso denegado. Revise usuario, contraseña o suspensión.")
    return cuenta


def menu_conductor(
    cuentas: Sequence[Cuenta],
    turnos: Sequence[Turno],
    incidencias: Sequence[Incidencia],
) -> tuple[tuple[Turno, ...], tuple[Incidencia, ...]]:
    """Menú de conductor para marcar turnos y reportar incidencias."""

    print("\nLOGIN CONDUCTOR")
    cuenta = pedir_login(cuentas, rol="conductor")
    if cuenta is None:
        return tuple(turnos), tuple(incidencias)

    while True:
        print("\nMENÚ CONDUCTOR")
        print("1. Marcar turno")
        print("2. Reportar incidencia")
        print("0. Volver")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            hora_programada = input("Hora programada (HH:MM): ").strip()
            hora_real = input("Hora real (HH:MM, ENTER para hora actual): ").strip()
            if not hora_real:
                hora_real = datetime.now().strftime("%H:%M")
            punto = input("Punto de salida: ").strip() or "Terminal"
            try:
                turnos = marcar_turno(
                    turnos,
                    linea=cuenta.linea,
                    placa=cuenta.placa,
                    hora_programada=hora_programada,
                    hora_real=hora_real,
                    punto=punto,
                )
                print(f"Turno registrado. Estado: {turnos[-1].estado}")
            except ValueError as exc:
                print(f"Error: {exc}")
        elif opcion == "2":
            paradero = input("Paradero con incidencia: ").strip()
            motivo = input("Motivo: ").strip() or "Reporte del conductor"
            incidencias = crear_incidencia(
                incidencias,
                tipo="congestion",
                paradero=paradero,
                motivo=motivo,
                linea=cuenta.linea,
            )
            print(f"Incidencia registrada con ID {incidencias[-1].id}.")
        elif opcion == "0":
            return tuple(turnos), tuple(incidencias)
        else:
            print("Opción no válida.")


def mostrar_dashboard(
    lineas: Sequence[Linea],
    incidencias: Sequence[Incidencia],
    turnos: Sequence[Turno],
) -> None:
    resumen = resumen_dashboard(lineas, incidencias, turnos)
    print("\nDASHBOARD ADMINISTRATIVO")
    print("-" * 60)
    for clave, valor in resumen.items():
        print(f"{clave.replace('_', ' ').title():<25}: {valor}")

    print("\nIncidencias activas:")
    activas = [i for i in incidencias if i.activa]
    if not activas:
        print("  No hay incidencias activas.")
    for incidencia in activas:
        print(
            f"  ID {incidencia.id}: {incidencia.tipo} en {incidencia.paradero} "
            f"| Línea: {incidencia.linea or 'General'} | {incidencia.motivo}"
        )


def menu_admin(
    cuentas: Sequence[Cuenta],
    lineas: Sequence[Linea],
    incidencias: Sequence[Incidencia],
    turnos: Sequence[Turno],
) -> tuple[tuple[Linea, ...], tuple[Incidencia, ...]]:
    """Menú administrativo."""

    print("\nLOGIN ADMINISTRADOR")
    cuenta = pedir_login(cuentas, rol="administrador")
    if cuenta is None:
        return tuple(lineas), tuple(incidencias)

    while True:
        print("\nMENÚ ADMINISTRADOR")
        print("1. Ver dashboard")
        print("2. Crear incidencia")
        print("3. Resolver incidencia")
        print("4. Ver líneas")
        print("0. Volver")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            mostrar_dashboard(lineas, incidencias, turnos)
        elif opcion == "2":
            tipo = input("Tipo (congestion/accidente/desvio): ").strip() or "congestion"
            paradero = input("Paradero: ").strip()
            motivo = input("Motivo: ").strip()
            incidencias = crear_incidencia(incidencias, tipo, paradero, motivo)
            print(f"Incidencia creada con ID {incidencias[-1].id}.")
        elif opcion == "3":
            try:
                incidencia_id = int(input("ID de incidencia a resolver: ").strip())
                incidencias = resolver_incidencia(incidencias, incidencia_id)
                print("Incidencia actualizada.")
            except ValueError:
                print("Debe ingresar un número válido.")
        elif opcion == "4":
            mostrar_lineas(lineas)
        elif opcion == "0":
            return tuple(lineas), tuple(incidencias)
        else:
            print("Opción no válida.")


def main() -> None:
    """Punto de entrada de la aplicación de consola."""

    configurar_logging()
    lineas, incidencias, cuentas, turnos = cargar_datos()

    # Se guardan una vez para dejar los JSON creados en caso de que no existan.
    guardar_lineas(LINEAS_PATH, lineas)
    guardar_datos_operacion(incidencias, turnos)

    while True:
        print("\nSISTEMA DE ORIENTACIÓN DE RUTAS - PUNO")
        print("=" * 60)
        print("1. Pasajero: recomendar ruta")
        print("2. Conductor: marcar turno / reportar incidencia")
        print("3. Administrador: dashboard / incidencias")
        print("4. Ver líneas y paraderos")
        print("0. Salir")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            menu_pasajero(lineas, incidencias)
        elif opcion == "2":
            turnos, incidencias = menu_conductor(cuentas, turnos, incidencias)
            guardar_datos_operacion(incidencias, turnos)
        elif opcion == "3":
            lineas, incidencias = menu_admin(cuentas, lineas, incidencias, turnos)
            guardar_datos_operacion(incidencias, turnos)
        elif opcion == "4":
            mostrar_lineas(lineas)
            mostrar_paraderos(lineas)
        elif opcion == "0":
            guardar_datos_operacion(incidencias, turnos)
            print("Sistema cerrado correctamente.")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
