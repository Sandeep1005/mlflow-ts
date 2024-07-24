from fastapi import FastAPI, Query, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from typing import List

from utils import *


app = FastAPI()

templates = Jinja2Templates(directory="static")

# Serve static files like CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Runs data
app.runs_data = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {'request': request, 'warning_message': ''})


@app.get("/e1", response_class=HTMLResponse)
async def e1(request: Request, mlflow_uri: str = Query()):
    # Get the items list here using mlflow artifacts
    if is_tracking_uri_valid(mlflow_uri):
        app.mlflow_tracking_uri = mlflow_uri
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
    selected_metrics = get_series_metrics_data_by_runids(selected_items, series_name='my_index', tracking_uri=app.mlflow_tracking_uri)
    merge_results = pd.merge(left=selected_data, right=selected_metrics, how='outer', on='run_id')
    return templates.TemplateResponse("e2.html", {"request": request, "selected_items": merge_results.to_dict(orient='records')})


@app.get("/vis")
async def read_root(request: Request):
    return templates.TemplateResponse("vis.html", {"request": request})

@app.get("/data1")
async def get_data():
    # Sample data
    dates = pd.date_range(start="2024-01-01", periods=12, freq='MS')
    actual = pd.Series([10, 12, 15, 13, 17, 19, 20, 18, 16, 14, 13, 15], index=dates)
    forecast = pd.Series([11, 13, 14, 14, 16, 18, 19, 17, 15, 14, 14, 16], index=dates)
    
    # Calculate errors
    errors = actual - forecast
    
    # Calculate CUSUM
    cusum = errors.cumsum()

    data = {
        "dates": dates.strftime("%Y-%m-%d").tolist(),
        "actual": actual.tolist(),
        "forecast": forecast.tolist(),
        "errors": errors.tolist(),
        "cusum": cusum.tolist()
    }
    
    return JSONResponse(content=data)


@app.get("/vis2")
async def read_root(request: Request):
    return templates.TemplateResponse("vis2.html", {"request": request})

@app.get("/data")
async def get_data():
    # Sample data
    dates = pd.date_range(start="2024-01-01", periods=12, freq='MS')
    actual = pd.Series([10, 12, 15, 13, 17, 19, 20, 18, 16, 14, 13, 15], index=dates)
    forecast_methods = {
        "Method 1": pd.Series([11, 13, 14, 14, 16, 18, 19, 17, 15, 14, 14, 16], index=dates),
        "Method 2": pd.Series([12, 11, 16, 12, 18, 17, 20, 18, 17, 15, 14, 17], index=dates),
        "Method 3": pd.Series([10, 14, 15, 13, 17, 19, 21, 18, 16, 14, 13, 15], index=dates)
    }
    
    forecasts = []
    for method, forecast in forecast_methods.items():
        errors = actual - forecast
        cusum = errors.cumsum()
        forecasts.append({
            "method": method,
            "values": forecast.tolist(),
            "cusum": cusum.tolist(),
            "errors": errors.tolist()
        })

    data = {
        "dates": dates.strftime("%Y-%m-%d").tolist(),
        "actual": actual.tolist(),
        "forecasts": forecasts
    }
    
    return JSONResponse(content=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
