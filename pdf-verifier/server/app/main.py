from fastapi import FastAPI
from .routes.pdf_upload import router as pdf_upload_router
from .routes.pdf_convert import router as pdf_convert_router
from .routes.pdf_extract import router as pdf_extract_router
from .routes.pdf_detect import router as pdf_detect_router
from .routes.pdf_verify import router as pdf_verify_router
from .routes.ocr import router as ocr_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="PDF Verification API",
        description="API pour l'analyse et la vérification des PDF",
        version="1.1.0"
    )
    # On associe chaque router avec un préfixe, ex: /pdf
    app.include_router(pdf_upload_router, prefix="/pdf")
    app.include_router(pdf_convert_router, prefix="/pdf")
    app.include_router(pdf_extract_router, prefix="/pdf")
    app.include_router(pdf_detect_router, prefix="/pdf")
    app.include_router(pdf_verify_router, prefix="/pdf")
    app.include_router(ocr_router, prefix="/pdf")
    return app

app = create_app()

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de vérification de PDF"}