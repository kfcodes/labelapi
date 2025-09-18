from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # If routes live at app/routes/__init__.py exporting `router`
    from .routes import router as api_router

    app.include_router(api_router)

    return app


# Optional: also expose a module-level `app` so you can run without --factory
app = create_app()
