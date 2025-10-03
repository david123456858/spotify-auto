import json
import requests

# Cargar credenciales
with open('config.json', 'r') as f:
    config = json.load(f)

print("🔍 Verificando credenciales...\n")

# Test 1: Spotify
print("1️⃣ Probando Spotify API...")
try:
    auth_url = 'https://accounts.spotify.com/api/token'
    import base64
    
    auth_header = base64.b64encode(
        f"{config['spotify_client_id']}:{config['spotify_client_secret']}".encode()
    ).decode()
    
    response = requests.post(
        auth_url,
        headers={'Authorization': f'Basic {auth_header}'},
        data={'grant_type': 'client_credentials'}
    )
    
    if response.status_code == 200:
        print("   ✅ Spotify: Credenciales válidas")
    else:
        print(f"   ❌ Spotify: Error {response.status_code}")
        print(f"   Respuesta: {response.text}")
except Exception as e:
    print(f"   ❌ Spotify: Error - {e}")

# Test 2: Genius
print("\n2️⃣ Probando Genius API...")
try:
    response = requests.get(
        'https://api.genius.com/search?q=test',
        headers={'Authorization': f'Bearer {config["genius_token"]}'}
    )
    
    if response.status_code == 200:
        print("   ✅ Genius: Token válido")
    else:
        print(f"   ❌ Genius: Error {response.status_code}")
except Exception as e:
    print(f"   ❌ Genius: Error - {e}")

# Test 3: Unsplash (opcional)
if 'unsplash_key' in config and config['unsplash_key']:
    print("\n3️⃣ Probando Unsplash API...")
    try:
        response = requests.get(
            'https://api.unsplash.com/search/photos?query=music&per_page=1',
            headers={'Authorization': f'Client-ID {config["unsplash_key"]}'}
        )
        
        if response.status_code == 200:
            print("   ✅ Unsplash: Access Key válido")
        else:
            print(f"   ❌ Unsplash: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Unsplash: Error - {e}")

print("\n✨ Verificación completada!")