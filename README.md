# Estimation Backend (FastAPI)

Pricefx-style architecture: Product Master (Items) + Projects → Estimations → Estimation Lines.

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API runs at: `http://127.0.0.1:8000`

## Endpoints (high level)

- **Items & Categories**
  - `POST /items/categories` `{ "name": "Concrete" }`
  - `GET  /items/categories`
  - `POST /items` `{ "item_code": "ITM-001", "item_description": "M25 Concrete", "unit": "m3", "rate": 120.5, "category_id": 1 }`
  - `GET  /items`

- **Projects & Estimations**
  - `POST /projects` `{ "project_name": "Montola Bridge", "client_name": "Client X" }`
  - `GET  /projects`
  - `POST /projects/{project_id}/estimations` `{ "estimation_name": "Phase 1" }`
  - `GET  /projects/{project_id}/estimations`

- **Estimation Lines**
  - `POST /estimations/{estimation_id}/lines`
    ```json
    {
      "item_id": 1,
      "sub_description": "Pier foundation",
      "no_of_units": 2,
      "length": 3.5,
      "width": 2.0,
      "thickness": 0.5,
      "quantity": null,
      "rate": null
    }
    ```
    - If `rate` is omitted, the item's master `rate` is used.
    - If `quantity` is provided, it's used directly; otherwise `no_of_units * length * width * thickness`.
  - `GET /estimations/{estimation_id}/lines`
  - `GET /estimations/{estimation_id}/total` → `{ "grand_total": 12345.67 }`

## Data Model

- `item_categories` → divisions
- `items` → product master
- `projects`
- `estimations` (belongs to project)
- `estimation_lines` (belongs to estimation, references item)

## Notes
- SQLite file `estimation.db` is created in project root.
- CORS is permissive for local development. Restrict in production.
