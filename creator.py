"""
Creador masivo de playlists en Spotify - OPTIMIZADO
Crea 25 playlists por cada usuario autorizado
Usa los URIs directamente para evitar búsquedas
"""
import os
import requests
import json
import time
import base64
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
config = os.path.join(base_dir,"./Credencials/config.json")
users = os.path.join(base_dir, "./Credencials/users.json")
songs = os.path.join(base_dir, "./outputs/Dragons_data.json")

# Cargar configuración
with open(config, 'r') as f:
    config = json.load(f)

CLIENT_ID = config['spotify_client_id']
CLIENT_SECRET = config['spotify_client_secret']

# Cargar usuarios autorizados
with open(users, 'r') as f:
    users = json.load(f)

# Cargar datos de canciones (generado por extract_spotify_data.py)
with open(songs, 'r', encoding='utf-8') as f:
    all_songs = json.load(f)


class SpotifyPlaylistCreator:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.spotify.com/v1"
        
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
        
    def get_artist_top_tracks(self, access_token, artist_id, country="US", limit=5):
        """Devuelve las canciones top del artista (para elegir 2 adicionales)"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/artists/{artist_id}/top-tracks?market={country}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            tracks = response.json().get("tracks", [])
            return tracks[:limit]  # devuelve solo las primeras n
        else:
            print(f"⚠️ Error obteniendo top tracks de {artist_id}: {response.text}")
            return []
    def create_playlist(self, access_token, user_id, name, description=""):
        """Crea una playlist vacía"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'name': name,
            'description': description,
            'public': True
        }
        
        response = requests.post(
            f"{self.base_url}/users/{user_id}/playlists",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Error creando playlist: {response.text}")
    
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
            # Descargar la imagen
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code != 200:
                return False
            
            # Convertir a base64 (Spotify requiere JPEG en base64)
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
            return False


def create_playlists_for_all_users():
    """Crea 25 playlists para cada usuario"""
    creator = SpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET)
    
    # Calcular distribución
    total_songs = len(all_songs)
    songs_per_playlist = 5  # Canciones por playlist
    
    print("\n" + "="*70)
    print("🎵 SPOTIFY PLAYLIST CREATOR")
    print("="*70)
    print(f"\n📊 Configuración:")
    print(f"   • Usuarios: {len(users)}")
    print(f"   • Playlists por usuario: 25")
    print(f"   • Total playlists: {len(users) * 25}")
    print(f"   • Canciones totales: {total_songs}")
    print(f"   • Canciones por playlist: ~{songs_per_playlist}")
    print("\n" + "="*70 + "\n")
    
    # Log
    log = open('creation_log.txt', 'w', encoding='utf-8')
    log.write(f"Inicio: {datetime.now()}\n\n")
    
    stats = {
        'total_playlists': 0,
        'total_errors': 0,
        'total_songs_added': 0
    }
    
    for user_idx, user in enumerate(users, 1):
        print(f"\n{'='*70}")
        print(f"👤 Usuario {user_idx}/{len(users)}: {user['user_id']}") # type: ignore
        print(f"{'='*70}")
        
        try:
            # Obtener token
            access_token = creator.get_access_token(user['refresh_token']) # type: ignore
            print("✅ Token obtenido")
            
                        # Crear 25 playlists
            for playlist_num in range(1, 2):
                try:
                    # === Selección circular de canción base según usuario y playlist ===
                    # Fórmula mejorada: hace que cada usuario empiece en distinta canción
                    song_idx = ((user_idx - 1) * 25 + (playlist_num - 1)) % len(all_songs)
                    first_song = all_songs[song_idx]

                    playlist_name = f"{first_song['song']} - {first_song['artist']}"
                    playlist_description = f"Playlist automática #{playlist_num} • Artista: {first_song['artist']}"

                    print(f"\n📝 [{playlist_num}/25] {playlist_name[:50]}...")

                    # Crear playlist
                    playlist = creator.create_playlist(
                        access_token,
                        user['user_id'],  # type: ignore
                        playlist_name,
                        playlist_description
                    )

                    playlist_id = playlist['id']
                    playlist_url = playlist['external_urls']['spotify']
                    print(f"   ✅ Creada: {playlist_id}")

                    # ===== Construcción de canciones =====
                    track_uris = []

                    # 1) Canción principal (del JSON)
                    track_uris.append(first_song['uri'])

                    # 2) Buscar ID del artista (ya viene en el JSON extraído)
                    artist_id = first_song.get("artist_id")
                    if not artist_id:
                        artist_search = requests.get(
                            f"https://api.spotify.com/v1/search",
                            headers={"Authorization": f"Bearer {access_token}"},
                            params={"q": first_song['artist'], "type": "artist", "limit": 1}
                        ).json()
                        if artist_search.get("artists", {}).get("items"):
                            artist_id = artist_search["artists"]["items"][0]["id"]

                    # 3) Extra tracks del artista (dos adicionales)
                    extra_tracks_uris = []
                    if artist_id:
                        top_tracks = creator.get_artist_top_tracks(access_token, artist_id, limit=5)
                        # evitar repetir la misma canción principal
                        extra_tracks_uris = [
                            t['uri'] for t in top_tracks if t['uri'] != first_song['uri']
                        ][:2]

                    # 4) Canciones promocionales (FIJAS o desde JSON aparte)
                    promo_tracks = [
                        "spotify:track:2O1YSaONzFP8V7pXAVdpWS",  # Promo 1
                        "spotify:track:0zWYg2LyzO3VjH2qoV6igp"   # Promo 2
                    ]

                    # 5) Orden final: main + promo + extra + promo + extra
                    ordered_tracks = [
                        first_song['uri'],
                        promo_tracks[0],
                        extra_tracks_uris[0] if len(extra_tracks_uris) > 0 else None,
                        promo_tracks[1],
                        extra_tracks_uris[1] if len(extra_tracks_uris) > 1 else None
                    ]

                    # Quitar None
                    ordered_tracks = [t for t in ordered_tracks if t]

                    # Agregar canciones a playlist
                    if ordered_tracks:
                        if creator.add_tracks_to_playlist(access_token, playlist_id, ordered_tracks):
                            print(f"   ✅ {len(ordered_tracks)} canciones agregadas")
                            stats['total_songs_added'] += len(ordered_tracks)
                        else:
                            print(f"   ❌ Error agregando canciones")
                            stats['total_errors'] += 1

                    # Imagen de portada
                    if first_song.get('image_url'):
                        if creator.upload_playlist_image(access_token, playlist_id, first_song['image_url']):
                            print(f"   ✅ Imagen subida")
                        else:
                            print(f"   ⚠️ Sin imagen")

                    # Log
                    log.write(f"✅ {user['user_id']} | PL#{playlist_num} | {playlist_name} | {playlist_url}\n")  # type: ignore
                    stats['total_playlists'] += 1

                    # Delay
                    time.sleep(2)

                except Exception as e:
                    error = f"❌ Error en playlist {playlist_num}: {str(e)}"
                    print(f"   {error}")
                    log.write(f"{error}\n")
                    stats['total_errors'] += 1
                    time.sleep(5)


            
            print(f"\n✅ Usuario completado: {user['user_id']}") # type: ignore
            
            # Delay entre usuarios
            if user_idx < len(users):
                print(f"\n⏸️ Esperando 15 segundos...")
                time.sleep(15)
        
        except Exception as e:
            error = f"❌ Error fatal con {user['user_id']}: {str(e)}" # type: ignore
            print(f"\n{error}")
            log.write(f"{error}\n")
            stats['total_errors'] += 1
    
    # Resumen
    print("\n" + "="*70)
    print("🎉 PROCESO COMPLETADO")
    print("="*70)
    print(f"\n📊 Estadísticas:")
    print(f"   ✅ Playlists creadas: {stats['total_playlists']}")
    print(f"   🎵 Canciones agregadas: {stats['total_songs_added']}")
    print(f"   ❌ Errores: {stats['total_errors']}")
    
    if stats['total_playlists'] > 0:
        success_rate = (stats['total_playlists'] / (stats['total_playlists'] + stats['total_errors']) * 100)
        print(f"   📈 Tasa de éxito: {success_rate:.1f}%")
    
    print(f"\n📄 Log: creation_log.txt")
    print("="*70 + "\n")
    
    log.write(f"\nFin: {datetime.now()}\n")
    log.write(f"Playlists: {stats['total_playlists']}\n")
    log.write(f"Canciones: {stats['total_songs_added']}\n")
    log.write(f"Errores: {stats['total_errors']}\n")
    log.close()


if __name__ == "__main__":
    import os
    
    # Verificar archivos
    required = ['./Credencials/config.json', './Credencials/users.json', './outputs/Dragons_data.json']
    missing = [f for f in required if not os.path.exists(f)]
    
    if missing:
        print(f"❌ Faltan archivos: {', '.join(missing)}")
        exit(1)
    
    print("\n⚠️ IMPORTANTE:")
    print(f"   • Se crearán {len(users) * 1} playlists")
    print(f"   • Proceso estimado: {len(users) * 1} minutos")
    print("   • No interrumpir hasta completar")
    
    confirm = input("\n¿Continuar? (si/no): ").lower()
    
    if confirm in ['si', 's', 'yes', 'y']:
        create_playlists_for_all_users()
    else:
        print("Cancelado.")