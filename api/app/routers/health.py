from fastapi import APIRouter
router = APIRouter(prefix="", tags=["health"])

@router.get("/healthz")
async def healthz():
    return {"ok": True}

@router.get("/readyz")
async def readyz():
    # Extend with real dependency checks if needed
    return {"ready": True}

