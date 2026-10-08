@echo off
if exist env\Scripts\pytest.exe (
    env\Scripts\pytest.exe -q
) else if exist .venv\Scripts\pytest.exe (
    .venv\Scripts\pytest.exe -q
) else (
    python -m pytest -q
)

