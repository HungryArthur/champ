import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from sklearn.preprocessing import LabelEncoder, StandardScaler
from Report import download_gpx, track_get, image_get, analysis_weather, analysis_region, step_frequency, terrain_type, data_augmentation

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


# Обёртки, которые вызывают уже существующие функции/код
def task_download_gpx(**context):
    download_gpx()


def task_track_get(**context):
    track_get()


def task_download_img(**context):
    image_get()


def temp_df():
    try:
        df_temp = pd.DataFrame()
        for i in range(0, 3):
            track_data = df[df["track_id"] == i]
            track_data_weather = analysis_weather(track_data)
            df_temp = pd.concat([df_temp, track_data_weather])
            print(f"track{i} добавлен")
        
        df = df_temp.copy()
    except Exception as e:
        print(f"Ошибка вызова функции: analysis_weather {e}")


def region_df():
    try:
        df_region = pd.DataFrame()
        for i in range(0, 3):
            track_data = df[df["track_id"] == i]
            track_data_region = analysis_region(track_data)
            df_region = pd.concat([df_region, track_data_region])
        
        df = df_region.copy()
    except Exception as e:
        print(f"Ошибка вызова функции: analysis_region {e}")


def step_df():
    try:
        df_step = pd.DataFrame()
        for i in range(0, 3):
            track_data = df[df["track_id"] == i]
            track_data_step = step_frequency(track_data)
            df_step = pd.concat([df_step, track_data_step])
        
        df = df_step.copy()
    except Exception as e:
        print(f"Ошибка вызова функции: analysis_region {e}")


def train_type_df():
    try:
        df_train_type = pd.DataFrame()
        for i in range(0, 3):
            track_data = df[df["track_id"] == i]
            track_data_step = terrain_type(track_data)
            df_train_type = pd.concat([df_train_type, track_data_step])
        
        df = df_train_type.copy()
    except Exception as e:
        print(f"Ошибка вызова функции: terrain_type {e}")


def sql_post(df):
    engine = create_engine("postgresql+psycopg2://arthur:146a@localhost:5430/db_arthur")
    df.to_sql("track_analysis", engine, if_exists="replace", index=False)


def encoder_df(df):
    le = LabelEncoder()
    df_corr = df.copy()
    df_corr['terrain_type'] = le.fit_transform(df['terrain_type'])
    df_corr["key_objects_str"] = le.fit_transform(df["key_objects_str"])
    df_corr['region'] = le.fit_transform(df['region'])
    
    return df_corr

import numpy as np
def new_colums(df_corr):
    df_corr['track_time'] = pd.to_datetime(df_corr['track_time'], errors="coerce")
    df_corr['season'] = df_corr['track_time'].dt.month % 12 // 3 + 1
    
    df_corr['temperature_category'] = pd.cut(df_corr['temperature'], bins=[-np.inf, 0, 10, 20, np.inf], labels=['very_cold', 'cold', 'moderate', 'warm'])
    
    return df_corr


# import matplotlib.pyplot as plt
# import seaborn as sns
# def matrix(df_corr):
    # features = df_corr.drop(columns=['track_id', 'track_time', 'region', 'temperature_category'])

    # corr_matrix = features.corr()
    
    # plt.figure(figsize=(8, 6))
    # sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    # plt.title('Матрица корреляции')
    # plt.show()


# def norm_or_not(df):
#     n = len(df.columns) // 5 + bool(len(df.columns) % 5)
#     fig, axes = plt.subplots(nrows=n, ncols=5, figsize=(15,20))
    
#     for idx, i in enumerate(df.columns):
#         sns.kdeplot(data=df, x=i, common_norm=False, ax=axes[idx // 5][idx%5])

#         plt.title(i) 
#     plt.show()


def augmentation_img():
    data_augmentation()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="gpx_report_agent",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["gpx", "report"],
) as dag:

    t_download_gpx = PythonOperator(
        task_id="download_gpx",
        python_callable=task_download_gpx,
    )

    t_track_get = PythonOperator(
        task_id="track_get",
        python_callable=task_track_get,
    )

    t_image_get = PythonOperator(
        task_id="image_get",
        python_callable=task_download_img,
    )
    
    t_download_gpx >> t_track_get >> t_image_get
