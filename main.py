"""
Sistema de OAuth para Spotify con FastAPI
Permite obtener los refresh tokens de múltiples usuarios

Instalación adicional necesaria:
pip install fastapi uvicorn python-multipart
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
import base64
import json
import os
from datetime import datetime
import uvicorn

app = FastAPI()

base_dir = os.path.dirname(os.path.abspath(__file__))
config = os.path.join(base_dir,"./Credencials/config.json")

# Cargar configuración
with open(config, 'r') as f:
    config = json.load(f)

CLIENT_ID = config['spotify_client_id']
CLIENT_SECRET = config['spotify_client_secret']
REDIRECT_URI = "https://da8033c1059d.ngrok-free.app/callback"

# Scopes necesarios para crear playlists y subir imágenes
SCOPES = "playlist-modify-public playlist-modify-private ugc-image-upload"

# Almacenamiento temporal de usuarios autorizados
authorized_users = []

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal con instrucciones"""
    
    users_html = ""
    for i, user in enumerate(authorized_users, 1):
        users_html += f"""
        <div style="background: #1ed760; padding: 15px; margin: 10px 0; border-radius: 8px;">
            <strong>Usuario {i}: {user['user_id']}</strong><br>
            <small>Autorizado: {user['timestamp']}</small>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify OAuth - PlaylistCreator</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #191414;
                color: white;
            }}
            .container {{
                background: #282828;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #1ed760;
                margin-bottom: 10px;
            }}
            .btn {{
                background: #1ed760;
                color: black;
                padding: 15px 30px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px 0;
                transition: all 0.3s;
            }}
            .btn:hover {{
                background: #1fdf64;
                transform: scale(1.05);
            }}
            .status {{
                background: #535353;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .warning {{
                background: #ff6b6b;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .success {{
                background: #51cf66;
                color: black;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .export-btn {{
                background: #2196F3;
                color: white;
            }}
            .export-btn:hover {{
                background: #1976D2;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Spotify Playlist Creator</h1>
            <p>Sistema de autorización para gestionar playlists de múltiples usuarios</p>
            
            <div class="status">
                <h3>📊 Estado: {len(authorized_users)}/10 usuarios autorizados</h3>
                {users_html if users_html else "<p>No hay usuarios autorizados aún</p>"}
            </div>
            
            {"<div class='success'><strong>✅ ¡Ya tienes 10 usuarios!</strong><br>Puedes exportar los tokens y empezar a crear playlists.</div>" if len(authorized_users) >= 10 else ""}
            
            {"<div class='warning'><strong>⚠️ Atención:</strong> Necesitas autorizar 10 usuarios de Spotify diferentes. Cada uno debe iniciar sesión con su propia cuenta.</div>" if len(authorized_users) < 10 else ""}
            
            <div style="margin: 30px 0;">
                <a href="/login" class="btn">
                    🔐 Autorizar Usuario {len(authorized_users) + 1}
                </a>
                
                {f'<a href="/export" class="btn export-btn">📥 Exportar Tokens (JSON)</a>' if authorized_users else ''}
                
                {f'<a href="/clear" class="btn" style="background: #ff6b6b;">🗑️ Limpiar Todo</a>' if authorized_users else ''}
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #535353;">
                <h3>📝 Instrucciones:</h3>
                <ol style="line-height: 2;">
                    <li>Haz clic en "Autorizar Usuario"</li>
                    <li>Inicia sesión con una cuenta de Spotify</li>
                    <li>Acepta los permisos</li>
                    <li>Serás redirigido de vuelta aquí</li>
                    <li>Repite para cada uno de los 10 usuarios</li>
                    <li>Exporta los tokens cuando termines</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/login")
async def login():
    """Redirige al usuario a la página de autorización de Spotify"""
    
    auth_url = "https://accounts.spotify.com/authorize"
    
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'show_dialog': 'true'  # Forzar login cada vez
    }
    
    # Construir URL con parámetros
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    full_url = f"{auth_url}?{query_string}"
    
    return RedirectResponse(url=full_url)

@app.get("/callback")
async def callback(code: str = None, error: str = None): # type: ignore
    """Callback que recibe el código de autorización de Spotify"""
    print(code)
    if error:
        return HTMLResponse(f"""
            <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ Error de Autorización</h1>
                <p>{error}</p>
                <a href="/" style="color: #1ed760;">Volver al inicio</a>
            </body>
            </html>
        """)
    
    if not code:
        return HTMLResponse("""
            <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ No se recibió código</h1>
                <a href="/" style="color: #1ed760;">Volver al inicio</a>
            </body>
            </html>
        """)
    
    # Intercambiar código por tokens
    try:
        auth_header = base64.b64encode(
            f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            return HTMLResponse(f"""
                <html>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: red;">❌ Error obteniendo tokens</h1>
                    <p>{response.text}</p>
                    <a href="/" style="color: #1ed760;">Volver al inicio</a>
                </body>
                </html>
            """)
        
        print("Status code:", response.status_code)
        print("Response body:", response.text)
        tokens = response.json()
        
        print(tokens)
        # Obtener información del usuario
        user_response = requests.get(
            'https://api.spotify.com/v1/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        
        
        user_data = user_response.json()
        
        # Guardar usuario
        user_info = {
            'user_id': user_data['id'],
            'display_name': user_data.get('display_name', user_data['id']),
            'email': user_data.get('email', 'N/A'),
            'refresh_token': tokens['refresh_token'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(user_data)
        # Verificar si el usuario ya existe
        existing = next((u for u in authorized_users if u['user_id'] == user_info['user_id']), None)
        
        if existing:
            # Actualizar token
            authorized_users.remove(existing)
            authorized_users.append(user_info)
            message = f"✅ Usuario actualizado: {user_info['display_name']}"
        else:
            # Agregar nuevo usuario
            authorized_users.append(user_info)
            message = f"✅ Usuario autorizado: {user_info['display_name']}"
        
        return HTMLResponse(f"""
            <html>
            <head>
                <meta http-equiv="refresh" content="3;url=/">
            </head>
            <body style="font-family: Arial; padding: 50px; text-align: center; background: #191414; color: white;">
                <h1 style="color: #1ed760;">✅ ¡Autorización Exitosa!</h1>
                <p style="font-size: 20px;">{message}</p>
                <p style="color: #b3b3b3;">Usuario: <strong>{user_info['user_id']}</strong></p>
                <p style="color: #b3b3b3;">Total de usuarios: <strong>{len(authorized_users)}/10</strong></p>
                <p style="margin-top: 30px;">Redirigiendo en 3 segundos...</p>
                <a href="/" style="color: #1ed760; font-size: 18px;">Volver ahora</a>
            </body>
            </html>
        """)
        
    except Exception as e:
        print(e)
        return HTMLResponse(f"""
            <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ Error {e}</h1>
                <p>{str(e)}</p>
                <a href="/" style="color: #1ed760;">Volver al inicio</a>
            </body>
            </html>
        """)

@app.get("/export")
async def export():
    """Exporta los tokens en formato JSON"""
    
    if not authorized_users:
        return HTMLResponse("""
            <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ No hay usuarios autorizados</h1>
                <a href="/" style="color: #1ed760;">Volver al inicio</a>
            </body>
            </html>
        """)
    
    # Crear archivo users.json
    users_export = [
        {
            'user_id': user['user_id'],
            'refresh_token': user['refresh_token']
        }
        for user in authorized_users
    ]
    
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users_export, f, indent=2, ensure_ascii=False)
    
    # Crear archivo users_backup.json con info completa
    with open('users_backup.json', 'w', encoding='utf-8') as f:
        json.dump(authorized_users, f, indent=2, ensure_ascii=False)
    
    users_list = "\n".join([
        f"<li><strong>{u['display_name']}</strong> ({u['user_id']}) - {u['timestamp']}</li>"
        for u in authorized_users
    ])
    
    return HTMLResponse(f"""
        <html>
        <body style="font-family: Arial; padding: 50px; background: #191414; color: white;">
            <div style="max-width: 800px; margin: 0 auto; background: #282828; padding: 30px; border-radius: 12px;">
                <h1 style="color: #1ed760;">✅ Tokens Exportados</h1>
                
                <div style="background: #535353; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>📁 Archivos creados:</h3>
                    <ul style="line-height: 2;">
                        <li><code>users.json</code> - Tokens para usar en el script</li>
                        <li><code>users_backup.json</code> - Backup con información completa</li>
                    </ul>
                </div>
                
                <div style="background: #1ed760; color: black; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>👥 Usuarios exportados ({len(authorized_users)}):</h3>
                    <ol style="line-height: 2;">
                        {users_list}
                    </ol>
                </div>
                
                <div style="background: #ff6b6b; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>⚠️ IMPORTANTE:</h3>
                    <p>Guarda estos archivos en un lugar seguro. Los refresh tokens NO expiran a menos que:</p>
                    <ul>
                        <li>El usuario revoque el acceso</li>
                        <li>El usuario cambie su contraseña</li>
                        <li>Pasen 6 meses sin uso</li>
                    </ul>
                </div>
                
                <a href="/" style="background: #1ed760; color: black; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; margin-top: 20px; font-weight: bold;">
                    🏠 Volver al Inicio
                </a>
            </div>
        </body>
        </html>
    """)

@app.get("/clear")
async def clear():
    """Limpia todos los usuarios autorizados"""
    authorized_users.clear()
    return RedirectResponse(url="/")

@app.get("/status")
async def status():
    """Endpoint JSON con el estado actual"""
    return {
        "total_users": len(authorized_users),
        "users": [
            {
                "user_id": u['user_id'],
                "display_name": u['display_name'],
                "timestamp": u['timestamp']
            }
            for u in authorized_users
        ]
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 SPOTIFY OAUTH SERVER")
    print("="*60)
    print("\n📍 Servidor iniciado en: http://localhost:8000")
    print("\n📝 Instrucciones:")
    print("   1. Abre tu navegador en: http://localhost:8000")
    print("   2. Autoriza 10 usuarios diferentes")
    print("   3. Exporta los tokens")
    print("   4. Usa users.json en tu script principal")
    print("\n⚠️  Para detener el servidor: Ctrl+C")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8888)
    
    
    
    
    promo_tracks = [
                        "spotify:track:0zWYg2LyzO3VjH2qoV6igp",  # promocional 1
                        "spotify:track:2O1YSaONzFP8V7pXAVdpWS"   # promocional 2
                    ]