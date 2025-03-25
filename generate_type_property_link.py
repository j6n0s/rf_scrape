#!/usr/bin/env python3
import csv

# Global constants
PRODUCT_TYPE_BVIN = '82A6ECC8-0B97-4640-AB29-CE624FBAE2B4'
STORE_ID = 1
SORT_ORDER = 0
INPUT_FILE = 'D:\\2022\\IT_Rendszerfejlesztes\\II_fazis\\kiegeszitok_kulacsok\\kulacsok_property.txt'

def main():
    # Read the file and extract the property IDs
    property_ids = []
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            try:
                prop_id = int(row['Id'])
                property_ids.append(prop_id)
            except ValueError:
                continue

    # Determine the boundaries from the file
    if property_ids:
        LOWER_BOUNDRY = min(property_ids)
        UPPER_BOUNDRY = max(property_ids)
    else:
        print("No valid property IDs found in the file.")
        return

    # Print boundaries for confirmation (optional)
    print(f"Lower Boundary: {LOWER_BOUNDRY}")
    print(f"Upper Boundary: {UPPER_BOUNDRY}\n")

    # Generate and print SQL INSERT statements
    for prop_id in property_ids:
        sql = (
            "INSERT INTO [PerfektDatabase].[dbo].[hcc_ProductTypeXProductProperty] "
            "(ProductTypeBvin, PropertyId, SortOrder, StoreId) "
            f"VALUES ('{PRODUCT_TYPE_BVIN}', {prop_id}, {SORT_ORDER}, {STORE_ID});"
        )
        print(sql)

if __name__ == "__main__":
    main()
