from fastapi import FastAPI, Query, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from typing import List

from utils import *


app = FastAPI()

templates = Jinja2Templates(directory="static")

# Serve static files like CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fake data
app.runs_data = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {'request': request, 'warning_message': ''})


@app.get("/e1", response_class=HTMLResponse)
async def e1(request: Request, mlflow_uri: str = Query()):
    # Get the items list here using mlflow artifacts
    if is_tracking_uri_valid(mlflow_uri):
        app.runs_data = get_mlflow_runs_with_tag(tag='time_series', tracking_uri=mlflow_uri)
        formatted_runs = format_filtered_runs(app.runs_data)
        return templates.TemplateResponse("e1.html", {"request": request, "items": formatted_runs.to_dict(orient='records')})
    else:
        return templates.TemplateResponse("index.html", {'request': request, 'warning_message': 'invalid tracking uri'})


@app.get("/e2", response_class=HTMLResponse)
async def e2(request: Request, selected_items: List[str] = Query([])):
    # Calculate metrics for the selected entries using the data and show them here
    selected_data = app.runs_data.loc[app.runs_data['run_id'].apply(lambda x: True if x in selected_items else False), :]
    selected_data = format_filtered_runs(selected_data)
    return templates.TemplateResponse("e2.html", {"request": request, "selected_items": selected_data.to_dict(orient='records')})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
