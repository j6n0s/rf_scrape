import os
import openpyxl

# 1) Projekt elérési út: 
PROJECT_PATH = r"D:\2022\IT_Rendszerfejlesztes\II_fazis\kiegeszitok_kulacsok"
EXPORT_PATH = PROJECT_PATH

# 2) Globális változó, amit manuálisan lehet módosítani:
GLOBAL_CATEGORY = "_kiegeszitok_kulacsok"

def generate_sql_insert_from_excel(excel_file_name, output_sql_file):
    """
    Beolvassa az excel_file_name fájlt a PROJECT_PATH alatt,
    kigyűjti a B oszlopból az egyedi PropertyName értékeket,
    kiegészíti őket a GLOBAL_CATEGORY értékkel,
    majd generál egy SQL insert fájlt.
    """

    # Excel fájl elérési útja
    excel_file_path = os.path.join(PROJECT_PATH, excel_file_name)

    # Excel betöltése
    wb = openpyxl.load_workbook(excel_file_path)
    ws = wb.active  # Ha több munkalap van, megadhatod pl. wb["Munka1"]

    # Egyedi tulajdonságnevek kinyerése a B oszlopból (2. oszlop),
    # kihagyva az első sort (a fejlécek miatt)
    property_names = set()
    for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        cell = row[0]
        if cell.value and isinstance(cell.value, str):
            prop = cell.value.strip()
            if prop:
                property_names.add(prop)

    # Rendezés (opcionális)
    sorted_property_names = sorted(property_names)

    # Először kiírjuk az egyedi értékeket a konzolra
    print("Egyedi property nevek (B oszlopból) - GLOBAL_CATEGORY hozzáfűzéssel:")
    for prop_name in sorted_property_names:
        # 3) Minden property névhez hozzáfűzzük a GLOBAL_CATEGORY-t
        prop_name_with_category = f"{prop_name}{GLOBAL_CATEGORY}"
        print(prop_name_with_category)

    # Ezután generáljuk az SQL INSERT parancsokat
    with open(output_sql_file, "w", encoding="utf-8") as f:
        for prop_name in sorted_property_names:
            # Itt is hozzáfűzzük a GLOBAL_CATEGORY-t
            prop_name_with_category = f"{prop_name}{GLOBAL_CATEGORY}"

            # Ha idézőjelet (') tartalmaz, duplázzuk
            safe_prop_name = prop_name_with_category.replace("'", "''")

            insert_statement = f"""
INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductProperty]
(
    [PropertyName],
    [DisplayOnSite],
    [DisplayToDropShipper],
    [TypeCode],
    [DefaultValue],
    [CultureCode],
    [LastUpdated],
    [StoreId],
    [DisplayOnSearch],
    [IsLocalizable]
)
VALUES
(
    '{safe_prop_name}',
    1,            -- DisplayOnSite
    0,            -- DisplayToDropShipper
    1,       -- TypeCode (példaként TEXT)
    '',           -- DefaultValue
    'hu-HU',      -- CultureCode
    GETDATE(),    -- LastUpdated
    1,            -- StoreId (példa)
    1,            -- DisplayOnSearch
    0             -- IsLocalizable
);
"""
            f.write(insert_statement)

if __name__ == "__main__":
    # Az Excel-fájl neve a projektmappában
    excel_file_name = "bringaland_hotcakes_import_tisztitott_property.xlsx"
    # A generált SQL-fájl neve (a script futtatásának helyén jön létre)
    output_sql_file = os.path.join(EXPORT_PATH, "new_properties_o_u_alk_vazak.sql")

    generate_sql_insert_from_excel(excel_file_name, output_sql_file)
    print(f"\nSQL parancsok elkészültek a(z) '{output_sql_file}' fájlban.")
