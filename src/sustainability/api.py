from fastapi import FastAPI, HTTPException

from .engine import demo_engine

app = FastAPI(title="Supplier Sustainability Risk Platform", version="1.0.0")
engine = demo_engine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/suppliers")
def suppliers():
    return engine.records()


@app.get("/suppliers/{supplier_id}/assessment")
def assessment(supplier_id: str):
    try:
        return engine.assess(supplier_id)
    except KeyError as exc:
        raise HTTPException(404, "supplier not found") from exc


@app.get("/actions")
def actions():
    return engine.action_queue()


@app.get("/scenario")
def scenario(renewable_uplift: float = 0.25):
    return engine.scenario(renewable_uplift)

