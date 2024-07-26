import mlflow
import pandas as pd
import numpy as np
import requests


def is_tracking_uri_valid(mlflow_uri):
    # Check health
    health_url = mlflow_uri.rstrip('/') + '/health'
    
    try:
        response = requests.get(health_url)
        response.raise_for_status()  # Raise exception for 4xx or 5xx errors
        
        if response.content.decode(encoding='utf-8') == 'OK':
            return True
        else:
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to MLflow server at {mlflow_uri}: {e}")
        return False


def get_mlflow_runs_with_tag(tag:str, tracking_uri:str):
    mlflow.set_tracking_uri(tracking_uri)

    tag_key = 'type_of_results'

    runs = mlflow.search_runs(search_all_experiments=True, filter_string=f"tags.`{tag_key}` = '{tag}'")
    return runs


def format_filtered_runs(runs):
    # Formatting the result to a suitable format
    final_result = pd.DataFrame()
    final_result['run_name'] = runs['tags.mlflow.runName']
    final_result['experiment_id'] = runs['experiment_id']
    final_result['run_id'] = runs['run_id']
    final_result['created_by'] = runs['tags.mlflow.user']
    # series_names_columns = [col for col in runs.columns if 'tags.time_series.' in col]
    # renamed_series_names = ['.'.join(col.split('.')[2:]) for col in series_names_columns]
    # final_result[renamed_series_names] = runs[series_names_columns]

    return final_result


def log_timeseries(actual:pd.DataFrame, forecast:pd.DataFrame, series_name:str):
    actual_html = actual.to_html(index=False)
    forecast_html = forecast.to_html(index=False)
    mlflow.log_text(actual_html, artifact_file='timeserieslogs/'+series_name+'_actual.html')
    mlflow.log_text(forecast_html, artifact_file='timeserieslogs/'+series_name+'_forecast.html')
    mlflow.set_tag(key='type_of_results', value='time_series')
    mlflow.set_tag(key='time_series.'+series_name, value=series_name)


def calculate_metrics(actual: pd.Series, forecast: pd.Series) -> dict:
    metrics = {}
    
    # Mean Absolute Error (MAE)
    mae = np.mean(np.abs(actual - forecast))
    metrics['MAE'] = mae
    
    # Mean Squared Error (MSE)
    mse = np.mean((actual - forecast) ** 2)
    metrics['MSE'] = mse
    
    # Root Mean Squared Error (RMSE)
    rmse = np.sqrt(mse)
    metrics['RMSE'] = rmse
    
    # Mean Absolute Percentage Error (MAPE)
    mape = np.mean(np.abs((actual - forecast) / actual)) * 100
    metrics['MAPE'] = mape
    
    # Symmetric Mean Absolute Percentage Error (sMAPE)
    smape = np.mean(2 * np.abs(actual - forecast) / (np.abs(actual) + np.abs(forecast))) * 100
    metrics['sMAPE'] = smape
    
    # R-squared (R²)
    ss_res = np.sum((actual - forecast) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    metrics['RSquared'] = r_squared
    
    # Correlation Coefficient
    correlation = np.corrcoef(actual, forecast)[0, 1]
    metrics['Correlation'] = correlation
    
    # Tracking Signal
    mad = np.mean(np.abs(actual - forecast))
    tracking_signal = np.sum(actual - forecast) / mad
    metrics['TrackingSignal'] = tracking_signal
    
    # Bias
    bias = np.mean(actual - forecast)
    metrics['Bias'] = bias
    
    # Theil's U Statistic
    numerator = np.sqrt(np.mean((actual - forecast) ** 2))
    denominator = np.sqrt(np.mean(actual ** 2)) + np.sqrt(np.mean(forecast ** 2))
    theils_u = numerator / denominator
    metrics['TheilsU'] = theils_u
    
    return metrics
    

def get_series_metrics_data_by_runids(runids, series_name:str, tracking_uri:str):
    results_df = []
    for runid in runids:
        actual = get_time_series_data_from_runid(runid, series_name=series_name, tag='_actual', tracking_uri=tracking_uri)
        forecast = get_time_series_data_from_runid(runid, series_name=series_name, tag='_forecast', tracking_uri=tracking_uri)
        
        metrics_dict = {}
        metrics_dict['run_id'] = runid
        metrics_dict.update(calculate_metrics(actual=actual, forecast=forecast))
        results_df.append(metrics_dict)
    
    return pd.DataFrame(results_df)


def get_time_series_data_from_runid(runid, series_name:str, tag:str, tracking_uri:str):
    mlflow.set_tracking_uri(tracking_uri)
    
    data = pd.read_html(mlflow.artifacts.download_artifacts(run_id=runid,
                                        artifact_path='timeserieslogs/'+series_name+tag+'.html',
                                        dst_path='./temp/timeserieslogs/'+series_name+tag+'.html',
                                        tracking_uri=tracking_uri))[0]
    drop_cols = [col for col in data.columns if 'Unnamed' in col]
    data.drop(drop_cols, axis=1, inplace=True)
    data['Date'] = pd.to_datetime(data['Date'])
    return data

