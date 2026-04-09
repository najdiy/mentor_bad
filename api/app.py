import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routers import schedule, supplements, intake, stock, stats, me


def create_app(bot=None) -> FastAPI:
    app = FastAPI(title="Mentor Labs API", docs_url="/api/docs")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store bot instance for use in routers
    app.state.bot = bot

    # API routers
    app.include_router(schedule.router, prefix="/api")
    app.include_router(supplements.router, prefix="/api")
    app.include_router(intake.router, prefix="/api")
    app.include_router(stock.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(me.router, prefix="/api")

    # Serve React static files if built
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_dir):
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app
