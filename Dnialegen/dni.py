from flask import Flask, render_template, request
import random
import requests

app = Flask(__name__)

# 🔑 Token de Decolecta (¡NO lo compartas!)
DECOLECTA_TOKEN = "sk_9562.CG4ChQPfiV1vJtXEb0rrDQG0LKhkglrd"

# ---------------------------
# LÓGICA DEL ALGORITMO LUHN
# ---------------------------
def calcular_digito_luhn(numero):
    suma = 0
    invertir = True
    for digito in reversed(numero):
        d = int(digito)
        if invertir:
            d *= 2
            if d > 9:
                d -= 9
        suma += d
        invertir = not invertir
    return str((10 - (suma % 10)) % 10)

def generar_dni_con_luhn_inicio_valido():
    primer_digito = random.choice(['1', '4', '7'])
    otros_digitos = ''.join(str(random.randint(0, 9)) for _ in range(6))
    base_dni = primer_digito + otros_digitos
    digito_luhn = calcular_digito_luhn(base_dni)
    return base_dni + digito_luhn

def generar_varios_dnis(cantidad):
    return [generar_dni_con_luhn_inicio_valido() for _ in range(cantidad)]

# ---------------------------
# RUTA PRINCIPAL
# ---------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    datos_dni = None

    if request.method == "POST":
        # Generar DNIs
        if "generar" in request.form:
            cantidad = int(request.form.get("cantidad", 10))
            if 1 <= cantidad <= 100:
                resultados = generar_varios_dnis(cantidad)
            else:
                resultados = ["Error: la cantidad debe estar entre 1 y 100."]

        # Consultar DNI
        elif "consultar" in request.form:
            dni = request.form.get("dni_buscar", "").strip()
            if dni.isdigit() and len(dni) == 8:
                url = f"https://api.decolecta.com/v1/reniec/dni?numero={dni}"
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {DECOLECTA_TOKEN}"
                }
                try:
                    respuesta = requests.get(url, headers=headers, timeout=5)
                    if respuesta.status_code == 200:
                        datos_originales = respuesta.json()
                        datos_dni = {
                            "Número de documento": datos_originales.get("document_number"),
                            "Nombres": datos_originales.get("first_name"),
                            "Apellido paterno": datos_originales.get("first_last_name"),
                            "Apellido materno": datos_originales.get("second_last_name"),
                            "Nombre completo": datos_originales.get("full_name")
                        }
                    else:
                        try:
                            error_msg = respuesta.json().get("message", f"Error {respuesta.status_code}")
                        except:
                            error_msg = f"Error HTTP {respuesta.status_code}"
                        datos_dni = {"error": error_msg}
                except requests.exceptions.Timeout:
                    datos_dni = {"error": "Tiempo de espera agotado al consultar la API."}
                except Exception as e:
                    datos_dni = {"error": f"Error de conexión: {str(e)}"}
            else:
                datos_dni = {"error": "El DNI debe tener exactamente 8 dígitos numéricos."}

    return render_template("index.html", resultados=resultados, datos_dni=datos_dni)

if __name__ == "__main__":
    app.run(debug=True)