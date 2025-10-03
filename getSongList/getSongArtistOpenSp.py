import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

json1_path = os.path.join(base_dir, "../chartsJson/openSp1.json")   # primera mitad
json2_path = os.path.join(base_dir, "../chartsJson/openSp2.json")   # segunda mitad
json3_path = os.path.join(base_dir, "../chartsJson/openSp3.json")   # por si hay un tecero

output_file = os.path.join(base_dir, "../outputs/Dragons.txt")


def procesar_json(json_path, mode, output_file):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["data"]["playlistV2"]["content"]["items"]

    with open(output_file, mode, encoding="utf-8") as out:
        for item in items:
            # Check if the item has valid track data
            item_data = item.get("itemV2", {}).get("data", {})
            
            # Skip items that don't have track information (e.g., NotFound items)
            if not item_data.get("name") or not item_data.get("artists"):
                continue
                
            track = item_data["name"]
            
            # Check if artists data exists and has items
            artists_data = item_data.get("artists", {}).get("items", [])
            if not artists_data:
                continue
                
            artists = [a["profile"]["name"] for a in artists_data if "profile" in a and "name" in a["profile"]]
            artists_str = ", ".join(artists)
            
            # Only write if we have both track name and artists
            if track and artists_str:
                out.write(f"{track} {artists_str}\n")


procesar_json(json1_path, "w", output_file)
procesar_json(json2_path, "a", output_file)
# procesar_json(json3_path, "a", output_file)
