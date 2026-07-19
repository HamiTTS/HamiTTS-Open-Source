import os
import json
import inspect
import time
import shutil
import tempfile
import threading
import subprocess
import webbrowser
import http.server
import socketserver
import urllib.parse
import atexit
from types import SimpleNamespace
from typing import Optional
import flet as ft

import sys

try:
    import winreg
except ImportError:
    winreg = None

try:
    import win32com.client
    _WIN32COM_DISPONIBLE = True
except ImportError:
    _WIN32COM_DISPONIBLE = False

_CARPETA_TEMPORAL = tempfile.mkdtemp(prefix="hamitts_fondo_")

class _ManejadorSilencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def _iniciar_servidor_local(directorio: str) -> int:
    manejador = lambda *args, **kwargs: _ManejadorSilencioso(*args, directory=directorio, **kwargs)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), manejador)
    puerto = httpd.server_address[1]
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    return puerto

_PUERTO_SERVIDOR = _iniciar_servidor_local(_CARPETA_TEMPORAL)

def _publicar_archivo_local(ruta_original: str) -> str:
    nombre_original = os.path.basename(ruta_original)
    nombre_unico = f"{int(time.time() * 1000)}_{nombre_original}"
    destino = os.path.join(_CARPETA_TEMPORAL, nombre_unico)
    shutil.copyfile(ruta_original, destino)
    return f"http://127.0.0.1:{_PUERTO_SERVIDOR}/{urllib.parse.quote(nombre_unico)}"

async def _invocar(resultado):
    if inspect.isawaitable(resultado):
        return await resultado
    return resultado

def _crear_dropdown(*, options, value, width, bgcolor, border_color, color, on_change, disabled=False):
    dd = ft.Dropdown(
        options=options,
        value=value,
        width=width,
        bgcolor=bgcolor,
        border_color=border_color,
        color=color,
    )
    dd.on_change = on_change
    dd.disabled = disabled
    return dd

EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

OPACIDAD_MIN = 0.0
OPACIDAD_MAX = 1.0
OPACIDAD_DEFECTO = 0.25
ANCHO_SLIDER_OPACIDAD = 400

ALFA_MIN = 0.04
ALFA_MAX = 0.55
BLUR_MIN = 0
BLUR_MAX = 22

def _alfa_desde_nivel(nivel: float) -> float:
    return ALFA_MIN + nivel * (ALFA_MAX - ALFA_MIN)

def _blur_desde_nivel(nivel: float) -> float:
    return BLUR_MIN + nivel * (BLUR_MAX - BLUR_MIN)

_CARPETA_CONFIG = os.path.join(os.path.expanduser("~"), ".hamitts")
_ARCHIVO_CONFIG = os.path.join(_CARPETA_CONFIG, "config.json")

def _cargar_configuracion() -> dict:
    try:
        with open(_ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, dict):
                return datos
    except Exception:
        pass
    return {}

def _guardar_configuracion(datos: dict) -> None:
    try:
        os.makedirs(_CARPETA_CONFIG, exist_ok=True)
        with open(_ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(datos, f)
    except Exception:
        pass

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_NAVEGADORES = os.path.join(BASE_DIR, "Navegadores y activadores")
CARPETA_CABLE_TEMPORAL = os.path.join(CARPETA_NAVEGADORES, "Cable virtual (temporal)")

ARCHIVO_HISTORIAL = os.path.join(BASE_DIR, "historial_tts.txt")

def _rutas_candidatas_logo() -> list:
    candidatas = [os.path.join(BASE_DIR, "logo.ico")]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidatas.append(os.path.join(meipass, "logo.ico"))

    if not getattr(sys, "frozen", False):
        candidatas.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico"))

    return candidatas

def obtener_ruta_icono_estable() -> Optional[str]:
    origen = next((ruta for ruta in _rutas_candidatas_logo() if os.path.isfile(ruta)), None)

    try:
        os.makedirs(_CARPETA_CONFIG, exist_ok=True)
        destino = os.path.join(_CARPETA_CONFIG, "logo.ico")

        if origen:
            necesita_copia = (
                not os.path.isfile(destino)
                or os.path.getsize(destino) != os.path.getsize(origen)
                or os.path.getmtime(origen) > os.path.getmtime(destino)
            )
            if necesita_copia:
                shutil.copyfile(origen, destino)

        if os.path.isfile(destino):
            return destino
    except Exception:
        pass

    return origen

def crear_acceso_directo_escritorio() -> None:
    if not _WIN32COM_DISPONIBLE or os.name != "nt":
        return
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        ruta_escritorio = shell.SpecialFolders("Desktop")
        ruta_acceso_directo = os.path.join(ruta_escritorio, "HamiTTS.lnk")

        acceso_directo = shell.CreateShortCut(ruta_acceso_directo)

        if getattr(sys, "frozen", False):
            acceso_directo.TargetPath = sys.executable
            acceso_directo.WorkingDirectory = BASE_DIR
        else:
            acceso_directo.TargetPath = sys.executable
            acceso_directo.Arguments = f'"{os.path.abspath(__file__)}"'
            acceso_directo.WorkingDirectory = BASE_DIR

        ruta_icono = obtener_ruta_icono_estable()
        if ruta_icono:
            acceso_directo.IconLocation = f"{ruta_icono}, 0"
        elif getattr(sys, "frozen", False):
            acceso_directo.IconLocation = f"{sys.executable}, 0"

        acceso_directo.Description = "Lanzador de HamiTTS"
        acceso_directo.Save()
    except Exception:
        pass

MAPA_CARPETA_NAVEGADOR = {
    "Opera GX / Opera": "Opera and OperaGX",
    "Google Chrome": "Chrome",
    "Microsoft Edge": "Edge",
    "Mozilla Firefox": "Firefox",
    "Brave Browser": "Brave",
}
MAPA_PREFIJO_NAVEGADOR = {
    "Opera GX / Opera": "OperaGX",
    "Google Chrome": "Chrome",
    "Microsoft Edge": "Edge",
    "Mozilla Firefox": "Firefox",
    "Brave Browser": "Brave",
}

MAPA_SUFIJO_TECLA = {"Español": "latino", "Inglés": "ingles"}
MAPA_CARACTER_TECLA = {"Español": "-", "Inglés": "/"}

def detectar_ahk_instalado() -> bool:
    if obtener_ruta_autohotkey_exe() is not None:
        return True

    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".ahk"):
            return True
    except OSError:
        return False

def detectar_cable_virtual_instalado() -> bool:
    try:
        comando = (
            'powershell -Command "Get-PnpDevice -PresentOnly -FriendlyName '
            "'*VB-Audio Virtual Cable*' -ErrorAction SilentlyContinue "
            "| Where-Object { $_.Status -eq 'OK' }\""
        )
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return "VB-Audio" in resultado.stdout
    except Exception as ex:
        return False

def obtener_ruta_autohotkey_exe() -> Optional[str]:
    es_sistema_64 = os.environ.get("PROGRAMFILES(X86)") is not None
    candidatos = ["AutoHotkey64.exe", "AutoHotkey32.exe"] if es_sistema_64 else ["AutoHotkey32.exe", "AutoHotkey64.exe"]
    for nombre in candidatos:
        ruta = os.path.join(CARPETA_NAVEGADORES, nombre)
        if os.path.isfile(ruta):
            return ruta
    return None

def limpiar_carpeta_cable_temporal_si_corresponde() -> None:
    try:
        if detectar_cable_virtual_instalado() and os.path.isdir(CARPETA_CABLE_TEMPORAL):
            shutil.rmtree(CARPETA_CABLE_TEMPORAL)
    except Exception:
        pass

def main(page: ft.Page):
    page.title = "HamiTTS v1.2"
    page.padding = 0
    page.window.resizable = True
    page.window.min_width = 950
    page.window.min_height = 650
    page.window.width = 1150
    page.window.height = 720
    page.theme_mode = ft.ThemeMode.DARK

    _ruta_icono = obtener_ruta_icono_estable()
    if _ruta_icono:
        try:
            page.window.icon = _ruta_icono
        except Exception:
            pass
    else:
        pass

    def mostrar_snackbar(mensaje: str):
        snack = ft.SnackBar(ft.Text(mensaje))
        try:
            if hasattr(page, "show_dialog"):
                page.show_dialog(snack)
            elif hasattr(page, "open"):
                page.open(snack)
            else:
                page.snack_bar = snack
                snack.open = True
                page.update()
        except Exception:
            pass

    config_guardada = _cargar_configuracion()

    def _recortar_opacidad(valor: float) -> float:
        return max(OPACIDAD_MIN, min(OPACIDAD_MAX, valor))

    limpiar_carpeta_cable_temporal_si_corresponde()

    estado = {
        "color_acento": config_guardada.get("color_acento", "#00E5FF"),
        "vista_actual": "Inicio",
        "fondo_url": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=1920",
        "fondo_ruta_original": config_guardada.get("fondo_ruta_original"),
        "opacidad_panel": _recortar_opacidad(config_guardada.get("opacidad_panel", OPACIDAD_DEFECTO)),
        "sidebar_abierta": True,
        "ahk_instalado": detectar_ahk_instalado(),
        "cable_instalado": detectar_cable_virtual_instalado(),
        "navegador_seleccionado": "Opera GX / Opera",
        "tecla_seleccionada": "Español",
        "motor_activo": False,
        "frases_inyectadas": 0,
        "proceso_ahk": None,
        "formato_hora": config_guardada.get("formato_hora", "12h"),
    }

    refs = {}

    def _guardar_estado_actual():
        _guardar_configuracion(
            {
                "fondo_ruta_original": estado.get("fondo_ruta_original"),
                "opacidad_panel": estado.get("opacidad_panel", OPACIDAD_DEFECTO),
                "color_acento": estado.get("color_acento", "#00E5FF"),
                "formato_hora": estado.get("formato_hora", "12h"),
            }
        )

    def btn_hover(e):
        objetivo = 1.05 if e.data == "true" else 1.0
        if e.control.scale != objetivo:
            e.control.scale = objetivo
            e.control.update()

    _paneles_cristal = []
    _paneles_permanentes = []

    def panel_cristal(content, width=None, height=None, padding=25, expand=False, persistente=False):
        nivel = estado["opacidad_panel"]
        radio_blur = _blur_desde_nivel(nivel)
        panel = ft.Container(
            content=content,
            width=width,
            height=height,
            padding=padding,
            expand=expand,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(_alfa_desde_nivel(nivel), "#000B18"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            blur=ft.Blur(radio_blur, radio_blur, ft.BlurTileMode.MIRROR),
        )
        if persistente:
            _paneles_permanentes.append(panel)
        else:
            _paneles_cristal.append(panel)
        return panel

    def _aplicar_opacidad_en_vivo(nivel: float):
        estado["opacidad_panel"] = nivel
        radio_blur = _blur_desde_nivel(nivel)
        alfa = _alfa_desde_nivel(nivel)
        for panel in _paneles_cristal + _paneles_permanentes:
            panel.bgcolor = ft.Colors.with_opacity(alfa, "#000B18")
            panel.blur = ft.Blur(radio_blur, radio_blur, ft.BlurTileMode.MIRROR)
            try:
                panel.update()
            except Exception:
                pass

    capa_dialogos = ft.Container(expand=True, visible=False)

    def mostrar_overlay(contenido):
        capa_dialogos.content = ft.Container(
            content=contenido,
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.with_opacity(0.65, "#000000"),
            on_click=lambda e: None,
        )
        capa_dialogos.visible = True
        capa_dialogos.update()

    def ocultar_overlay():
        capa_dialogos.visible = False
        capa_dialogos.content = None
        capa_dialogos.update()

    def panel_dialogo(icono, titulo, mensaje, botones, color_icono=None):
        filas_botones = []
        for texto, manejador, es_primario in botones:
            filas_botones.append(
                ft.Container(
                    content=ft.Text(
                        texto,
                        size=13,
                        weight=ft.FontWeight.W_800,
                        color="#000B18" if es_primario else ft.Colors.WHITE,
                        no_wrap=True,
                    ),
                    alignment=ft.Alignment.CENTER,
                    height=46,
                    padding=ft.Padding.symmetric(horizontal=16),
                    border_radius=10,
                    bgcolor=estado["color_acento"] if es_primario else ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    border=None if es_primario else ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                    on_click=manejador,
                    ink=True,
                    on_hover=btn_hover,
                    animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                    scale=1.0,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icono, color=color_icono or estado["color_acento"], size=42),
                    ft.Container(height=10),
                    ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Text(mensaje, size=13, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    ft.Row(
                        filas_botones,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                        run_spacing=12,
                        wrap=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            width=520,
            padding=30,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.55, "#000B18"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
            blur=ft.Blur(18, 18, ft.BlurTileMode.MIRROR),
        )

    def mostrar_bloqueo_ahk():

        async def cerrar_programa(e):
            try:
                _cerrar_ahk_al_salir()
            except Exception:
                pass
            try:
                await _invocar(page.window.destroy())
            except Exception:
                try:
                    page.window.prevent_close = False
                    await _invocar(page.window.close())
                except Exception:
                    pass
            os._exit(0)

        def abrir_pagina_ahk(e):
            webbrowser.open("https://www.autohotkey.com")

        mostrar_overlay(
            panel_dialogo(
                icono=ft.Icons.WARNING_ROUNDED,
                color_icono=ft.Colors.RED_ACCENT_400,
                titulo="AutoHotkey no está instalado",
                mensaje=(
                    "HamiTTS necesita AutoHotkey instalado en este equipo para poder "
                    "inyectar el texto en Roblox. Instálalo y vuelve a abrir el "
                    "programa: no es posible continuar sin él."
                ),
                botones=[
                    ("Instalar AutoHotkey v2.0 aquí", abrir_pagina_ahk, False),
                    ("Cerrar Programa", cerrar_programa, True),
                ],
            )
        )

    capa_imagen = ft.Container(
        expand=True,
        image=ft.DecorationImage(src=estado["fondo_url"], fit="cover"),
        clip_behavior="hardEdge",
    )

    ruta_guardada = estado.get("fondo_ruta_original")
    if ruta_guardada and os.path.exists(ruta_guardada):
        try:
            url_inicial = _publicar_archivo_local(ruta_guardada)
            estado["fondo_url"] = url_inicial
            capa_imagen.image = ft.DecorationImage(src=url_inicial, fit="cover")
        except Exception:
            pass

    async def cambiar_fondo(e):

        try:
            archivos = getattr(e, "files", None)

            if not archivos:
                return

            archivo = archivos[0]
            ruta = archivo.path

            extension = os.path.splitext(ruta)[1].lower().lstrip(".")

            if extension not in EXTENSIONES_IMAGEN:
                mostrar_snackbar(f"Formato no soportado: .{extension}")
                return

            url = _publicar_archivo_local(ruta)

            estado["fondo_url"] = url
            estado["fondo_ruta_original"] = ruta

            capa_imagen.image = ft.DecorationImage(src=url, fit="cover")
            capa_imagen.update()

            _guardar_estado_actual()

        except Exception as ex:
            import traceback
            traceback.print_exc()

    selector_archivos = ft.FilePicker()
    selector_archivos.on_result = cambiar_fondo
    if hasattr(page, "services"):
        page.services.append(selector_archivos)
    else:
        page.overlay.append(selector_archivos)

    async def abrir_explorador(e):
        resultado = await _invocar(
            selector_archivos.pick_files(
                dialog_title="Selecciona una imagen de fondo",
                allow_multiple=False,
                allowed_extensions=list(EXTENSIONES_IMAGEN),
            )
        )

        archivos = None
        if isinstance(resultado, list):
            archivos = resultado
        elif resultado is not None:
            archivos = getattr(resultado, "files", None)

        if archivos:
            await cambiar_fondo(SimpleNamespace(files=archivos))
        else:
            pass

    def _resetear_historial_archivo():
        try:
            os.makedirs(os.path.dirname(ARCHIVO_HISTORIAL), exist_ok=True)
            with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8"):
                pass
        except Exception:
            pass

    def _leer_historial():
        entradas = []
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8", errors="ignore") as f:
                for linea in f:
                    linea = linea.rstrip("\r\n")
                    if not linea.strip():
                        continue
                    if "\t" in linea:
                        hora, frase = linea.split("\t", 1)
                    else:
                        hora, frase = "", linea
                    entradas.append((hora, frase))
        except Exception:
            pass
        return entradas

    def _formatear_hora_para_mostrar(hora_cruda: str) -> str:
        if not hora_cruda:
            return hora_cruda
        if estado.get("formato_hora", "12h") != "12h":
            return hora_cruda
        try:
            partes = hora_cruda.split(":")
            hora24 = int(partes[0])
            resto = ":".join(partes[1:]) if len(partes) > 1 else "00"
            sufijo = "a. m." if hora24 < 12 else "p. m."
            hora12 = hora24 % 12
            if hora12 == 0:
                hora12 = 12
            return f"{hora12:02d}:{resto} {sufijo}"
        except Exception:
            return hora_cruda

    def _construir_tarjetas_historial(entradas):
        if not entradas:
            return [
                ft.Container(
                    content=ft.Text(
                        "Aún no se ha inyectado ninguna frase en esta sesión.",
                        color=ft.Colors.WHITE54,
                        size=13,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=30,
                )
            ]

        tarjetas = []
        for hora, frase in reversed(entradas):
            tarjetas.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    _formatear_hora_para_mostrar(hora) or "--:--:--",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=estado["color_acento"],
                                ),
                                width=90,
                            ),
                            ft.Text(frase, size=13, color=ft.Colors.WHITE, expand=True, selectable=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(vertical=10, horizontal=14),
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                )
            )
        return tarjetas

    def _hilo_vigilar_historial():
        ultima_marca = None
        while True:
            try:
                marca = os.path.getmtime(ARCHIVO_HISTORIAL)
            except Exception:
                marca = None

            if marca != ultima_marca:
                ultima_marca = marca
                entradas = _leer_historial()
                estado["frases_inyectadas"] = len(entradas)

                texto_contador = refs.get("texto_contador")
                if texto_contador is not None and estado["vista_actual"] == "Inicio":
                    try:
                        texto_contador.value = str(len(entradas))
                        texto_contador.update()
                    except Exception:
                        pass

                lista_historial = refs.get("lista_historial")
                if lista_historial is not None and estado["vista_actual"] == "Frases Rápidas":
                    try:
                        lista_historial.controls = _construir_tarjetas_historial(entradas)
                        lista_historial.update()
                    except Exception:
                        pass

            time.sleep(1)

    def _terminar_proceso_ahk():
        proceso = estado.get("proceso_ahk")
        if proceso is not None:
            try:
                proceso.terminate()
            except Exception:
                pass
            estado["proceso_ahk"] = None

    def _cerrar_ahk_al_salir():
        _terminar_proceso_ahk()
        for nombre_exe in ("AutoHotkey.exe", "AutoHotkey64.exe", "AutoHotkey32.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", nombre_exe, "/T"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            except Exception:
                pass

    atexit.register(_cerrar_ahk_al_salir)

    async def _al_cerrar_ventana(e):
        tipo = str(getattr(e, "type", "") or getattr(e, "data", "")).lower()
        if "close" not in tipo:
            return
        _cerrar_ahk_al_salir()
        try:
            await _invocar(page.window.destroy())
        except Exception:
            try:
                await _invocar(page.window.close())
            except Exception:
                pass

    try:
        page.window.prevent_close = True
        page.window.on_event = _al_cerrar_ventana
    except Exception:
        pass

    def detener_tts():
        estado["motor_activo"] = False
        _terminar_proceso_ahk()
        actualizar_interfaz()

    def iniciar_tts(e):
        if estado.get("motor_activo"):
            detener_tts()
            return

        if not estado.get("ahk_instalado"):
            mostrar_bloqueo_ahk()
            return

        dropdown_navegador = refs.get("dropdown_navegador")
        if dropdown_navegador is not None and dropdown_navegador.value:
            estado["navegador_seleccionado"] = dropdown_navegador.value

        dropdown_tecla = refs.get("dropdown_tecla")
        if dropdown_tecla is not None and dropdown_tecla.value:
            estado["tecla_seleccionada"] = dropdown_tecla.value

        navegador = estado.get("navegador_seleccionado")
        tecla = estado.get("tecla_seleccionada")

        carpeta_nav = MAPA_CARPETA_NAVEGADOR.get(navegador)
        prefijo_nav = MAPA_PREFIJO_NAVEGADOR.get(navegador)
        sufijo_tecla = MAPA_SUFIJO_TECLA.get(tecla)

        if not (carpeta_nav and prefijo_nav and sufijo_tecla):
            mostrar_snackbar("Selecciona un navegador y una tecla de activación válidos.")
            return

        nombre_script = f"{prefijo_nav} roblox {sufijo_tecla}.ahk"
        ruta_script = os.path.join(CARPETA_NAVEGADORES, carpeta_nav, nombre_script)

        if not os.path.isfile(ruta_script):
            mostrar_snackbar(f"No se encontró el script: {nombre_script}")
            return

        ruta_ahk_exe = obtener_ruta_autohotkey_exe()
        if not ruta_ahk_exe:
            mostrar_snackbar("No se encontró AutoHotkey32.exe / AutoHotkey64.exe en 'Navegadores y activadores'.")
            return

        if not estado.get("cable_instalado"):
            mostrar_snackbar("Aviso: el Cable Virtual no está conectado, puede que no se escuche el audio en Roblox.")

        _resetear_historial_archivo()
        estado["frases_inyectadas"] = 0

        lista_historial = refs.get("lista_historial")
        if lista_historial is not None and estado["vista_actual"] == "Frases Rápidas":
            try:
                lista_historial.controls = _construir_tarjetas_historial([])
                lista_historial.update()
            except Exception:
                pass

        try:
            proceso = subprocess.Popen([ruta_ahk_exe, ruta_script], cwd=os.path.dirname(ruta_script))
        except Exception as ex:
            mostrar_snackbar(f"No se pudo iniciar el script: {ex}")
            return

        estado["proceso_ahk"] = proceso
        estado["motor_activo"] = True
        actualizar_interfaz()

        try:
            webbrowser.open("https://fish.audio/es/app/")
        except Exception:
            pass

    def _actualizar_estado_dependencias():
        estado["ahk_instalado"] = detectar_ahk_instalado()
        estado["cable_instalado"] = detectar_cable_virtual_instalado()

    def _hilo_monitor_dependencias():
        while True:
            nuevo_valor = detectar_cable_virtual_instalado()
            if nuevo_valor != estado.get("cable_instalado"):
                estado["cable_instalado"] = nuevo_valor
                if estado["vista_actual"] in ("Inicio", "Herramientas"):
                    try:
                        actualizar_interfaz()
                    except Exception:
                        pass
            time.sleep(4)

    area_contenido = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=500,
        reverse_duration=300,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        expand=True,
    )

    def construir_vista_inicio():
        tarjeta_ruta = panel_cristal(
            content=ft.Column(
                [
                    ft.Text("RUTA DE SISTEMA", color=ft.Colors.WHITE54, size=10, weight=ft.FontWeight.W_800),
                    ft.Row(
                        [
                            ft.Text("Navegador", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=estado["color_acento"], size=14),
                            ft.Text("Cable Virtual", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=estado["color_acento"], size=14),
                            ft.Text("Roblox Voice", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=120,
        )

        def _cambiar_navegador(e):
            estado["navegador_seleccionado"] = e.control.value

        def _cambiar_tecla(e):
            estado["tecla_seleccionada"] = e.control.value

        motor_activo = estado.get("motor_activo", False)
        etiqueta_boton = "DETENER TTS" if motor_activo else "INICIAR TTS"
        color_boton = ft.Colors.RED_ACCENT_400 if motor_activo else estado["color_acento"]
        color_texto_boton = ft.Colors.WHITE if motor_activo else "#000B18"

        dropdown_navegador = _crear_dropdown(
            options=[
                ft.DropdownOption(key="Opera GX / Opera", text="Opera GX / Opera"),
                ft.DropdownOption(key="Google Chrome", text="Google Chrome"),
                ft.DropdownOption(key="Microsoft Edge", text="Microsoft Edge"),
                ft.DropdownOption(key="Mozilla Firefox", text="Mozilla Firefox"),
                ft.DropdownOption(key="Brave Browser", text="Brave Browser"),
            ],
            value=estado["navegador_seleccionado"],
            width=440,
            bgcolor=ft.Colors.with_opacity(0.3, "#000000"),
            border_color=estado["color_acento"],
            color=ft.Colors.WHITE,
            on_change=_cambiar_navegador,
            disabled=motor_activo,
        )
        refs["dropdown_navegador"] = dropdown_navegador

        dropdown_tecla = _crear_dropdown(
            options=[
                ft.DropdownOption(key="Español", text="Español Latinoamérica (Tecla '-')"),
                ft.DropdownOption(key="Inglés", text="Inglés (Tecla '/')"),
            ],
            value=estado["tecla_seleccionada"],
            width=440,
            bgcolor=ft.Colors.with_opacity(0.3, "#000000"),
            border_color=estado["color_acento"],
            color=ft.Colors.WHITE,
            on_change=_cambiar_tecla,
            disabled=motor_activo,
        )
        refs["dropdown_tecla"] = dropdown_tecla

        config_panel = panel_cristal(
            content=ft.Column(
                [
                    ft.Text("Configuración de Inyección", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), height=20),
                    ft.Text("Navegador de origen:", color=ft.Colors.WHITE70, size=12),
                    dropdown_navegador,
                    ft.Container(height=10),
                    ft.Text("Tecla de activación:", color=ft.Colors.WHITE70, size=12),
                    dropdown_tecla,
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Text(etiqueta_boton, size=14, weight=ft.FontWeight.W_900, color=color_texto_boton),
                        alignment=ft.Alignment.CENTER,
                        height=50,
                        border_radius=10,
                        bgcolor=color_boton,
                        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                        scale=1.0,
                        on_hover=btn_hover,
                        on_click=iniciar_tts,
                        ink=True,
                        shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=color_boton, offset=ft.Offset(0, 0)),
                    ),
                ]
            ),
        )

        def indicador(texto_activo, texto_inactivo, activo, clave):
            color = ft.Colors.GREEN_ACCENT_400 if activo else ft.Colors.RED_ACCENT_400
            icono = ft.Icon(ft.Icons.CIRCLE, color=color, size=12)
            texto = ft.Text(texto_activo if activo else texto_inactivo, color=ft.Colors.WHITE, size=13)
            refs[f"icono_{clave}"] = icono
            refs[f"texto_{clave}"] = texto
            return ft.Row([icono, texto])

        texto_contador = ft.Text(
            str(estado.get("frases_inyectadas", 0)),
            size=45,
            weight=ft.FontWeight.W_900,
            color=estado["color_acento"],
        )
        refs["texto_contador"] = texto_contador

        estado_panel = panel_cristal(
            content=ft.Column(
                [
                    ft.Text("Sistema", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), height=20),
                    indicador("AutoHotkey Detectado", "AutoHotkey No Detectado", estado.get("ahk_instalado", False), "ahk"),
                    ft.Container(height=10),
                    indicador("Cable Conectado", "Cable Desconectado", estado.get("cable_instalado", False), "cable"),
                    ft.Container(height=30),
                    ft.Text("Sesión", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), height=20),
                    texto_contador,
                    ft.Text("Frases inyectadas", color=ft.Colors.WHITE70, size=11),
                ]
            ),
        )

        config_col = ft.Column([tarjeta_ruta, config_panel], expand=2, spacing=20)
        sistema_col = ft.Column([estado_panel], expand=1)

        return ft.Row([config_col, sistema_col], spacing=30, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)

    def construir_vista_personalizacion():
        def cambiar_color(e):
            estado["color_acento"] = e.control.bgcolor
            _guardar_estado_actual()
            actualizar_interfaz()

        def crear_circulo_color(color_hex):
            return ft.Container(
                width=40,
                height=40,
                border_radius=20,
                bgcolor=color_hex,
                animate_scale=ft.Animation(200, ft.AnimationCurve.BOUNCE_OUT),
                scale=1.0,
                on_hover=btn_hover,
                on_click=cambiar_color,
                ink=True,
                border=ft.Border.all(2, ft.Colors.WHITE) if estado["color_acento"] == color_hex else None,
            )

        colores_filas = [
            ["#00E5FF", "#FF3366", "#B026FF", "#00E676", "#FFEA00", "#FFFFFF"],
            ["#FF4FA3", "#FF8C00", "#2979FF", "#00BFA5", "#7C4DFF", "#C6FF00"],
            ["#FFB3C6", "#A0C4FF", "#BDB2FF", "#CAFFBF", "#FDFFB6", "#FFD6A5"],
        ]

        def _porcentaje(valor: float) -> int:
            return int(((valor - OPACIDAD_MIN) / (OPACIDAD_MAX - OPACIDAD_MIN)) * 100)

        etiqueta_valor = ft.Text(
            f"{_porcentaje(estado['opacidad_panel'])}%",
            color=estado["color_acento"],
            size=13,
            weight=ft.FontWeight.BOLD,
        )

        def al_mover_slider(e):
            valor = float(e.control.value)
            _aplicar_opacidad_en_vivo(valor)
            etiqueta_valor.value = f"{_porcentaje(valor)}%"
            etiqueta_valor.update()

        def al_soltar_slider(e):
            _guardar_estado_actual()

        slider_opacidad = ft.Slider(
            min=OPACIDAD_MIN,
            max=OPACIDAD_MAX,
            value=estado["opacidad_panel"],
            width=ANCHO_SLIDER_OPACIDAD,
            active_color=estado["color_acento"],
            on_change=al_mover_slider,
            on_change_end=al_soltar_slider,
        )

        def restablecer_opacidad(e):
            slider_opacidad.value = OPACIDAD_DEFECTO
            slider_opacidad.update()
            _aplicar_opacidad_en_vivo(OPACIDAD_DEFECTO)
            etiqueta_valor.value = f"{_porcentaje(OPACIDAD_DEFECTO)}%"
            etiqueta_valor.update()
            _guardar_estado_actual()

        control_opacidad = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Opacidad del panel", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD),
                        etiqueta_valor,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=15,
                ),
                slider_opacidad,
                ft.Container(height=8),
                ft.TextButton(
                    "Restablecer a valor predeterminado",
                    icon=ft.Icons.RESTART_ALT_ROUNDED,
                    on_click=restablecer_opacidad,
                ),
            ],
            spacing=6,
        )

        return panel_cristal(
            content=ft.Column(
                [
                    ft.Text("Fondo de Pantalla", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(
                        "Selecciona una imagen para el fondo del programa. "
                        "Se abrirá el explorador de archivos de Windows.",
                        color=ft.Colors.WHITE70,
                        size=13,
                    ),
                    ft.Container(height=15),
                    ft.Button(
                        "Examinar Archivos...",
                        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                        color="#000B18",
                        bgcolor=estado["color_acento"],
                        on_click=abrir_explorador,
                    ),
                    ft.Container(height=40),
                    ft.Text("Color de Acento", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Cambia el color principal de los botones y bordes.", color=ft.Colors.WHITE70, size=13),
                    ft.Container(height=15),
                    ft.Column(
                        [ft.Row([crear_circulo_color(c) for c in fila], spacing=15) for fila in colores_filas],
                        spacing=15,
                    ),
                    ft.Container(height=40),
                    ft.Text("Opacidad", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(
                        "Ajusta qué tan transparentes se ven los paneles sobre el fondo.",
                        color=ft.Colors.WHITE70,
                        size=13,
                    ),
                    ft.Container(height=15),
                    control_opacidad,
                    ft.Container(height=20),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def construir_vista_herramientas():
        cable_ok = estado.get("cable_instalado", False)

        def elegir_bits(bits):
            def _click(e):
                ocultar_overlay()
                nombre_instalador = "VBCABLE_Setup_x64.exe" if bits == 64 else "VBCABLE_Setup.exe"
                ruta_instalador = os.path.join(CARPETA_CABLE_TEMPORAL, nombre_instalador)
                if not os.path.isfile(ruta_instalador):
                    mostrar_snackbar(
                        "No se encontró el instalador. La carpeta 'Cable virtual (temporal)' "
                        "pudo haberse eliminado ya porque el Cable Virtual está instalado."
                    )
                    return

                def _hilo_instalador():
                    try:
                        ruta_segura = ruta_instalador.replace("\\", "/")
                        comando_ps = [
                            "powershell",
                            "-NoProfile",
                            "-WindowStyle", "Hidden",
                            "-Command",
                            f"Start-Process -FilePath '{ruta_segura}' -Wait -Verb RunAs",
                        ]
                        subprocess.run(
                            comando_ps,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                        )

                        _actualizar_estado_dependencias()
                        if estado.get("cable_instalado") and os.path.isdir(CARPETA_CABLE_TEMPORAL):
                            try:
                                shutil.rmtree(CARPETA_CABLE_TEMPORAL)
                            except Exception:
                                pass
                        if estado["vista_actual"] in ("Inicio", "Herramientas"):
                            actualizar_interfaz()
                    except Exception as ex:
                        mostrar_snackbar(f"No se pudo iniciar el instalador: {ex}")

                mostrar_snackbar(
                    "Instalador iniciado. Sigue los pasos en la ventana que se abrió "
                    "(puede pedirte permisos de administrador)."
                )
                threading.Thread(target=_hilo_instalador, daemon=True).start()
            return _click

        def preguntar_arquitectura(e):
            mostrar_overlay(
                panel_dialogo(
                    icono=ft.Icons.MEMORY_ROUNDED,
                    titulo="¿Tu sistema es de 32 o 64 bits?",
                    mensaje=(
                        "Elige la arquitectura de tu Windows para instalar el driver "
                        "correcto del Cable de Audio Virtual."
                    ),
                    botones=[
                        ("32 bits", elegir_bits(32), False),
                        ("64 bits", elegir_bits(64), True),
                    ],
                )
            )

        def volver_a_comprobar(e):
            _actualizar_estado_dependencias()
            actualizar_interfaz()

        def abrir_tutorial_audio(e):
            try:
                subprocess.Popen("control mmsys.cpl,,1", shell=True)
            except Exception as ex:
                mostrar_snackbar(f"No se pudo abrir el panel de sonido: {ex}")

            def ir_a_mezclador(e2):
                ocultar_overlay()
                try:
                    subprocess.Popen("start ms-settings:apps-volume", shell=True)
                except Exception as ex:
                    mostrar_snackbar(f"No se pudo abrir el mezclador de volumen: {ex}")

            mostrar_overlay(
                panel_dialogo(
                    icono=ft.Icons.VOLUME_UP_ROUNDED,
                    titulo="Tutorial de Configuración",
                    mensaje=(
                        "Paso 1: Selecciona 'CABLE Output'.\n"
                        "Paso 2: Presiona el botón 'Propiedades'.\n"
                        "Paso 3: En la nueva ventana, ve a la pestaña 'Escuchar'.\n"
                        "Paso 4: Marca la casilla 'Escuchar este dispositivo'.\n"
                        "Paso 5: Toca en 'Aplicar' y después en 'Aceptar'.\n"
                        "Paso 6: Presiona 'Aceptar' en la ventana original de "
                        "'Sonido' para cerrarla.\n\n"
                        "Cuando hayas terminado todos los pasos, presiona "
                        "'Ir a siguiente paso' para abrir el Mezclador de Volumen."
                    ),
                    botones=[
                        ("Cancelar", lambda e2: ocultar_overlay(), False),
                        ("Ir a siguiente paso", ir_a_mezclador, True),
                    ],
                )
            )

        contenido = [
            ft.Text("Cable de Audio Virtual", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text(
                "El Cable Virtual enruta el audio del TTS hacia el micrófono que usa "
                "Roblox Voice. Es necesario para que se escuche dentro del juego.",
                color=ft.Colors.WHITE70,
                size=13,
            ),
            ft.Container(height=15),
        ]

        if cable_ok:
            contenido.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_ACCENT_400, size=20),
                        ft.Text("El Cable Virtual ya está instalado en este equipo.", color=ft.Colors.WHITE, size=13),
                    ]
                )
            )
        else:
            contenido.append(
                ft.Button(
                    "Instalar Cable Virtual...",
                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                    color="#000B18",
                    bgcolor=estado["color_acento"],
                    on_click=preguntar_arquitectura,
                )
            )

        contenido.append(ft.Container(height=15))
        contenido.append(
            ft.TextButton(
                "Volver a comprobar",
                icon=ft.Icons.REFRESH_ROUNDED,
                on_click=volver_a_comprobar,
            )
        )

        contenido.append(ft.Container(height=35))
        contenido.append(ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), height=1))
        contenido.append(ft.Container(height=25))
        contenido.append(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Cambiar Salida de Audio", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(
                                "Sigue el tutorial para enrutar el audio del TTS hacia "
                                "el micrófono que usa Roblox Voice.",
                                color=ft.Colors.WHITE70,
                                size=13,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Button(
                        "Configurar",
                        icon=ft.Icons.VOLUME_UP_ROUNDED,
                        color="#000B18",
                        bgcolor=estado["color_acento"],
                        on_click=abrir_tutorial_audio,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        contenido.append(ft.Container(height=35))
        contenido.append(ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), height=1))
        contenido.append(ft.Container(height=25))

        def cambiar_formato_hora(nuevo_formato):
            def _click(e):
                if estado.get("formato_hora", "12h") == nuevo_formato:
                    return
                estado["formato_hora"] = nuevo_formato
                _guardar_estado_actual()
                actualizar_interfaz()
            return _click

        def _boton_formato_hora(etiqueta, valor):
            activo = estado.get("formato_hora", "12h") == valor
            return ft.Container(
                content=ft.Text(
                    etiqueta,
                    size=13,
                    weight=ft.FontWeight.W_800 if activo else ft.FontWeight.NORMAL,
                    color="#000B18" if activo else ft.Colors.WHITE,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(vertical=10, horizontal=18),
                border_radius=10,
                bgcolor=estado["color_acento"] if activo else ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
                border=None if activo else ft.Border.all(1, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
                on_click=cambiar_formato_hora(valor),
                ink=True,
                on_hover=btn_hover,
                animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                scale=1.0,
            )

        contenido.append(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Formato de Hora", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(
                                "Cómo se muestra la hora de cada frase en 'Frases Rápidas'. "
                                "Por defecto: 12 horas.",
                                color=ft.Colors.WHITE70,
                                size=13,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            _boton_formato_hora("12 horas", "12h"),
                            _boton_formato_hora("24 horas", "24h"),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        return panel_cristal(
            content=ft.Column(contenido, scroll=ft.ScrollMode.AUTO),
            expand=True,
        )

    def construir_vista_frases_rapidas():
        entradas = _leer_historial()

        lista_historial = ft.Column(
            _construir_tarjetas_historial(entradas),
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        refs["lista_historial"] = lista_historial

        return panel_cristal(
            content=ft.Column(
                [
                    ft.Text("Frases Rápidas", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(
                        "Historial de las frases que se han inyectado en esta sesión, con la "
                        "hora exacta en que se enviaron. Se reinicia cada vez que presionas "
                        "'Iniciar TTS' en Inicio.",
                        color=ft.Colors.WHITE70,
                        size=13,
                    ),
                    ft.Container(height=15),
                    lista_historial,
                ],
                expand=True,
            ),
            expand=True,
        )

    def actualizar_interfaz():
        _paneles_cristal.clear()
        if estado["vista_actual"] == "Inicio":
            area_contenido.content = construir_vista_inicio()
        elif estado["vista_actual"] == "Personalización":
            area_contenido.content = construir_vista_personalizacion()
        elif estado["vista_actual"] == "Herramientas":
            area_contenido.content = construir_vista_herramientas()
        elif estado["vista_actual"] == "Frases Rápidas":
            area_contenido.content = construir_vista_frases_rapidas()
        else:
            area_contenido.content = panel_cristal(ft.Text(f"Módulo '{estado['vista_actual']}' en construcción...", color=ft.Colors.WHITE), expand=True)

        dibujar_sidebar()
        page.update()

    ANCHO_SIDEBAR_ABIERTA = 240
    ANCHO_SIDEBAR_CERRADA = 84

    columna_menu = ft.Column(spacing=10)

    def alternar_menu(e):
        estado["sidebar_abierta"] = not estado["sidebar_abierta"]
        contenedor_sidebar.width = ANCHO_SIDEBAR_ABIERTA if estado["sidebar_abierta"] else ANCHO_SIDEBAR_CERRADA
        dibujar_sidebar()
        contenedor_sidebar.update()
        columna_menu.update()

    def dibujar_sidebar():
        columna_menu.controls.clear()
        abierta = estado["sidebar_abierta"]

        encabezado = [
            ft.IconButton(
                icon=ft.Icons.MENU_OPEN_ROUNDED if abierta else ft.Icons.MENU_ROUNDED,
                icon_color=ft.Colors.WHITE,
                icon_size=22,
                on_click=alternar_menu,
                tooltip="Ocultar menú" if abierta else "Mostrar menú",
            )
        ]
        if abierta:
            encabezado.insert(
                0,
                ft.Text("HamiTTS", size=24, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE, italic=True),
            )

        columna_menu.controls.append(
            ft.Container(
                content=ft.Row(
                    encabezado,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN if abierta else ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.only(bottom=15, left=10 if abierta else 0),
            )
        )

        opciones = [
            (ft.Icons.SPACE_DASHBOARD_ROUNDED, "Inicio"),
            (ft.Icons.BOLT_ROUNDED, "Frases Rápidas"),
            (ft.Icons.BUILD_ROUNDED, "Herramientas"),
            (ft.Icons.PALETTE_ROUNDED, "Personalización"),
        ]

        for icono, texto in opciones:
            activo = estado["vista_actual"] == texto

            def crear_evento(nombre_vista):
                def al_clickear(e):
                    estado["vista_actual"] = nombre_vista
                    actualizar_interfaz()

                return al_clickear

            contenido_boton = [ft.Icon(icono, color=estado["color_acento"] if activo else ft.Colors.WHITE70, size=18)]
            if abierta:
                contenido_boton.append(
                    ft.Text(texto, color=ft.Colors.WHITE if activo else ft.Colors.WHITE70, weight=ft.FontWeight.BOLD if activo else ft.FontWeight.NORMAL)
                )

            btn = ft.Container(
                content=ft.Row(contenido_boton, alignment=ft.MainAxisAlignment.START if abierta else ft.MainAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(vertical=15, horizontal=20 if abierta else 10),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.15, estado["color_acento"]) if activo else ft.Colors.TRANSPARENT,
                border=ft.Border.all(1, estado["color_acento"]) if activo else None,
                animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                scale=1.0,
                on_hover=btn_hover,
                on_click=crear_evento(texto),
                ink=True,
                tooltip=texto if not abierta else None,
            )
            columna_menu.controls.append(btn)

    barra_superior = ft.Row(
        [ft.Text("Panel de Control", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    dibujar_sidebar()
    area_contenido.content = construir_vista_inicio()

    contenedor_sidebar = ft.Container(
        content=panel_cristal(content=columna_menu, padding=18, persistente=True),
        width=ANCHO_SIDEBAR_ABIERTA,
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        clip_behavior="hardEdge",
    )

    columna_principal = ft.Column([barra_superior, area_contenido], expand=True, spacing=20)

    layout_maestro = ft.Row([contenedor_sidebar, columna_principal], expand=True, spacing=20)

    raiz = ft.Stack(
        controls=[
            capa_imagen,
            ft.Container(content=layout_maestro, padding=30, expand=True),
            capa_dialogos,
        ],
        expand=True,
    )

    page.add(raiz)

    if not estado["ahk_instalado"]:
        mostrar_bloqueo_ahk()

    threading.Thread(target=_hilo_monitor_dependencias, daemon=True).start()

    threading.Thread(target=_hilo_vigilar_historial, daemon=True).start()

if __name__ == "__main__":
    crear_acceso_directo_escritorio()

    try:
        ft.run(main)
    except AttributeError:
        ft.app(target=main)
