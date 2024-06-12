import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import folium_static

import config
from utils import (
    calculate_center_of_mass,
    get_analytical_info,
    load_data,
    load_model,
    logger,
    predict_fire_station,
    prepare_data,
    prepare_heatmap_data,
    train_model,
)


def main():
    st.set_page_config(page_title="Fire Station Locator", layout="wide")
    st.title("Оптимальные места для пожарных частей")

    data = load_data(extended=True)
    if data is not None:
        X, y, data_prepared = prepare_data(data)
        model = load_model()  # Загружаем модель
        if model is None:
            model = train_model(X, y)  # Обучаем модель, если она не загружена
        heatmap_data = prepare_heatmap_data(data_prepared)
        global_avg_brightness = data_prepared["brightness"].mean()
    else:
        X, y, model, heatmap_data, global_avg_brightness = None, None, None, None, None

    if model is not None and heatmap_data is not None:
        with st.sidebar:
            st.header("Параметры анализа")
            city = st.selectbox("Выберите город", list(config.CITIES.keys()))
            selected_coord = config.CITIES[city]
            st.write(f"Вы выбрали: {city} ({selected_coord[0]}, {selected_coord[1]})")

            click_lat = st.number_input("Широта", value=selected_coord[0])
            click_lon = st.number_input("Долгота", value=selected_coord[1])
            radius = st.slider(
                "Выберите радиус интересующий зоны(км)", min_value=10, max_value=100, value=50
            )

        st.write("Кликните на карту, чтобы выбрать точку для анализа")
        map_center = selected_coord
        mymap = folium.Map(location=map_center, zoom_start=10)

        HeatMap(heatmap_data, radius=10).add_to(mymap)

        # Добавляем функциональность клика на карту
        def add_marker_click(map_object):
            map_object.add_child(folium.LatLngPopup())

        add_marker_click(mymap)
        folium_static(mymap)

        # Обработка клика на карте
        if "last_clicked" in st.session_state:
            click_lat, click_lon = map(
                float, st.session_state["last_clicked"].split(",")
            )

        st.session_state["last_clicked"] = st.text_input(
            "Координаты клика (широта, долгота)", f"{click_lat}, {click_lon}"
        )

        if st.button("Проанализировать выбранную точку"):
            click_lat, click_lon = map(
                float, st.session_state["last_clicked"].split(",")
            )
            proba = predict_fire_station(model, click_lat, click_lon)
            num_fires, avg_brightness, nearby_fires, monthly_stats = (
                get_analytical_info(
                    data_prepared, click_lat, click_lon, threshold_distance=radius
                )
            )
            center_lat, center_lon = calculate_center_of_mass(
                data_prepared, click_lat, click_lon, threshold_distance=radius
            )

            st.session_state["analysis"] = {
                "proba": proba,
                "num_fires": num_fires,
                "avg_brightness": avg_brightness,
                "global_avg_brightness": global_avg_brightness,
                "center_lat": center_lat,
                "center_lon": center_lon,
                "nearby_fires": nearby_fires,
                "monthly_stats": monthly_stats,
            }

        if "analysis" in st.session_state:
            analysis = st.session_state["analysis"]
            proba = analysis["proba"]
            num_fires = analysis["num_fires"]
            avg_brightness = analysis["avg_brightness"]
            global_avg_brightness = analysis["global_avg_brightness"]
            center_lat = analysis["center_lat"]
            center_lon = analysis["center_lon"]
            nearby_fires = analysis["nearby_fires"]
            monthly_stats = analysis["monthly_stats"]

            st.header("Результаты анализа")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Основные параметры")
                st.metric(
                    label="Количество пожаров вблизи (в радиусе 50 км)", value=num_fires
                )
                st.metric(
                    label="Средняя яркость пожаров вблизи",
                    value=f"{avg_brightness:.2f}",
                )
                st.metric(
                    label="Глобальная средняя яркость пожаров",
                    value=f"{global_avg_brightness:.2f}",
                )
                if center_lat and center_lon:
                    st.metric(
                        label="Центр масс пожаров",
                        value=f"({center_lat:.2f}, {center_lon:.2f})",
                    )

            with col2:
                st.subheader("Рекомендация")
                recommendation = "Установка пожарной станции не требуется"
                reason = "Низкая вероятность пожара на основе исторических данных."
                if proba > 0.5 or (
                    abs(click_lat - center_lat) < 0.5
                    and abs(click_lon - center_lon) < 0.5
                ):
                    recommendation = "Рекомендуется установить пожарную станцию"
                    reason = "Высокая вероятность пожара на основе исторических данных или близость к центру масс пожаров."
                # st.write(
                #     f"Оптимальность установки пожарной станции: {proba:.2f}"
                # )
                st.write(f"Причина: {reason}")
                if recommendation.startswith("Рекомендуется"):
                    st.success(recommendation)
                else:
                    st.error(recommendation)
                if avg_brightness > global_avg_brightness:
                    brightness_context = "выше глобальной средней яркости, что указывает на интенсивные пожары"
                else:
                    brightness_context = "ниже глобальной средней яркости, что указывает на менее интенсивные пожары"
                st.write(
                    f"- Средняя яркость пожаров вблизи: {avg_brightness:.2f} ({brightness_context})"
                )

            st.subheader("Карта с результатами анализа")
            mymap = folium.Map(location=[click_lat, click_lon], zoom_start=10)
            HeatMap(heatmap_data, radius=10).add_to(mymap)
            folium.Marker(
                location=[click_lat, click_lon],
                icon=folium.Icon(color="red", icon="info-sign"),
                popup="Выбранная точка",
            ).add_to(mymap)
            if center_lat and center_lon:
                folium.Marker(
                    location=[center_lat, center_lon],
                    icon=folium.Icon(color="blue", icon="info-sign"),
                    popup="Центр масс пожаров",
                ).add_to(mymap)
            for _, fire in nearby_fires.iterrows():
                folium.Circle(
                    location=[fire["latitude"], fire["longitude"]],
                    radius=100,
                    color="orange",
                    fill=True,
                    fill_color="orange",
                ).add_to(mymap)
            folium_static(mymap)

            st.subheader("Статистика по месяцам")
            st.dataframe(monthly_stats)
    else:
        st.error(
            "Нет данных для анализа. Пожалуйста, убедитесь, что данные загружены и извлечены "
            "корректно."
        )
        logger.error("Данные не загружены или обработаны неправильно")


if __name__ == "__main__":
    main()
