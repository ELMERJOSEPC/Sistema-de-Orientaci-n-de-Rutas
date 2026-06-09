"""Tipos de datos inmutables del Sistema de Orientación de Rutas - Puno.

El proyecto usa NamedTuple para respetar el paradigma funcional descrito en el
informe: los datos no se modifican directamente; cada operación devuelve una
nueva estructura.
"""

from __future__ import annotations

from typing import NamedTuple, Optional, Tuple


class Vehiculo(NamedTuple):
    """Vehículo asociado a una línea de transporte."""

    placa: str
    capacidad: int


class Linea(NamedTuple):
    """Línea de transporte con paraderos ordenados."""

    numero: str
    color: str
    costo: float
    frecuencia_min: int
    paraderos: Tuple[str, ...]
    vehiculos: Tuple[Vehiculo, ...]


class Segmento(NamedTuple):
    """Tramo recorrido en una línea, desde un paradero de subida hasta uno de bajada."""

    linea: str
    color: str
    subir: str
    bajar: str
    costo: float
    tramos: int


class Ruta(NamedTuple):
    """Ruta compuesta por uno o más segmentos, con o sin transbordos."""

    segmentos: Tuple[Segmento, ...]
    costo_total: float
    transbordos: int


class Recomendacion(NamedTuple):
    """Resultado de la recomendación para el usuario pasajero."""

    recomendada: Optional[Linea]
    tramos: int
    alternativas: Tuple[Linea, ...]
    entropia: float
    requiere_transbordo: bool
    ruta_transbordo: Optional[Ruta]
    alerta: str


class Turno(NamedTuple):
    """Turno de salida marcado por un conductor."""

    linea: str
    placa: str
    hora_programada: str
    punto: str
    estado: str
    hora_real: str


class Aviso(NamedTuple):
    """Aviso enviado a un conductor o al pasajero."""

    placa: str
    mensaje: str
    fecha: str
    tipo: str


class Cuenta(NamedTuple):
    """Cuenta de usuario para conductor o administrador."""

    usuario: str
    clave_hash: str
    rol: str
    linea: str
    placa: str
    suspendido: bool = False


class Incidencia(NamedTuple):
    """Incidencia activa o resuelta en la red de transporte."""

    id: int
    tipo: str
    paradero: str
    linea: str
    motivo: str
    activa: bool


class Reporte(NamedTuple):
    """Reporte administrativo para control de sanciones."""

    id: int
    placa: str
    linea: str
    motivo: str
    estado: str
