import mlflow
import numpy as np
import pandas as pd

from utils import *


def get_random_time_series_dict():
    values = np.random.rand(12)
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')

    result = pd.DataFrame()
    result['Date'] = monthly_dates
    result['Values'] = values

    return result


def generate_mlflow_test_runs():
    # Making more runs
    mlflow.set_tracking_uri('http://10.209.240.25:6401')

    exp = mlflow.set_experiment('Test_exp2')
    actual = get_random_time_series_dict()

    for i in range(10):
        with mlflow.start_run(experiment_id=exp.experiment_id) as run:
            forecast = get_random_time_series_dict()
            log_timeseries(actual, forecast, 'my_index')
            # forecast2 = get_random_time_series_dict()
            # log_timeseries(actual, forecast2, 'my_index2')


if __name__ == '__main__':
    generate_mlflow_test_runs()