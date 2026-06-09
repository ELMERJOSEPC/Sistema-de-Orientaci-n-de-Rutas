"""Persistencia robusta en archivos JSON.

La lógica del dominio no depende de archivos. Este módulo funciona como
"cáscara imperativa": lee y escribe datos en JSON y los transforma a tipos
inmutables.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Sequence

from .models import Cuenta, Incidencia, Linea, Turno, Vehiculo

LOGGER = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """Error controlado de carga o guardado de archivos."""


def _read_json(path: str | Path, default: Any) -> Any:
    """Lee JSON con tolerancia a archivos inexistentes o vacíos."""

    ruta = Path(path)
    if not ruta.exists():
        LOGGER.warning("No existe %s. Se usará valor por defecto.", ruta)
        return default
    try:
        contenido = ruta.read_text(encoding="utf-8").strip()
        if not contenido:
            return default
        return json.loads(contenido)
    except json.JSONDecodeError as exc:
        raise StorageError(f"El archivo {ruta} no tiene JSON válido.") from exc
    except OSError as exc:
        raise StorageError(f"No se pudo leer {ruta}.") from exc


def _write_json(path: str | Path, data: Any) -> None:
    """Guarda JSON creando carpetas si es necesario."""

    ruta = Path(path)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"No se pudo guardar {ruta}.") from exc


def _vehiculo_from_dict(data: dict[str, Any]) -> Vehiculo:
    return Vehiculo(placa=str(data["placa"]), capacidad=int(data["capacidad"]))


def _linea_from_dict(data: dict[str, Any]) -> Linea:
    return Linea(
        numero=str(data["numero"]),
        color=str(data["color"]),
        costo=float(data["costo"]),
        frecuencia_min=int(data["frecuencia_min"]),
        paraderos=tuple(str(p) for p in data["paraderos"]),
        vehiculos=tuple(_vehiculo_from_dict(v) for v in data.get("vehiculos", [])),
    )


def _linea_to_dict(linea: Linea) -> dict[str, Any]:
    return {
        "numero": linea.numero,
        "color": linea.color,
        "costo": linea.costo,
        "frecuencia_min": linea.frecuencia_min,
        "paraderos": list(linea.paraderos),
        "vehiculos": [v._asdict() for v in linea.vehiculos],
    }


def cargar_lineas(path: str | Path) -> tuple[Linea, ...]:
    """Carga líneas desde JSON."""

    data = _read_json(path, default=[])
    return tuple(_linea_from_dict(item) for item in data)


def guardar_lineas(path: str | Path, lineas: Sequence[Linea]) -> None:
    """Guarda líneas en JSON."""

    _write_json(path, [_linea_to_dict(linea) for linea in lineas])


def _incidencia_from_dict(data: dict[str, Any]) -> Incidencia:
    return Incidencia(
        id=int(data["id"]),
        tipo=str(data["tipo"]),
        paradero=str(data["paradero"]),
        linea=str(data.get("linea", "")),
        motivo=str(data.get("motivo", "")),
        activa=bool(data.get("activa", True)),
    )


def _incidencia_to_dict(incidencia: Incidencia) -> dict[str, Any]:
    return incidencia._asdict()


def cargar_incidencias(path: str | Path) -> tuple[Incidencia, ...]:
    data = _read_json(path, default=[])
    return tuple(_incidencia_from_dict(item) for item in data)


def guardar_incidencias(path: str | Path, incidencias: Sequence[Incidencia]) -> None:
    _write_json(path, [_incidencia_to_dict(incidencia) for incidencia in incidencias])


def _cuenta_from_dict(data: dict[str, Any]) -> Cuenta:
    return Cuenta(
        usuario=str(data["usuario"]),
        clave_hash=str(data["clave_hash"]),
        rol=str(data["rol"]),
        linea=str(data.get("linea", "")),
        placa=str(data.get("placa", "")),
        suspendido=bool(data.get("suspendido", False)),
    )


def cargar_cuentas(path: str | Path) -> tuple[Cuenta, ...]:
    data = _read_json(path, default=[])
    return tuple(_cuenta_from_dict(item) for item in data)


def guardar_cuentas(path: str | Path, cuentas: Sequence[Cuenta]) -> None:
    _write_json(path, [cuenta._asdict() for cuenta in cuentas])


def _turno_from_dict(data: dict[str, Any]) -> Turno:
    return Turno(
        linea=str(data["linea"]),
        placa=str(data["placa"]),
        hora_programada=str(data["hora_programada"]),
        punto=str(data["punto"]),
        estado=str(data["estado"]),
        hora_real=str(data.get("hora_real", "")),
    )


def cargar_turnos(path: str | Path) -> tuple[Turno, ...]:
    data = _read_json(path, default=[])
    return tuple(_turno_from_dict(item) for item in data)


def guardar_turnos(path: str | Path, turnos: Sequence[Turno]) -> None:
    _write_json(path, [turno._asdict() for turno in turnos])
