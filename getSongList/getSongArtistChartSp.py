import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

json_path = os.path.join(base_dir, "..", "chartsJson", "chartsSp.json")
output_file = os.path.join(base_dir, "..", "outputs", "salidaChartSp.txt")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

entries = data["chartEntryViewResponses"][0]["entries"]

with open(output_file, "w", encoding="utf-8") as out:
    for entry in entries:
        track = entry["trackMetadata"]["trackName"]
        artists = [artist["name"] for artist in entry["trackMetadata"]["artists"]]
        artists_str = ", ".join(artists)
        out.write(f"{track} {artists_str}\n")

