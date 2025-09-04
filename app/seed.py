import json
import os
import sys

# Adjust the path to allow imports from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Item, ItemCategory

# Provided data
data = [
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/01/01",
    "description": "Maintenance and protection of Traffic",
    "unit": "L S",
    "rate": 124275.34
  },
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/02/04",
    "description": "Provision, maintence and removal of sign boards",
    "unit": "L S",
    "rate": 180881.15
  },
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/02/05",
    "description": "Provision and maintenance of Survey Equipment",
    "unit": "Month",
    "rate": 25116.27
  },
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/02/07",
    "description": "Progress photographs",
    "unit": "Month",
    "rate": 665.58
  },
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/03/01",
    "description": "Provide and removal of site laboratory & equipment",
    "unit": "L/S",
    "rate": 243958.74
  },
  {
    "item_category": "General & Site Facilities",
    "item_code": "01/03/02",
    "description": "Maintain site laboratory.",
    "unit": "Month",
    "rate": 6027.9
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/02/02",
    "description": "Roadway Excavation in suitable Soil",
    "unit": "Cum",
    "rate": 118.32
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/05/01",
    "description": "Excavation and backfill for structure",
    "unit": "Cum",
    "rate": 409.39
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/05/03",
    "description": "Sand backfill for structure",
    "unit": "Cum",
    "rate": 1333.92
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/06/02",
    "description": "Embankment fill from borrow pit in contractor's arranged land",
    "unit": "Cum",
    "rate": 178.88
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/07/02",
    "description": "Preparation of sub grade 450 mm depth",
    "unit": "Sqm",
    "rate": 32.6
  },
  {
    "item_category": "Earth Work",
    "item_code": "02/08/01",
    "description": "Improved Sub-grade",
    "unit": "Cum",
    "rate": 1111.6
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/02/01(a)",
    "description": "Sub-Base",
    "unit": "Cum",
    "rate": 4569.9
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/03/01(a)",
    "description": "Aggregate Base Type-I",
    "unit": "Cum",
    "rate": 8866.92
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/03/02(a)",
    "description": "Aggregate Base Type-II",
    "unit": "Cum",
    "rate": 4994.37
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/06/01a",
    "description": "Bituminous Prime Coat (Plant Placed)",
    "unit": "Sqm",
    "rate": 118.91
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/07/01a",
    "description": "Bituminous Tack Coat (Plant work)",
    "unit": "Sqm",
    "rate": 53.3
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/10/01(b)",
    "description": "Dense Bituminous Surfacing-Base Course (Plant Method) (Bitumen Grade 60/70)",
    "unit": "Cum",
    "rate": 24792.02
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/10/02(b)",
    "description": "Dense Bituminous Surfacing (Plant Method) (Bitumen Grade 60/70)",
    "unit": "Cum",
    "rate": 26100.83
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/13/01(a)",
    "description": "Brick on End Edging (1st class)",
    "unit": "Lin. M",
    "rate": 214.11
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/13/02(a)",
    "description": "Single Layer Brick Flat Soling i/c 75mm thick compacted sand cushion (1st class)",
    "unit": "Sqm",
    "rate": 601.94
  },
  {
    "item_category": "Pavement Work",
    "item_code": "03/13/03(a)",
    "description": "Herring Bond Brick Pavement i/c 12mm sand cushion (1st class)",
    "unit": "Sqm",
    "rate": 843.65
  },
  {
    "item_category": "Foundation Work",
    "item_code": "04/01/01c",
    "description": "Bored cast in place piles(dia 750mm)",
    "unit": "Lin. M",
    "rate": 10244.06
  },
  {
    "item_category": "Foundation Work",
    "item_code": "04/01/04",
    "description": "High Yield Deformed  Steel Reinforcing bars (Grade 60 )",
    "unit": "M Ton",
    "rate": 97903.25
  },
  {
    "item_category": "Foundation Work",
    "item_code": "04/04/01b",
    "description": "Load Test on cast in place piles (For 100 Ton)",
    "unit": "Number",
    "rate": 290557.67
  },
  {
    "item_category": "Foundation Work",
    "item_code": "04/04/01c",
    "description": "Load Test on cast in place piles (For 200 Ton)",
    "unit": "Number",
    "rate": 290557.67
  },
  {
    "item_category": "Foundation Work",
    "item_code": "04/07/05",
    "description": "Sand Filling",
    "unit": "Cum",
    "rate": 1334.3
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/01",
    "description": "Single Layer Brick Flat soling",
    "unit": "Sqm",
    "rate": 532.84
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02a",
    "description": "Concrete class as detailed on drawings (Class 10)(Concrete Mixer)",
    "unit": "Cum",
    "rate": 11539.14
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02b",
    "description": "Concrete class - 20 (Foundation) (Concrete Mixer)",
    "unit": "Cum",
    "rate": 18405.24
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02c",
    "description": "Concrete class - 20 (Vertical member col. Pier, abutment/wing wall, culvert etc.) (Concrete Mixer)",
    "unit": "Cum",
    "rate": 20843.58
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02f",
    "description": "Concrete class - 20 (rail & post.)(Concrete Mixer)",
    "unit": "Cum",
    "rate": 0
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02g",
    "description": "Concrete class-25 (Foundation)(Concrete Mixer)",
    "unit": "Cum",
    "rate": 17989.3
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02h",
    "description": "Concrete class - 25 (Vertical member of column, pier, abutment /wing wall, culvert etc.)(Concrete Mixer)",
    "unit": "Cum",
    "rate": 20968.63
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02i",
    "description": "Concrete class - 25 (Girder, cross girder, diaphram, beam etc.)(Concrete Mixer)",
    "unit": "Cum",
    "rate": 23541.45
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02k",
    "description": "Concrete class - 35 (Deck slab, side walk, wheel guard, curb etc. (Concrete Mixer)",
    "unit": "Cum",
    "rate": 0
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02l",
    "description": "Concrete class - 35 (Deck slab (Concrete Mixer)",
    "unit": "Cum",
    "rate": 30266.84
  },
  {
    "item_category": "Structures",
    "item_code": "05/01/02m",
    "description": "Concrete class - 40 (Pre-stressed Girder.) (Concrete Mixer)",
    "unit": "Cum",
    "rate": 30748.19
  },
  {
    "item_category": "Structures",
    "item__code": "05/02/02",
    "description": "High yield reinforcement bars ( Grade 60 )",
    "unit": "M Ton",
    "rate": 96459.06
  },
  {
    "item_category": "Structures",
    "item_code": "05/03/01",
    "description": "Prestressing Wire or Strand",
    "unit": "M Ton",
    "rate": 279403.64
  },
  {
    "item_category": "Structures",
    "item_code": "05/05/01",
    "description": "New and Extended Brick work",
    "unit": "Cum",
    "rate": 9337.91
  },
  {
    "item_category": "Structures",
    "item_code": "05/05/02",
    ".description": "Brick drainage layer",
    "unit": "Cum",
    "rate": 5839.53
  },
  {
    "item_category": "Structures",
    "item_code": "Pwd: 16.6",
    "description": "Painting to door and window frames and shutters.",
    "unit": "Sqm",
    "rate": 175.81
  },
  {
    "item_category": "Structures",
    "item_code": "05/08/01",
    "description": "Expansion joint complete as detailed on the drawing in the location described in the BoQ.",
    "unit": "Lin. m",
    "rate": 10160.35
  },
  {
    "item_category": "Structures",
    "item_code": "05/13/01a",
    "description": "Neoprene Rubber Bearing or Elastomeric Bearing supplying & fitting fixing, etc.",
    "unit": "Nos",
    "rate": 19883.71
  },
  {
    "item_category": "Structures",
    "item_code": "05/16/01",
    "description": "Dismantling of deck slab, thickness 175mm.",
    "unit": "Sqm",
    "rate": 6757
  },
  {
    "item_category": "Incidental",
    "item_code": "06/01/02",
    "description": "Concrete slope protection",
    "unit": "Sqm",
    "rate": 1879.85
  },
  {
    "item_category": "Incidental",
    "item_code": "6/2/1",
    "description": "Reinforced concrete culvert pipe class A",
    "unit": "Lin. m",
    "rate": 5990
  },
  {
    "item_category": "Incidental",
    "item_code": "06/05/01",
    "description": "Road Marking- Thermoplastic Material (indicate if screed or spray application)",
    "unit": "Sqm",
    "rate": 1019.54
  },
  {
    "item_category": "Incidental",
    "item_code": "06/12/01",
    "description": "Geotextile Filter Fabric (as detailed on the drawing)",
    "unit": "Sqm",
    "rate": 215.21
  },
  {
    "item_category": "Incidental",
    "item_code": "06/15/01",
    "description": "Concrete Guide Post (1.6m long, 200mm dia)",
    "unit": "Nos",
    "rate": 2515
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item No-01 BWDB 40-650-30",
    "description": "Supply and placing sand as filter (F.M 1 to 1.5)",
    "unit": "Cum",
    "rate": 967.53
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item No-02 BWDB 40-610-30",
    "description": "Supply and placing Jhama Khoa as filter (Size 20mm to 5mm)",
    "unit": "Cum",
    "rate": 3630.22
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item No-03",
    "description": "Providing 50 mm U-Pvc Pipe for weep hole",
    "unit": "Lin. M",
    "rate": 22.6
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item-04 (No-8.7, PWD Sch.-2018)",
    "description": "Providing bearing joint fixed or free with 250x375x10 mm M.S. (Grade - A36) shoe plate...",
    "unit": "Nos",
    "rate": 100
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item-05 (No-26.36.01 PWD Sch.-2018)",
    "description": "12.5 mm dia GI Pipe with wall thickness 2.65 mm...",
    "unit": "Metre",
    "rate": 101
  },
  {
    "item_category": "Incidental",
    "item_code": "Special Item- 06 (No-26.38.09 PWD Sch.2018)",
    "description": "100 mm dia G.I Pipee with wall thickness 5.40 mm...",
    "unit": "Metre",
    "rate": 2520
  }
]

def seed_data():
    print("Starting to seed data...")
    db = SessionLocal()
    print("Database session created.")
    try:
        category_cache = {}
        for i, item_data in enumerate(data):
            print(f"Processing item {i+1}/{len(data)}: {item_data.get('item_code') or item_data.get('item__code')}")
            category_name = item_data["item_category"]
            if category_name in category_cache:
                category = category_cache[category_name]
                print(f"Found category '{category_name}' in cache.")
            else:
                print(f"Querying for category '{category_name}'.")
                category = db.query(ItemCategory).filter(ItemCategory.name == category_name).first()
                if not category:
                    print(f"Category '{category_name}' not found, creating new one.")
                    category = ItemCategory(name=category_name)
                    db.add(category)
                    db.flush()  # Flush to get the category_id
                    print(f"Created and flushed new category with ID: {category.category_id}")
                else:
                    print(f"Found category '{category_name}' in database.")
                category_cache[category_name] = category

            # Handle potential malformed keys
            item_code = item_data.get("item_code") or item_data.get("item__code") or item_data.get("item_code")
            description = item_data.get("description") or item_data.get(".description")

            if not item_code or not description:
                print(f"Skipping item due to missing 'item_code' or 'description': {item_data}")
                continue

            item = Item(
                category_id=category.category_id,
                item_code=item_code,
                item_description=description,
                unit=item_data["unit"],
                rate=item_data["rate"]
            )
            db.add(item)
            print(f"Added item '{item_code}' to session.")
        
        print("Committing changes to the database...")
        db.commit()
        print("Commit successful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        print("Database rollback.")
    finally:
        db.close()
        print("Database session closed.")

if __name__ == "__main__":
    seed_data()
    print("Seeding completed!")
