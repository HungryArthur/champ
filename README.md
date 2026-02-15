# В РАЗРАБОТКЕ!!!

# Проект: Классификация территорий по степени опасности и сложности эвакуации

## 📌 Описание решения
В рамках чемпионата по компетенции **«Машинное обучение и большие данные»** разработана модель для классификации территорий. Для поддержания актуальности прогнозов организовано непрерывное обучение с использованием **Apache Airflow**. Вся инфраструктура контейнеризована с помощью **Docker**.

## 🏗 Архитектура проекта

Решение построено на микросервисной архитектуре и включает следующие ключевые компоненты:

### 1. 🧠 Модель машинного обучения
*   Классификация участков по уровню риска.
*   Прогнозирование динамики рисков (пожары, затопления).

### 2. ⚙️ API (FastAPI)
Предоставляет REST-интерфейс для взаимодействия:
*   **Оценка риска** по координатам.
*   **Прогноз пожароопасности** и затоплений.
*   **Оценка сложности эвакуации** на период до 10 лет.

### 3. 🗄️ База данных (PostgreSQL)
*   Централизованное хранение входных данных, результатов прогнозов и метаданных моделей.

### 4. 🔄 Оркестрация (Apache Airflow)
*   Автоматизация регулярного переобучения и обновления модели.
*   Обработка вновь поступивших данных.

### 5. 📊 Визуализация (Streamlit)
*   Интерактивный графический интерфейс.
*   Визуализация рисков вдоль заданного пользователем маршрута.

### 💻 Стек технологий

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white)
![Scikit Learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
