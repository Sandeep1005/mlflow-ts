import mlflow
import pandas as pd


def is_tracking_uri_valid(tracking_uri):
    return True


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
    