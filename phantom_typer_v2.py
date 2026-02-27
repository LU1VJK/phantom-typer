import subprocess
import datetime
import os
import serial
import time
import readline
import random
import sys
import fcntl
import re

# --- CONFIGURACIÓN INICIAL ---
CALLSIGN = ""
BAUD = "100"
SERIAL_PORT = "/dev/ttyUSB0"
LOG_FILE = os.path.expanduser("~/PHANTOM-TYPER/phantom_history.log")
PTT_METHOD = "DTR"
BANDA_ACTUAL = ""
FREQ_ACTUAL = ""
CORRESPONSAL_ACTUAL = "" 
HORA_INICIO_QSO = ""
HISTORIAL_PANTALLA = [] 

TABLA_BANDAS = {
    "1": {"n": "80M", "f": "3.580"},
    "2": {"n": "40M", "f": "7.040"},
    "3": {"n": "20M", "f": "14.080"},
    "4": {"n": "15M", "f": "21.080"},
    "5": {"n": "10M", "f": "28.080"}
}

C_GREEN  = "\033[92m"
C_BLUE   = "\033[94m"
C_CYAN   = "\033[96m"
C_RED    = "\033[91m"
C_PURPLE = "\033[95m"
C_MAGENT = "\033[35m"
C_GRAY   = "\033[37m"
C_BOLD   = "\033[1m"
C_END    = "\033[0m"

FRASES_DESPEDIDA = [
    "Estudiar para ganarse el ascenso de categoría, es el equivalente a ganar un concurso sin hacer trampa.",
    "La radioafición no es solo hablar, es experimentar y aprender constantemente.",
    "73 cordiales!."
]

def intro_phreaking():
    os.system('clear')
    skull = [
        "            __            ",
        "         ,gS$$$Sk.        ",
        "      ,d$$$$$$$$$$$k.     ",
        "    /?^?$7°' '`?$SS$$L.   ",
        "   ,?  $SL.__ ,d$iIS$$SL  ",
        "  j$Su%$S$$$$$?:iIS$$Sb   ",
        " :?°?^4$S$$\"°?$SL:iIS$SI:  ",
        " :'   '/`?$' .  `?Lis$$SI: ",
        "  '      '      ?kiSSI?   ",
        "      :.      $k _ `?Si7  ",
        "      .._.._  i$S%7·:i?'  ",
        "     ?%uS%uod$$$?`·?°`    ",
        "     S$$$$$$$$$$i         ",
        "     `?$$S?               "
    ]
    for _ in range(15):
        os.system('clear')
        for line in skull:
            colored_line = "      "
            for i, char in enumerate(line):
                if i < 10: color = C_PURPLE
                elif i < 20: color = C_RED
                else: color = C_MAGENT
                if "$" in char and 10 < i < 22:
                    colored_line += C_BOLD + C_RED + char + C_END
                else:
                    colored_line += color + char + C_END
            print(colored_line)
        time.sleep(0.1)

    print(f"\n{C_BLUE}{C_BOLD}>>> CONFIGURACIÓN INICIAL <<<{C_END}")
    global CALLSIGN, PTT_METHOD, BANDA_ACTUAL, FREQ_ACTUAL
    while not CALLSIGN:
        CALLSIGN = input(f"{C_GREEN}Ingresa tu Distintiva: {C_END}").strip().upper()
    print(f"\n{C_PURPLE}Selecciona Banda HF:{C_END}")
    for k, v in TABLA_BANDAS.items():
        print(f"{k}. {v['n']} ({v['f']} MHz)")
    b_choice = input(f"{C_GREEN}# {C_END}").strip()
    target = TABLA_BANDAS.get(b_choice, TABLA_BANDAS["2"])
    BANDA_ACTUAL = target["n"]
    FREQ_ACTUAL = target["f"]
    print(f"\n{C_PURPLE}Selecciona PTT (1: VOX, 2: DTR):{C_END}")
    choice = input(f"{C_GREEN}# {C_END} ").strip()
    PTT_METHOD = "VOX" if choice == "1" else "DTR"

def print_banner():
    os.system('clear')
    print(f"""{C_GREEN}{C_BOLD}
    .-----------.
    | PHANTOM   |--.
    | TYPER v1.2|  |  {C_RED}[OP: {CALLSIGN}]{C_GREEN}
    '-----------'  |  {C_BLUE}[PTT: {PTT_METHOD} | BAND: {BANDA_ACTUAL}]{C_GREEN}
       '-----------' {C_END}
    {C_BLUE}>> PHANTOM-TYPER <<{C_END}""")

def log_adif(remote_call):
    date_utc = datetime.datetime.utcnow().strftime("%Y%m%d")
    time_utc = HORA_INICIO_QSO if HORA_INICIO_QSO else datetime.datetime.utcnow().strftime("%H%M")
    entry = f"<QSO_DATE:8>{date_utc} <TIME_ON:4>{time_utc} <CALL:{len(remote_call)}>{remote_call} <BAND:{len(BANDA_ACTUAL)}>{BANDA_ACTUAL} <FREQ:{len(FREQ_ACTUAL)}>{FREQ_ACTUAL} <MODE:7>AFSK100 <RST_SENT:3>599 <EOR>"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
        f.flush()

def log_rx(text):
    timestamp = datetime.datetime.now().strftime("%H%M")
    HISTORIAL_PANTALLA.append(f"{C_GREEN}RX_{timestamp}: {text}{C_END}")

def mostrar_contexto():
    print(f"{C_BLUE}--- ACTIVIDAD DEL QSO ---{C_END}")
    for msg in HISTORIAL_PANTALLA[-15:]:
        print(msg)
    
    if os.path.exists(LOG_FILE):
        print(f"{C_BLUE}--- ÚLTIMOS 10 LOGS GUARDADOS ---{C_END}")
        with open(LOG_FILE, "r") as f:
            lines = [line.strip() for line in f.readlines() if "<QSO_DATE" in line]
            # Seleccionamos las últimas 10 entradas y las invertimos
            ultimos_diez = lines[-10:]
            for l in reversed(ultimos_diez):
                call = re.search(r'<CALL:\d+>(.*?) <BAND', l)
                time_match = re.search(r'<TIME_ON:4>(\d+)', l)
                if call:
                    t = time_match.group(1) if time_match else "--"
                    print(f"{C_CYAN}LOG: {t} QSO con {call.group(1)} OK{C_END}")
    print(f"{C_BLUE}---------------------------------------{C_END}")

def enviar_mensaje(texto, remote_call=None):
    global CORRESPONSAL_ACTUAL
    if remote_call is True:
        target = CORRESPONSAL_ACTUAL
        mensaje_completo = f"{target} {texto} DE {CALLSIGN}\n"
    elif isinstance(remote_call, str):
        target = remote_call
        mensaje_completo = f"{texto} DE {CALLSIGN}\n"
    else:
        target = CORRESPONSAL_ACTUAL if CORRESPONSAL_ACTUAL else "QSO"
        mensaje_completo = f"{texto} DE {CALLSIGN}\n"

    try:
        ser = None
        if PTT_METHOD == "DTR":
            try:
                ser = serial.Serial(SERIAL_PORT)
                ser.setDTR(True)
                time.sleep(0.5)
            except: pass
        print(f"{C_RED}[TX] Transmitiendo: {mensaje_completo.strip()}...{C_END}")
        proc = subprocess.Popen(['minimodem', '--tx', BAUD], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=mensaje_completo)
        if PTT_METHOD == "DTR" and ser:
            time.sleep(0.2)
            ser.setDTR(False)
            ser.close()
        
        t_now = datetime.datetime.now().strftime("%H%M")
        HISTORIAL_PANTALLA.append(f"{C_RED}{t_now} {mensaje_completo.strip()}{C_END}")

    except Exception as e:
        print(f"Error: {e}")

def transmitir(dirigido=False):
    global CORRESPONSAL_ACTUAL
    if dirigido and not CORRESPONSAL_ACTUAL:
        print(f"\n{C_RED}ERROR: No hay corresponsal guardado.{C_END}")
        time.sleep(1)
        return
    try:
        print(f"{C_BOLD}MENSAJE:{C_END}")
        msg = input("> ")
        if msg:
            enviar_mensaje(msg, remote_call=dirigido)
    except KeyboardInterrupt:
        print(f"\n{C_RED}TX ABORTADA.{C_END}")
        time.sleep(0.5)

def modo_operativo():
    global CORRESPONSAL_ACTUAL, HORA_INICIO_QSO, HISTORIAL_PANTALLA
    spinner = ['|', '/', '-', '\\']
    idx = 0
    old_settings = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, old_settings | os.O_NONBLOCK)
    
    print_banner()
    mostrar_contexto()
    print(f"\n{C_BOLD}MODO RX | {BANDA_ACTUAL} ({FREQ_ACTUAL} MHz){C_END}")
    print(f"{C_BOLD}1.{C_END} TX | {C_BOLD}2.{C_END} MENÚ | {C_BOLD}3.{C_END} CQ | {C_BOLD}4.{C_END} AGN | {C_BOLD}5.{C_END} CALL | {C_BOLD}6.{C_END} DIR | {C_BOLD}7.{C_END} RST | {C_BOLD}8.{C_END} SAVE | {C_BOLD}9.{C_END} CLEAR")

    cmd = "stdbuf -oL minimodem --rx " + BAUD + " -q"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
    fd_rx = proc.stdout.fileno()
    fl_rx = fcntl.fcntl(fd_rx, fcntl.F_GETFL)
    fcntl.fcntl(fd_rx, fcntl.F_SETFL, fl_rx | os.O_NONBLOCK)
    
    try:
        while True:
            try:
                line = proc.stdout.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        log_rx(clean_line)
                        print_banner()
                        mostrar_contexto()
                        print(f"\n{C_BOLD}MODO RX | {BANDA_ACTUAL} ({FREQ_ACTUAL} MHz){C_END}")
                        print(f"{C_BOLD}1.{C_END} TX | {C_BOLD}2.{C_END} MENÚ | {C_BOLD}3.{C_END} CQ | {C_BOLD}4.{C_END} AGN | {C_BOLD}5.{C_END} CALL | {C_BOLD}6.{C_END} DIR | {C_BOLD}7.{C_END} RST | {C_BOLD}8.{C_END} SAVE | {C_BOLD}9.{C_END} CLEAR")
            except IOError: pass
            
            try:
                key = sys.stdin.read(1)
                if key:
                    if key in ['1', '3', '4', '5', '6', '7', '8', '9']:
                        proc.terminate()
                        proc.wait()
                        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, old_settings)
                        if key == '1': transmitir(dirigido=False)
                        elif key == '3': enviar_mensaje("CQ CQ CQ", "CQ")
                        elif key == '4': enviar_mensaje("AGN AGN", "AGN")
                        elif key == '5':
                            print(f"\n{C_BOLD}CALLSIGN CORRESPONSAL:{C_END}")
                            new_call = input("> ").strip().upper()
                            if new_call: 
                                CORRESPONSAL_ACTUAL = new_call
                                HORA_INICIO_QSO = datetime.datetime.utcnow().strftime("%H%M")
                        elif key == '6': transmitir(dirigido=True)
                        elif key == '7':
                            if not CORRESPONSAL_ACTUAL:
                                print(f"\n{C_RED}ERROR: No hay corresponsal.{C_END}")
                                time.sleep(1)
                            else:
                                enviar_mensaje("599", True)
                        elif key == '8':
                            if CORRESPONSAL_ACTUAL:
                                log_adif(CORRESPONSAL_ACTUAL)
                                print(f"\n{C_GREEN}DATOS DEL QSO CON {CORRESPONSAL_ACTUAL} GUARDADOS.{C_END}")
                                CORRESPONSAL_ACTUAL = ""
                                HORA_INICIO_QSO = ""
                                time.sleep(1)
                            else:
                                print(f"\n{C_RED}ERROR: No hay datos para guardar.{C_END}")
                                time.sleep(1)
                        elif key == '9':
                            HISTORIAL_PANTALLA = []
                        return modo_operativo() 
                    elif key == '2':
                        break
            except IOError: pass
            
            sys.stdout.write(f"\rEscuchando {spinner[idx % 4]}  ")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass 
    finally:
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, old_settings)
        if proc.poll() is None:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        os.makedirs(os.path.dirname(LOG_FILE))
    try:
        intro_phreaking()
    except KeyboardInterrupt:
        sys.exit(0)
    while True:
        try:
            print_banner()
            mostrar_contexto()
            print(f"{C_BOLD}1.{C_END} START (RX)")
            print(f"{C_BOLD}2.{C_END} Ver Log ADIF")
            print(f"{C_BOLD}3.{C_END} Limpiar Pantalla (Visual)")
            print(f"{C_BOLD}4.{C_END} Salir")
            op = input(f"\n{C_GREEN}{CALLSIGN}@PHANTOM-TYPER:~ #{C_END} ")
            if op == "1": modo_operativo()
            elif op == "2":
                if os.path.exists(LOG_FILE):
                    os.system('clear')
                    print(open(LOG_FILE, "r").read())
                    input("\nEnter para volver...")
            elif op == "3":
                HISTORIAL_PANTALLA = []
                print(f"\n{C_CYAN}Historial visual limpio.{C_END}")
                time.sleep(1)
            elif op == "4":
                print(f"\n{random.choice(FRASES_DESPEDIDA)}\n")
                break
        except KeyboardInterrupt:
            print(f"\nUsa la opción 4 para salir.")
            time.sleep(1)
