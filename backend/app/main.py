from fastapi import FastAPI

app = FastAPI(title="PrintServer")


@app.get("/health")
def health():
    return {"status": "ok"}
