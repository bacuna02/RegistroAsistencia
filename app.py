# archivo: app.py
from flask import Flask, request, render_template_string, url_for
from datetime import datetime
import math
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Coordenadas del taller (ejemplo: Villa María del Triunfo, Lima)
TALLER_LAT = -12.218535
TALLER_LON = -76.908586
RADIO_PERMITIDO = 0.05  # en km (50 metros)

# Definir zona horaria de Lima
tz = pytz.timezone("America/Lima")

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "/etc/secrets/registroasistencia-506822-3b8cf94e41bd.json", scope)
client = gspread.authorize(creds)

# Abre tu hoja llamada "Asistencia"
sheet = client.open("RegistroAsistencia_Taller").sheet1

def distancia(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def guardar_google_sheets(nombre, dni, fecha, hora, tipo, lat, lon):
    registros = sheet.get_all_values()
    for fila in registros:
        if len(fila) >= 5 and fila[1] == dni and fila[2] == fecha and fila[4] == tipo:
            return False
    sheet.append_row([nombre, dni, fecha, hora, tipo, lat, lon])
    return True

@app.route("/", methods=["GET", "POST"])
def asistencia():
    mensaje = None
    clase = None

    if request.method == "POST":
        nombre = request.form["nombre"]
        dni = request.form["dni"]
        tipo = request.form["tipo"]
        lat = float(request.form["lat"])
        lon = float(request.form["lon"])
        fecha = datetime.now(tz).strftime("%Y-%m-%d")
        hora = datetime.now(tz).strftime("%H:%M:%S")

        if distancia(lat, lon, TALLER_LAT, TALLER_LON) > RADIO_PERMITIDO:
            mensaje = "❌ No estás en el taller, registro rechazado"
            clase = "error"
        elif not guardar_google_sheets(nombre, dni, fecha, hora, tipo, lat, lon):
            mensaje = f"❌ Ya registraste {tipo} hoy"
            clase = "warning"
        else:
            mensaje = f"✅ {tipo} registrada correctamente a las {hora}"
            clase = "success"

    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Registro de Asistencia</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Roboto', sans-serif;
                    background-color: #f4f4f4;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .contenedor {{
                    background: white;
                    padding: 30px 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    text-align: center;
                    width: 340px;
                }}
                .alert {{
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 15px;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .warning {{
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeeba;
                }}
                input, select {{
                    margin: 10px 0;
                    padding: 8px;
                    width: 90%;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                button {{
                    background-color: #ffcc00;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    color: #333;
                    transition: background-color 0.3s;
                }}
                button:hover {{
                    background-color: #e6b800;
                }}
            </style>
        </head>
        <body>
            <div class="contenedor">
                <img src="{{{{ url_for('static', filename='logo.png') }}}}" alt="Logo Creativ Proyectos">
                <h2>Registro de Asistencia</h2>
                {% if mensaje %}
                    <div class="alert {{clase}}">{{mensaje}}</div>
                {% endif %}
                <form method="post" onsubmit="return enviarUbicacion();">
                    <input type="text" name="nombre" placeholder="Nombre" required><br>
                    <input type="text" name="dni" placeholder="DNI" required><br>
                    <select name="tipo" required>
                        <option value="Entrada">Entrada</option>
                        <option value="Salida">Salida</option>
                    </select><br>
                    <input type="hidden" name="lat" id="lat">
                    <input type="hidden" name="lon" id="lon">
                    <button type="submit">Marcar asistencia</button>
                </form>
            </div>
            <script>
            function enviarUbicacion() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(function(pos) {{
                        document.getElementById("lat").value = pos.coords.latitude;
                        document.getElementById("lon").value = pos.coords.longitude;
                        document.forms[0].submit();
                    }});
                    return false;
                }} else {{
                    alert("Tu navegador no soporta GPS");
                    return false;
                }}
            }}
            </script>
        </body>
        </html>
    ''', mensaje=mensaje, clase=clase)

if __name__ == "__main__":
    app.run(debug=True)
