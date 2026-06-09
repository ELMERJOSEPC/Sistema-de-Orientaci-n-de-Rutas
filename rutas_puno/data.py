"""Datos de prueba del sistema de rutas de Puno.

Los datos son pequeños y editables para que el proyecto funcione sin base de
datos. Se pueden reemplazar por archivos JSON usando el módulo storage.py.
"""

from __future__ import annotations

from .models import Cuenta, Incidencia, Linea, Turno, Vehiculo
from .security import hash_password


LINEAS = (
    Linea(
        numero="L50",
        color="Azul",
        costo=1.00,
        frecuencia_min=7,
        paraderos=(
            "EsSalud Salcedo",
            "Av. El Sol",
            "Terminal Terrestre",
            "Mercado Central",
            "Universidad",
            "Hospital Regional",
        ),
        vehiculos=(Vehiculo("VAA-501", 28), Vehiculo("VAA-502", 28)),
    ),
    Linea(
        numero="L15",
        color="Rojo",
        costo=1.00,
        frecuencia_min=8,
        paraderos=(
            "EsSalud Salcedo",
            "Av. Circunvalacion",
            "Parque Pino",
            "Plaza Vea",
            "Av. La Torre",
            "Universidad",
            "Hospital Regional",
        ),
        vehiculos=(Vehiculo("VBB-151", 25), Vehiculo("VBB-152", 25)),
    ),
    Linea(
        numero="L20",
        color="Verde",
        costo=1.20,
        frecuencia_min=10,
        paraderos=(
            "EsSalud Salcedo",
            "Mercado Bellavista",
            "Terminal Terrestre",
            "UNA Puno",
            "Universidad",
        ),
        vehiculos=(Vehiculo("VCC-201", 26), Vehiculo("VCC-202", 26)),
    ),
    Linea(
        numero="L30",
        color="Naranja",
        costo=1.50,
        frecuencia_min=12,
        paraderos=(
            "EsSalud Salcedo",
            "Puerto Muelle",
            "Plaza de Armas",
            "Terminal Terrestre",
            "Universidad",
        ),
        vehiculos=(Vehiculo("VDD-301", 24),),
    ),
    Linea(
        numero="L40",
        color="Morado",
        costo=1.00,
        frecuencia_min=11,
        paraderos=(
            "Chulluni",
            "Puerto Muelle",
            "Mercado Central",
            "Terminal Terrestre",
        ),
        vehiculos=(Vehiculo("VEE-401", 24),),
    ),
)


INCIDENCIAS = (
    Incidencia(
        id=1,
        tipo="congestion",
        paradero="Terminal Terrestre",
        linea="",
        motivo="Alta congestión en hora punta",
        activa=False,
    ),
)


CUENTAS = (
    Cuenta(
        usuario="admin",
        clave_hash=hash_password("admin123"),
        rol="administrador",
        linea="",
        placa="",
    ),
    Cuenta(
        usuario="chofer1",
        clave_hash=hash_password("clave123"),
        rol="conductor",
        linea="L50",
        placa="VAA-501",
    ),
)


TURNOS = (
    Turno(
        linea="L50",
        placa="VAA-501",
        hora_programada="08:00",
        punto="EsSalud Salcedo",
        estado="programado",
        hora_real="",
    ),
)
