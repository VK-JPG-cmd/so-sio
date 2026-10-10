"""Development runner script for BrandShield AI."""

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
