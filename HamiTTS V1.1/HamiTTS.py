import customtkinter as ctk
import subprocess
import webbrowser
from tkinter import messagebox, colorchooser
import os
import sys
import winreg
import win32com.client
import threading
import urllib.request
import json
import shutil

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("HamiTTS")
app.resizable(False, False)

try:
    app.iconbitmap("nuevologo.ico")
except:
    pass

carpetas_nav = {
    "Opera GX / Opera": "Opera and OperaGX",
    "Google Chrome": "Chrome",
    "Microsoft Edge": "Edge",
    "Mozilla Firefox": "Firefox",
    "Brave Browser": "Brave"
}

archivos_base = {
    "Opera GX / Opera": "OperaGX roblox",
    "Google Chrome": "Chrome roblox",
    "Microsoft Edge": "Edge roblox",
    "Mozilla Firefox": "Firefox roblox",
    "Brave Browser": "Brave roblox"
}

teclas = {
    "Español Latinoamérica (Tecla '-')": "latino",
    "Inglés (Tecla '/')": "ingles"
}

proceso_ahk = None
boton_iniciar = None

def oscurecer_color(hex_color, factor=0.75):
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#14375e"

def obtener_ruta_config():
    if getattr(sys, 'frozen', False):
        directorio_base = os.path.dirname(sys.executable)
    else:
        directorio_base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directorio_base, "config.json")

def cargar_configuracion():
    config_default = {
        "navegador": "Opera GX / Opera",
        "tecla": "Español Latinoamérica (Tecla '-')",
        "color": "#1f538d" 
    }
    ruta_config = obtener_ruta_config()
    try:
        if os.path.exists(ruta_config):
            with open(ruta_config, "r", encoding="utf-8") as archivo:
                config_guardada = json.load(archivo)
                if config_guardada.get("navegador") in carpetas_nav and config_guardada.get("tecla") in teclas:
                    if "color" not in config_guardada or not str(config_guardada.get("color")).startswith("#"):
                        config_guardada["color"] = config_default["color"]
                    return config_guardada
    except:
        pass
    return config_default

def guardar_configuracion(nav, tecla, color):
    ruta_config = obtener_ruta_config()
    try:
        with open(ruta_config, "w", encoding="utf-8") as archivo:
            json.dump({"navegador": nav, "tecla": tecla, "color": color}, archivo)
    except:
        pass

def crear_acceso_directo_pypiwin32():
    if getattr(sys, 'frozen', False):
        try:
            ruta_exe = sys.executable
            directorio_base = os.path.dirname(ruta_exe)
            
            shell = win32com.client.Dispatch("WScript.Shell")
            ruta_escritorio = shell.SpecialFolders("Desktop")
            ruta_acceso_directo = os.path.join(ruta_escritorio, "HamiTTS.lnk")
            
            if not os.path.exists(ruta_acceso_directo):
                shortcut = shell.CreateShortCut(ruta_acceso_directo)
                shortcut.TargetPath = ruta_exe
                shortcut.WorkingDirectory = directorio_base
                shortcut.IconLocation = f"{ruta_exe}, 0"
                shortcut.Description = "Lanzador de HamiTTS"
                shortcut.Save()
        except:
            pass

def detectar_autohotkey():
    try:
        if getattr(sys, 'frozen', False):
            directorio_base = os.path.dirname(sys.executable)
        else:
            directorio_base = os.path.dirname(os.path.abspath(__file__))
        
        ruta_ahk = os.path.join(directorio_base, "Navegadores y activadores", "AutoHotkey.exe")
        ruta_ahk64 = os.path.join(directorio_base, "Navegadores y activadores", "AutoHotkey64.exe")
        
        if os.path.exists(ruta_ahk) or os.path.exists(ruta_ahk64):
            return True
    except:
        pass

    try:
        clave = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"AutoHotkeyScript\Shell\Open\Command")
        valor, tipo = winreg.QueryValueEx(clave, "")
        winreg.CloseKey(clave)
        if valor:
            return True
    except FileNotFoundError:
        pass

    nombres_exe = [
        "AutoHotkey.exe", "AutoHotkey64.exe", "AutoHotkey32.exe", 
        "AutoHotkeyU64.exe", "AutoHotkeyU32.exe", "AutoHotkeyA32.exe", "AutoHotkeyUX.exe"
    ]
    
    carpetas_base = [
        os.path.expandvars(r"%ProgramFiles%\AutoHotkey"),
        os.path.expandvars(r"%ProgramFiles(x86)%\AutoHotkey"),
        os.path.expandvars(r"%ProgramFiles%\AutoHotkey\v2"),
        os.path.expandvars(r"%ProgramFiles(x86)%\AutoHotkey\v2")
    ]
    
    for carpeta in carpetas_base:
        for exe in nombres_exe:
            ruta_completa = os.path.join(carpeta, exe)
            if os.path.exists(ruta_completa):
                return True

    try:
        resultado = subprocess.run(["where", "autohotkey"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if resultado.returncode == 0:
            return True
    except:
        pass
        
    return False

def detectar_cable_virtual():
    try:
        comando = 'powershell -Command "Get-PnpDevice -FriendlyName \'*VB-Audio Virtual Cable*\' -ErrorAction SilentlyContinue"'
        resultado = subprocess.run(comando, capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return "VB-Audio" in resultado.stdout
    except:
        return False

def instalar_cable_local():
    ventana_bits = ctk.CTkToplevel(app)
    ventana_bits.title("Versión de Windows")
    ventana_bits.geometry("350x150")
    ventana_bits.resizable(False, False)
    ventana_bits.transient(app)
    ventana_bits.grab_set()

    try:
        ventana_bits.iconbitmap("nuevologo.ico")
    except:
        pass

    ctk.CTkLabel(ventana_bits, text="¿Tu sistema es de 32 o 64 bits?", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 15))

    def ejecutar_instalador(bits):
        ventana_bits.destroy()
        
        if getattr(sys, 'frozen', False):
            directorio_base = os.path.dirname(sys.executable)
        else:
            directorio_base = os.path.dirname(os.path.abspath(__file__))
            
        nombre_exe = "VBCABLE_Setup_x64.exe" if bits == 64 else "VBCABLE_Setup.exe"
        
        ruta_carpeta_temporal = os.path.join(directorio_base, "Navegadores y activadores", "cable virtual (temporal)")
        ruta_instalador = os.path.join(ruta_carpeta_temporal, nombre_exe)
        
        if not os.path.exists(ruta_instalador):
            messagebox.showerror("Archivo no encontrado", f"No se encontró el instalador:\n{ruta_instalador}\n\nAsegúrate de haber puesto los archivos en la carpeta correcta.")
            return

        def proceso_hilo():
            try:
                messagebox.showinfo("Instalación", f"Se abrirá el instalador de {bits} bits.\n\nSigue las instrucciones en pantalla y ACEPTA los permisos de administrador. Cuando termines y cierres el instalador, verificaremos si se instaló correctamente.")
                
                ruta_segura = ruta_instalador.replace("\\", "/")
                
                comando_ps = [
                    "powershell",
                    "-NoProfile",
                    "-WindowStyle", "Hidden",
                    "-Command",
                    f"Start-Process -FilePath '{ruta_segura}' -Wait -Verb RunAs"
                ]
                
                subprocess.run(comando_ps, creationflags=subprocess.CREATE_NO_WINDOW)
                
                if detectar_cable_virtual():
                    try:
                        shutil.rmtree(ruta_carpeta_temporal)
                        messagebox.showinfo("Instalación Exitosa", "¡El cable virtual se ha instalado correctamente!\n\nLa carpeta temporal ha sido eliminada automáticamente para ahorrar espacio.\nRecuerda reiniciar tu PC para que Windows lo active por completo.")
                    except Exception as e:
                        print(e)
                        pass
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un problema al abrir el instalador:\n{e}")

        hilo = threading.Thread(target=proceso_hilo)
        hilo.start()

    frame_botones = ctk.CTkFrame(ventana_bits, fg_color="transparent")
    frame_botones.pack()

    config_actual = cargar_configuracion()
    color_base = config_actual.get("color", "#1f538d")
    color_hover = oscurecer_color(color_base)

    boton_64 = ctk.CTkButton(frame_botones, text="64 Bits", width=100, fg_color=color_base, hover_color=color_hover, command=lambda: ejecutar_instalador(64))
    boton_64.pack(side="left", padx=10)

    boton_32 = ctk.CTkButton(frame_botones, text="32 Bits", width=100, fg_color=color_base, hover_color=color_hover, command=lambda: ejecutar_instalador(32))
    boton_32.pack(side="left", padx=10)

def abrir_enlace_ahk():
    webbrowser.open("https://www.autohotkey.com")

def salir_programa():
    global proceso_ahk
    
    if proceso_ahk is not None:
        try:
            proceso_ahk.terminate()
        except:
            pass

    ejecutables_para_cerrar = ["AutoHotkey.exe", "AutoHotkey64.exe", "AutoHotkey32.exe"]
    for exe in ejecutables_para_cerrar:
        try:
            subprocess.run(["taskkill", "/F", "/IM", exe, "/T"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    app.destroy()

app.protocol("WM_DELETE_WINDOW", salir_programa)

def abrir_menu_config():
    ventana_config = ctk.CTkToplevel(app)
    ventana_config.title("Color de HamiTTS")
    ventana_config.geometry("300x150")
    ventana_config.resizable(False, False)
    ventana_config.transient(app) 
    ventana_config.grab_set() 
    
    try:
        ventana_config.iconbitmap("nuevologo.ico")
    except:
        pass
    
    config_actual = cargar_configuracion()
    color_actual = config_actual.get("color", "#1f538d")
    
    ctk.CTkLabel(ventana_config, text="Personaliza el color de la interfaz:", font=ctk.CTkFont(weight="bold")).pack(pady=(25,15))
    
    def elegir_nuevo_color():
        color_elegido = colorchooser.askcolor(color=color_actual, title="Paleta de Colores")[1]
        
        if color_elegido:
            guardar_configuracion(config_actual["navegador"], config_actual["tecla"], color_elegido)
            ventana_config.destroy()
            cargar_interfaz_principal()
            
    boton_aplicar = ctk.CTkButton(ventana_config, text="🎨 Elegir Color", command=elegir_nuevo_color, fg_color=color_actual, hover_color=oscurecer_color(color_actual))
    boton_aplicar.pack(pady=5)

def iniciar_script():
    global proceso_ahk, boton_iniciar
    
    config_actual = cargar_configuracion()
    nav_elegido = combo_navegador.get()
    tecla_elegida = combo_teclado.get()

    carpeta = carpetas_nav[nav_elegido]
    archivo_base = archivos_base[nav_elegido]
    sufijo_tecla = teclas[tecla_elegida]

    nombre_archivo = f"{archivo_base} {sufijo_tecla}.ahk"
    
    if getattr(sys, 'frozen', False):
        directorio_base = os.path.dirname(sys.executable)
    else:
        directorio_base = os.path.dirname(os.path.abspath(__file__))

    ruta_script = os.path.join(directorio_base, "Navegadores y activadores", carpeta, nombre_archivo)
    
    ruta_ahk_preinstalado = os.path.join(directorio_base, "Navegadores y activadores", "AutoHotkey.exe")
    ruta_ahk_preinstalado64 = os.path.join(directorio_base, "Navegadores y activadores", "AutoHotkey64.exe")

    if os.path.exists(ruta_script):
        try:
            if proceso_ahk is not None:
                proceso_ahk.terminate()
                
            if os.path.exists(ruta_ahk_preinstalado):
                proceso_ahk = subprocess.Popen([ruta_ahk_preinstalado, ruta_script])
            elif os.path.exists(ruta_ahk_preinstalado64):
                proceso_ahk = subprocess.Popen([ruta_ahk_preinstalado64, ruta_script])
            else:
                os.startfile(ruta_script)
                
            guardar_configuracion(nav_elegido, tecla_elegida, config_actual["color"])
            
            boton_iniciar.configure(
                text="✓ HamiTTS está en segundo plano", 
                fg_color="#4c516d", 
                hover_color="#4c516d", 
                state="disabled"
            )
            
            mensaje = f"¡Iniciado con éxito!\n\nSe está ejecutando:\n{nombre_archivo}\n\nYa puedes entrar a jugar."
            messagebox.showinfo("Listo", mensaje)
            webbrowser.open("https://fish.audio/es/app/discovery/")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar:\n{e}")
    else:
        messagebox.showerror("Error de ubicación", f"No se encontró el archivo:\n{nombre_archivo}\n\nAsegúrate de que este programa esté junto a la carpeta 'Navegadores y activadores'.")

def cambiar_salida_audio():
    subprocess.Popen('control mmsys.cpl,,1')
    
    instrucciones = (
        "Paso 1: Selecciona 'CABLE Output'.\n"
        "Paso 2: Presiona el botón 'Propiedades'.\n"
        "Paso 3: En la nueva ventana, ve a la pestaña 'Escuchar'.\n"
        "Paso 4: Marca la casilla 'Escuchar este dispositivo'.\n"
        "Paso 5: Toca en 'Aplicar' y después en 'Aceptar'.\n"
        "Paso 6: Presiona 'Aceptar' en la ventana original de 'Sonido' para cerrarla.\n\n"
        "Cuando hayas terminado todos los pasos, presiona 'Aceptar' AQUÍ para continuar."
    )
    
    respuesta = messagebox.askokcancel("Tutorial de Configuración", instrucciones)
    
    if respuesta:
        subprocess.Popen('start ms-settings:apps-volume', shell=True)

def cargar_interfaz_principal():
    global combo_navegador, combo_teclado, boton_iniciar
    
    app.geometry("500x490")
    for widget in app.winfo_children():
        widget.destroy()

    config_actual = cargar_configuracion()
    
    color_base = config_actual.get("color", "#1f538d")
    color_hover = oscurecer_color(color_base)

    boton_config = ctk.CTkButton(app, text="⚙️", width=30, height=30, fg_color="transparent", hover_color="#333333", font=ctk.CTkFont(size=20), command=abrir_menu_config)
    boton_config.place(relx=0.97, rely=0.03, anchor="ne")

    label_titulo = ctk.CTkLabel(app, text="BIENVENIDO A HAMITTS", font=ctk.CTkFont(size=24, weight="bold"))
    label_titulo.pack(pady=(20, 5))

    label_subtitulo = ctk.CTkLabel(app, text="TTS de navegador integrado a Roblox", font=ctk.CTkFont(size=14))
    label_subtitulo.pack(pady=(0, 15))

    cable_instalado = detectar_cable_virtual()

    if cable_instalado:
        label_estado_cable = ctk.CTkLabel(app, text="✓ EL CABLE VIRTUAL ESTÁ INSTALADO Y LISTO.", text_color=color_base, font=ctk.CTkFont(weight="bold"))
        label_estado_cable.pack(pady=5)
    else:
        label_estado_cable = ctk.CTkLabel(app, text="⚠️ IMPORTANTE: NECESITAS TENER UN CABLE VIRTUAL.", text_color="#FF4040", font=ctk.CTkFont(weight="bold"))
        label_estado_cable.pack(pady=5)
        
        boton_descargar = ctk.CTkButton(app, text="INSTALARLO AQUÍ", fg_color="transparent", text_color=color_base, hover_color="#2b2b2b", command=instalar_cable_local)
        boton_descargar.pack(pady=(0, 10))

    tabview = ctk.CTkTabview(app, width=450, height=200, segmented_button_selected_color=color_base, segmented_button_selected_hover_color=color_hover)
    tabview.pack(pady=10, padx=20)

    tabview.add("Navegador y Teclado")
    tabview.add("Salida de Audio")

    label_nav = ctk.CTkLabel(tabview.tab("Navegador y Teclado"), text="1. Selecciona el navegador que vas a utilizar:", font=ctk.CTkFont(weight="bold"))
    label_nav.pack(pady=(10, 5), anchor="w", padx=20)

    combo_navegador = ctk.CTkComboBox(tabview.tab("Navegador y Teclado"), values=list(carpetas_nav.keys()), width=400, state="readonly")
    combo_navegador.set(config_actual["navegador"])
    combo_navegador.pack(pady=(0, 15), padx=20)

    label_tec = ctk.CTkLabel(tabview.tab("Navegador y Teclado"), text="2. Selecciona la tecla para activar el chat:", font=ctk.CTkFont(weight="bold"))
    label_tec.pack(pady=(0, 5), anchor="w", padx=20)

    combo_teclado = ctk.CTkComboBox(tabview.tab("Navegador y Teclado"), values=list(teclas.keys()), width=400, state="readonly")
    combo_teclado.set(config_actual["tecla"])
    combo_teclado.pack(pady=(0, 20), padx=20)

    label_info_audio = ctk.CTkLabel(
        tabview.tab("Salida de Audio"), 
        text="Configura el audio de tu navegador para enviarlo al juego.\n\nNota: Si ya configuraste esto antes o dejaste de jugar,\npuedes dejarlo como está (Predeterminado).", 
        justify="center"
    )
    label_info_audio.pack(pady=(15, 20))

    boton_cambiar_audio = ctk.CTkButton(tabview.tab("Salida de Audio"), text="Cambiar Salida de Audio", command=cambiar_salida_audio, fg_color="#4a4a4a", hover_color="#333333")
    boton_cambiar_audio.pack(pady=10)

    if cable_instalado:
        boton_iniciar = ctk.CTkButton(app, text="Aplicar e Iniciar", command=iniciar_script, width=200, height=40, font=ctk.CTkFont(weight="bold"), fg_color=color_base, hover_color=color_hover)
    else:
        boton_iniciar = ctk.CTkButton(app, text="HamiTTS no se puede ejecutar sin el cable virtual", width=320, height=40, font=ctk.CTkFont(weight="bold"), fg_color="#4c516d", hover_color="#4c516d", state="disabled")
    
    boton_iniciar.pack(pady=15)

def cargar_interfaz_alerta():
    app.geometry("460x300")
    for widget in app.winfo_children():
        widget.destroy()

    label_alerta_titulo = ctk.CTkLabel(app, text="REQUISITO DEL SISTEMA", text_color="#FF4040", font=ctk.CTkFont(size=22, weight="bold"))
    label_alerta_titulo.pack(pady=(25, 15))

    texto_explicativo = (
        "HamiTTS requiere el programa 'AutoHotkey' para poder funcionar.\n\n"
        "Sin este componente instalado en tu sistema, el programa\n"
        "tendrá problemas severos y no podrá transferir el TTS al juego."
    )
    label_alerta_texto = ctk.CTkLabel(app, text=texto_explicativo, font=ctk.CTkFont(size=13), justify="center")
    label_alerta_texto.pack(pady=10)

    boton_instalar_ahk = ctk.CTkButton(app, text="Instalar AutoHotkey", command=abrir_enlace_ahk, width=220, height=38, font=ctk.CTkFont(weight="bold"))
    boton_instalar_ahk.pack(pady=(15, 5))

    boton_cancelar_ahk = ctk.CTkButton(app, text="Cerrar HamiTTS", command=salir_programa, fg_color="transparent", border_width=1, border_color="#555555", text_color="#aaaaaa", hover_color="#2b2b2b", width=220, height=32)
    boton_cancelar_ahk.pack(pady=5)

    verificar_en_bucle()

def verificar_en_bucle():
    if detectar_autohotkey():
        cargar_interfaz_principal()
    else:
        app.after(2000, verificar_en_bucle)

if detectar_autohotkey():
    cargar_interfaz_principal()
else:
    cargar_interfaz_alerta()

crear_acceso_directo_pypiwin32()

app.mainloop()
