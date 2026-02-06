```_____  _                 _                   _______                             
 |  __ \| |               | |                 |__   __|                            
 | |__) | |__   __ _ _ __ | |_ ___  _ __ ___     | |_   _ _ __   ___ _ __          
 |  ___/| '_ \ / _` | '_ \| __/ _ \| '_ ` _ \    | | | | | '_ \ / _ \ '__|         
 | |    | | | | (_| | | | | |_| (_) | | | | | |   | | |_| | |_) |  __/ |            
 |_|    |_| |_|\__,_|_| |_|\__\___/|_| |_| |_|   |_|\__, | .__/ \___|_|            
                                                     __/ | |                       
 >> TERMINAL AFSK V1.1 | DE LU1VJK | BARILOCHE DX <<|___/|_|
```
PhantomTyper es una interfaz de comunicación por texto para HF y VHF diseñada para el intercambio asincrónico de datos. Este desarrollo nace de una cuenta pendiente que traía desde los años 90: en esa época, cuando decodificaba mis primeros mensajes POCSAG con el POC32 y más adelante con el PDW, me quedó grabada la idea de desarrollar un sistema propio. Pasó el tiempo, pero la intención de concretarlo siempre estuvo ahí; hoy, el PhantomTyper es el resultado de ese proyecto que finalmente pude cerrar.

Mi visión con este proyecto fue alejarme de los modos digitales modernos que dependen de interfaces gráficas pesadas y complejas. Quise recuperar la esencia del phreaking y esa mística de las terminales de comandos de los 80, pero adaptándolas a lo que hoy busco como radioaficionado: simplicidad, control y un entorno de operación limpio. Sobre todo, busqué cero complejidad en lo que es la programación, sin poner el foco en el "look and feel" web, sino todo lo contrario: lo más rústico y básico posible.

Cómo funca el sistema
Para la transmisión, elegí modulación AFSK a 100 baudios. Mi prioridad no fue la velocidad, sino lograr un equilibrio: quería que el texto fluyera de forma natural en la pantalla, pero con la robustez necesaria para bancarse el ruido o el fading. El programa está desarrollado en Python sobre una Raspberry Pi, gestiona el PTT automáticamente mediante DTR y mantiene un registro histórico de cada QSO.

No busqué competir con los protocolos automáticos que dominan la radio hoy en día, ni ofrecer una solución matemática al ruido creando algo nuevo; simplemente me dediqué a utilizar librerías disponibles y experimentar hasta que salga algo medianamente potable y funcional. Mis conocimientos de programación nunca tuvieron el foco en las comunicaciones vía radio, así que esto fue pura exploración.

Mi idea fue desarrollar algo simple, tener una herramienta (un juguete, si se quiere) que me dé la satisfacción de estar frente a una terminal pura, donde la comunicación es directa y tenga ese sabor a radioafición clásica. Es, básicamente, las ganas de experimentar, jugar a la radio y concretar algo a casi 30 años de anhelar algo similar.

Espero convencer a algún colega que se sienta cómodo con una consola, en vez de un entorno gráfico, para hacer algunas pruebas entre estaciones.
