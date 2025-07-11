import uvicorn
from Loader.server import app

if __name__ == "__main__":
    uvicorn.run("Loader.server:app", host="127.0.0.1", port=8000, reload=True)
