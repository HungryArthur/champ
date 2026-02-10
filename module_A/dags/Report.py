import numpy as np
import requests
import geopandas as gpd
import gpxpy
import matplotlib.pyplot as plt
import contextily as ctx
import time
import seaborn as sns
import pickle
import os

from geopy.distance import geodesic
from shapely.geometry import box, LineString
from random import randint, uniform
from PIL import Image, ImageEnhance

os.makedirs("/opt/airflow/agent/data/gpx", exist_ok=True)
os.makedirs("/opt/airflow/agent/data/image", exist_ok=True)

def download_gpx():
    links = []

    with open("Links.txt", mode="r", encoding="UTF-8") as f:
        for i in f:
            links.append(i.strip())
    
    
    for num, url in enumerate(links):
        try:
            response = requests.get(url)
            filename = f"track{num}.gpx"
            
            with open(f"/opt/airflow/agent/data/gpx/{filename}", mode="wb") as f:
                f.write(response.content)
        except Exception as e:
            print("Ошибка при скачивании", e)

gpx_list = os.listdir("/opt/airflow/agent/data/gpx")
gpx_list.sort()

import pandas as pd
df = pd.DataFrame(columns=["track_id", "track_time", "latitude", "longitude", "altitude"])
df['track_time'] = pd.to_datetime(df['track_time'])
df['track_time'] = df['track_time'].dt.strftime('%Y-%m-%d')


margin = 0.02
lats, lons = [], []

def track_get():
	for i, file in enumerate(gpx_list):
		with open(f"{"/opt/airflow/agent/data/gpx"}/{file}", mode="r", encoding="UTF-8") as f:
			gpx = gpxpy.parse(f)
		
		for track in gpx.tracks:
			for segment in track.segments:
				for point in segment.points:
					lats.append(point.latitude)
					lons.append(point.longitude)
					df.loc[len(df)] = [i, point.time, point.latitude, point.longitude, point.elevation]


def image_get():
    for file in gpx_list:
        bbox = box(
            min(lons) - margin,
            min(lats) - margin,
            max(lons) + margin,
            max(lats) + margin
        )
        track_line = LineString(zip(lons, lats))

        gdf_bbox = gpd.GeoDataFrame(geometry=[bbox], crs="EPSG:4326")
        gdf_bbox_web = gdf_bbox.to_crs(epsg=3857)

        gdf_track = gpd.GeoDataFrame(geometry=[track_line], crs="EPSG:4326")
        gdf_track_web = gdf_track.to_crs(epsg=3857)

        _, ax = plt.subplots(figsize=(10, 8))

        gdf_bbox_web.plot(ax=ax, alpha=0)
        gdf_track_web.plot(ax=ax, color="red", linewidth=2)

        ctx.add_basemap(ax, crs=gdf_bbox_web.crs, source=ctx.providers.OpenStreetMap.Mapnik)

        ax.set_axis_off()

        plt.savefig(f"{"/opt/airflow/agent/data/image"}/{file[:-4]}", dpi=150, bbox_inches="tight", pad_inches=0)
        plt.close()


def temp(lat, lon, date):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        'latitude': lat,        # Ширина
        'longitude': lon,       # Долгота
        'start_date': date,
        'end_date': date,
        'hourly': 'temperature_2m',
        "timezone":"auto"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    if response.status_code == 200:
        data = response.json()
        return data["hourly"]['temperature_2m'][12]
    else:
        print(f"Данные не получены")


def analysis_weather(df):
    '''
    Функция для интерполяции температур между опорными точками.
    Использует 5 опорных точек для интерполяции температуры для всех строк.
    '''
    n = len(df)
    key_indexes = [0, n//4, n//2, 3*n//4, n-1]
    temperatures_at_key_points = {}
    
    for idx in key_indexes:
        lat = df.iloc[idx]["latitude"]
        lon = df.iloc[idx]["longitude"]
        date = df.iloc[idx]["track_time"]
        
        temp_value = temp(lat, lon, date)
        
        temperatures_at_key_points[idx] = temp_value

    
    if len(temperatures_at_key_points) < 2:
        print("Недостаточно данных для интерполяции, проверьте работоспособность API")
        df["temperature"] = None
        return df
    
    all_temperatures = []
    left_idx = 0
    right_idx = 1
    
    for i in range(n):
        # Если текущий индекс превысил правую границу и есть следующий интервал
        if (right_idx < len(key_indexes) - 1 and i >= key_indexes[right_idx]):
            left_idx += 1
            right_idx += 1
        
        left_key = key_indexes[left_idx]
        right_key = key_indexes[right_idx]
        
        left_temp = temperatures_at_key_points[left_key]
        right_temp = temperatures_at_key_points[right_key]
        
        # Если текущая строка - одна из опорных точек
        if i in temperatures_at_key_points:
            temperature = temperatures_at_key_points[i]
        elif left_temp is not None and right_temp is not None:
            # Линейная интерполяция между двумя опорными точками
            temperature = left_temp + (right_temp - left_temp) * (i - left_key) / (right_key - left_key)
        else:
            # Если нет данных для интерполяции
            temperature = left_temp if left_temp is not None else right_temp
        
        all_temperatures.append(temperature)
    
    df = df.copy()
    df["temperature"] = all_temperatures
    
    return df


def extract_map_region(lat: float, lon: float):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/536.36 (KHTML, like Gecko) Chrome/58.0.3029.100 Safari/536.3'}
        response = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
        json = response.json()
        time.sleep(1.5)
        if "county" in json["address"]:
            return json["address"]["county"]
        if "state" in json["address"]:
            return json["address"]["state"]
        return json["address"]["country"]
    except Exception as e:
        print(f"Error {e}")


def analysis_region(df):
    '''
    Функция для определения регионов между опорными точками.
    '''
    try:
        lat = df.iloc[0]["latitude"]
        lon = df.iloc[0]["longitude"]
        df = df.copy()
        df["region"] = extract_map_region(lat, lon)
        return df
    except Exception as e:
        print(f"Ошибка вызова функции extract_map_region {e}")


def step_frequency(df):
    points = list(zip(df["latitude"], df["longitude"]))
    step = [0]
    
    for p1, p2 in zip(points, points[1:]):
        dist = geodesic(p1, p2).meters
        step.append(dist / 0.75)
    df["steps"] = step
    return df


def terrain_type(df):
    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/cgi/interpreter"
    ]
    try:
        points = list(zip(df["latitude"], df["longitude"]))
        rep_points = [points[0], points[len(points)//2], points[-1]] # 3 точки
        
        all_landuse, all_natural, all_key_objects = [], [], set()
        
        for lat, lon in rep_points:
            overpass_query = f"""
            [out:json][timeout:45];
            (
                way(around:500,{lat},{lon})["landuse"];
                way(around:500,{lat},{lon})["natural"];
                way(around:500,{lat},{lon})["leisure"];
                way(around:500,{lat},{lon})["waterway"="river"];
                way(around:500,{lat},{lon})["waterway"="stream"];
                way(around:500,{lat},{lon})["natural"="water"];
                node(around:500,{lat},{lon})["place"="city"];
                node(around:500,{lat},{lon})["place"="town"];
                node(around:500,{lat},{lon})["place"="village"];
                node(around:500,{lat},{lon})["natural"="peak"];
                node(around:500,{lat},{lon})["natural"="mountain"];
            );
            out tags center;
            """
            
            for endpoint in overpass_endpoints:
                response = requests.get(endpoint, params={'data': overpass_query}, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    break
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                
                if 'landuse' in tags:
                    all_landuse.append(tags['landuse'])
                elif 'natural' in tags:
                    all_natural.append(tags['natural'])
                    if tags['natural'] in ['peak', 'mountain'] and 'name' in tags:
                        all_key_objects.add(f"Mountain: {tags['name']}")
                
                if 'waterway' in tags and tags['waterway'] in ['river', 'stream'] and 'name' in tags:
                    all_key_objects.add(f"River: {tags['name']}")
                
                if 'place' in tags and tags['place'] in ['city', 'town', 'village'] and 'name' in tags:
                    all_key_objects.add(f"Settlement: {tags['name']} ({tags['place']})")
                
                if element.get('type') == 'way' and 'natural' in tags and tags['natural'] == 'water' and 'name' in tags:
                    all_key_objects.add(f"Lake: {tags['name']}")
            
            time.sleep(1.5)
        
        terrain_type = "unknown"
        if all_landuse:
            terrain_type = max(set(all_landuse), key=all_landuse.count)
        elif all_natural:
            terrain_type = max(set(all_natural), key=all_natural.count)
        
        key_objects_str = "; ".join(sorted(all_key_objects)) if all_key_objects else None
        
        df["terrain_type"] = terrain_type
        df["key_objects_str"] = key_objects_str
    except Exception as e:
        print("Ошибка", e)
    return df


def data_augmentation():
    images_path = "../data/image"
    for filename in os.listdir(images_path):
        if filename.lower().endswith(".png") and not any(word in filename for word in ["rotated", "contrasted", "brightness"]):
            img = Image.open(f"{images_path}/{filename}")
            
            rotated_img = img.rotate(randint(10, 60))
            rotated_img.save(f"{images_path}/rotated_{filename}")
            
            contrasted_img = ImageEnhance.Contrast(img).enhance(randint(2, 4))
            contrasted_img.save(f"{images_path}/contrasted_{filename}")
            
            brightness_img = ImageEnhance.Brightness(img).enhance(uniform(1.2, 1.6))
            brightness_img.save(f"{images_path}/brightness_{filename}")
