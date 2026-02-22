import sys
import json
import os
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QMessageBox, QInputDialog, QMenu, QHBoxLayout)
from PyQt6.QtCore import QTimer, Qt, QPoint, QDateTime, QSize
from PyQt6.QtGui import QFont, QPixmap, QAction, QCursor
from io import BytesIO

class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Файл настроек
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.load_config()

        # Настройка окна
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.old_pos = None

        # Интерфейс
        self.init_ui()
        
        # Таймеры
        self.timer_time = QTimer()
        self.timer_time.timeout.connect(self.update_time)
        self.timer_time.start(1000)

        self.timer_weather = QTimer()
        self.timer_weather.timeout.connect(self.update_weather)
        self.timer_weather.start(600000) # 10 минут

    def load_config(self):
        default_config = {
            "city": "Moscow",
            "pos": [100, 100],
            "openweathermap_key": "",
            "openrouter_key": ""
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(5)
        
        # Стили (Glassmorphism)
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: rgba(25, 25, 25, 210);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 20px;
            }
            QLabel {
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                background: transparent;
            }
            QLabel#TimeLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
            }
            QLabel#DateLabel {
                color: #AAAAAA;
                font-size: 11px;
                margin-top: -5px;
            }
            QLabel#WeatherLabel {
                color: #4CC9FE;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#AiLabel {
                color: #ADFF2F;
                font-size: 10px;
                font-style: italic;
            }
        """)

        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.container_layout = QVBoxLayout(self.container)

        # Время и Дата
        self.label_time = QLabel("00:00:00")
        self.label_time.setObjectName("TimeLabel")
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_date = QLabel("Загрузка...")
        self.label_date.setObjectName("DateLabel")
        self.label_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Погода (Иконка + Текст)
        self.weather_layout = QHBoxLayout()
        self.label_icon = QLabel()
        self.label_icon.setFixedSize(40, 40)
        
        self.label_weather = QLabel("Загрузка...")
        self.label_weather.setObjectName("WeatherLabel")
        self.label_weather.setWordWrap(True)

        self.weather_layout.addWidget(self.label_icon)
        self.weather_layout.addWidget(self.label_weather)

        # AI Совет
        self.label_ai = QLabel("Жду погоду...")
        self.label_ai.setObjectName("AiLabel")
        self.label_ai.setWordWrap(True)
        self.label_ai.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Прогноз (Горизонтальный блок)
        self.forecast_container = QWidget()
        self.forecast_layout = QHBoxLayout(self.forecast_container)
        self.forecast_layout.setContentsMargins(0, 5, 0, 0)
        self.forecast_items = [] # Будем хранить тут (icon, temp, time)
        
        for _ in range(3):
            item_layout = QVBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(30, 30)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            temp_lbl = QLabel("--°C")
            temp_lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
            temp_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            time_lbl = QLabel("00:00")
            time_lbl.setStyleSheet("font-size: 8px; color: #888;")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            item_layout.addWidget(time_lbl)
            item_layout.addWidget(icon_lbl)
            item_layout.addWidget(temp_lbl)
            self.forecast_layout.addLayout(item_layout)
            self.forecast_items.append({"icon": icon_lbl, "temp": temp_lbl, "time": time_lbl})

        self.container_layout.addWidget(self.label_time)
        self.container_layout.addWidget(self.label_date)
        self.container_layout.addLayout(self.weather_layout)
        self.container_layout.addWidget(self.label_ai)
        self.container_layout.addWidget(self.forecast_container)
        
        self.main_layout.addWidget(self.container)
        self.setLayout(self.main_layout)

        # Восстановление позиции
        x, y = self.config.get("pos", [100, 100])
        self.setGeometry(x, y, 220, 240)
        self.setFixedSize(220, 260)

        self.update_time()
        self.update_weather()

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.label_time.setText(current_time.toString("HH:mm:ss"))
        self.label_date.setText(current_time.toString("dd MMMM yyyy").lower())

    def update_weather(self):
        city = self.config.get("city", "Moscow")
        api_key = self.config.get("openweathermap_key", "")
        if not api_key:
            self.label_weather.setText("Введите OpenWeather API Key")
            return
        
        # 1. Текущая погода
        url_now = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        
        try:
            response = requests.get(url_now, timeout=10)
            data = response.json()
            if data.get("cod") == 200:
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"].capitalize()
                icon_code = data["weather"][0]["icon"]
                
                self.label_weather.setText(f"{desc}\n{temp}°C")
                self.load_icon_to_label(self.label_icon, icon_code, 40)
                
                # Запрос к AI (OpenRouter)
                self.get_ai_advice(city, temp, desc)
                
                # 2. Прогноз
                self.update_forecast(city, api_key)
            else:
                self.label_weather.setText("Город не найден")
        except Exception as e:
            self.label_weather.setText("Ошибка сети")

    def update_forecast(self, city, api_key):
        url_fc = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ru"
        try:
            res = requests.get(url_fc, timeout=10)
            data = res.json()
            if data.get("cod") == "200":
                # Берем следующие 3 записи (каждые 3 часа)
                for i in range(3):
                    forecast_data = data["list"][i+1] # i+1 потому что первый - это почти текущее время
                    temp = round(forecast_data["main"]["temp"])
                    icon_code = forecast_data["weather"][0]["icon"]
                    time_str = forecast_data["dt_txt"].split(" ")[1][:5] # только HH:mm
                    
                    self.forecast_items[i]["temp"].setText(f"{temp}°C")
                    self.forecast_items[i]["time"].setText(time_str)
                    self.load_icon_to_label(self.forecast_items[i]["icon"], icon_code, 30)
        except:
            pass

    def load_icon_to_label(self, label, icon_code, size):
        try:
            url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            res = requests.get(url, timeout=5)
            pixmap = QPixmap()
            pixmap.loadFromData(res.content)
            label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except:
            pass

    def get_ai_advice(self, city, temp, desc):
        key = self.config.get("openrouter_key", "")
        if not key:
            self.label_ai.setText("Введите OpenRouter API Key")
            return

        self.label_ai.setText("ИИ думает...")
        
        prompt = f"Погода в {city}: {desc}, {temp} градусов. Дай очень короткий совет (10 слов максимум), что надеть или взять с собой. Без приветствий."
        
        try:
            # Используем бесплатную модель для примера
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "google/gemini-2.0-flash-001", 
                    "messages": [{"role": "user", "content": prompt}]
                }),
                timeout=15
            )
            data = response.json()
            advice = data['choices'][0]['message']['content'].strip()
            self.label_ai.setText(f"Совет: {advice}")
        except Exception as e:
            print(f"OpenRouter error: {e}")
            self.label_ai.setText("ИИ недоступен")

    # --- Настройки и Контекстное меню ---
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #444; }")
        
        change_city_action = QAction("📍 Изменить город", self)
        change_city_action.triggered.connect(self.change_city)
        
        set_openweather_key_action = QAction("🔑 Ввести OpenWeather Key", self)
        set_openweather_key_action.triggered.connect(self.set_openweathermap_key)
        
        set_key_action = QAction("🔑 Ввести OpenRouter Key", self)
        set_key_action.triggered.connect(self.set_api_key)
        
        refresh_action = QAction("🔄 Обновить всё", self)
        refresh_action.triggered.connect(self.update_weather)
        
        exit_action = QAction("❌ Выход", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(change_city_action)
        menu.addAction(set_openweather_key_action)
        menu.addAction(set_key_action)
        menu.addSeparator()
        menu.addAction(refresh_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        menu.exec(event.globalPos())

    def change_city(self):
        new_city, ok = QInputDialog.getText(self, "Город", "Введите город:", text=self.config["city"])
        if ok and new_city.strip():
            self.config["city"] = new_city.strip()
            self.save_config()
            self.update_weather()

    def set_api_key(self):
        key, ok = QInputDialog.getText(self, "API Key", "OpenRouter API Key:", text=self.config.get("openrouter_key", ""))
        if ok:
            self.config["openrouter_key"] = key.strip()
            self.save_config()
            self.update_weather()

    def set_openweathermap_key(self):
        key, ok = QInputDialog.getText(self, "API Key", "OpenWeather API Key:", text=self.config.get("openweathermap_key", ""))
        if ok:
            self.config["openweathermap_key"] = key.strip()
            self.save_config()
            self.update_weather()

    # --- Перетаскивание ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
            
            # Сохраняем позицию
            self.config["pos"] = [self.x(), self.y()]
            self.save_config()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = InfoWidget()
    widget.show()
    sys.exit(app.exec())