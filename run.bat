@echo off
if exist env\Scripts\python.exe (
    env\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
) else if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
) else (
    python -m uvicorn app.main:app --reload --reload-dir app
)

