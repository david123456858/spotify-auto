import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "..", "chartsJson", "chartsYt.json")
output_file = os.path.join(base_dir, "..", "outputs", "salidaChartYt.txt")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

track_views = data["contents"]["sectionListRenderer"]["contents"][0] \
    ["musicAnalyticsSectionRenderer"]["content"]["trackTypes"][0]["trackViews"]

rows = []
for track in track_views:
    title = track.get("name", "")
    artists = [a["name"] for a in track.get("artists", [])]
    artist_str = ", ".join(artists)
    combined = f"{title} {artist_str}"
    rows.append(combined)

# Guardar en un TXT, cada fila en una línea
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(rows))
