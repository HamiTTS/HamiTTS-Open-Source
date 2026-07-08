import customtkinter as ctk
import subprocess
import webbrowser
from tkinter import messagebox
import os
import sys
import winreg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("HamiTTS")
app.resizable(False, False)

try:
    app.iconbitmap("logo.ico")
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

def detectar_autohotkey():
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

def abrir_enlace_cable():
    webbrowser.open("https://vb-audio.com/Cable/")

def abrir_enlace_ahk():
    webbrowser.open("https://www.autohotkey.com")

def salir_programa():
    app.destroy()

def iniciar_script():
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

    if os.path.exists(ruta_script):
        try:
            os.startfile(ruta_script)
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
    global combo_navegador, combo_teclado
    
    app.geometry("500x450")
    for widget in app.winfo_children():
        widget.destroy()

    label_titulo = ctk.CTkLabel(app, text="BIENVENIDO A HAMITTS", font=ctk.CTkFont(size=24, weight="bold"))
    label_titulo.pack(pady=(20, 5))

    label_subtitulo = ctk.CTkLabel(app, text="TTS de navegador integrado a Roblox", font=ctk.CTkFont(size=14))
    label_subtitulo.pack(pady=(0, 15))

    if detectar_cable_virtual():
        label_estado_cable = ctk.CTkLabel(app, text="✓ EL CABLE VIRTUAL ESTÁ INSTALADO Y LISTO.", text_color="#00FF00", font=ctk.CTkFont(weight="bold"))
        label_estado_cable.pack(pady=5)
    else:
        label_estado_cable = ctk.CTkLabel(app, text="⚠️ IMPORTANTE: NECESITAS TENER UN CABLE VIRTUAL.", text_color="#FF4040", font=ctk.CTkFont(weight="bold"))
        label_estado_cable.pack(pady=5)
        
        boton_descargar = ctk.CTkButton(app, text="DESCARGARLO AQUÍ", fg_color="transparent", text_color="#3b8ed0", hover_color="#2b2b2b", command=abrir_enlace_cable)
        boton_descargar.pack(pady=(0, 10))

    tabview = ctk.CTkTabview(app, width=450, height=200)
    tabview.pack(pady=10, padx=20)

    tabview.add("Navegador y Teclado")
    tabview.add("Salida de Audio")

    label_nav = ctk.CTkLabel(tabview.tab("Navegador y Teclado"), text="1. Selecciona el navegador que vas a utilizar:", font=ctk.CTkFont(weight="bold"))
    label_nav.pack(pady=(10, 5), anchor="w", padx=20)

    combo_navegador = ctk.CTkComboBox(tabview.tab("Navegador y Teclado"), values=list(carpetas_nav.keys()), width=400)
    combo_navegador.pack(pady=(0, 15), padx=20)

    label_tec = ctk.CTkLabel(tabview.tab("Navegador y Teclado"), text="2. Selecciona la tecla para activar el chat:", font=ctk.CTkFont(weight="bold"))
    label_tec.pack(pady=(0, 5), anchor="w", padx=20)

    combo_teclado = ctk.CTkComboBox(tabview.tab("Navegador y Teclado"), values=list(teclas.keys()), width=400)
    combo_teclado.pack(pady=(0, 20), padx=20)

    label_info_audio = ctk.CTkLabel(
        tabview.tab("Salida de Audio"), 
        text="Configura el audio de tu navegador para enviarlo al juego.\n\nNota: Si ya configuraste esto antes o dejaste de jugar,\npuedes dejarlo como está (Predeterminado).", 
        justify="center"
    )
    label_info_audio.pack(pady=(15, 20))

    boton_cambiar_audio = ctk.CTkButton(tabview.tab("Salida de Audio"), text="Cambiar Salida de Audio", command=cambiar_salida_audio, fg_color="#4a4a4a", hover_color="#333333")
    boton_cambiar_audio.pack(pady=10)

    boton_iniciar = ctk.CTkButton(app, text="Aplicar e Iniciar", command=iniciar_script, width=200, height=40, font=ctk.CTkFont(weight="bold"))
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

app.mainloop()
