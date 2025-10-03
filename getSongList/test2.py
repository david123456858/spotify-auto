import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
json1_path = os.path.join(base_dir, "../chartsJson/openSp1.json")
json2_path = os.path.join(base_dir, "../chartsJson/openSp2.json")
json3_path = os.path.join(base_dir, "../chartsJson/openSp3.json")

# Salidas
output_txt = os.path.join(base_dir, "../outputs/t.txt")
output_json = os.path.join(base_dir, "../outputs/t.json")

all_tracks = [
    {
        'uri': 'spotify:track:0zWYg2LyzO3VjH2qoV6igp',  # Canción promo 1
        'song': 'Given up on Me',
        'artist': 'Jinko'
    },
    {
        'uri': 'spotify:track:2O1YSaONzFP8V7pXAVdpWS',  # Canción promo 2
        'song': 'Wake Me Up',
        'artist': 'Jinko'
    }
]

def procesar_json(json_path, all_tracks):
    """Procesa un archivo JSON y extrae track, artista, URI e imagen"""
    if not os.path.exists(json_path):
        print(f"⚠️ No existe: {json_path}")
        return
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    items = data["data"]["playlistV2"]["content"]["items"]
    
    for item in items:
        item_data = item.get("itemV2", {}).get("data", {})
        
        # Skip items sin información válida
        if not item_data.get("name") or not item_data.get("artists"):
            continue
        
        track_name = item_data["name"]
        track_uri = item_data.get("uri", "")
        
        # Extraer artistas
        artists_data = item_data.get("artists", {}).get("items", [])
        if not artists_data:
            continue
        
        artists = [a["profile"]["name"] for a in artists_data if "profile" in a and "name" in a["profile"]]
        artists_str = ", ".join(artists)
        
        # Extraer artist URI (importante para obtener sus canciones)
        artist_uri = None
        if artists_data and "uri" in artists_data[0]:
            artist_uri = artists_data[0]["uri"]
        
        # Extraer imagen del álbum (usar la más grande: 640x640)
        album_data = item_data.get("albumOfTrack", {})
        cover_art = album_data.get("coverArt", {}).get("sources", [])
        
        # Buscar la imagen más grande (640x640)
        image_url = None
        for source in cover_art:
            if source.get("width") == 640:
                image_url = source.get("url")
                break
        
        # Si no hay de 640, usar la primera disponible
        if not image_url and cover_art:
            image_url = cover_art[0].get("url")
        
        # Solo guardar si tenemos datos completos
        if track_name and artists_str:
            track_info = {
                "song": track_name,
                "artist": artists_str,
                "uri": track_uri,
                "image_url": image_url
            }
            all_tracks.append(track_info)

# Procesar todos los JSON
print("Procesando archivos JSON...")
procesar_json(json1_path, all_tracks)
procesar_json(json2_path, all_tracks)
procesar_json(json3_path, all_tracks)

print(f"✅ Total de canciones procesadas: {len(all_tracks)}")

# Guardar en TXT (formato simple)
with open(output_txt, "w", encoding="utf-8") as f:
    for track in all_tracks:
        f.write(f"{track['song']} {track['artist']}\n")

print(f"✅ TXT guardado en: {output_txt}")

# Guardar en JSON (con toda la información)
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_tracks, f, indent=2, ensure_ascii=False)

print(f"✅ JSON guardado en: {output_json}")

# Mostrar preview
print("\n📝 Preview de las primeras 3 canciones:")
for i, track in enumerate(all_tracks[:3], 1):
    print(f"\n{i}. {track['song']}")
    print(f"   Artista: {track['artist']}")
    print(f"   URI: {track['uri']}")
    print(f"   Imagen: {track['image_url'][:60]}..." if track['image_url'] else "   Imagen: No disponible")