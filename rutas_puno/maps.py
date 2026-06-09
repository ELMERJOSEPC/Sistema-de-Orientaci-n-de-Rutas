"""Utilidades simples para abrir rutas en Google Maps."""

from __future__ import annotations

from urllib.parse import quote_plus

from .models import Linea, Ruta


def google_maps_url(paraderos: tuple[str, ...]) -> str:
    """Crea una URL de Google Maps usando origen, destino y paraderos intermedios."""

    if len(paraderos) < 2:
        raise ValueError("Se necesitan al menos dos paraderos para crear el mapa.")

    origen = quote_plus(f"{paraderos[0]}, Puno, Perú")
    destino = quote_plus(f"{paraderos[-1]}, Puno, Perú")
    intermedios = paraderos[1:-1]

    url = f"https://www.google.com/maps/dir/?api=1&origin={origen}&destination={destino}"
    if intermedios:
        waypoints = quote_plus("|".join(f"{p}, Puno, Perú" for p in intermedios))
        url += f"&waypoints={waypoints}"
    return url


def mapa_linea(linea: Linea, origen: str, destino: str) -> str:
    """Genera una URL de mapa para el tramo de una línea."""

    origen_index = next(i for i, p in enumerate(linea.paraderos) if p.lower() == origen.lower())
    destino_index = next(i for i, p in enumerate(linea.paraderos) if p.lower() == destino.lower())
    inicio, fin = sorted((origen_index, destino_index))
    return google_maps_url(tuple(linea.paraderos[inicio : fin + 1]))


def mapa_ruta(ruta: Ruta) -> str:
    """Genera una URL aproximada para una ruta con transbordos."""

    if not ruta.segmentos:
        raise ValueError("La ruta no contiene segmentos.")

    paraderos = [ruta.segmentos[0].subir]
    paraderos.extend(segmento.bajar for segmento in ruta.segmentos)
    return google_maps_url(tuple(paraderos))
