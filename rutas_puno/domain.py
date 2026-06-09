"""Núcleo funcional puro del Sistema de Orientación de Rutas - Puno.

Aquí se concentran las reglas principales: entropía de Shannon, recomendación
de líneas, búsqueda BFS con transbordos, incidencias, turnos y sanciones.
"""

from __future__ import annotations

import math
from collections import deque
from datetime import datetime, time
from typing import Iterable, Optional, Sequence

from .models import Incidencia, Linea, Recomendacion, Reporte, Ruta, Segmento, Turno


HORA_APERTURA = time(6, 0)
HORA_CIERRE = time(21, 0)


def normalizar(texto: str) -> str:
    """Normaliza un texto para comparaciones simples sin modificar el original."""

    return " ".join(texto.strip().lower().split())


def buscar_paradero(linea: Linea, paradero: str) -> Optional[int]:
    """Busca un paradero en una línea y devuelve su índice, o None si no existe."""

    objetivo = normalizar(paradero)
    for indice, nombre in enumerate(linea.paraderos):
        if normalizar(nombre) == objetivo:
            return indice
    return None


def esta_operativo(hora: time) -> bool:
    """Indica si el sistema está dentro del horario de operación 06:00-21:00."""

    return HORA_APERTURA <= hora <= HORA_CIERRE


def entropia_shannon(alternativas: int | Sequence[object]) -> float:
    """Calcula H = log2(n) para alternativas equiprobables.

    Args:
        alternativas: Número de alternativas o secuencia de opciones.

    Returns:
        Entropía en bits. Si no hay alternativas, devuelve 0.
    """

    n = alternativas if isinstance(alternativas, int) else len(alternativas)
    if n <= 0:
        return 0.0
    return round(math.log2(n), 4)


def paraderos_bloqueados(incidencias: Sequence[Incidencia]) -> frozenset[str]:
    """Obtiene el conjunto inmutable de paraderos bloqueados por incidencias activas."""

    return frozenset(
        normalizar(incidencia.paradero)
        for incidencia in incidencias
        if incidencia.activa
    )


def paraderos_entre(linea: Linea, origen: str, destino: str) -> tuple[str, ...]:
    """Devuelve los paraderos recorridos desde origen hasta destino en una línea."""

    i_origen = buscar_paradero(linea, origen)
    i_destino = buscar_paradero(linea, destino)
    if i_origen is None or i_destino is None or i_origen == i_destino:
        return tuple()

    inicio, fin = sorted((i_origen, i_destino))
    return tuple(linea.paraderos[inicio : fin + 1])


def tramos_hasta(linea: Linea, origen: str, destino: str) -> int:
    """Calcula el número de tramos entre origen y destino."""

    i_origen = buscar_paradero(linea, origen)
    i_destino = buscar_paradero(linea, destino)
    if i_origen is None or i_destino is None or i_origen == i_destino:
        return 0
    return abs(i_destino - i_origen)


def cubre_trayecto(linea: Linea, origen: str, destino: str) -> bool:
    """Indica si una línea contiene origen y destino."""

    return tramos_hasta(linea, origen, destino) > 0


def cubre_trayecto_libre(
    linea: Linea,
    origen: str,
    destino: str,
    bloqueados: Iterable[str],
) -> bool:
    """Verifica si una línea cubre el trayecto sin pasar por paraderos bloqueados."""

    bloqueados_set = frozenset(normalizar(p) for p in bloqueados)
    recorrido = paraderos_entre(linea, origen, destino)
    return bool(recorrido) and not any(normalizar(p) in bloqueados_set for p in recorrido)


def buscar_rutas_directas(
    origen: str,
    destino: str,
    lineas: Sequence[Linea],
    bloqueados: Iterable[str],
) -> tuple[Linea, ...]:
    """Filtra líneas directas que evitan incidencias activas."""

    return tuple(
        linea
        for linea in lineas
        if cubre_trayecto_libre(linea, origen, destino, bloqueados)
    )


def elegir_linea_mas_directa(
    directas: Sequence[Linea],
    origen: str,
    destino: str,
) -> Linea:
    """Elige la línea con menor número de tramos y, ante empate, menor costo."""

    if not directas:
        raise ValueError("No hay líneas directas disponibles.")
    return min(directas, key=lambda linea: (tramos_hasta(linea, origen, destino), linea.costo))


def crear_segmento(linea: Linea, origen: str, destino: str) -> Segmento:
    """Crea un segmento inmutable entre dos paraderos usando una línea."""

    if not cubre_trayecto(linea, origen, destino):
        raise ValueError(f"La línea {linea.numero} no cubre {origen} -> {destino}.")
    return Segmento(
        linea=linea.numero,
        color=linea.color,
        subir=origen,
        bajar=destino,
        costo=linea.costo,
        tramos=tramos_hasta(linea, origen, destino),
    )


def construir_ruta(segmentos: Sequence[Segmento]) -> Ruta:
    """Construye una ruta calculando costo total y cantidad de transbordos."""

    segmentos_tuple = tuple(segmentos)
    costo = round(sum(segmento.costo for segmento in segmentos_tuple), 2)
    transbordos = max(0, len(segmentos_tuple) - 1)
    return Ruta(segmentos=segmentos_tuple, costo_total=costo, transbordos=transbordos)


def _paraderos_disponibles(linea: Linea, bloqueados: frozenset[str]) -> tuple[str, ...]:
    """Devuelve los paraderos de una línea excluyendo bloqueados."""

    return tuple(p for p in linea.paraderos if normalizar(p) not in bloqueados)


def expandir_desde_paradero(
    actual: str,
    lineas: Sequence[Linea],
    bloqueados: frozenset[str],
) -> tuple[Segmento, ...]:
    """Genera todos los segmentos posibles desde un paradero actual.

    Se permite avanzar hacia cualquier paradero de la misma línea, evitando
    paraderos bloqueados. Esto representa subir a una línea y bajar más adelante
    o antes, según el sentido disponible.
    """

    segmentos: list[Segmento] = []
    for linea in lineas:
        if buscar_paradero(linea, actual) is None:
            continue
        for destino in _paraderos_disponibles(linea, bloqueados):
            if normalizar(destino) == normalizar(actual):
                continue
            recorrido = paraderos_entre(linea, actual, destino)
            if recorrido and not any(normalizar(p) in bloqueados for p in recorrido):
                segmentos.append(crear_segmento(linea, actual, destino))
    return tuple(segmentos)


def buscar_mejor_ruta(
    origen: str,
    destino: str,
    lineas: Sequence[Linea],
    bloqueados: Iterable[str],
    max_profundidad: int = 4,
) -> Optional[Ruta]:
    """Busca una ruta con transbordos mediante BFS.

    Args:
        origen: Paradero inicial.
        destino: Paradero final.
        lineas: Red de líneas disponibles.
        bloqueados: Paraderos que no pueden ser usados.
        max_profundidad: Máximo de segmentos permitidos para evitar ciclos largos.

    Returns:
        La mejor ruta por menor cantidad de transbordos, costo y tramos; o None.
    """

    bloqueados_set = frozenset(normalizar(p) for p in bloqueados)
    if normalizar(origen) in bloqueados_set or normalizar(destino) in bloqueados_set:
        return None

    frontera = deque([(origen, tuple(), frozenset({normalizar(origen)}))])
    soluciones: list[Ruta] = []

    while frontera:
        actual, segmentos, visitados = frontera.popleft()

        if normalizar(actual) == normalizar(destino):
            soluciones.append(construir_ruta(segmentos))
            continue

        if len(segmentos) >= max_profundidad:
            continue

        for segmento in expandir_desde_paradero(actual, lineas, bloqueados_set):
            siguiente = segmento.bajar
            siguiente_key = normalizar(siguiente)
            if siguiente_key in visitados:
                continue
            nuevos_segmentos = segmentos + (segmento,)
            frontera.append((siguiente, nuevos_segmentos, visitados | {siguiente_key}))

    if not soluciones:
        return None

    return min(
        soluciones,
        key=lambda ruta: (
            ruta.transbordos,
            ruta.costo_total,
            sum(segmento.tramos for segmento in ruta.segmentos),
        ),
    )


def recomendar_linea(
    origen: str,
    destino: str,
    lineas: Sequence[Linea],
    incidencias: Sequence[Incidencia] = (),
) -> Recomendacion:
    """Recomienda la mejor línea directa o una ruta alterna con transbordo.

    Pasos:
    1. Obtiene paraderos bloqueados.
    2. Filtra líneas directas libres de congestión.
    3. Calcula entropía de Shannon sobre las alternativas.
    4. Elige la línea más directa; si no existe, usa BFS con transbordos.
    """

    if normalizar(origen) == normalizar(destino):
        raise ValueError("El origen y el destino no pueden ser iguales.")

    bloqueados = paraderos_bloqueados(incidencias)
    directas = buscar_rutas_directas(origen, destino, lineas, bloqueados)
    entropia = entropia_shannon(directas)

    if directas:
        recomendada = elegir_linea_mas_directa(directas, origen, destino)
        tramos = tramos_hasta(recomendada, origen, destino)
        alerta = (
            f"Se encontraron {len(directas)} alternativa(s). "
            f"La incertidumbre es H={entropia} bits."
        )
        return Recomendacion(
            recomendada=recomendada,
            tramos=tramos,
            alternativas=directas,
            entropia=entropia,
            requiere_transbordo=False,
            ruta_transbordo=None,
            alerta=alerta,
        )

    ruta = buscar_mejor_ruta(origen, destino, lineas, bloqueados)
    alerta = "No hay línea directa libre. Se buscó una ruta con transbordo."
    return Recomendacion(
        recomendada=None,
        tramos=0,
        alternativas=tuple(),
        entropia=0.0,
        requiere_transbordo=True,
        ruta_transbordo=ruta,
        alerta=alerta,
    )


def crear_incidencia(
    incidencias: Sequence[Incidencia],
    tipo: str,
    paradero: str,
    motivo: str,
    linea: str = "",
) -> tuple[Incidencia, ...]:
    """Devuelve una nueva lista de incidencias agregando una incidencia activa."""

    nuevo_id = max((incidencia.id for incidencia in incidencias), default=0) + 1
    nueva = Incidencia(
        id=nuevo_id,
        tipo=tipo,
        paradero=paradero,
        linea=linea,
        motivo=motivo,
        activa=True,
    )
    return tuple(incidencias) + (nueva,)


def resolver_incidencia(
    incidencias: Sequence[Incidencia],
    incidencia_id: int,
) -> tuple[Incidencia, ...]:
    """Devuelve una nueva tupla marcando una incidencia como resuelta."""

    return tuple(
        incidencia._replace(activa=False)
        if incidencia.id == incidencia_id
        else incidencia
        for incidencia in incidencias
    )


def minutos_desde_medianoche(hora_hhmm: str) -> int:
    """Convierte HH:MM a minutos desde medianoche."""

    try:
        hora = datetime.strptime(hora_hhmm, "%H:%M").time()
    except ValueError as exc:
        raise ValueError("La hora debe tener formato HH:MM, por ejemplo 08:30.") from exc
    return hora.hour * 60 + hora.minute


def clasificar_turno(hora_programada: str, hora_real: str) -> str:
    """Clasifica un turno como en tiempo, retrasado o crítico."""

    diferencia = minutos_desde_medianoche(hora_real) - minutos_desde_medianoche(hora_programada)
    if diferencia <= 5:
        return "en tiempo"
    if diferencia <= 15:
        return "retrasado"
    return "crítico"


def marcar_turno(
    turnos: Sequence[Turno],
    linea: str,
    placa: str,
    hora_programada: str,
    hora_real: str,
    punto: str,
) -> tuple[Turno, ...]:
    """Registra un turno devolviendo una nueva tupla inmutable."""

    estado = clasificar_turno(hora_programada, hora_real)
    turno = Turno(
        linea=linea,
        placa=placa,
        hora_programada=hora_programada,
        hora_real=hora_real,
        punto=punto,
        estado=estado,
    )
    return tuple(turnos) + (turno,)


def registrar_sancion(
    reportes: Sequence[Reporte],
    placa: str,
    linea: str,
    motivo: str,
) -> tuple[Reporte, ...]:
    """Registra una sanción administrativa de forma inmutable."""

    nuevo_id = max((reporte.id for reporte in reportes), default=0) + 1
    return tuple(reportes) + (
        Reporte(id=nuevo_id, placa=placa, linea=linea, motivo=motivo, estado="sancionado"),
    )


def debe_suspenderse(reportes: Sequence[Reporte], placa: str, limite: int = 3) -> bool:
    """Indica si una placa debe suspenderse tras alcanzar el límite de sanciones."""

    total = sum(
        1
        for reporte in reportes
        if reporte.placa == placa and reporte.estado == "sancionado"
    )
    return total >= limite


def resumen_dashboard(
    lineas: Sequence[Linea],
    incidencias: Sequence[Incidencia],
    turnos: Sequence[Turno],
) -> dict[str, int]:
    """Genera conteos para un dashboard administrativo simple."""

    return {
        "lineas": len(lineas),
        "vehiculos": sum(len(linea.vehiculos) for linea in lineas),
        "incidencias_activas": sum(1 for incidencia in incidencias if incidencia.activa),
        "turnos": len(turnos),
        "turnos_criticos": sum(1 for turno in turnos if turno.estado == "crítico"),
    }
