"""Configuración de logging del proyecto."""

from __future__ import annotations

import logging


def configurar_logging(level: int = logging.INFO) -> None:
    """Activa mensajes de log con formato legible."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
