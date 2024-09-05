from fastapi import FastAPI, Query, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from typing import List
import json

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
    

@app.get("/next")
async def next_endpoint(request: Request):
    run_ids = list(request.query_params.values())
    print(request.query_params.values())
    return JSONResponse(content={"selected_run_ids": run_ids})
    

@app.get("/e1v2", response_class=HTMLResponse)
async def e1(request: Request, mlflow_uri: str = Query()):
    # Get the items list here using mlflow artifacts
    if is_tracking_uri_valid(mlflow_uri):
        app.mlflow_tracking_uri = mlflow_uri
        app.runs_data = get_mlflow_runs_with_tag(tag='time_series', tracking_uri=mlflow_uri)
        formatted_runs, series_names = format_filtered_runs(app.runs_data)

        return templates.TemplateResponse("e2v3.html", {"request": request, 
                                                         "selected_runs": formatted_runs.to_dict(orient='records'),
                                                         "series_names": series_names})
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
    selected_items = []
    selected_series = None
    for key, value in request.query_params.items():
        if 'run_id' in key:
            selected_items.append(value)
        elif key == 'selected_series':
            selected_series = value

    if selected_series is None:
        return JSONResponse({'message', 'No value is chosen for "selected_series"'})

    # Downloading mlflow runs data
    all_forecasts_df = pd.DataFrame()
    print(selected_items)
    all_exp_names = {}
    for runid in selected_items:
        actual_df = get_time_series_data_from_runid(runid=runid, series_name=selected_series, tag='_actual', tracking_uri=app.mlflow_tracking_uri)
        forecast_df = get_time_series_data_from_runid(runid=runid, series_name=selected_series, tag='_forecast', tracking_uri=app.mlflow_tracking_uri)

        actual_df.index = actual_df['Date']
        forecast_df.index = forecast_df['Date']

        # Get experiment name assiciated with this runid
        exp_name = mlflow.get_run(run_id=runid).info.run_name
        if exp_name in all_exp_names.keys():
            all_exp_names[exp_name] += 1
        else:
            all_exp_names[exp_name] = 1

        if all_exp_names[exp_name] == 1:
            series_plot_name = exp_name
        else:
            series_plot_name = exp_name + ':' + str(all_exp_names[exp_name]) + ':' + str(runid)[0:10] + '...'

        all_forecasts_df[series_plot_name] = forecast_df['Values']

    ensemble_mean = all_forecasts_df.mean(axis=1)
    ensemble_median = all_forecasts_df.median(axis=1)

    all_forecasts_df['EnsembleMean'] = ensemble_mean
    all_forecasts_df['EnsembleMedian'] = ensemble_median

    metrics = []
    forecasts = []
    for col in list(all_forecasts_df.columns):
        cur_metrics = {'method': col}
        cur_metrics.update(calculate_metrics(actual_df['Values'], all_forecasts_df[col]))
        metrics.append(cur_metrics)

        errors = actual_df['Values'] - all_forecasts_df[col]
        cumsum = errors.cumsum()

        forecasts.append({
            "method": col,
            "dates": all_forecasts_df.index.strftime("%Y-%m-%d").tolist(),
            "values": all_forecasts_df[col].tolist(),
            "cumsum": cumsum.tolist(),
            "errors": errors.tolist(),
            "mean": all_forecasts_df[col].mean(),
            "sum": all_forecasts_df[col].sum()
        })

    data = {
        "dates": actual_df['Date'].dt.strftime("%Y-%m-%d").tolist(),
        "actual": actual_df['Values'].tolist(),
        "actual_mean": actual_df['Values'].mean(),
        "actual_sum": actual_df['Values'].sum(),
        "forecasts": forecasts
    }

    return templates.TemplateResponse("vis2.html", {"request": request, 'forecast_data':json.dumps(data), 'forecast_metrics':metrics})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
