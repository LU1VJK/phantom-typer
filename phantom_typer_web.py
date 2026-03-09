import os
import sys
import datetime
import subprocess
import threading
import time
import re
import serial
import signal
import struct
import math
import pyaudio
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

BAUD = "100"
SERIAL_PORT = "/dev/ttyUSB0"
LOG_FOLDER = os.path.expanduser("~/PHANTOM-TYPER/")
TABLA_BANDAS = {
    "80M": "3.580", "40M": "7.040", "20M": "14.080", "15M": "21.080", "10M": "28.080"
}
AUDIO_RATE = 8000
AUDIO_CHUNK = 1024

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'phantom_secret_key!'
socketio = SocketIO(app, async_mode='threading')

state = {
    "callsign": "",
    "band": "40M",
    "freq": "7.080",
    "ptt_method": "VOX",
    "corresponsal": "",
    "hora_inicio_qso": "",
    "configured": False,
    "rx_active": True
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Phantom Typer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --primary: #bb86fc;
            --secondary: #ffffff; 
            --danger: #cf6679;
            --text-main: #e1e1e1;
            --text-dim: #ffffff;  
            --border: #333;
            --tx-color: #00ff00; 
            --btn-tx: #2e7d32; 
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 10px; height: 100vh; box-sizing: border-box; overflow: hidden; }
        
        #config-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(18, 18, 18, 0.98); z-index: 10; display: flex;
            justify-content: center; align-items: center; flex-direction: column;
            overflow-y: auto;
        }
        #config-overlay.hidden { display: none; }
        .config-box { background: var(--card-bg); padding: 30px; border-radius: 15px; width: 90%; max-width: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { margin-top: 0; color: var(--primary); text-align: center; text-transform: uppercase; letter-spacing: 2px; }
        
        .skull-pre {
            font-family: monospace; font-size: 10px; line-height: 1; color: #8833ff;
            text-align: center; margin-bottom: 20px; white-space: pre; background: none; border: none;
        }
        .s-p { color: #8833ff; } .s-r { color: #ff0000; font-weight: bold; } .s-m { color: #ff00ff; } 

        input, select {
            background: #2c2c2c; color: var(--text-main); border: 1px solid var(--border);
            padding: 12px; margin: 5px 0; font-size: 16px; width: 100%; box-sizing: border-box;
            border-radius: 8px;
        }
        
        .btn-main { width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .btn-start { background: var(--primary); color: #000; }
        
        .main-container { display: flex; flex-direction: column; height: 100%; max-height: 100vh; gap: 8px; }
        
        .header {
            display: flex; justify-content: space-between; align-items: center;
            background: var(--card-bg); padding: 10px; border-radius: 12px;
        }
        .header-item { text-align: center; display: flex; flex-direction: column; align-items: center; }
        .header-label { font-size: 10px; color: var(--text-dim); text-transform: uppercase; }
        .header-value { font-size: 16px; font-weight: bold; color: var(--secondary); }

        #status-led { width: 12px; height: 12px; border-radius: 50%; background: #ff0000; margin-top: 5px; }

        .console-container {
            flex: 1; background: var(--card-bg); border-radius: 12px;
            padding: 12px; overflow-y: auto; font-family: 'Courier New', monospace;
            border: 1px solid var(--border); font-size: 14px; line-height: 1.3;
            min-height: 200px;
        }
        .tx-msg { color: var(--tx-color); font-weight: bold; } 
        .rx-msg { color: var(--secondary); } 
        .sys-msg { color: #ffffff !important; font-size: 15px; font-weight: 900; }

        .controls-section { background: var(--bg-color); padding-top: 5px; }
        .controls-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
        .input-row { display: grid; grid-template-columns: 3fr 1fr; gap: 6px; margin-bottom: 6px; }
        
        .ctrl-btn {
            background: #2c2c2c; color: var(--text-main); border: 1px solid var(--border);
            padding: 10px 5px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 12px;
        }
        .btn-tx { grid-column: span 4; background: var(--btn-tx); color: #fff; border: none; padding: 12px; }
        .btn-cq { background: #3d5afe; color: #fff; }
        .btn-agn { background: #ff9100; color: #000; }
        .btn-rst { background: var(--secondary); color: #000; }
        .btn-73 { background: var(--btn-tx); color: #fff; border: none; }
        .btn-set { background: #00bcd4; color: #000; }
        .btn-clear { background: #fdd835; color: #000; border: none; }
        .btn-settings { background: #aa00ff; color: #fff; }
        .btn-save { background: var(--primary); color: #000; }
        .btn-stop { background: #b00020; color: #fff; border: none; }

        @media (min-width: 900px) {
            .main-layout-wrapper { display: grid; grid-template-columns: 3fr 1fr; gap: 15px; height: 100%; }
            .log-container { display: block; background: var(--card-bg); border-radius: 12px; padding: 15px; overflow-y: auto; }
            .log-title { color: var(--primary); border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 10px; font-weight: bold; }
            .log-entry { color: #a0a0a0; font-size: 12px; margin-bottom: 5px; border-bottom: 1px solid #252525; padding-bottom: 2px; }
        }
        .hidden { display: none !important; }
    </style>
</head>
<body>

    <div id="config-overlay">
        <pre class="skull-pre">
<span class="s-p">            __            </span>
<span class="s-p">         ,gS$$</span><span class="s-r">$Sk.        </span>
<span class="s-p">      ,d$$$$$$</span><span class="s-r">$$$$$k.     </span>
<span class="s-p">    /?^?$7°' '</span><span class="s-r">`?$SS$$L.   </span>
<span class="s-p">    ,?  $SL.__</span><span class="s-r"> ,d$iIS$$SL  </span>
<span class="s-p">   j$Su%$S$$$$</span><span class="s-r">$?:iIS$$Sb   </span>
<span class="s-p"> :?°?^4$S$$"°?</span><span class="s-r">$SL:iIS$SI:  </span>
<span class="s-p"> :'    '/`?$' </span><span class="s-r">.  `?Lis$$SI: </span>
<span class="s-p">  '      '    </span><span class="s-m">  ?kiSSI?    </span>
<span class="s-p">      :.      </span><span class="s-m">$k _ `?Si7  </span>
<span class="s-p">      .._.._  </span><span class="s-m">i$S%7·:i?'  </span>
<span class="s-p">      ?%uS%uod</span><span class="s-m">$$$?`·?°`    </span>
<span class="s-p">      S$$$$$$$</span><span class="s-m">$SSi         </span>
<span class="s-p">      `?$$S?  </span><span class="s-m">             </span></pre>
        <div class="config-box">
            <h2>Phantom Typer</h2>
            <input type="text" id="input_call" placeholder="Tu Distintiva">
            <select id="input_band">{% for b, f in bands.items() %}<option value="{{ b }}">{{ b }} ({{ f }} MHz)</option>{% endfor %}</select>
            <select id="input_ptt">
                <option value="VOX">PTT: VOX</option>
                <option value="DTR">PTT: DTR (Serial)</option>
            </select>
            <button class="btn-main btn-start" onclick="save_config()">INICIAR</button>
        </div>
    </div>

    <div id="main-ui" class="hidden">
        <div class="main-layout-wrapper">
            <div class="main-container">
                <div class="header">
                    <div class="header-item">
                        <div class="header-label">Operador</div>
                        <div class="header-value" id="disp_call">---</div>
                    </div>
                    <div class="header-item">
                        <div class="header-label">Banda</div>
                        <div class="header-value" id="disp_band">---</div>
                    </div>
                    <div class="header-item">
                        <div class="header-label">Power</div>
                        <div id="status-led"></div>
                    </div>
                    <div class="header-item">
                        <div class="header-label">Modo</div>
                        <div class="header-value" id="status_text">RX</div>
                    </div>
                </div>

                <div class="console-container" id="console"></div>

                <div class="controls-section">
                    <div class="input-row">
                        <input type="text" id="to_call" placeholder="Corresponsal">
                        <button class="ctrl-btn btn-set" onclick="set_corresponsal()">SET</button>
                    </div>
                    <div class="input-row">
                        <input type="text" id="msg_text" placeholder="Mensaje" onkeypress="if(event.keyCode==13) send_tx();">
                    </div>

                    <div class="controls-grid">
                        <button class="ctrl-btn btn-tx" onclick="send_tx()">TX ENVIAR</button>
                        <button class="ctrl-btn btn-cq" onclick="send_cq()">CQ</button>
                        <button class="ctrl-btn btn-agn" onclick="send_agn()">AGN</button>
                        <button class="ctrl-btn btn-rst" onclick="send_rst()">RST 599</button>
                        <button class="ctrl-btn btn-73" onclick="send_73()">TNX 73</button>
                        <button class="ctrl-btn btn-clear" onclick="clear_screen()">LIMPIAR</button>
                        <button class="ctrl-btn btn-settings" onclick="open_settings()">AJUSTES</button>
                        <button class="ctrl-btn btn-save" onclick="save_log()">SAVE LOG</button>
                        <button class="ctrl-btn btn-stop" onclick="shutdown_server()">APAGAR</button>
                    </div>
                </div>
            </div>

            <div class="log-container">
                <div class="log-title">HISTORIAL DE LOGS</div>
                <div id="log-history">Sin datos.</div>
            </div>
        </div>
    </div>

    <script type="text/javascript">
        var socket = io();
        var consoleDiv = document.getElementById('console');
        var statusText = document.getElementById('status_text');
        var logHistoryDiv = document.getElementById('log-history');
        var configOverlay = document.getElementById('config-overlay');
        var mainUi = document.getElementById('main-ui');
        var statusLed = document.getElementById('status-led');
        var currentCorresponsal = "";

        socket.on('connect', function() { socket.emit('get_state'); });

        socket.on('state_update', function(data) {
            document.getElementById('disp_call').innerText = data.callsign;
            document.getElementById('disp_band').innerText = data.band;
            currentCorresponsal = data.corresponsal;
            if(data.configured) {
                configOverlay.classList.add('hidden');
                mainUi.classList.remove('hidden');
                statusLed.style.background = "#00ff00";
            } else {
                configOverlay.classList.remove('hidden');
                mainUi.classList.add('hidden');
                statusLed.style.background = "#ff0000";
                consoleDiv.innerHTML = "";
            }
        });

        socket.on('update_logs', function(html) { logHistoryDiv.innerHTML = html; });

        socket.on('rx_message', function(data) {
            var cls = data.type || 'rx-msg';
            var line = '<div class="' + cls + '">[' + data.time + '] ' + data.text + '</div>';
            consoleDiv.innerHTML += line;
            
            var lines = consoleDiv.getElementsByTagName('div');
            if (lines.length > 10) {
                consoleDiv.removeChild(lines[0]);
            }
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        });

        socket.on('status_update', function(data) {
            statusText.innerText = data.msg;
        });

        function clean_call(val) { return val.toUpperCase().replace(/[^A-Z0-9]/g, ''); }

        function save_config() {
            var call = clean_call(document.getElementById('input_call').value);
            if(call.length < 3) { alert("Distintiva inválida"); return; }
            socket.emit('save_config', {callsign: call, band: document.getElementById('input_band').value, ptt: document.getElementById('input_ptt').value});
        }
        
        function set_corresponsal() { 
            var c = clean_call(document.getElementById('to_call').value);
            if(!c) { alert("Ingresa una distintiva válida."); return; }
            currentCorresponsal = c;
            document.getElementById('to_call').value = c;
            socket.emit('set_corresponsal', {call: c}); 
        }

        function send_tx() { var m=document.getElementById('msg_text').value; if(m){socket.emit('transmit', {msg: m, directed: false}); document.getElementById('msg_text').value='';} }
        function send_cq() { socket.emit('transmit_cq', {msg: 'CQ CQ CQ'}); }
        function send_agn() { socket.emit('transmit_agn', {msg: 'AGN AGN'}); }
        
        function send_rst() { 
            if(!currentCorresponsal) { alert("Error: No has cargado corresponsal."); return; }
            socket.emit('transmit_rst', {msg: '599'}); 
        }
        
        function send_73() { 
            if(!currentCorresponsal) { alert("Error: No has cargado corresponsal."); return; }
            socket.emit('transmit_73', {msg: 'TNX FOR QSO, 73!'}); 
        }
        
        function save_log() {
            if(!currentCorresponsal) { alert("Error: No has cargado corresponsal."); return; }
            socket.emit('save_log', {call: currentCorresponsal}); 
            document.getElementById('to_call').value=''; 
            currentCorresponsal = "";
        }

        function clear_screen() { consoleDiv.innerHTML = ""; }
        function open_settings() { socket.emit('reset_config'); }
        function shutdown_server() {
            if(confirm("¿Seguro que quieres detener el servidor?")) {
                socket.emit('shutdown_request');
            }
        }
    </script>
</body>
</html>
"""

def get_log_history_html():
    log_file = os.path.join(LOG_FOLDER, f"{state['callsign']}.log")
    html = ""
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = [line.strip() for line in f.readlines() if "<QSO_DATE" in line]
            for l in reversed(lines[-10:]):
                call = re.search(r'<CALL:\d+>(.*?) <BAND', l)
                time_match = re.search(r'<TIME_ON:4>(\d+)', l)
                if call:
                    t = time_match.group(1) if time_match else "--"
                    html += f"<div class='log-entry'>{t} -> {call.group(1)}</div>"
    return html if html else "<div style='color:#555; font-size:12px;'>Sin logs.</div>"

def log_adif(remote_call):
    date_utc = datetime.datetime.utcnow().strftime("%Y%m%d")
    time_utc = state['hora_inicio_qso'] if state['hora_inicio_qso'] else datetime.datetime.utcnow().strftime("%H%M")
    log_file = os.path.join(LOG_FOLDER, f"{state['callsign']}.log")
    entry = f"<QSO_DATE:8>{date_utc} <TIME_ON:4>{time_utc} <STATION_CALLSIGN:{len(state['callsign'])}>{state['callsign']} <CALL:{len(remote_call)}>{remote_call} <BAND:{len(state['band'])}>{state['band']} <FREQ:{len(state['freq'])}>{state['freq']} <MODE:7>AFSK100 <RST_SENT:3>599 <EOR>"
    with open(log_file, "a") as f: f.write(entry + "\n")

def generate_wav_header():
    return struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 0x7FFFFFFF, b'WAVE', b'fmt ', 16, 1, 1, 8000, 16000, 2, 16, b'data', 0x7FFFFFFF)

def process_rx():
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=AUDIO_RATE, input=True, frames_per_buffer=AUDIO_CHUNK)
    except:
        return

    cmd = ['minimodem', '--rx', BAUD, '-q', '-R', '8000', '--file', '-']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc.stdin.write(generate_wav_header())
    proc.stdin.flush()
    socketio.emit('status_update', {'msg': 'RX ACTIVO'})
    
    while state['rx_active']:
        try:
            data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
            proc.stdin.write(data)
            proc.stdin.flush()
            import select
            ready, _, _ = select.select([proc.stdout], [], [], 0.01)
            if ready:
                line = proc.stdout.readline().decode('utf-8', errors='replace').strip()
                if line:
                    socketio.emit('rx_message', {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'text': line, 'type': 'rx-msg'})
        except:
            break
            
    stream.stop_stream()
    stream.close()
    p.terminate()
    proc.terminate()

def transmit_audio_logic(text, remote_call=None):
    msg_completo = ""
    if remote_call is True: msg_completo = f"{state['corresponsal']} {text} DE {state['callsign']}\n"
    elif isinstance(remote_call, str): msg_completo = f"{text} DE {state['callsign']}\n"
    else: msg_completo = f"{text} DE {state['callsign']}\n"

    socketio.emit('rx_message', {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'text': msg_completo.strip(), 'type': 'tx-msg'})
    socketio.emit('status_update', {'msg': 'TX ACTIVE'})

    ser = None
    try:
        if state['ptt_method'] == "DTR":
            try:
                ser = serial.Serial(SERIAL_PORT)
                ser.setDTR(True)
                time.sleep(0.5)
            except:
                ser = None
        
        proc = subprocess.Popen(['minimodem', '--tx', BAUD], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=msg_completo)
        
        if ser:
            time.sleep(0.2)
            ser.setDTR(False)
            ser.close()
        socketio.emit('status_update', {'msg': 'RX ACTIVO'})
    except:
        if ser: ser.close()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, state=state, bands=TABLA_BANDAS)

@socketio.on('get_state')
def handle_get_state():
    emit('state_update', state)
    if state['configured']: emit('update_logs', get_log_history_html())

@socketio.on('save_config')
def handle_save_config(data):
    state['callsign'] = data['callsign']
    state['band'] = data['band']
    state['freq'] = TABLA_BANDAS[data['band']]
    state['ptt_method'] = data['ptt']
    state['configured'] = True
    emit('state_update', state)
    emit('update_logs', get_log_history_html())
    threading.Thread(target=process_rx, daemon=True).start()

@socketio.on('reset_config')
def handle_reset():
    state['configured'] = False
    emit('state_update', state)

@socketio.on('set_corresponsal')
def handle_set_corresponsal(data):
    state['corresponsal'] = data['call'].upper()
    state['hora_inicio_qso'] = datetime.datetime.utcnow().strftime("%H%M")
    socketio.emit('status_update', {'msg': f'QSO: {state["corresponsal"]}'})

@socketio.on('transmit')
def handle_transmit(data):
    target = True if data['directed'] else None
    threading.Thread(target=transmit_audio_logic, args=(data['msg'], target)).start()

@socketio.on('transmit_cq')
def handle_cq(data): threading.Thread(target=transmit_audio_logic, args=(data['msg'], "CQ")).start()

@socketio.on('transmit_agn')
def handle_agn(data): threading.Thread(target=transmit_audio_logic, args=(data['msg'], "AGN")).start()

@socketio.on('transmit_rst')
def handle_rst(data): threading.Thread(target=transmit_audio_logic, args=(data['msg'], True)).start()

@socketio.on('transmit_73')
def handle_73(data): threading.Thread(target=transmit_audio_logic, args=(data['msg'], True)).start()

@socketio.on('save_log')
def handle_log(data):
    log_adif(data['call'].upper())
    state['corresponsal'] = ""; state['hora_inicio_qso'] = ""
    socketio.emit('update_logs', get_log_history_html())
    socketio.emit('rx_message', {'time': datetime.datetime.now().strftime("%H:%M:%S"), 'text': f'[LOG] GUARDADO: {data["call"]}', 'type': 'sys-msg'})

@socketio.on('shutdown_request')
def handle_shutdown():
    os._exit(0)

if __name__ == '__main__':
    print("\n>>> PHANTOM TYPER WEB v3.0 <<<")
    print(f">>> Abre en tu navegador: http://IP_RASPBERRY:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
