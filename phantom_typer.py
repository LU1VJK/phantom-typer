import subprocess
import datetime
import os
import serial
import time
import readline
import random

CALLSIGN = "LU1VJK"
BAUD = "100"
SERIAL_PORT = "/dev/ttyUSB0"
LOG_FILE = os.path.expanduser("~/PHANTOM-TYPER/phantom_history.log")

C_GREEN = "\033[92m"
C_BLUE  = "\033[94m"
C_RED   = "\033[91m"
C_BOLD  = "\033[1m"
C_END   = "\033[0m"

FRASES_DESPEDIDA = [
    "Estudiar para ganarse el ascenso de categoría, es el equivalente a ganar un concurso sin hacer trampa.",
    "La radioafición no es solo hablar, es experimentar y aprender constantemente.",
    "Mantener la ética en radio y fuera de la radio es lo que nos define como verdaderos operadores.",
    "73 cordiales!."
]

def print_banner():
    os.system('clear')
    print(f"""{C_GREEN}{C_BOLD}
    .-----------.
    | PHANTOM   |--.
    | TYPER v1.1|  |  {C_RED}[OP: {CALLSIGN}]{C_GREEN}
    '-----------'  |
       '-----------' {C_END}
    {C_BLUE}>> PHANTOM-TYPER HUB <<{C_END}""")

def log_message(mode, text):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"[{timestamp}] {mode}: {text}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
        f.flush()

def mostrar_contexto():
    if os.path.exists(LOG_FILE):
        print(f"{C_BLUE}--- HISTORIAL DE QSO ---{C_END}")
        with open(LOG_FILE, "r") as f:
            lineas = f.readlines()
            for l in lineas[-15:]:
                color = C_GREEN if "RX:" in l else C_RED
                print(f"{color}{l.strip()}{C_END}")
        print(f"{C_BLUE}-------------------------{C_END}")

def transmitir():
    print(f"\n{C_BOLD}MENSAJE (Ctrl+C para cancelar):{C_END}")
    msg = input("> ")
    if msg:
        try:
            full_payload = f"{msg} DE {CALLSIGN}\n"
            ser = serial.Serial(SERIAL_PORT)
            ser.setDTR(True)
            time.sleep(0.5)
            print(f"{C_RED}[TX] Transmitiendo...{C_END}")
            
            proc = subprocess.Popen(['minimodem', '--tx', BAUD], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=full_payload)
            
            time.sleep(0.2)
            ser.setDTR(False)
            ser.close()
            log_message("TX", full_payload.strip())
        except Exception as e:
            print(f"{C_RED}Error Serial: {e}{C_END}")
            time.sleep(2)

def recibir():
    print(f"\n{C_BLUE}[RX]{C_END} Escuchando... {C_GREEN}(Ctrl+C para Menú){C_END}")
    cmd = "stdbuf -oL minimodem --rx " + BAUD + " -q"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
    try:
        while True:
            line = proc.stdout.readline()
            if not line: break
            clean_line = line.strip()
            if clean_line:
                timestamp = datetime.datetime.now().strftime("%H:%M")
                print(f"{C_GREEN}[{timestamp}] RX: {clean_line}{C_END}")
                log_message("RX", clean_line)
    except KeyboardInterrupt:
        proc.terminate()
        print(f"\n{C_BLUE}[RX] Escucha finalizada.{C_END}")
        time.sleep(1)

if __name__ == "__main__":
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        os.makedirs(os.path.dirname(LOG_FILE))
    
    while True:
        try:
            print_banner()
            mostrar_contexto()
            
            print(f"{C_BOLD}1.{C_END} Escuchar (RX)")
            print(f"{C_BOLD}2.{C_END} Transmitir (TX)")
            print(f"{C_BOLD}3.{C_END} Ver Log Completo")
            print(f"{C_BOLD}4.{C_END} Borrar Log")
            print(f"{C_BOLD}5.{C_END} Salir")
            
            op = input(f"\n{C_GREEN}{CALLSIGN}@PHANTOM-HUB:~ #{C_END} ")
            
            if op == "1":
                recibir()
            elif op == "2":
                transmitir()
            elif op == "3":
                if os.path.exists(LOG_FILE):
                    os.system('clear')
                    print(f"{C_BLUE}--- LIBRO DE GUARDIA ---{C_END}")
                    print(open(LOG_FILE, "r").read())
                    input("\nEnter para volver...")
            elif op == "4":
                confirm = input(f"{C_RED}¿Borrar historial? (s/n): {C_END}")
                if confirm.lower() == 's':
                    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
                    print("Log borrado.")
                    time.sleep(1)
            elif op == "5":
                frase = random.choice(FRASES_DESPEDIDA)
                print(f"\n\n" + " " * 5 + f"{C_BLUE}{C_BOLD}{frase}{C_END}" + "\n")
                time.sleep(3)
                break
        except KeyboardInterrupt:
            print(f"\n{C_RED}Operación cancelada.{C_END}")
            time.sleep(1)
            continue
