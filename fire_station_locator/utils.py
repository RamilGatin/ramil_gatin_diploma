import glob
import os
import sys

import joblib
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import config

MODEL_PATH = "fire_station_locator/model/random_forest_model.pkl"


def load_data(extended=False):
    logger.info("Начало загрузки данных")

    base_dir = os.path.abspath(os.path.dirname(__file__))
    if not extended:
        all_files = glob.glob(os.path.join(base_dir, config.DATA_DIR, "*.txt"))
    else:
        all_files = glob.glob(os.path.join(base_dir, config.EXTENDED_DATA_DIR, "*.csv"))
        logger.debug(all_files)

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    if li:
        data = pd.concat(li, axis=0, ignore_index=True)
        logger.info(f"Загружено {len(data)} записей данных")
        return data
    else:
        logger.warning("Данные не найдены")
        return None


def prepare_data(data):
    logger.debug("Подготовка данных для обучения модели")
    if data is not None:
        data = data[data["confidence"] > 50]
        data["acq_date"] = pd.to_datetime(data["acq_date"])
        data["month"] = data["acq_date"].dt.month
        data["day"] = data["acq_date"].dt.day
        data["hour"] = data["acq_date"].dt.hour

        X = data[["latitude", "longitude", "brightness", "month", "day", "hour"]]
        y = (
            data["confidence"] > 80
        )  # Целевая переменная: высокий уровень уверенности пожара

        logger.info("Данные подготовлены для обучения модели")
        return X, y, data
    else:
        logger.warning("Нет данных для подготовки")
        return None, None, None


def train_model(X, y):
    logger.debug("Обучение классификатора")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    logger.info(f"Точность модели: {accuracy:.2f}")

    # Проверка и создание директории, если она не существует
    model_dir = os.path.dirname(MODEL_PATH)
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # Сохранение модели
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Модель сохранена в {MODEL_PATH}")

    return model


def load_model():
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        logger.info("Модель загружена")
        return model
    else:
        logger.error("Модель не найдена, обучите модель сначала")
        return None


def predict_fire_station(model, lat, lon):
    month = 6  # Пример текущего месяца
    day = 15  # Пример текущего дня
    hour = 12  # Пример текущего часа
    X_new = pd.DataFrame(
        [[lat, lon, 300, month, day, hour]],
        columns=["latitude", "longitude", "brightness", "month", "day", "hour"],
    )
    proba = model.predict_proba(X_new)[0][1]
    return proba


def get_analytical_info(data, lat, lon, threshold_distance=50):
    logger.debug("Получение аналитической информации по выбранной точке")
    nearby_fires = data[
        (abs(data["latitude"] - lat) <= threshold_distance / 111)
        & (abs(data["longitude"] - lon) <= threshold_distance / 111)
    ]
    num_fires = len(nearby_fires)
    avg_brightness = nearby_fires["brightness"].mean() if num_fires > 0 else 0
    monthly_stats = (
        get_monthly_fire_statistics(nearby_fires)
        if "month" in nearby_fires.columns
        else pd.DataFrame()
    )
    return num_fires, avg_brightness, nearby_fires, monthly_stats


def calculate_center_of_mass(data, lat, lon, threshold_distance=50):
    nearby_fires = data[
        (abs(data["latitude"] - lat) <= threshold_distance / 111)
        & (abs(data["longitude"] - lon) <= threshold_distance / 111)
    ]
    if not nearby_fires.empty:
        center_lat = nearby_fires["latitude"].mean()
        center_lon = nearby_fires["longitude"].mean()
        return center_lat, center_lon
    else:
        return None, None


def prepare_heatmap_data(data):
    logger.debug("Подготовка данных для тепловой карты")
    heatmap_data = data[["latitude", "longitude", "brightness"]].values.tolist()
    logger.info(f"Подготовлено {len(heatmap_data)} записей для тепловой карты")
    return heatmap_data


def get_monthly_fire_statistics(nearby_fires):
    monthly_stats = (
        nearby_fires.groupby(nearby_fires["month"]).size().reset_index(name="counts")
    )
    monthly_stats = monthly_stats.rename(
        columns={"month": "Месяц", "counts": "Количество пожаров"}
    )
    return monthly_stats


def setup_logging(log_file=None):
    logger.remove()

    console_format = (
        "<dim>{time:YYYY-MM-DD HH:mm:ss.SSS}</dim> | "
        "<level>{level:.1s}</level> | "
        "<cyan>{file}</cyan>:<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{message}"
    )
    logger.add(
        sys.stdout, format=console_format, level="DEBUG", colorize=True, enqueue=True
    )

    if log_file:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level:.1s} | "
            "{file}:{name}:{function}:{line} | "
            "{message}"
        )
        logger.add(
            log_file, rotation="10 MB", level="INFO", format=file_format, enqueue=True
        )

    return logger


logger = setup_logging()
