"""
BOT DE WHATSAPP BUSINESS API - v1.0
Integración oficial con Meta
Responde automáticamente a mensajes en WhatsApp
"""

from flask import Flask, request
import requests
import json
import re
from datetime import datetime

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN - EDITA ESTOS VALORES
# ═══════════════════════════════════════════════════════════

# Obtén estos valores de tu cuenta Meta
PHONE_ID = "TU_PHONE_ID_AQUI"  # Ej: 102010...
TOKEN = "TU_TOKEN_AQUI"         # Ej: EAABsZA...
VERIFY_TOKEN = "TU_VERIFY_TOKEN_AQUI"  # El que creaste en webhooks
BUSINESS_ACCOUNT_ID = "TU_BUSINESS_ID_AQUI"  # Ej: 100258...

# URL base de la API
API_URL = f"https://graph.instagram.com/v18.0/{PHONE_ID}/messages"

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RESPUESTAS POR CONTACTO
# ═══════════════════════════════════════════════════════════

RESPUESTAS_POR_CONTACTO = {
    'johana': {
        'hola': "¡Hola Johana! ¿Qué tal? 😊",
        'productos': "Johana, tenemos: Laptop, Mouse, Teclado",
        'precios': "Para ti, Johana: Laptop $800, Mouse $20, Teclado $50",
    },
    'rene': {
        'hola': "¡Hola Rene! Gracias por contactarnos 🙏",
        'productos': "Rene, nuestros productos son: Laptop, Mouse, Teclado",
        'precios': "Cotización para Rene: Laptop $800, Mouse $20, Teclado $50",
    }
}

RESPUESTAS_DEFECTO = {
    'hola': "¡Hola! ¿En qué te puedo ayudar?",
    'productos': "Vendemos: Laptop, Mouse, Teclado. ¿Cuál te interesa?",
    'precios': "Los precios son: Laptop $800, Mouse $20, Teclado $50",
}

# ═══════════════════════════════════════════════════════════
# PATRONES PARA DETECTAR PALABRAS CLAVE
# ═══════════════════════════════════════════════════════════

PATRONES = {
    'hola': [
        r'\bhola\b',
        r'\bholaa+\b',
        r'\bHOLA\b',
        r'\bHi\b',
        r'\bhey\b',
        r'\bHey\b',
    ],
    'productos': [
        r'\bcuales?\s+son?\s+los?\s+productos',
        r'\bqué\s+productos\s+vendes?',
        r'\bqué\s+venden?',
        r'\bcuales?\s+productos\s+tienen?',
        r'\bqué\s+tienen\s+disponible',
        r'\bproductos\b',
        r'\bcatálogo\b',
        r'\blista\s+de\s+productos',
        r'\bvenden\b',
    ],
    'precios': [
        r'\bcuál\s+es?\s+el?\s+precio',
        r'\bcuánto\s+cuesta',
        r'\bcuánto\s+vales?',
        r'\bprecio',
        r'\bcosto',
        r'\btarifa',
        r'\bvalor\b',
        r'\bcuántos?\s+dinero',
    ]
}

# ═══════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ═══════════════════════════════════════════════════════════

def detectar_palabra_clave(mensaje, nombre_contacto=None):
    """
    Detecta palabras clave en el mensaje y devuelve la respuesta apropiada
    """
    mensaje_limpio = mensaje.strip().lower()
    
    # Busca en los patrones
    for categoria, patrones in PATRONES.items():
        for patron in patrones:
            if re.search(patron, mensaje_limpio, re.IGNORECASE):
                # Busca respuesta personalizada por contacto
                if nombre_contacto and nombre_contacto.lower() in RESPUESTAS_POR_CONTACTO:
                    respuesta = RESPUESTAS_POR_CONTACTO[nombre_contacto.lower()].get(
                        categoria,
                        RESPUESTAS_DEFECTO[categoria]
                    )
                else:
                    # Respuesta por defecto
                    respuesta = RESPUESTAS_DEFECTO[categoria]
                
                return categoria, respuesta
    
    return None, None


def enviar_mensaje(numero_destinatario, texto_respuesta):
    """
    Envía un mensaje a través de WhatsApp Business API
    """
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destinatario,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": texto_respuesta
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Mensaje enviado a {numero_destinatario}")
            return True
        else:
            print(f"❌ Error al enviar mensaje: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def procesar_mensaje_entrante(data):
    """
    Procesa un mensaje entrante de WhatsApp
    """
    try:
        # Extrae información del mensaje
        cambios = data.get('entry', [{}])[0].get('changes', [{}])[0]
        valor = cambios.get('value', {})
        
        # Obtiene los mensajes
        mensajes = valor.get('messages', [])
        if not mensajes:
            return
        
        mensaje_data = mensajes[0]
        numero_remitente = mensaje_data.get('from')
        texto_mensaje = mensaje_data.get('text', {}).get('body', '')
        
        # Obtiene información del contacto
        contactos = valor.get('contacts', [])
        nombre_contacto = contactos[0].get('profile', {}).get('name') if contactos else None
        
        print(f"\n{'='*60}")
        print(f"📨 Mensaje recibido")
        print(f"De: {nombre_contacto or 'Desconocido'} ({numero_remitente})")
        print(f"Texto: {texto_mensaje}")
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Detecta palabra clave
        categoria, respuesta = detectar_palabra_clave(texto_mensaje, nombre_contacto)
        
        if categoria:
            print(f"✓ Detectado: '{categoria}'")
            if nombre_contacto and nombre_contacto.lower() in RESPUESTAS_POR_CONTACTO:
                print(f"📍 Usando respuesta personalizada para {nombre_contacto.upper()}")
            else:
                print(f"📍 Usando respuesta por defecto")
            
            # Envía la respuesta
            if enviar_mensaje(numero_remitente, respuesta):
                print(f"✉️ Respuesta enviada: {respuesta}\n")
        else:
            print(f"✗ No contiene palabras clave - sin respuesta\n")
    
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")


# ═══════════════════════════════════════════════════════════
# RUTAS DE FLASK (WEBHOOKS)
# ═══════════════════════════════════════════════════════════

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Maneja los webhooks de WhatsApp
    """
    if request.method == 'GET':
        # Meta verifica que el webhook es válido
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            print(f"✅ Webhook verificado")
            return challenge
        else:
            print(f"❌ Token de verificación inválido")
            return 'Invalid verification token', 403
    
    elif request.method == 'POST':
        # Meta envía los mensajes aquí
        data = request.get_json()
        
        # Procesa el mensaje
        procesar_mensaje_entrante(data)
        
        # Responde a Meta que recibimos el mensaje
        return '{"status":"ok"}', 200


@app.route('/status', methods=['GET'])
def status():
    """
    Verifica que el bot está funcionando
    """
    return {
        "status": "activo",
        "hora": datetime.now().isoformat(),
        "mensaje": "Bot de WhatsApp Business API funcionando"
    }


# ═══════════════════════════════════════════════════════════
# INICIAR EL SERVIDOR
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
