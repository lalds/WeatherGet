import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt, QPoint, QDateTime
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtGui import QFont
import requests

class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 1. Настройка окна
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | # Без рамок
            Qt.WindowType.WindowStaysOnTopHint | # Поверх всех окон
            Qt.WindowType.Tool # Не отображать в панели задач (по желанию)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Прозрачный фон
        
        # Переменные для перемещения окна
        self.old_pos = None

        # 2. Интерфейс
        self.init_ui()
        
        
        # 5. Таймеры обновления
        self.timer_time = QTimer()
        self.timer_time.timeout.connect(self.update_time)
        self.timer_time.start(1000) # Обновлять каждую секунду

        self.timer_weather = QTimer()
        self.timer_weather.timeout.connect(self.update_weather)
        self.timer_weather.start(600000) # Погоду обновляем раз в 10 минут

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Стили (CSS-подобный QSS)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 180); /* Полупрозрачный темный фон */
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Метка времени
        self.label_time = QLabel("00:00:00")
        self.label_time.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Сначала определяем город (автоматически)
        detected_city = self.get_my_city()
        
        # 2. Спрашиваем пользователя
        self.current_city = self.ask_about_city(detected_city)

        # Метка даты
        self.label_date = QLabel("Загрузка...")
        self.label_date.setFont(QFont("Arial", 10))
        self.label_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Метка погоды
        self.label_weather = QLabel("Погода: --°C")
        self.label_weather.setFont(QFont("Arial", 12))
        self.label_weather.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label_time)
        layout.addWidget(self.label_date)
        layout.addWidget(self.label_weather)
        
        self.setLayout(layout)
        self.update_time()
        self.update_weather()
        
        # Устанавливаем размер и положение (правый верхний угол)
        self.setGeometry(100, 100, 200, 120)

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.label_time.setText(current_time.toString("HH:mm:ss"))
        self.label_date.setText(current_time.toString("dd MMMM yyyy"))
    
    def ask_about_city(self, city):
        # Передаем None, чтобы окно не наследовало темную тему главного виджета
        msg = QMessageBox(None) 
        msg.setWindowTitle("Настройка города")
        msg.setText(f"Ваш город — {city}?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # Чтобы окно не пряталось за основной виджет
        msg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        ret = msg.exec()

        if ret == QMessageBox.StandardButton.Yes:
            return city
        else:
            # Для ввода текста тоже используем None
            # Это создаст стандартное белое окно Windows
            new_city, ok = QInputDialog.getText(
                None, 
                "Ввод города", 
                "Введите название вашего города:",
                flags=Qt.WindowType.WindowStaysOnTopHint
            )
            
            if ok and new_city.strip():
                return new_city.strip()
            return city

    def get_my_city(self):
        try:
            # Делаем запрос к сервису геолокации
            # timeout=5 нужен, чтобы программа не зависла навсегда, если нет интернета
            response = requests.get("http://ip-api.com/json/", timeout=5).json()

            # Пытаемся достать город. Если не получилось — берем Москву
            city = response.get("city", "Moscow")
            return city
        except Exception as e:
            # Если вообще нет интернета или сайт лежит
            print(f"Ошибка при определении города: {e}")
            return "Moscow" 


    def update_weather(self):
        api_key = "e4a2cdc28404e413911f8e7d8ca9719e"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.current_city}&appid={api_key}&units=metric&lang=ru"
        print(requests.get(url).json())  # Для отладки
        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            print(data)
            if (data["cod"] == 200):
                temp = "Температура: " + str(data["main"]["temp"])
                condition = data["weather"][0]["description"].capitalize()
                self.label_weather.setText(f"{condition}, {temp}°C")
            else:
                self.label_weather.setText("Ошибка получения погоды")
        except Exception as e:
            self.label_weather.setText("Ошибка подключения")
        

    # --- Функции для перетаскивания окна мышкой ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = InfoWidget()
    widget.show()
    sys.exit(app.exec())