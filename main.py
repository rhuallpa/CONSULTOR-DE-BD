from flask import Flask, request, render_template, jsonify
import psycopg2
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno del archivo .env
load_dotenv()

# Configurar API Key y URL de la base de datos desde el archivo .env
API_KEY = os.getenv('API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# Configuración de la API de Google
genai.configure(api_key=API_KEY)

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Función para conectar a la base de datos
def consulta_bd(query):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(query)
        # Obtener nombres de columnas
        column_names = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        conn.close()
        # Emparejar datos con nombres de columnas
        return {"columns": column_names, "rows": data}
    except psycopg2.Error as e:
        return {"error": str(e)}

# Generación de consultas SQL mejorada
def generate_sql_query(user_input):
    user_input = user_input.lower()

    # Consultas generales
    if "cliente" in user_input:
        if "mas compran" in user_input:
            return "SELECT clientes.name, COUNT(compras.id) AS total_compras FROM clientes LEFT JOIN compras ON clientes.id = compras.cliente_id GROUP BY clientes.name ORDER BY total_compras DESC LIMIT 1;"
        elif "menos compran" in user_input:
            return "SELECT clientes.name, COUNT(compras.id) AS total_compras FROM clientes LEFT JOIN compras ON clientes.id = compras.cliente_id GROUP BY clientes.name ORDER BY total_compras ASC LIMIT 1;"
        else:
            return "SELECT * FROM clientes;"

    elif "producto" in user_input:
        if "mas vendido" in user_input:
            return "SELECT productos.nombre, SUM(compras.cantidad) AS total_vendido FROM productos LEFT JOIN compras ON productos.id = compras.producto_id GROUP BY productos.nombre ORDER BY total_vendido DESC LIMIT 1;"
        elif "menos vendido" in user_input:
            return "SELECT productos.nombre, SUM(compras.cantidad) AS total_vendido FROM productos LEFT JOIN compras ON productos.id = compras.producto_id GROUP BY productos.nombre ORDER BY total_vendido ASC LIMIT 1;"
        elif "mas caro" in user_input:
            return "SELECT nombre, precio FROM productos ORDER BY precio DESC LIMIT 1;"
        elif "mas barato" in user_input:
            return "SELECT nombre, precio FROM productos ORDER BY precio ASC LIMIT 1;"
        elif "stock mas alto" in user_input:
            return "SELECT nombre, stock FROM productos ORDER BY stock DESC LIMIT 1;"
        elif "stock bajo" in user_input or "acabando stock" in user_input:
            return "SELECT nombre, stock FROM productos WHERE stock > 0 ORDER BY stock ASC LIMIT 1;"
        else:
            return "SELECT * FROM productos;"

    elif "compra" in user_input:
        if "fecha mas ventas" in user_input:
            return "SELECT fecha_compra, SUM(cantidad) AS ventas_totales FROM compras GROUP BY fecha_compra ORDER BY ventas_totales DESC LIMIT 1;"
        elif "mes mas ventas" in user_input:
            return "SELECT TO_CHAR(fecha_compra, 'Month') AS mes, SUM(cantidad) AS ventas_totales FROM compras GROUP BY mes ORDER BY ventas_totales DESC LIMIT 1;"
        elif "ventas totales" in user_input:
            return "SELECT SUM(cantidad) AS ventas_totales FROM compras;"
        else:
            return "SELECT * FROM compras;"
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    
    # Generar consulta SQL basada en el input del usuario
    query = generate_sql_query(user_input)
    if query:
        data = consulta_bd(query)
        if "error" not in data:
            return jsonify({"table": data})
        else:
            return jsonify({"response": f"Error en la consulta: {data['error']}"})
    else:
        # Usar la API de Google para generar respuestas
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(user_input)
        return jsonify({"response": response.text})

if __name__ == "__main__":
    app.run(debug=True)
