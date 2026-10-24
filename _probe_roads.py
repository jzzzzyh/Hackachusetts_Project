import requests
h = {"User-Agent": "Mozilla/5.0"}
base = "https://testgisportal.boston.gov/arcgis/rest/services/Infrastructure/OpenData/MapServer"

# --- Sidewalk layer (0): SCI + MATERIAL ---
q0 = f"{base}/0/query"
r = requests.get(q0, params={"where": "1=1", "outFields": "SCI,MATERIAL,DISTRICT", "resultRecordCount": 10, "returnGeometry": "false", "f": "json"}, headers=h, timeout=60)
print("SIDEWALK sample:")
for a in r.json().get("features", [])[:10]:
    print(" ", a["attributes"])

# --- MassDOT Road Inventory layer (14): road material + condition ---
q14 = f"{base}/14/query"
r = requests.get(q14, params={"where": "1=1", "outFields": "St_Name,Surface_Tp,Struct_Cnd,City", "resultRecordCount": 10, "returnGeometry": "false", "f": "json"}, headers=h, timeout=60)
print("\nROAD sample:")
for a in r.json().get("features", [])[:10]:
    print(" ", a["attributes"])

# road surface-type domain / distinct
r = requests.get(q14, params={"where": "1=1", "outFields": "Surface_Tp", "returnDistinctValues": "true", "f": "json"}, headers=h, timeout=60)
print("\nroad Surface_Tp distinct:", sorted({str(a['attributes']['Surface_Tp']) for a in r.json().get('features', [])}))
r = requests.get(q14, params={"where": "1=1", "outFields": "Struct_Cnd", "returnDistinctValues": "true", "f": "json"}, headers=h, timeout=60)
print("road Struct_Cnd distinct:", sorted({str(a['attributes']['Struct_Cnd']) for a in r.json().get('features', [])}))
