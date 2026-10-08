"""
Bulk Certificate Generator - Server Runner

Runs the FastAPI application with uvicorn.
Restricts auto-reload watching to the 'app' directory to prevent
unwanted reload loops caused by database writes, certificate PDF creation,
or virtual environment modifications.
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("Starting Bulk Certificate Generator server on http://127.0.0.1:8000 ...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info",
    )
