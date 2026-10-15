import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "mesc_catalog.db"

def normalize(text):
    text = str(text).translate(str.maketrans("يىكۀة", "ییکهه")).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).lower()
    return re.sub(r"\s+", " ", text.replace("‌", " ").strip())

def parse_query(query):
    text = normalize(query)
    tokens = []
    item_type = None
    item_subtype = None
    item_patterns = [("pipe", r"\b(?:pipe|tube|لوله)\b"), ("valve", r"(?:gate|ball|globe|check|butterfly)\s*valve|شیر\s*(?:دروازه|توپی|کروی|یکطرفه|پروانه)")]
    for value, pattern in item_patterns:
        if re.search(pattern, text):
            item_type = value
            tokens.append(value)
            break
    for value, pattern in [("Gate Valve", r"gate\s*valve|شیر\s*دروازه"), ("Ball Valve", r"ball\s*valve|شیر\s*توپی"), ("Globe Valve", r"globe\s*valve|شیر\s*کروی"), ("Check Valve", r"check\s*valve|شیر\s*یکطرفه"), ("Butterfly Valve", r"butterfly\s*valve|شیر\s*پروانه")]:
        if re.search(pattern, text):
            item_subtype = value
            break
    if re.search(r"plastic|پلاستیک|پلاستیکی|pvc|upvc|hdpe|pp-r", text):
        tokens.append("plastic")
    if re.search(r"steel|فولاد|استیل", text):
        tokens.append("steel")
    if re.search(r"\b(?:dutch|داچ|داتچ)\b", text):
        tokens.append("Dutch")
    number_words = {"نیم": 0.5, "یک": 1, "دو": 2, "سه": 3, "چهار": 4, "شش": 6, "هشت": 8, "ده": 10, "دوازده": 12}
    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:inch|in|اینچ|اینچی|\")", text)
    if size_match:
        size = float(size_match.group(1))
    else:
        size = next((value for word, value in number_words.items() if re.search(rf"(?:^|\s){re.escape(word)}(?:\s|$)", text) and ("اینچ" in text or "لوله" in text)), None)
    material_family = "plastic" if "plastic" in tokens else None
    material = next((value for value in ["PVC", "UPVC", "HDPE", "PP-R", "Carbon Steel", "Stainless Steel"] if normalize(value) in text), None)
    class_match = re.search(r"(?:class|کلاس|رده)\s*(\d+)", text)
    pressure_class = int(class_match.group(1)) if class_match else None
    connection = None
    for value, pattern in [("Threaded", r"thread|رزوه"), ("Flanged", r"flange|فلنج"), ("Butt Weld", r"butt\s*weld|جوش"), ("Socket", r"socket|سوکت")]:
        if re.search(pattern, text):
            connection = value
            break
    standard_match = re.search(r"\b(?:api|asme|astm|iso|din)\s*[a-z]?\s*\d+(?:\.\d+)?\b", text, re.IGNORECASE)
    standard = standard_match.group(0).upper().replace(" ", "") if standard_match else None
    return {"normalized": text, "tokens": tokens, "size_inch": size, "material": material, "material_family": material_family, "manufacturer": "Dutch" if "Dutch" in tokens else None, "item_type": item_type, "item_subtype": item_subtype, "pressure_class": pressure_class, "connection": connection, "standard": standard}

def search_parsed(query, parsed, limit=10):
    parsed = {"normalized": normalize(query), "tokens": [], "size_inch": None, "material": None, "material_family": None, "manufacturer": None, "item_type": None, "item_subtype": None, "pressure_class": None, "connection": None, "standard": None, **parsed}
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    where = ["status = 'ACTIVE'"]
    params = []
    if parsed["item_type"]:
        where.append("item_type = ?")
        params.append(parsed["item_type"])
    if parsed["item_subtype"]:
        where.append("description_en LIKE ?")
        params.append(f"%{parsed['item_subtype']}%")
    if parsed["manufacturer"]:
        where.append("manufacturer = ?")
        params.append(parsed["manufacturer"])
    if parsed["material_family"]:
        where.append("material_family = ?")
        params.append(parsed["material_family"])
    if parsed["material"]:
        where.append("material = ?")
        params.append(parsed["material"])
    if parsed["size_inch"] is not None:
        where.append("ABS(size_inch - ?) <= 0.001")
        params.append(parsed["size_inch"])
    if parsed["pressure_class"] is not None:
        where.append("pressure_class = ?")
        params.append(parsed["pressure_class"])
    if parsed["connection"]:
        where.append("connection LIKE ?")
        params.append(f"%{parsed['connection']}%")
    if parsed["standard"]:
        where.append("REPLACE(UPPER(standard), ' ', '') LIKE ?")
        params.append(f"%{parsed['standard'].replace(' ', '').upper()}%")
    rows = connection.execute(f"SELECT * FROM catalog WHERE {' AND '.join(where)}", params).fetchall()
    if not rows:
        rows = connection.execute("SELECT * FROM catalog WHERE status = 'ACTIVE'").fetchall()
    scored = []
    for row in rows:
        score = 0.0
        matched = []
        if parsed["item_type"] and row["item_type"] == parsed["item_type"]:
            score += 0.30
            matched.append("item_type")
        if parsed["item_subtype"] and parsed["item_subtype"].lower() in row["description_en"].lower():
            score += 0.10
            matched.append("item_subtype")
        if parsed["manufacturer"] and row["manufacturer"] == parsed["manufacturer"]:
            score += 0.25
            matched.append("manufacturer")
        if parsed["material_family"] and row["material_family"] == parsed["material_family"]:
            score += 0.20
            matched.append("material_family")
        if parsed["material"] and row["material"].lower() == parsed["material"].lower():
            score += 0.08
            matched.append("material")
        if parsed["size_inch"] is not None and abs(row["size_inch"] - parsed["size_inch"]) < 0.001:
            score += 0.15
            matched.append("size_inch")
        if parsed["pressure_class"] is not None and row["pressure_class"] == parsed["pressure_class"]:
            score += 0.06
            matched.append("pressure_class")
        if parsed["connection"] and parsed["connection"].lower() in row["connection"].lower():
            score += 0.04
            matched.append("connection")
        if parsed["standard"] and parsed["standard"].replace(" ", "").lower() in row["standard"].replace(" ", "").lower():
            score += 0.04
            matched.append("standard")
        text = normalize(f"{row['description_en']} {row['description_fa']} {row['standard']} {row['connection']}")
        overlap = sum(1 for token in parsed["tokens"] if normalize(token) in text)
        score += min(overlap / max(len(parsed["tokens"]), 1), 1.0) * 0.10
        requested = []
        differences = []
        if parsed["size_inch"] is not None:
            requested.append(f"size_inch={parsed['size_inch']:g}")
            if abs(row["size_inch"] - parsed["size_inch"]) > 0.001:
                differences.append(f"size_inch={row['size_inch']:g}")
        if parsed["material_family"]:
            requested.append(f"material_family={parsed['material_family']}")
            if row["material_family"] != parsed["material_family"]:
                differences.append(f"material_family={row['material_family']}")
        if parsed["material"]:
            requested.append(f"material={parsed['material']}")
            if row["material"].lower() != parsed["material"].lower():
                differences.append(f"material={row['material']}")
        if parsed["manufacturer"]:
            requested.append(f"manufacturer={parsed['manufacturer']}")
            if row["manufacturer"] != parsed["manufacturer"]:
                differences.append(f"manufacturer={row['manufacturer']}")
        if parsed["pressure_class"] is not None:
            requested.append(f"pressure_class={parsed['pressure_class']}")
            if row["pressure_class"] != parsed["pressure_class"]:
                differences.append(f"pressure_class={row['pressure_class']}")
        if parsed["connection"]:
            requested.append(f"connection={parsed['connection']}")
            if row["connection"] != parsed["connection"]:
                differences.append(f"connection={row['connection']}")
        if parsed["standard"]:
            requested.append(f"standard={parsed['standard']}")
            if parsed["standard"].replace(" ", "").lower() not in row["standard"].replace(" ", "").lower():
                differences.append(f"standard={row['standard']}")
        scored.append({"mesc_code": row["mesc_code"], "description_en": row["description_en"], "description_fa": row["description_fa"], "manufacturer": row["manufacturer"], "material": row["material"], "size_inch": row["size_inch"], "connection": row["connection"], "standard": row["standard"], "score": round(score, 4), "matched_fields": matched, "differences": differences, "synthetic": bool(row["is_synthetic"])})
    connection.close()
    scored.sort(key=lambda item: (-item["score"], item["mesc_code"]))
    return {"query": query, "parsed": parsed, "count": len(scored), "results": scored[:limit]}

def search(query, limit=10):
    return search_parsed(query, parse_query(query), limit)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if not DB_PATH.exists():
        print("Database not found. Run: python scripts/generate_demo.py", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(search(" ".join(args.query), args.limit), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
