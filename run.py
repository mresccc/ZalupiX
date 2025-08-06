#!/usr/bin/env python3
"""
Файл запуска FastAPI приложения
"""

import uvicorn

from app.config import HOST, PORT, RELOAD

if __name__ == "__main__":
    uvicorn.run("app.app:app", host=HOST, port=PORT, reload=RELOAD)
