"""Funciones puras para autenticación y control de cuentas."""

from __future__ import annotations

import hashlib
from typing import Optional, Sequence

from .models import Cuenta


def hash_password(password: str) -> str:
    """Devuelve el hash SHA-256 de una contraseña.

    Args:
        password: Contraseña en texto plano.

    Returns:
        Hash hexadecimal SHA-256.
    """

    if not password:
        raise ValueError("La contraseña no puede estar vacía.")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verificar_login(
    cuentas: Sequence[Cuenta],
    usuario: str,
    password: str,
    rol: Optional[str] = None,
) -> Optional[Cuenta]:
    """Valida credenciales y devuelve la cuenta si el acceso es correcto.

    La función no imprime, no lee archivos y no modifica estados; por eso es
    fácil de probar con unit tests.
    """

    if not usuario or not password:
        return None

    password_hash = hash_password(password)
    for cuenta in cuentas:
        rol_valido = rol is None or cuenta.rol == rol
        if (
            cuenta.usuario == usuario
            and cuenta.clave_hash == password_hash
            and rol_valido
            and not cuenta.suspendido
        ):
            return cuenta
    return None


def suspender_cuenta(cuentas: Sequence[Cuenta], placa: str) -> tuple[Cuenta, ...]:
    """Devuelve una nueva tupla de cuentas con la cuenta del conductor suspendida."""

    return tuple(
        cuenta._replace(suspendido=True) if cuenta.placa == placa else cuenta
        for cuenta in cuentas
    )
