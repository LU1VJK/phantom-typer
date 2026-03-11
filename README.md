```_____  _                 _                   _______                             
 |  __ \| |               | |                 |__   __|                            
 | |__) | |__   __ _ _ __ | |_ ___  _ __ ___     | |_   _ _ __   ___ _ __          
 |  ___/| '_ \ / _` | '_ \| __/ _ \| '_ ` _ \    | | | | | '_ \ / _ \ '__|         
 | |    | | | | (_| | | | | |_| (_) | | | | | |   | | |_| | |_) |  __/ |            
 |_|    |_| |_|\__,_|_| |_|\__\___/|_| |_| |_|   |_|\__, | .__/ \___|_|            
                                                     __/ | |                       
 >> TERMINAL AFSK V3 | DE LU1VJK | BARILOCHE DX <<|___/|_|
```
Phantom Typer v3.0 (Web Edition)
Esta nueva versión del Phantom Typer evoluciona de una interfaz de comandos pura a un servidor web basado en Flask y SocketIO. El objetivo sigue siendo el mismo: mantener la simplicidad y la mística de las terminales de los 80, pero permitiendo operar la Raspberry Pi desde cualquier dispositivo (celular, tablet o PC) mediante un navegador, sin perder la robustez de la modulación AFSK a 100 baudios.

Novedades de la Versión 3.0
Interfaz Web Responsiva: Panel de control accesible vía HTTP.

Gestión de PTT Dual: Soporte para VOX y control directo por DTR (Serial).

Sistema de Logs Automático: Generación de registros en formato ADIF para fácil exportación.

Macros Integradas: Botones rápidos para CQ, AGN, RST y 73.

Historial en Tiempo Real: Visualización del tráfico RX/TX y logs previos en la misma pantalla.

Requisitos Técnicos
Hardware: Raspberry Pi (probado en Pi 3/4) con interfaz de audio (USB o integrada).

Software: Python 3, Flask, Flask-SocketIO, PyAudio, y el motor de modulación minimodem.

Dependencias de Sistema:
sudo apt-get install minimodem portaudio19-dev python3-pyaudio

Configuración y Uso
Ejecución: Corre el script phantom_typer.py en tu Raspberry Pi.

Acceso: Abre un navegador en la red local e ingresa a http://<IP_DE_TU_PI>:5000.

Configuración Inicial: Al ingresar, el sistema solicitará tu distintiva (Callsign), la banda de operación y el método de PTT.

Operación: * Usa el campo Corresponsal y el botón SET para iniciar un QSO. Esto permite que las macros y el log automático funcionen correctamente.

El botón TX ENVIAR o la tecla Enter transmiten el texto escrito en el campo de mensaje.

Al finalizar el contacto, el botón SAVE LOG guarda la información en formato ADIF dentro de la carpeta ~/PHANTOM-TYPER/.

Estructura del Proyecto
El núcleo del sistema utiliza threading para gestionar el flujo de audio de minimodem sin bloquear la interfaz web. El audio es capturado y procesado a una tasa de 8000 Hz, optimizada para la decodificación de señales de radio en condiciones de ruido.

"La idea sigue siendo la misma: una herramienta rústica, funcional y directa. Menos look-and-feel moderno, más sabor a radioafición clásica."
