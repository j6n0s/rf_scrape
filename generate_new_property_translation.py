#!/usr/bin/env python3
import os

filename = r"D:\2022\IT_Rendszerfejlesztes\II_fazis\kiegeszitok_kulacsok\kulacsok_property.txt"

# Globális változó, mely tartalmazza azt az értéket, amit eltávolítunk
global_tag = "_kiegeszitok_kulacsok"

# Ellenőrizzük, hogy a fájl létezik-e
if not os.path.exists(filename):
    print(f"A(z) {filename} fájl nem található!")
    exit(1)

# Fájl beolvasása, sortörésenként
with open(filename, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

# Az első sor a fejléc, azt kihagyjuk
header = lines[0]
data_lines = lines[1:]

# Kiírjuk a globális SQL változó deklarációját
print(f"DECLARE @global_tag NVARCHAR(10) = '{global_tag}';\n")

# Minden sor feldolgozása
for line in data_lines:
    # Üres sorok kihagyása
    if not line.strip():
        continue
    # Feltételezzük, hogy tab karakterrel vannak elválasztva a mezők
    parts = line.split('\t')
    # Ha nem tab-okkal vannak elválasztva, akkor szóközökkel próbálkozunk
    if len(parts) < 2:
        parts = line.split()
    if len(parts) < 2:
        continue

    property_id = parts[0].strip()
    property_name = parts[1].strip()

    # SQL INSERT statement generálása
    sql = f"""INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductPropertyTranslations]
           ([ProductPropertyId], [Culture], [DisplayName], [DefaultLocalizableValue])
VALUES 
({property_id}, 'hu-HU', REPLACE('{property_name}', @global_tag, ''), 'NULL');
"""
    print(sql)