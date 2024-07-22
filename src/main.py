from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List

app = FastAPI()

# Mount the static directory containing your HTML and CSS files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sample data (replace with your actual data source)
fake_data = [
    {"id": 1, "name": "Item 1", "category": "Category A"},
    {"id": 2, "name": "Item 2", "category": "Category B"},
    {"id": 3, "name": "Item 3", "category": "Category A"},
    {"id": 4, "name": "Item 4", "category": "Category C"},
]

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=open("static/index.html", "r").read())

@app.get("/items")
async def get_items(category: Optional[str] = None):
    if category:
        filtered_items = [item for item in fake_data if item['category'] == category]
    else:
        filtered_items = fake_data
    return filtered_items

@app.post("/compare")
async def compare_items(selected_ids: List[int]):
    # Perform comparison logic here (e.g., retrieving details of selected items)
    selected_items = [item for item in fake_data if item['id'] in selected_ids]
    
    # Dummy comparison logic (replace with actual logic)
    result = f"Selected items: {selected_items}"
    
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
