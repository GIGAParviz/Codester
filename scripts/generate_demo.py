import csv
import json
import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
CSV_PATH = DATA / "mesc_catalog_synthetic.csv"
DB_PATH = DATA / "mesc_catalog.db"

random.seed(20261015)

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

groups = {
    "pipe": "74",
    "valve": "77",
    "fitting": "76",
    "flange": "76",
    "pump": "27",
    "gasket": "85",
    "cable": "68",
    "instrument": "60",
    "fastener": "50",
}

brands = ["Dutch", "Apex", "Flowline", "Negin", "ParsPipe", "Atlas", "Mekran"]
brand_fa = {"Dutch": "داچ", "Apex": "ایپکس", "Flowline": "فلولاین", "Negin": "نگین", "ParsPipe": "پارس پایپ", "Atlas": "اطلس", "Mekran": "مکران"}
sizes = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 10, 12]
indicators = [1, 1, 1, 1, 9]

pipe_materials = [("PVC", "پلاستیک", "plastic"), ("HDPE", "پلاستیک", "plastic"), ("PP-R", "پلاستیک", "plastic"), ("UPVC", "پلاستیک", "plastic"), ("Carbon Steel", "فولاد کربنی", "carbon steel"), ("Stainless Steel", "فولاد ضدزنگ", "stainless steel"), ("GRE", "کامپوزیت", "composite")]
pipe_connections = [("Socket", "سوکتی"), ("Butt Fusion", "جوش لب به لب"), ("Flanged", "فلنجی"), ("Threaded", "رزوه ای")]
pipe_standards = ["ASTM D1785", "ISO 4427", "DIN 8077", "ASME B36.10", "ASTM A312", "API 5L"]

def code_for(kind, index, local=False):
    group = groups[kind]
    subgroup = str(10 + (index % 80)).zfill(2)
    subsub = str(10 + ((index * 7) % 80)).zfill(2)
    buying = str(100 + (index % 899)).zfill(3)
    indicator = "9" if local else "1"
    return f"{group}.{subgroup}.{subsub}.{buying}.{indicator}"

def row(kind, index, **fields):
    fields["record_id"] = f"SYN-{index:05d}"
    fields["item_type"] = kind
    fields["mesc_code"] = code_for(kind, index, fields.get("indicator") == 9)
    fields["indicator"] = fields.get("indicator", 1)
    fields["status"] = fields.get("status", "ACTIVE" if index % 37 else "INACTIVE")
    fields["uom"] = fields.get("uom", "EA")
    fields["catalogue_revision"] = "SYN-2026.10"
    fields["source"] = "synthetic_fixture_v1"
    fields["is_synthetic"] = True
    fields["technical_attributes_json"] = json.dumps({k: fields[k] for k in ["size_inch", "nominal_size_mm", "material", "material_family", "pressure_class", "connection", "standard", "manufacturer", "actuation", "service"] if k in fields}, ensure_ascii=False, separators=(",", ":"))
    fields["search_text"] = " ".join(str(fields.get(k, "")) for k in ["item_type", "description_en", "description_fa", "manufacturer", "material", "material_family", "connection", "standard", "service"])
    return fields

records = []
index = 1

for i in range(1200):
    material, material_fa, family = pipe_materials[i % len(pipe_materials)]
    connection, connection_fa = pipe_connections[i % len(pipe_connections)]
    size = sizes[i % len(sizes)]
    brand = brands[(i * 3) % len(brands)]
    pressure = [10, 16, 40, 80, 150][i % 5]
    standard = pipe_standards[i % len(pipe_standards)]
    mm = int(size * 25.4)
    description_en = f"Pipe, {material}, {size:g} inch, {connection}, Class {pressure}, {standard}, Manufacturer {brand}"
    description_fa = f"لوله {size:g} اینچ {material_fa} اتصال {connection_fa} کلاس {pressure} استاندارد {standard} برند {brand_fa[brand]}"
    records.append(row("pipe", index, description_en=description_en, description_fa=description_fa, manufacturer=brand, manufacturer_fa=brand_fa[brand], material=material, material_family=family, size_inch=size, nominal_size_mm=mm, pressure_class=pressure, connection=connection, connection_fa=connection_fa, standard=standard, service=["water", "air", "hydrocarbon", "chemical"][i % 4], indicator=indicators[i % len(indicators)]))
    index += 1

valve_types = [("Gate Valve", "شیر دروازه ای"), ("Ball Valve", "شیر توپی"), ("Globe Valve", "شیر کروی"), ("Check Valve", "شیر یکطرفه"), ("Butterfly Valve", "شیر پروانه ای")]
valve_materials = [("Carbon Steel", "فولاد کربنی", "carbon steel"), ("Stainless Steel", "فولاد ضدزنگ", "stainless steel"), ("Ductile Iron", "چدن نشکن", "ductile iron")]
for i in range(500):
    valve, valve_fa = valve_types[i % len(valve_types)]
    material, material_fa, family = valve_materials[i % len(valve_materials)]
    size = sizes[(i + 2) % len(sizes)]
    brand = brands[(i + 1) % len(brands)]
    pressure = [150, 300, 600, 900][i % 4]
    connection = ["RF Flanged", "Butt Weld", "Threaded"][i % 3]
    standard = ["API 600", "API 608", "API 594", "ASME B16.34"][i % 4]
    description_en = f"{valve}, {material}, {size:g} inch, {connection}, Class {pressure}, {standard}, Manufacturer {brand}"
    description_fa = f"{valve_fa} {size:g} اینچ {material_fa} اتصال {connection} کلاس {pressure} استاندارد {standard} برند {brand_fa[brand]}"
    records.append(row("valve", index, description_en=description_en, description_fa=description_fa, manufacturer=brand, manufacturer_fa=brand_fa[brand], material=material, material_family=family, size_inch=size, nominal_size_mm=int(size * 25.4), pressure_class=pressure, connection=connection, standard=standard, service=["water", "steam", "hydrocarbon"][i % 3], actuation=["manual", "pneumatic", "electric"][i % 3], indicator=indicators[i % len(indicators)]))
    index += 1

templates = {
    "fitting": ("Elbow", "زانو", ["Carbon Steel", "Stainless Steel", "HDPE"], ["Butt Weld", "Socket", "Threaded"], ["ASME B16.9", "ASTM D3261", "ASME B16.11"]),
    "flange": ("Weld Neck Flange", "فلنج گردن دار", ["Carbon Steel", "Stainless Steel", "Forged Steel"], ["RF", "RTJ", "FF"], ["ASME B16.5", "ASME B16.47"]),
    "pump": ("Centrifugal Pump", "پمپ سانتریفیوژ", ["Cast Iron", "Stainless Steel", "Duplex Steel"], ["Flanged", "Threaded"], ["API 610", "ISO 5199"]),
    "gasket": ("Spiral Wound Gasket", "گسکت اسپیرال وند", ["Graphite/SS316", "PTFE/SS304", "Graphite/Carbon Steel"], ["RF", "RTJ"], ["ASME B16.20", "API 601"]),
    "cable": ("Control Cable", "کابل کنترل", ["Copper/PVC", "Copper/XLPE", "Aluminium/XLPE"], ["Armoured", "Unarmoured"], ["IEC 60502", "BS 5308"]),
    "instrument": ("Pressure Transmitter", "ترانسمیتر فشار", ["316SS", "Hastelloy", "Aluminium"], ["Threaded", "Flanged"], ["IEC 61508", "ASME B40.100"]),
    "fastener": ("Hex Bolt", "پیچ شش گوش", ["Carbon Steel", "Stainless Steel", "Alloy Steel"], ["Plain", "Hot Dip Galvanized"], ["ASTM A193", "ISO 898-1"]),
}

for kind, template in templates.items():
    noun, noun_fa, materials, connections, standards = template
    for i in range(200):
        material = materials[i % len(materials)]
        connection = connections[i % len(connections)]
        standard = standards[i % len(standards)]
        brand = brands[(i + len(kind)) % len(brands)]
        size = sizes[(i + 3) % len(sizes)]
        pressure = [150, 300, 600][i % 3]
        description_en = f"{noun}, {material}, {size:g} inch, {connection}, Class {pressure}, {standard}, Manufacturer {brand}"
        description_fa = f"{noun_fa} {size:g} اینچ {material} اتصال {connection} کلاس {pressure} استاندارد {standard} برند {brand_fa[brand]}"
        records.append(row(kind, index, description_en=description_en, description_fa=description_fa, manufacturer=brand, manufacturer_fa=brand_fa[brand], material=material, material_family="metal" if "Steel" in material or "Aluminium" in material or "Iron" in material else "composite", size_inch=size, nominal_size_mm=int(size * 25.4), pressure_class=pressure, connection=connection, standard=standard, service=["water", "air", "hydrocarbon"][i % 3], indicator=indicators[i % len(indicators)]))
        index += 1

columns = ["record_id", "mesc_code", "item_type", "description_en", "description_fa", "manufacturer", "manufacturer_fa", "material", "material_family", "size_inch", "nominal_size_mm", "pressure_class", "connection", "connection_fa", "standard", "service", "actuation", "uom", "status", "indicator", "catalogue_revision", "source", "is_synthetic", "technical_attributes_json", "search_text"]

with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    writer.writerows({column: record.get(column, "") for column in columns} for record in records)

connection = sqlite3.connect(DB_PATH)
connection.executescript("DROP TABLE IF EXISTS catalog; DROP TABLE IF EXISTS catalog_fts; CREATE TABLE catalog (id INTEGER PRIMARY KEY, record_id TEXT UNIQUE, mesc_code TEXT, item_type TEXT, description_en TEXT, description_fa TEXT, manufacturer TEXT, material TEXT, material_family TEXT, size_inch REAL, nominal_size_mm INTEGER, pressure_class INTEGER, connection TEXT, standard TEXT, service TEXT, actuation TEXT, uom TEXT, status TEXT, indicator INTEGER, catalogue_revision TEXT, source TEXT, is_synthetic INTEGER, technical_attributes_json TEXT, search_text TEXT);")
connection.executemany("INSERT INTO catalog (record_id, mesc_code, item_type, description_en, description_fa, manufacturer, material, material_family, size_inch, nominal_size_mm, pressure_class, connection, standard, service, actuation, uom, status, indicator, catalogue_revision, source, is_synthetic, technical_attributes_json, search_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [tuple(1 if record.get(column) is True else record.get(column, "") for column in ["record_id", "mesc_code", "item_type", "description_en", "description_fa", "manufacturer", "material", "material_family", "size_inch", "nominal_size_mm", "pressure_class", "connection", "standard", "service", "actuation", "uom", "status", "indicator", "catalogue_revision", "source", "is_synthetic", "technical_attributes_json", "search_text"]) for record in records])
connection.execute("CREATE INDEX idx_catalog_type ON catalog(item_type)")
connection.execute("CREATE INDEX idx_catalog_size ON catalog(size_inch)")
connection.execute("CREATE INDEX idx_catalog_material_family ON catalog(material_family)")
connection.execute("CREATE INDEX idx_catalog_manufacturer ON catalog(manufacturer)")
connection.execute("CREATE VIRTUAL TABLE catalog_fts USING fts5(mesc_code, description_en, description_fa, manufacturer, material, material_family, connection, standard, service, search_text, content='catalog', content_rowid='id')")
connection.execute("INSERT INTO catalog_fts(catalog_fts) VALUES('rebuild')")
connection.commit()
connection.close()
print(json.dumps({"rows": len(records), "csv": str(CSV_PATH), "db": str(DB_PATH)}, ensure_ascii=False))
