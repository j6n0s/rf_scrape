## Scrape script
- Fel kell promptolni
- Lefuttatása után a Main sheettel rendelkező excelt fel kell tölteni Hotcakesbe
- SQL táblákban a StoreId-t át kell írni, hogy megjelenjenek a termékek
## SQL update queryvel hozzá kell adni a ProductTypebvin-jét a Productokhoz
## Futattni kell az images_saver.py scriptet
- generál egy import_images foldert amit át kell másolni a vm gépre manuálisan
- ez s truktúra:
      - bvin
        - image.jpg
        small
          - image.jpg
        medium
          - image.jpg
## Extrák:
## ProdutPropertyName-ek beállítása
- a scripteket fel kell promtolni, majd a kód által elvárt struktúrában bizonyos lekérdezéseket ki kell exportálni az SQL Server Managerből txt formátumban.
- a következő Fájlokat kell futtatni:
  - generate_new_property_inserts.py
  - generate_new_property_translation.py
  - generate_type_property_link.py
## Propertyk hozzárandelése a Productokhoz
- ismét promptolás.
- a következő fájlok futtatása:
  - generate_type_properties.py
  - generate_type_properties_link.py

#### A scriptekkel generált sql inserteket/updateket természetesen futtatni, kell az adatbázisban.
