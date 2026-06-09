"""Pruebas unitarias de autenticación."""

from __future__ import annotations

import unittest

from rutas_puno.data import CUENTAS
from rutas_puno.security import hash_password, suspender_cuenta, verificar_login


class TestSecurity(unittest.TestCase):
    def test_hash_password_sha256(self) -> None:
        self.assertEqual(len(hash_password("admin123")), 64)

    def test_login_administrador_correcto(self) -> None:
        cuenta = verificar_login(CUENTAS, "admin", "admin123", rol="administrador")
        self.assertIsNotNone(cuenta)
        self.assertEqual(cuenta.rol, "administrador")

    def test_login_con_password_incorrecto(self) -> None:
        cuenta = verificar_login(CUENTAS, "admin", "error", rol="administrador")
        self.assertIsNone(cuenta)

    def test_cuenta_suspendida_no_accede(self) -> None:
        cuentas = suspender_cuenta(CUENTAS, "VAA-501")
        cuenta = verificar_login(cuentas, "chofer1", "clave123", rol="conductor")
        self.assertIsNone(cuenta)


if __name__ == "__main__":
    unittest.main()
