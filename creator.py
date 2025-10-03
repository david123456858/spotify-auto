"""
Creador masivo de playlists en Spotify - CORREGIDO
Distribuye las canciones circularmente entre usuarios
Una canción por playlist, rotando entre todos los usuarios
Incluye letras en descripciones usando Genius API
"""
import os
import requests
import json
import time
import base64
from datetime import datetime
import lyricsgenius

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, "./Credencials/config.json")
users_path = os.path.join(base_dir, "./Credencials/users.json")
songs_path = os.path.join(base_dir, "./outputs/Dragons_data.json")

# Cargar configuración
with open(config_path, 'r') as f:
    config = json.load(f)

CLIENT_ID = config['spotify_client_id']
CLIENT_SECRET = config['spotify_client_secret']
GENIUS_TOKEN = config['genius_token']

# Cargar usuarios autorizados
with open(users_path, 'r') as f:
    users = json.load(f)

# Cargar datos de canciones
with open(songs_path, 'r', encoding='utf-8') as f:
    all_songs = json.load(f)


class SpotifyPlaylistCreator:
    def __init__(self, client_id, client_secret, genius_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.spotify.com/v1"
        
        # Inicializar Genius API
        self.genius = lyricsgenius.Genius(genius_token)
        self.genius.verbose = False
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True
        self.genius.timeout = 15
        
    def get_access_token(self, refresh_token):
        """Obtiene un access token usando el refresh token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            raise Exception(f"Error obteniendo token: {response.text}")
    
    def get_lyrics(self, song_name, artist_name):
        """
        Obtiene las letras de una canción usando Genius API
        Retorna None si no se encuentran
        """
        try:
            print(f"      🔍 Buscando letra: {song_name} {artist_name}")
            song = self.genius.search_song(song_name, artist_name)
            
            if song and song.lyrics:
                # Limpiar la letra (Genius agrega encabezados que no queremos)
                lyrics = song.lyrics
                
                # Remover texto innecesario al inicio
                if lyrics.startswith("Lyrics"):
                    lyrics = lyrics[6:].strip()
                
                # Remover números de línea, URLs y otros metadatos
                lines = lyrics.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    # Filtrar líneas que son solo números o contienen "Embed"
                    if line and not line.isdigit() and "Embed" not in line and "You might also like" not in line:
                        clean_lines.append(line)
                
                clean_lyrics = '\n'.join(clean_lines)
                print(f"      ✅ Letra encontrada ({len(clean_lyrics)} caracteres)")
                return clean_lyrics
            else:
                print(f"      ⚠️ Letra no encontrada")
                return None
                
        except Exception as e:
            print(f"      ❌ Error buscando letra: {e}")
            return None
    
    def clean_text_for_spotify(self, text):
        """
        Limpia el texto para que sea aceptado por Spotify
        Remueve caracteres especiales problemáticos
        """
        import re
        
        # Remover emojis y caracteres no ASCII problemáticos
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Remover caracteres de control y otros problemáticos
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_playlist_title(self, song_name, artist_name, lyrics_preview):
        import re  # ← 1️⃣ AGREGAMOS ESTO AL INICIO
    
        # Limpiar nombres
        song_name = self.clean_text_for_spotify(song_name)
        artist_name = self.clean_text_for_spotify(artist_name)
    
        base_title = f"{song_name} {artist_name}"
    
        if len(base_title) >= 100:
            return base_title[:97] + "..."
    
        if not lyrics_preview:
            return base_title
    
        # ============================================
        # 2️⃣ AQUÍ VA EL BLOQUE DE LIMPIEZA (REEMPLAZA TODO LO VIEJO)
        # ============================================
    
        # Paso 1: Convertir saltos de línea en espacios
        lyrics_preview = lyrics_preview.replace('\n', ' ')
        lyrics_preview = lyrics_preview.replace('\r', ' ')
    
        # Paso 2: Limpiar espacios múltiples
        lyrics_preview = re.sub(r'\s+', ' ', lyrics_preview)
    
        # Paso 3: Limpiar caracteres especiales
        lyrics_preview = self.clean_text_for_spotify(lyrics_preview)
    
        # ============================================
        # FIN DEL BLOQUE DE LIMPIEZA
        # ============================================
    
        # Calcular espacio disponible
        available_space = 100 - len(base_title) - 3
    
        if available_space > 10:
            # 3️⃣ AQUÍ CAMBIA LA LÓGICA (YA NO USAMOS split)
        
            if len(lyrics_preview) <= available_space:
                return f"{base_title}  {lyrics_preview}"
            else:
                truncated = lyrics_preview[:available_space-3]
                last_space = truncated.rfind(' ')
                if last_space > 10:
                    truncated = truncated[:last_space]
                return f"{base_title}  {truncated}..."
    
        return base_title
    
    def create_playlist_description(self, lyrics):
        """
        Crea la descripción de la playlist SOLO con la letra
        Spotify limita a 300 caracteres
        """
        if not lyrics:
            # ⚠️ DESCRIPCIÓN CUANDO NO HAY LETRA
            return "Letra no disponible."

        import re
        
        # 🔧 ORDEN CORRECTO: Primero reemplazar saltos de línea, LUEGO limpiar con clean_text
        # Paso 1: Convertir saltos de línea en espacios (esto asegura separación)
        lyrics = lyrics.replace('\n', ' ')
        lyrics = lyrics.replace('\r', ' ')
        
        # Paso 2: Limpiar espacios múltiples
        lyrics = re.sub(r'\s+', ' ', lyrics)
        
        # Paso 3: Ahora sí, aplicar clean_text_for_spotify (que remueve caracteres especiales)
        lyrics = self.clean_text_for_spotify(lyrics)
        
        # Debug temporal (puedes eliminar después de verificar)
        print(f"\n   🔍 DEBUG LETRA LIMPIA:")
        print(f"      Original length: {len(lyrics)}")
        print(f"      Preview: {lyrics[:150]}...")
        
        # Limitar a 300 caracteres
        if len(lyrics) <= 300:
            return lyrics.strip()
        else:
            truncated = lyrics[:297]
            last_space = truncated.rfind(' ')
            if last_space > 280:  # evita cortar palabras
                truncated = truncated[:last_space]
            return truncated.strip() + "..."

    
    def get_artist_top_tracks(self, access_token, artist_id, country="US", limit=5):
        """Devuelve las canciones top del artista"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/artists/{artist_id}/top-tracks?market={country}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            tracks = response.json().get("tracks", [])
            return tracks[:limit]
        else:
            print(f"   ⚠️ Error obteniendo top tracks: {response.status_code}")
            return []
    
    def create_playlist(self, access_token, user_id, name, description=""):
        """Crea una playlist vacía"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Limpiar y validar datos
        name = self.clean_text_for_spotify(name)
        description = self.clean_text_for_spotify(description)
        
        # Truncar si es necesario
        name = name[:100] if len(name) > 100 else name
        description = description[:300] if len(description) > 300 else description
        
        data = {
            'name': name,
            'description': description,
            'public': True
        }
        
        # DEBUG: Imprimir lo que se está enviando
        print(f"   🔍 DEBUG - Enviando a Spotify:")
        print(f"      User ID: {user_id}")
        print(f"      Título ({len(name)} chars): {name[:80]}...")
        print(f"      Descripción ({len(description)} chars): {description[:80]}...")
        
        response = requests.post(
            f"{self.base_url}/users/{user_id}/playlists",
            headers=headers,
            json=data
        )
        
        # DEBUG: Mostrar respuesta completa si hay error
        if response.status_code != 201:
            print(f"   ❌ DEBUG - Respuesta completa:")
            print(f"      Status: {response.status_code}")
            print(f"      Body: {response.text}")
            print(f"      Headers enviados: {headers}")
            print(f"      Data enviado: {json.dumps(data, indent=2)}")
            raise Exception(f"Error creando playlist: {response.text}")
        
        return response.json()
    
    def add_tracks_to_playlist(self, access_token, playlist_id, track_uris):
        """Agrega canciones a una playlist"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Spotify permite hasta 100 tracks por petición
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            data = {'uris': batch}
            
            response = requests.post(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=headers,
                json=data
            )
            
            if response.status_code != 201:
                print(f"   ⚠️ Error agregando canciones: {response.text}")
                return False
            
            time.sleep(0.5)
        
        return True
    
    def upload_playlist_image(self, access_token, playlist_id, image_url):
        """Descarga una imagen y la sube como cover de la playlist"""
        try:
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code != 200:
                return False
            
            image_base64 = base64.b64encode(img_response.content).decode()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'image/jpeg'
            }
            
            response = requests.put(
                f"{self.base_url}/playlists/{playlist_id}/images",
                headers=headers,
                data=image_base64
            )
            
            return response.status_code == 202
            
        except Exception as e:
            print(f"   ⚠️ Error subiendo imagen: {e}")
            return False


def create_playlists_circular_distribution():
    """
    Crea playlists distribuyendo canciones circularmente entre usuarios
    
    Lógica:
    - Canción 1 → Usuario 1
    - Canción 2 → Usuario 2
    - ...
    - Canción 10 → Usuario 10
    - Canción 11 → Usuario 1 (reinicia)
    """
    creator = SpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET, GENIUS_TOKEN)
    
    # Canciones promocionales (fijas para todas las playlists)
    promo_tracks = [
        "spotify:track:4pem1s55isBqZ6HDbuFRG9",  # Promo 1 Open Hearts
        "spotify:track:0zWYg2LyzO3VjH2qoV6igp"   # Promo 2 Given up on Me
    ]
    
    print("\n" + "="*70)
    print("🎵 SPOTIFY PLAYLIST CREATOR - DISTRIBUCIÓN CIRCULAR")
    print("="*70)
    print(f"\n📊 Configuración:")
    print(f"   • Total de usuarios: {len(users)}")
    print(f"   • Total de canciones: {len(all_songs)}")
    print(f"   • Playlists a crear: {len(all_songs)} (una por canción)")
    print(f"   • Distribución: Circular entre {len(users)} usuarios")
    print(f"   • Canciones por playlist: ~5 (1 principal + 2 extras + 2 promos)")
    print("\n" + "="*70 + "\n")
    
    # Log
    log = open('creation_log.txt', 'w', encoding='utf-8')
    log.write(f"Inicio: {datetime.now()}\n")
    log.write(f"Distribución Circular: {len(all_songs)} canciones entre {len(users)} usuarios\n\n")
    
    stats = {
        'total_playlists': 0,
        'total_errors': 0,
        'total_songs_added': 0,
        'playlists_por_usuario': {user['user_id']: 0 for user in users}
    }
    
    # Obtener tokens de todos los usuarios al inicio
    user_tokens = {}
    print("🔐 Obteniendo tokens de acceso...\n")
    for user in users:
        try:
            token = creator.get_access_token(user['refresh_token'])
            user_tokens[user['user_id']] = token
            print(f"   ✅ Token obtenido: {user['user_id']}")
        except Exception as e:
            print(f"   ❌ Error obteniendo token para {user['user_id']}: {e}")
            log.write(f"❌ Error token: {user['user_id']} - {e}\n")
    
    print("\n" + "="*70 + "\n")
    
    # ===== DISTRIBUCIÓN CIRCULAR =====
    # 🔧 PRUEBA: Cambiar all_songs por all_songs[:10] para probar solo 10 canciones
    # 🔧 PRUEBA: Cambiar all_songs por all_songs[:1] para probar solo 1 canción
    test_songs = all_songs[:1]  # ← CAMBIAR AQUÍ: [:1] = 1 canción, [:10] = 10 canciones, o quitar para todas
    
    # print(f"⚠️  MODO PRUEBA: Procesando {len(test_songs)} de {len(all_songs)} canciones\n")
    
    # Iterar sobre las canciones (de prueba o todas)
    for song_idx, song in enumerate(all_songs):
        # Calcular a qué usuario le toca (distribución circular)
        user_idx = song_idx % len(users)  # Módulo para hacer circular
        current_user = users[user_idx]
        
        # Verificar si tenemos token para este usuario
        if current_user['user_id'] not in user_tokens:
            print(f"⚠️ [{song_idx + 1}/{len(test_songs)}] Sin token para {current_user['user_id']}, saltando...")
            stats['total_errors'] += 1
            continue
        
        access_token = user_tokens[current_user['user_id']]
        
        try:
            print(f"\n📝 [{song_idx + 1}/{len(test_songs)}] 👤 Usuario: {current_user['user_id']}")
            print(f"   🎵 Canción: {song['song']} - {song['artist']}")
            
            # ===== OBTENER LETRA =====
            # 🔧 MODO DEBUG: Comentar esta línea para probar sin letras
            lyrics = creator.get_lyrics(song['song'], song['artist'])
            # 🔧 MODO DEBUG: Descomentar esto para probar SIN buscar letras
            # lyrics = None
            # print(f"      ⚠️ MODO DEBUG: Saltando búsqueda de letra")
            
            # ===== CREAR TÍTULO Y DESCRIPCIÓN =====
            # 🎨 AQUÍ SE GENERA EL NOMBRE DE LA PLAYLIST
            # Puedes cambiarlo manualmente aquí si quieres un formato diferente:
            playlist_name = creator.create_playlist_title(
                song['song'], 
                song['artist'], 
                lyrics
            )
            
            # 🎨 O usar un formato personalizado:
            # playlist_name = f"{song['song']} - {song['artist']}"  # Simple
            # playlist_name = f"🎵 {song['song']}"  # Solo canción con emoji
            # playlist_name = f"{song['artist']}: {song['song']}"  # Artista primero
            
            playlist_description = creator.create_playlist_description(
                lyrics
            )
            
            print(f"   📋 Título: {playlist_name[:60]}...")
            print(f"   📄 Descripción: {len(playlist_description)} caracteres")
            
            # Crear playlist
            playlist = creator.create_playlist(
                access_token,
                current_user['user_id'],
                playlist_name,
                playlist_description
            )
            
            playlist_id = playlist['id']
            playlist_url = playlist['external_urls']['spotify']
            print(f"   ✅ Playlist creada: {playlist_id}")
            
            # ===== Construcción de canciones =====
            track_uris = []
            
            # 1) Canción principal
            track_uris.append(song['uri'])
            
            # 2) Obtener 2 canciones adicionales del artista
            extra_tracks = []
            if song.get('artist_id'):
                top_tracks = creator.get_artist_top_tracks(
                    access_token, 
                    song['artist_id'], 
                    limit=5
                )
                # Evitar repetir la canción principal
                extra_tracks = [
                    t['uri'] for t in top_tracks 
                    if t['uri'] != song['uri']
                ][:2]
            
            # 3) Orden final: Principal → Promo1 → Extra1 → Promo2 → Extra2
            ordered_tracks = [song['uri']]
            
            if len(promo_tracks) > 0:
                ordered_tracks.append(promo_tracks[0])
            
            if len(extra_tracks) > 0:
                ordered_tracks.append(extra_tracks[0])
            
            if len(promo_tracks) > 1:
                ordered_tracks.append(promo_tracks[1])
            
            if len(extra_tracks) > 1:
                ordered_tracks.append(extra_tracks[1])
            
            # Agregar canciones
            if creator.add_tracks_to_playlist(access_token, playlist_id, ordered_tracks):
                print(f"   ✅ {len(ordered_tracks)} canciones agregadas")
                stats['total_songs_added'] += len(ordered_tracks)
            else:
                print(f"   ⚠️ Error agregando canciones")
            
            # Subir imagen
            if song.get('image_url'):
                if creator.upload_playlist_image(access_token, playlist_id, song['image_url']):
                    print(f"   ✅ Imagen subida")
                else:
                    print(f"   ⚠️ Sin imagen")
            
            # Actualizar estadísticas
            stats['total_playlists'] += 1
            stats['playlists_por_usuario'][current_user['user_id']] += 1
            
            # Log
            log.write(f"✅ [{song_idx + 1}] {current_user['user_id']} | {playlist_name} | {playlist_url}\n")
            
            # Delay entre peticiones (importante para evitar rate limits)
            time.sleep(2)
            
        except Exception as e:
            error_msg = f"❌ Error en canción {song_idx + 1}: {str(e)}"
            print(f"   {error_msg}")
            log.write(f"{error_msg}\n")
            stats['total_errors'] += 1
            time.sleep(3)
    
    # ===== RESUMEN FINAL =====
    print("\n" + "="*70)
    print("🎉 PROCESO COMPLETADO")
    print("="*70)
    print(f"\n📊 Estadísticas Globales:")
    print(f"   ✅ Playlists creadas: {stats['total_playlists']}/{len(test_songs)}")
    print(f"   🎵 Canciones agregadas: {stats['total_songs_added']}")
    print(f"   ❌ Errores: {stats['total_errors']}")
    
    if stats['total_playlists'] > 0:
        success_rate = (stats['total_playlists'] / len(test_songs) * 100)
        print(f"   📈 Tasa de éxito: {success_rate:.1f}%")
    
    print(f"\n📊 Distribución por Usuario:")
    for user_id, count in stats['playlists_por_usuario'].items():
        print(f"   • {user_id}: {count} playlists")
    
    print(f"\n📄 Log detallado: creation_log.txt")
    print("="*70 + "\n")
    
    # Guardar log final
    log.write(f"\n{'='*60}\n")
    log.write(f"Fin: {datetime.now()}\n")
    log.write(f"Playlists creadas: {stats['total_playlists']}\n")
    log.write(f"Canciones agregadas: {stats['total_songs_added']}\n")
    log.write(f"Errores: {stats['total_errors']}\n\n")
    log.write("Distribución por usuario:\n")
    for user_id, count in stats['playlists_por_usuario'].items():
        log.write(f"  {user_id}: {count} playlists\n")
    log.close()


if __name__ == "__main__":
    # Verificar archivos necesarios
    required = ['./Credencials/config.json', './Credencials/users.json', './outputs/Dragons_data.json']
    missing = [f for f in required if not os.path.exists(os.path.join(base_dir, f))]
    
    if missing:
        print(f"❌ Faltan archivos: {', '.join(missing)}")
        exit(1)
    
    print("\n" + "="*70)
    print("⚠️  INFORMACIÓN IMPORTANTE")
    print("="*70)
    print(f"\n📋 Se crearán:")
    print(f"   • {len(all_songs)} playlists (una por cada canción del JSON)")
    print(f"   • Distribuidas circularmente entre {len(users)} usuarios")
    print(f"   • Cada playlist tendrá ~5 canciones (1 principal + extras + promos)")
    print(f"\n⏱️  Tiempo estimado: ~{len(all_songs) * 2 / 60:.0f} minutos")
    print(f"⚠️  No interrumpir el proceso hasta completar")
    print("="*70 + "\n")
    
    confirm = input("¿Continuar? (si/no): ").lower()
    
    if confirm in ['si', 's', 'yes', 'y']:
        create_playlists_circular_distribution()
    else:
        print("\n❌ Proceso cancelado.")