from fastapi import FastAPI, Query
from pydantic import BaseModel
import re

app = FastAPI(title="Always-Result RC API")

RC_DATA = {
    "UP12AB1234": {
        "owner_name": "Amit Kumar",
        "vehicle_type": "Motorcycle",
        "brand": "Hero",
        "model": "Splendor Plus",
        "fuel": "Petrol",
        "engine_cc": "97",
        "registration_date": "2019-08-22"
    }
}

PREFIX_HINTS = {
    "UP12": {"likely_brands": ["Hero", "Bajaj", "Honda"], "vehicle_type": "Motorcycle"},
    "DL05": {"likely_brands": ["Maruti", "Hyundai", "Tata"], "vehicle_type": "Car"},
}

class RCResponse(BaseModel):
    status: str
    vehicle_number: str
    api_mode: str
    vehicle_type: str
    brand: str
    model: str
    fuel: str = None
    engine_cc: str = None
    year_estimated: str = None
    owner_name: str = None
    note: str = None

def normalize_rc(rc: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', rc or '').upper()

def format_state_prefix(rc_norm: str) -> str:
    return rc_norm[:4] if len(rc_norm) >= 4 else rc_norm[:2]

def predict_from_pattern(rc_norm: str):
    prefix = format_state_prefix(rc_norm)
    hint = PREFIX_HINTS.get(prefix, {})
    vehicle_type = hint.get("vehicle_type", "Motorcycle")
    likely_brands = hint.get("likely_brands", ["UnknownBrand"])
    model_est = f"{likely_brands[0]} model (estimated)"
    engine = "100cc (approx)" if vehicle_type.lower().startswith("motor") else "1000-1200cc (approx)"
    m = re.search(r'(\d{4})$', rc_norm)
    year_est = "2016-2023"
    if m:
        num = int(m.group(1))
        year_est = "2005-2015" if num < 3000 else "2016-2023"
    return {
        "vehicle_type": vehicle_type,
        "brand": likely_brands[0],
        "model": model_est,
        "fuel": "Petrol (likely)",
        "engine_cc": engine,
        "year_estimated": year_est
    }

@app.get("/api/rc", response_model=RCResponse)
def get_rc_info(rc: str = Query(..., description="Vehicle registration number, e.g. UP12AB1234")):
    rc_norm = normalize_rc(rc)
    if rc_norm in RC_DATA:
        data = RC_DATA[rc_norm]
        return RCResponse(
            status="success",
            vehicle_number=rc_norm,
            api_mode="database",
            vehicle_type=data.get("vehicle_type","Unknown"),
            brand=data.get("brand","Unknown"),
            model=data.get("model","Unknown"),
            fuel=data.get("fuel"),
            engine_cc=data.get("engine_cc"),
            year_estimated=data.get("registration_date"),
            owner_name=data.get("owner_name"),
            note="Exact match from local database."
        )
    pred = predict_from_pattern(rc_norm)
    return RCResponse(
        status="success",
        vehicle_number=rc_norm,
        api_mode="predicted+database",
        vehicle_type=pred["vehicle_type"],
        brand=pred["brand"],
        model=pred["model"],
        fuel=pred["fuel"],
        engine_cc=pred["engine_cc"],
        year_estimated=pred["year_estimated"],
        owner_name=None,
        note="No local DB match. Using prediction to always return result."
    )

@app.get("/")
def root():
    return {"message": "Always-Result RC API — try /api/rc?rc=UP12AB1234"}
