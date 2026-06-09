"""Interfaz gráfica profesional para el Sistema de Orientación de Rutas - Puno.

La GUI actúa como la "cáscara imperativa" del proyecto: lee/guarda archivos,
atiende clics del usuario y muestra resultados. El cálculo importante sigue en
el núcleo funcional puro de ``domain.py``.
"""

from __future__ import annotations

import math
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Iterable, Optional

from . import data as seed_data
from .domain import (
    crear_incidencia,
    marcar_turno,
    paraderos_entre,
    recomendar_linea,
    resolver_incidencia,
    resumen_dashboard,
    tramos_hasta,
)
from .maps import mapa_linea, mapa_ruta
from .models import Cuenta, Incidencia, Linea, Recomendacion, Turno, Vehiculo
from .security import verificar_login
from .storage import (
    StorageError,
    cargar_cuentas,
    cargar_incidencias,
    cargar_lineas,
    cargar_turnos,
    guardar_incidencias,
    guardar_lineas,
    guardar_turnos,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LINEAS_PATH = DATA_DIR / "lineas.json"
INCIDENCIAS_PATH = DATA_DIR / "incidencias.json"
USUARIOS_PATH = DATA_DIR / "usuarios.json"
TURNOS_PATH = DATA_DIR / "turnos.json"

APP_BG = "#f4f7fb"
CARD_BG = "#ffffff"
NAVY = "#0f2942"
PRIMARY = "#006994"
ACCENT = "#0ea5a8"
TEXT = "#1f2937"
MUTED = "#64748b"
DANGER = "#b91c1c"
SUCCESS = "#15803d"
WARNING = "#b45309"


class RutasPunoApp(tk.Tk):
    """Ventana principal del sistema."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Sistema de Orientación de Rutas - Puno")
        self.geometry("1220x780")
        self.minsize(1080, 680)
        self.configure(bg=APP_BG)

        self.lineas: tuple[Linea, ...] = tuple()
        self.incidencias: tuple[Incidencia, ...] = tuple()
        self.cuentas: tuple[Cuenta, ...] = tuple()
        self.turnos: tuple[Turno, ...] = tuple()

        self.conductor_actual: Optional[Cuenta] = None
        self.admin_actual: Optional[Cuenta] = None
        self.ultima_recomendacion: Optional[Recomendacion] = None
        self.ultimo_origen = ""
        self.ultimo_destino = ""

        self._configurar_estilos()
        self._cargar_datos()
        self._crear_interfaz()
        self._refrescar_todo()

    # ------------------------------------------------------------------
    # Configuración y carga de datos
    # ------------------------------------------------------------------
    def _configurar_estilos(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = ("Segoe UI", 10)
        self.option_add("*Font", default_font)

        style.configure("TFrame", background=APP_BG)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        style.configure("Header.TFrame", background=NAVY)
        style.configure("TLabel", background=APP_BG, foreground=TEXT)
        style.configure("Header.TLabel", background=NAVY, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background=NAVY, foreground="#dbeafe", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=CARD_BG, foreground=NAVY, font=("Segoe UI", 12, "bold"))
        style.configure("CardText.TLabel", background=CARD_BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED)
        style.configure("Success.TLabel", background=CARD_BG, foreground=SUCCESS, font=("Segoe UI", 10, "bold"))
        style.configure("Danger.TLabel", background=CARD_BG, foreground=DANGER, font=("Segoe UI", 10, "bold"))
        style.configure("Warning.TLabel", background=CARD_BG, foreground=WARNING, font=("Segoe UI", 10, "bold"))

        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=PRIMARY, foreground="white", bordercolor=PRIMARY)
        style.map("Primary.TButton", background=[("active", "#005a7c")])
        style.configure("Accent.TButton", background=ACCENT, foreground="white", bordercolor=ACCENT)
        style.map("Accent.TButton", background=[("active", "#0b8f92")])
        style.configure("Danger.TButton", background=DANGER, foreground="white", bordercolor=DANGER)
        style.map("Danger.TButton", background=[("active", "#991b1b")])

        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", PRIMARY)])

        style.configure(
            "Treeview",
            background=CARD_BG,
            fieldbackground=CARD_BG,
            foreground=TEXT,
            rowheight=28,
            bordercolor="#e2e8f0",
            borderwidth=1,
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), foreground=NAVY)

        style.configure("TLabelframe", background=APP_BG, bordercolor="#dbe4ef")
        style.configure("TLabelframe.Label", background=APP_BG, foreground=NAVY, font=("Segoe UI", 11, "bold"))

    def _cargar_datos(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self.lineas = cargar_lineas(LINEAS_PATH) or seed_data.LINEAS
            self.incidencias = cargar_incidencias(INCIDENCIAS_PATH) or seed_data.INCIDENCIAS
            self.cuentas = cargar_cuentas(USUARIOS_PATH) or seed_data.CUENTAS
            self.turnos = cargar_turnos(TURNOS_PATH) or seed_data.TURNOS
        except (StorageError, KeyError, ValueError) as exc:
            messagebox.showwarning(
                "Datos de ejemplo cargados",
                "No se pudieron leer correctamente los JSON. "
                "Se usarán datos de prueba.\n\nDetalle: " + str(exc),
            )
            self.lineas = seed_data.LINEAS
            self.incidencias = seed_data.INCIDENCIAS
            self.cuentas = seed_data.CUENTAS
            self.turnos = seed_data.TURNOS

        self._guardar_estado()

    def _guardar_estado(self) -> None:
        guardar_lineas(LINEAS_PATH, self.lineas)
        guardar_incidencias(INCIDENCIAS_PATH, self.incidencias)
        guardar_turnos(TURNOS_PATH, self.turnos)

    # ------------------------------------------------------------------
    # Construcción visual
    # ------------------------------------------------------------------
    def _crear_interfaz(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(22, 16))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Sistema de Orientación de Rutas - Puno",
            style="Header.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Recomendación de líneas, entropía de Shannon, incidencias y control operativo",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self.tab_pasajero = ttk.Frame(self.notebook, padding=14)
        self.tab_conductor = ttk.Frame(self.notebook, padding=14)
        self.tab_admin = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.tab_pasajero, text="Pasajero")
        self.notebook.add(self.tab_conductor, text="Conductor")
        self.notebook.add(self.tab_admin, text="Administrador")

        self._crear_tab_pasajero()
        self._crear_tab_conductor()
        self._crear_tab_admin()

        self.status_var = tk.StringVar(value="Sistema listo.")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(14, 7))
        status.pack(fill="x")

    def _card(self, parent: tk.Widget, padding: int | tuple[int, int] = 14) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=padding)
        return frame

    def _crear_tab_pasajero(self) -> None:
        self.tab_pasajero.columnconfigure(1, weight=1)
        self.tab_pasajero.rowconfigure(0, weight=1)

        left = self._card(self.tab_pasajero)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Consulta de ruta", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            left,
            text="Elige el origen y destino para calcular la línea más directa.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        ttk.Label(left, text="Origen", style="CardText.TLabel").grid(row=2, column=0, sticky="w")
        self.origen_var = tk.StringVar(value="EsSalud Salcedo")
        self.origen_cb = ttk.Combobox(left, textvariable=self.origen_var, width=34, state="readonly")
        self.origen_cb.grid(row=3, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(left, text="Destino", style="CardText.TLabel").grid(row=4, column=0, sticky="w")
        self.destino_var = tk.StringVar(value="Universidad")
        self.destino_cb = ttk.Combobox(left, textvariable=self.destino_var, width=34, state="readonly")
        self.destino_cb.grid(row=5, column=0, sticky="ew", pady=(4, 12))

        ttk.Button(
            left,
            text="Recomendar ruta",
            style="Primary.TButton",
            command=self._accion_recomendar,
        ).grid(row=6, column=0, sticky="ew", pady=(4, 8))

        ttk.Button(
            left,
            text="Abrir recorrido en Google Maps",
            style="Accent.TButton",
            command=self._accion_abrir_mapa,
        ).grid(row=7, column=0, sticky="ew", pady=(0, 18))

        ttk.Separator(left).grid(row=8, column=0, sticky="ew", pady=12)
        ttk.Label(left, text="Incidencias activas", style="CardTitle.TLabel").grid(row=9, column=0, sticky="w")
        self.alertas_text = tk.Text(left, height=8, width=36, wrap="word", relief="flat", bg="#f8fafc")
        self.alertas_text.grid(row=10, column=0, sticky="nsew", pady=(8, 0))
        self.alertas_text.configure(state="disabled")

        right = ttk.Frame(self.tab_pasajero)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)

        result_card = self._card(right)
        result_card.grid(row=0, column=0, sticky="ew")
        result_card.columnconfigure(0, weight=1)
        ttk.Label(result_card, text="Resultado de recomendación", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.resultado_text = tk.Text(result_card, height=9, wrap="word", relief="flat", bg="#f8fafc")
        self.resultado_text.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.resultado_text.configure(state="disabled")

        ttk.Label(right, text="Recorrido sugerido", font=("Segoe UI", 11, "bold"), foreground=NAVY).grid(
            row=1, column=0, sticky="w", pady=(14, 6)
        )
        self.recorrido_tree = ttk.Treeview(
            right,
            columns=("paso", "linea", "paradero", "accion"),
            show="headings",
            height=8,
        )
        self._config_tree(
            self.recorrido_tree,
            {
                "paso": ("Paso", 70),
                "linea": ("Línea", 100),
                "paradero": ("Paradero", 290),
                "accion": ("Acción", 160),
            },
        )
        self.recorrido_tree.grid(row=2, column=0, sticky="nsew")

        ttk.Label(right, text="Alternativas encontradas", font=("Segoe UI", 11, "bold"), foreground=NAVY).grid(
            row=3, column=0, sticky="w", pady=(14, 6)
        )
        self.alternativas_tree = ttk.Treeview(
            right,
            columns=("linea", "color", "costo", "tramos", "frecuencia", "vehiculos"),
            show="headings",
            height=7,
        )
        self._config_tree(
            self.alternativas_tree,
            {
                "linea": ("Línea", 80),
                "color": ("Color", 90),
                "costo": ("Costo", 80),
                "tramos": ("Tramos", 80),
                "frecuencia": ("Frecuencia", 110),
                "vehiculos": ("Vehículos", 200),
            },
        )
        self.alternativas_tree.grid(row=4, column=0, sticky="nsew")

    def _crear_tab_conductor(self) -> None:
        self.tab_conductor.columnconfigure(1, weight=1)
        self.tab_conductor.rowconfigure(0, weight=1)

        login = self._card(self.tab_conductor)
        login.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        login.columnconfigure(0, weight=1)
        ttk.Label(login, text="Acceso de conductor", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.cond_user = tk.StringVar(value="chofer1")
        self.cond_pass = tk.StringVar(value="clave123")
        self.cond_info = tk.StringVar(value="No ha iniciado sesión.")

        ttk.Label(login, text="Usuario", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=(16, 0))
        ttk.Entry(login, textvariable=self.cond_user, width=30).grid(row=2, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(login, text="Contraseña", style="CardText.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(login, textvariable=self.cond_pass, show="*", width=30).grid(row=4, column=0, sticky="ew", pady=(4, 12))
        ttk.Button(login, text="Iniciar sesión", style="Primary.TButton", command=self._login_conductor).grid(
            row=5, column=0, sticky="ew"
        )
        ttk.Label(login, textvariable=self.cond_info, style="Muted.TLabel", wraplength=260).grid(
            row=6, column=0, sticky="w", pady=(14, 0)
        )

        form = self._card(self.tab_conductor)
        form.grid(row=0, column=1, sticky="nsew")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Marcar turno", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        self.turno_programado_var = tk.StringVar(value="08:00")
        self.turno_real_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))
        self.turno_punto_var = tk.StringVar(value="EsSalud Salcedo")

        labels = ["Hora programada (HH:MM)", "Hora real (HH:MM)", "Punto de salida"]
        vars_ = [self.turno_programado_var, self.turno_real_var, self.turno_punto_var]
        for idx, (label, var) in enumerate(zip(labels, vars_), start=1):
            ttk.Label(form, text=label, style="CardText.TLabel").grid(row=idx, column=0, sticky="w", pady=(12, 0))
            if label == "Punto de salida":
                self.turno_punto_cb = ttk.Combobox(form, textvariable=var, state="readonly")
                self.turno_punto_cb.grid(row=idx, column=1, sticky="ew", padx=(12, 0), pady=(12, 0))
            else:
                ttk.Entry(form, textvariable=var).grid(row=idx, column=1, sticky="ew", padx=(12, 0), pady=(12, 0))

        ttk.Button(form, text="Actualizar hora actual", command=self._actualizar_hora_real).grid(
            row=4, column=0, sticky="ew", pady=(16, 8)
        )
        ttk.Button(form, text="Registrar turno", style="Accent.TButton", command=self._marcar_turno).grid(
            row=4, column=1, sticky="ew", padx=(12, 0), pady=(16, 8)
        )

        ttk.Label(form, text="Turnos registrados", style="CardTitle.TLabel").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(18, 8)
        )
        self.turnos_conductor_tree = ttk.Treeview(
            form,
            columns=("linea", "placa", "programada", "real", "punto", "estado"),
            show="headings",
            height=12,
        )
        self._config_tree(
            self.turnos_conductor_tree,
            {
                "linea": ("Línea", 80),
                "placa": ("Placa", 100),
                "programada": ("Programada", 100),
                "real": ("Real", 90),
                "punto": ("Punto", 220),
                "estado": ("Estado", 110),
            },
        )
        self.turnos_conductor_tree.grid(row=6, column=0, columnspan=2, sticky="nsew")
        form.rowconfigure(6, weight=1)

    def _crear_tab_admin(self) -> None:
        self.tab_admin.columnconfigure(0, weight=1)
        self.tab_admin.rowconfigure(2, weight=1)

        top = self._card(self.tab_admin)
        top.grid(row=0, column=0, sticky="ew")
        for col in range(6):
            top.columnconfigure(col, weight=1)

        ttk.Label(top, text="Panel administrativo", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.admin_user = tk.StringVar(value="admin")
        self.admin_pass = tk.StringVar(value="admin123")
        self.admin_info = tk.StringVar(value="Acceso requerido para crear/resolver incidencias y editar líneas.")

        ttk.Entry(top, textvariable=self.admin_user, width=16).grid(row=0, column=1, sticky="ew", padx=(10, 4))
        ttk.Entry(top, textvariable=self.admin_pass, show="*", width=16).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(top, text="Login admin", style="Primary.TButton", command=self._login_admin).grid(
            row=0, column=3, sticky="ew", padx=4
        )
        ttk.Label(top, textvariable=self.admin_info, style="Muted.TLabel").grid(
            row=0, column=4, columnspan=2, sticky="w", padx=(10, 0)
        )

        dash = ttk.Frame(self.tab_admin)
        dash.grid(row=1, column=0, sticky="ew", pady=14)
        for col in range(5):
            dash.columnconfigure(col, weight=1)
        self.dash_vars: dict[str, tk.StringVar] = {}
        for idx, (key, title) in enumerate(
            [
                ("lineas", "Líneas"),
                ("vehiculos", "Vehículos"),
                ("incidencias_activas", "Incidencias activas"),
                ("turnos", "Turnos"),
                ("turnos_criticos", "Turnos críticos"),
            ]
        ):
            card = self._card(dash, padding=(14, 12))
            card.grid(row=0, column=idx, sticky="ew", padx=5)
            var = tk.StringVar(value="0")
            self.dash_vars[key] = var
            ttk.Label(card, text=title, style="Muted.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=var, background=CARD_BG, foreground=PRIMARY, font=("Segoe UI", 20, "bold")).pack(anchor="w")

        body = ttk.PanedWindow(self.tab_admin, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew")

        incidencias_frame = self._card(body)
        lineas_frame = self._card(body)
        body.add(incidencias_frame, weight=1)
        body.add(lineas_frame, weight=1)

        self._crear_admin_incidencias(incidencias_frame)
        self._crear_admin_lineas(lineas_frame)

    def _crear_admin_incidencias(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(6, weight=1)
        ttk.Label(parent, text="Gestión de incidencias", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.inc_tipo = tk.StringVar(value="congestion")
        self.inc_paradero = tk.StringVar(value="Terminal Terrestre")
        self.inc_linea = tk.StringVar(value="")
        self.inc_motivo = tk.StringVar(value="Alta congestión en hora punta")

        fields = [
            ("Tipo", self.inc_tipo),
            ("Paradero bloqueado", self.inc_paradero),
            ("Línea relacionada (opcional)", self.inc_linea),
            ("Motivo", self.inc_motivo),
        ]
        for idx, (label, var) in enumerate(fields, start=1):
            ttk.Label(parent, text=label, style="CardText.TLabel").grid(row=idx, column=0, sticky="w", pady=(8, 0))
            if label == "Paradero bloqueado":
                self.inc_paradero_cb = ttk.Combobox(parent, textvariable=var, state="readonly")
                self.inc_paradero_cb.grid(row=idx, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
            else:
                ttk.Entry(parent, textvariable=var).grid(row=idx, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        buttons = ttk.Frame(parent, style="Card.TFrame")
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 8))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Crear incidencia", style="Accent.TButton", command=self._crear_incidencia_admin).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(buttons, text="Resolver seleccionada", style="Danger.TButton", command=self._resolver_incidencia_admin).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        self.incidencias_tree = ttk.Treeview(
            parent,
            columns=("id", "tipo", "paradero", "linea", "activa", "motivo"),
            show="headings",
            height=13,
        )
        self._config_tree(
            self.incidencias_tree,
            {
                "id": ("ID", 50),
                "tipo": ("Tipo", 90),
                "paradero": ("Paradero", 180),
                "linea": ("Línea", 70),
                "activa": ("Activa", 70),
                "motivo": ("Motivo", 230),
            },
        )
        self.incidencias_tree.grid(row=6, column=0, columnspan=2, sticky="nsew")

    def _crear_admin_lineas(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(8, weight=1)
        ttk.Label(parent, text="CRUD de líneas", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        self.linea_numero = tk.StringVar(value="L99")
        self.linea_color = tk.StringVar(value="Celeste")
        self.linea_costo = tk.StringVar(value="1.00")
        self.linea_frecuencia = tk.StringVar(value="10")
        self.linea_paraderos = tk.StringVar(value="EsSalud Salcedo, Terminal Terrestre, Universidad")
        self.linea_vehiculos = tk.StringVar(value="VZZ-999:25")

        fields = [
            ("Número", self.linea_numero),
            ("Color", self.linea_color),
            ("Costo S/", self.linea_costo),
            ("Frecuencia min", self.linea_frecuencia),
            ("Paraderos separados por coma", self.linea_paraderos),
            ("Vehículos placa:capacidad", self.linea_vehiculos),
        ]
        for idx, (label, var) in enumerate(fields, start=1):
            ttk.Label(parent, text=label, style="CardText.TLabel").grid(row=idx, column=0, sticky="w", pady=(8, 0))
            ttk.Entry(parent, textvariable=var).grid(row=idx, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        buttons = ttk.Frame(parent, style="Card.TFrame")
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 8))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Agregar línea", style="Accent.TButton", command=self._agregar_linea_admin).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(buttons, text="Eliminar seleccionada", style="Danger.TButton", command=self._eliminar_linea_admin).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        self.lineas_tree = ttk.Treeview(
            parent,
            columns=("numero", "color", "costo", "frecuencia", "paraderos", "vehiculos"),
            show="headings",
            height=13,
        )
        self._config_tree(
            self.lineas_tree,
            {
                "numero": ("Número", 80),
                "color": ("Color", 90),
                "costo": ("Costo", 80),
                "frecuencia": ("Frecuencia", 100),
                "paraderos": ("Paraderos", 250),
                "vehiculos": ("Vehículos", 150),
            },
        )
        self.lineas_tree.grid(row=8, column=0, columnspan=2, sticky="nsew")

    # ------------------------------------------------------------------
    # Acciones del pasajero
    # ------------------------------------------------------------------
    def _accion_recomendar(self) -> None:
        origen = self.origen_var.get().strip()
        destino = self.destino_var.get().strip()
        if not origen or not destino:
            messagebox.showerror("Datos incompletos", "Selecciona origen y destino.")
            return

        try:
            recomendacion = recomendar_linea(origen, destino, self.lineas, self.incidencias)
        except ValueError as exc:
            messagebox.showerror("No se puede recomendar", str(exc))
            return

        self.ultima_recomendacion = recomendacion
        self.ultimo_origen = origen
        self.ultimo_destino = destino
        self._mostrar_recomendacion(origen, destino, recomendacion)
        self.status_var.set("Recomendación calculada correctamente.")

    def _mostrar_recomendacion(self, origen: str, destino: str, rec: Recomendacion) -> None:
        self._limpiar_tree(self.recorrido_tree)
        self._limpiar_tree(self.alternativas_tree)

        if rec.recomendada:
            linea = rec.recomendada
            salidas = ", ".join(_proximas_salidas(linea))
            texto = (
                f"✅ Línea recomendada: {linea.numero} ({linea.color})\n"
                f"Origen: {origen}\nDestino: {destino}\n"
                f"Costo estimado: S/ {linea.costo:.2f}\n"
                f"Tramos hasta destino: {rec.tramos}\n"
                f"Frecuencia: cada {linea.frecuencia_min} minutos\n"
                f"Próximas salidas estimadas: {salidas}\n"
                f"Entropía de Shannon: H = {rec.entropia} bits\n\n"
                f"{rec.alerta}\n"
                "La entropía mide cuánta incertidumbre tenía el pasajero antes de elegir. "
                "Mientras más alternativas existan, mayor es la incertidumbre; el sistema la reduce "
                "seleccionando una sola línea eficiente."
            )
            recorrido = paraderos_entre(linea, origen, destino)
            for idx, paradero in enumerate(recorrido, start=1):
                accion = "Subir" if idx == 1 else "Bajar" if idx == len(recorrido) else "Continuar"
                self.recorrido_tree.insert("", "end", values=(idx, linea.numero, paradero, accion))

            for alt in rec.alternativas:
                self.alternativas_tree.insert(
                    "",
                    "end",
                    values=(
                        alt.numero,
                        alt.color,
                        f"S/ {alt.costo:.2f}",
                        tramos_hasta(alt, origen, destino),
                        f"{alt.frecuencia_min} min",
                        ", ".join(v.placa for v in alt.vehiculos),
                    ),
                )
        else:
            ruta = rec.ruta_transbordo
            if ruta is None:
                texto = (
                    "❌ No se encontró una ruta disponible.\n"
                    "Revisa si el origen o destino están bloqueados por una incidencia activa."
                )
            else:
                texto = (
                    "⚠️ No hay línea directa libre. Se encontró una ruta con transbordo.\n"
                    f"Costo total: S/ {ruta.costo_total:.2f}\n"
                    f"Transbordos: {ruta.transbordos}\n"
                    f"Segmentos: {len(ruta.segmentos)}"
                )
                paso = 1
                for segmento in ruta.segmentos:
                    self.recorrido_tree.insert("", "end", values=(paso, segmento.linea, segmento.subir, "Subir"))
                    paso += 1
                    self.recorrido_tree.insert("", "end", values=(paso, segmento.linea, segmento.bajar, "Bajar / transbordar"))
                    paso += 1

        self._set_text(self.resultado_text, texto)

    def _accion_abrir_mapa(self) -> None:
        if not self.ultima_recomendacion:
            messagebox.showinfo("Primero recomienda", "Calcula una ruta antes de abrir el mapa.")
            return

        try:
            if self.ultima_recomendacion.recomendada:
                url = mapa_linea(
                    self.ultima_recomendacion.recomendada,
                    self.ultimo_origen,
                    self.ultimo_destino,
                )
            elif self.ultima_recomendacion.ruta_transbordo:
                url = mapa_ruta(self.ultima_recomendacion.ruta_transbordo)
            else:
                messagebox.showwarning("Sin mapa", "No hay recorrido para abrir.")
                return
            webbrowser.open(url)
            self.status_var.set("Google Maps abierto en el navegador.")
        except Exception as exc:  # pragma: no cover - protección de interfaz
            messagebox.showerror("Error al abrir mapa", str(exc))

    # ------------------------------------------------------------------
    # Acciones del conductor
    # ------------------------------------------------------------------
    def _login_conductor(self) -> None:
        cuenta = verificar_login(
            self.cuentas,
            self.cond_user.get().strip(),
            self.cond_pass.get(),
            rol="conductor",
        )
        if not cuenta:
            self.conductor_actual = None
            self.cond_info.set("Credenciales inválidas o cuenta suspendida.")
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return

        self.conductor_actual = cuenta
        self.cond_info.set(f"Sesión activa: línea {cuenta.linea}, placa {cuenta.placa}.")
        self.status_var.set("Conductor autenticado correctamente.")
        self._refrescar_turnos_conductor()

    def _actualizar_hora_real(self) -> None:
        self.turno_real_var.set(datetime.now().strftime("%H:%M"))

    def _marcar_turno(self) -> None:
        if not self.conductor_actual:
            messagebox.showwarning("Login requerido", "Inicia sesión como conductor primero.")
            return

        try:
            self.turnos = marcar_turno(
                self.turnos,
                linea=self.conductor_actual.linea,
                placa=self.conductor_actual.placa,
                hora_programada=self.turno_programado_var.get().strip(),
                hora_real=self.turno_real_var.get().strip(),
                punto=self.turno_punto_var.get().strip(),
            )
            guardar_turnos(TURNOS_PATH, self.turnos)
        except ValueError as exc:
            messagebox.showerror("Hora inválida", str(exc))
            return

        self._refrescar_todo()
        messagebox.showinfo("Turno registrado", "El turno fue registrado correctamente.")

    # ------------------------------------------------------------------
    # Acciones administrativas
    # ------------------------------------------------------------------
    def _login_admin(self) -> None:
        cuenta = verificar_login(
            self.cuentas,
            self.admin_user.get().strip(),
            self.admin_pass.get(),
            rol="administrador",
        )
        if not cuenta:
            self.admin_actual = None
            self.admin_info.set("Acceso denegado.")
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return
        self.admin_actual = cuenta
        self.admin_info.set(f"Sesión activa: {cuenta.usuario}.")
        self.status_var.set("Administrador autenticado correctamente.")

    def _requiere_admin(self) -> bool:
        if self.admin_actual:
            return True
        messagebox.showwarning("Login requerido", "Inicia sesión como administrador para realizar esta acción.")
        return False

    def _crear_incidencia_admin(self) -> None:
        if not self._requiere_admin():
            return
        paradero = self.inc_paradero.get().strip()
        motivo = self.inc_motivo.get().strip()
        tipo = self.inc_tipo.get().strip() or "congestion"
        if not paradero or not motivo:
            messagebox.showerror("Datos incompletos", "Indica paradero y motivo de la incidencia.")
            return

        self.incidencias = crear_incidencia(
            self.incidencias,
            tipo=tipo,
            paradero=paradero,
            motivo=motivo,
            linea=self.inc_linea.get().strip(),
        )
        guardar_incidencias(INCIDENCIAS_PATH, self.incidencias)
        self._refrescar_todo()
        messagebox.showinfo("Incidencia creada", "La incidencia activa fue registrada.")

    def _resolver_incidencia_admin(self) -> None:
        if not self._requiere_admin():
            return
        item = self._seleccion_unica(self.incidencias_tree, "Selecciona una incidencia.")
        if not item:
            return
        incidencia_id = int(self.incidencias_tree.item(item, "values")[0])
        self.incidencias = resolver_incidencia(self.incidencias, incidencia_id)
        guardar_incidencias(INCIDENCIAS_PATH, self.incidencias)
        self._refrescar_todo()
        messagebox.showinfo("Incidencia resuelta", "La incidencia fue marcada como resuelta.")

    def _agregar_linea_admin(self) -> None:
        if not self._requiere_admin():
            return
        try:
            nueva = self._linea_desde_formulario()
        except ValueError as exc:
            messagebox.showerror("Línea inválida", str(exc))
            return

        if any(linea.numero == nueva.numero for linea in self.lineas):
            messagebox.showerror("Duplicado", f"Ya existe la línea {nueva.numero}.")
            return

        self.lineas = self.lineas + (nueva,)
        guardar_lineas(LINEAS_PATH, self.lineas)
        self._refrescar_todo()
        messagebox.showinfo("Línea agregada", f"La línea {nueva.numero} fue agregada.")

    def _eliminar_linea_admin(self) -> None:
        if not self._requiere_admin():
            return
        item = self._seleccion_unica(self.lineas_tree, "Selecciona una línea.")
        if not item:
            return
        numero = self.lineas_tree.item(item, "values")[0]
        if not messagebox.askyesno("Confirmar eliminación", f"¿Eliminar la línea {numero}?"):
            return
        self.lineas = tuple(linea for linea in self.lineas if linea.numero != numero)
        guardar_lineas(LINEAS_PATH, self.lineas)
        self._refrescar_todo()
        messagebox.showinfo("Línea eliminada", "La línea fue eliminada del JSON.")

    def _linea_desde_formulario(self) -> Linea:
        numero = self.linea_numero.get().strip().upper()
        color = self.linea_color.get().strip().title()
        if not numero or not color:
            raise ValueError("Número y color son obligatorios.")
        try:
            costo = float(self.linea_costo.get().strip())
            frecuencia = int(self.linea_frecuencia.get().strip())
        except ValueError as exc:
            raise ValueError("Costo debe ser decimal y frecuencia debe ser entero.") from exc
        if costo <= 0 or frecuencia <= 0:
            raise ValueError("Costo y frecuencia deben ser mayores que cero.")

        paraderos = tuple(p.strip() for p in self.linea_paraderos.get().split(",") if p.strip())
        if len(paraderos) < 2:
            raise ValueError("Ingresa al menos dos paraderos separados por coma.")

        vehiculos = tuple(_parsear_vehiculos(self.linea_vehiculos.get()))
        return Linea(
            numero=numero,
            color=color,
            costo=round(costo, 2),
            frecuencia_min=frecuencia,
            paraderos=paraderos,
            vehiculos=vehiculos,
        )

    # ------------------------------------------------------------------
    # Refresco de tablas y widgets
    # ------------------------------------------------------------------
    def _refrescar_todo(self) -> None:
        self._refrescar_combos()
        self._refrescar_alertas()
        self._refrescar_dashboard()
        self._refrescar_incidencias()
        self._refrescar_lineas()
        self._refrescar_turnos_conductor()

    def _refrescar_combos(self) -> None:
        paraderos = _paraderos_unicos(self.lineas)
        for combo in (self.origen_cb, self.destino_cb, self.turno_punto_cb, self.inc_paradero_cb):
            combo.configure(values=paraderos)
        if paraderos:
            if self.origen_var.get() not in paraderos:
                self.origen_var.set(paraderos[0])
            if self.destino_var.get() not in paraderos:
                self.destino_var.set(paraderos[-1])
            if self.turno_punto_var.get() not in paraderos:
                self.turno_punto_var.set(paraderos[0])
            if self.inc_paradero.get() not in paraderos:
                self.inc_paradero.set(paraderos[0])

    def _refrescar_alertas(self) -> None:
        activas = [inc for inc in self.incidencias if inc.activa]
        if not activas:
            texto = "No hay incidencias activas. La red opera con normalidad."
        else:
            texto = "\n".join(
                f"• {inc.tipo.upper()} en {inc.paradero}: {inc.motivo}"
                for inc in activas
            )
        self._set_text(self.alertas_text, texto)

    def _refrescar_dashboard(self) -> None:
        resumen = resumen_dashboard(self.lineas, self.incidencias, self.turnos)
        for key, value in resumen.items():
            if key in self.dash_vars:
                self.dash_vars[key].set(str(value))

    def _refrescar_incidencias(self) -> None:
        self._limpiar_tree(self.incidencias_tree)
        for inc in self.incidencias:
            self.incidencias_tree.insert(
                "",
                "end",
                values=(inc.id, inc.tipo, inc.paradero, inc.linea or "-", "Sí" if inc.activa else "No", inc.motivo),
            )

    def _refrescar_lineas(self) -> None:
        self._limpiar_tree(self.lineas_tree)
        for linea in self.lineas:
            self.lineas_tree.insert(
                "",
                "end",
                values=(
                    linea.numero,
                    linea.color,
                    f"S/ {linea.costo:.2f}",
                    f"{linea.frecuencia_min} min",
                    " → ".join(linea.paraderos),
                    ", ".join(v.placa for v in linea.vehiculos),
                ),
            )

    def _refrescar_turnos_conductor(self) -> None:
        self._limpiar_tree(self.turnos_conductor_tree)
        turnos: Iterable[Turno] = self.turnos
        if self.conductor_actual:
            turnos = [t for t in self.turnos if t.placa == self.conductor_actual.placa]
        for turno in turnos:
            self.turnos_conductor_tree.insert(
                "",
                "end",
                values=(turno.linea, turno.placa, turno.hora_programada, turno.hora_real, turno.punto, turno.estado),
            )

    # ------------------------------------------------------------------
    # Utilidades visuales
    # ------------------------------------------------------------------
    def _config_tree(self, tree: ttk.Treeview, columns: dict[str, tuple[str, int]]) -> None:
        for key, (title, width) in columns.items():
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w", stretch=True)

    def _limpiar_tree(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _seleccion_unica(self, tree: ttk.Treeview, mensaje: str) -> Optional[str]:
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Sin selección", mensaje)
            return None
        return selected[0]


def _paraderos_unicos(lineas: Iterable[Linea]) -> list[str]:
    vistos: set[str] = set()
    resultado: list[str] = []
    for linea in lineas:
        for paradero in linea.paraderos:
            clave = paradero.strip().lower()
            if clave not in vistos:
                vistos.add(clave)
                resultado.append(paradero)
    return resultado


def _parsear_vehiculos(texto: str) -> Iterable[Vehiculo]:
    if not texto.strip():
        return tuple()

    vehiculos: list[Vehiculo] = []
    for parte in texto.split(","):
        item = parte.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError("Cada vehículo debe tener formato placa:capacidad. Ejemplo: VAA-100:25")
        placa, capacidad = item.split(":", 1)
        placa = placa.strip().upper()
        try:
            capacidad_int = int(capacidad.strip())
        except ValueError as exc:
            raise ValueError("La capacidad del vehículo debe ser un número entero.") from exc
        if not placa or capacidad_int <= 0:
            raise ValueError("La placa no puede estar vacía y la capacidad debe ser positiva.")
        vehiculos.append(Vehiculo(placa=placa, capacidad=capacidad_int))
    return tuple(vehiculos)


def _proximas_salidas(linea: Linea, cantidad: int = 3) -> tuple[str, ...]:
    ahora = datetime.now()
    apertura = 6 * 60
    cierre = 21 * 60
    actual = ahora.hour * 60 + ahora.minute

    if actual <= apertura:
        siguiente = apertura
    else:
        ciclos = math.ceil((actual - apertura) / linea.frecuencia_min)
        siguiente = apertura + ciclos * linea.frecuencia_min

    salidas: list[str] = []
    for i in range(cantidad):
        minutos = siguiente + i * linea.frecuencia_min
        if minutos > cierre:
            break
        salidas.append(f"{minutos // 60:02d}:{minutos % 60:02d}")
    return tuple(salidas) if salidas else ("Fuera de horario",)


def main() -> None:
    """Punto de entrada de la interfaz gráfica."""

    app = RutasPunoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
