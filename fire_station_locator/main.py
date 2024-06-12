import glob
import os

import pandas as pd

import config
from utils import logger


def load_data(extended=False):
    logger.info("Начало загрузки данных")

    # Проверка правильности пути к директории
    base_dir = os.path.abspath(os.path.dirname(__file__))
    logger.debug(f"Текущая рабочая директория: {base_dir}")
    extended_dir = os.path.join(base_dir, config.EXTENDED_DATA_DIR)
    logger.debug(f"Полный путь к директории extended: {extended_dir}")

    if not extended:
        all_files = glob.glob(os.path.join(config.DATA_DIR, "*.txt"))
    else:
        logger.debug(f"Путь поиска: {extended_dir}/*.csv")
        all_files = glob.glob(os.path.join(extended_dir, "*.csv"))
        logger.debug(f"Найденные файлы: {all_files}")

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


def main():
    data = load_data(extended=True)
    print(data)


if __name__ == "__main__":
    main()
