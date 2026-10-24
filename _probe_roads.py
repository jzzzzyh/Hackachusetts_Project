import requests
h = {"User-Agent": "Mozilla/5.0"}
q = "https://testgisportal.boston.gov/arcgis/rest/services/Infrastructure/OpenData/MapServer/0/query"
r = requests.get(q, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, headers=h, timeout=60)
print("total sidewalk segments:", r.json())
# sample values
r = requests.get(q, params={"where": "SCI>0", "outFields": "SCI,MATERIAL,DISTRICT", "resultRecordCount": 15, "f": "json"}, headers=h, timeout=60)
for a in r.json().get("features", [])[:15]:
    print(a["attributes"])
# distinct materials
r = requests.get(q, params={"where": "1=1", "outFields": "MATERIAL", "returnDistinctValues": "true", "f": "json"}, headers=h, timeout=60)
print("materials:", sorted({a["attributes"]["MATERIAL"] for a in r.json().get("features", []) if a["attributes"]["MATERIAL"]}))
