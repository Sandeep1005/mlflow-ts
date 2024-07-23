from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from typing import List

app = FastAPI()

templates = Jinja2Templates(directory="static")

# Serve static files like CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fake data
fake_data = [
    {"id": 1, "name": "Item 1", "category": "Category A"},
    {"id": 2, "name": "Item 2", "category": "Category B"},
    {"id": 3, "name": "Item 3", "category": "Category A"},
    {"id": 4, "name": "Item 4", "category": "Category C"},
]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {'request': request})

@app.get("/e1", response_class=HTMLResponse)
async def e1(request: Request):
    # Get the items list here using mlflow artifacts
    
    return templates.TemplateResponse("e1.html", {"request": request, "items": fake_data})

@app.get("/e2", response_class=HTMLResponse)
async def e2(request: Request, selected_items: List[int] = Query([])):
    # Calculate metrics for the selected entries using the data and show them here

    selected_data = [item for item in fake_data if item['id'] in selected_items]
    return templates.TemplateResponse("e2.html", {"request": request, "selected_items": selected_data})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
