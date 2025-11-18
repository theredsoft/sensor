#!/usr/bin/env python3
"""
VL53L1X Distance Sensor Reader с использованием библиотеки Adafruit
Альтернативная версия для совместимости с Python 3.13+
"""

import time
import sys
import board
import busio
from datetime import datetime

try:
    import adafruit_vl53l1x
except ImportError:
    print("Ошибка: Библиотека adafruit-circuitpython-vl53l1x не установлена.")
    print("Установите её командой: pip3 install adafruit-circuitpython-vl53l1x")
    sys.exit(1)


class VL53L1XAdafruitReader:
    """Класс для работы с датчиком VL53L1X через Adafruit библиотеку"""

    def __init__(self):
        """Инициализация датчика"""
        self.sensor = None
        self.i2c = None

    def initialize(self):
        """Инициализация и настройка датчика"""
        try:
            print("Инициализация датчика VL53L1X (Adafruit)...")

            # Создание I2C интерфейса
            self.i2c = busio.I2C(board.SCL, board.SDA)

            # Создание объекта датчика
            self.sensor = adafruit_vl53l1x.VL53L1X(self.i2c)

            # Настройка режима измерения
            # distance_mode: 1=Short (1.3m), 2=Long (4m)
            self.sensor.distance_mode = 1

            # timing_budget в мс (16, 20, 33, 50, 100, 200, 500)
            self.sensor.timing_budget = 50

            # Запуск измерений
            self.sensor.start_ranging()

            print("Датчик успешно инициализирован (Adafruit версия)")
            print(f"Режим измерения: {'Short' if self.sensor.distance_mode == 1 else 'Long'}")
            print(f"Timing budget: {self.sensor.timing_budget} мс")
            print("-" * 50)

            return True

        except Exception as e:
            print(f"Ошибка при инициализации датчика: {e}")
            print("Проверьте:")
            print("1. Подключение датчика к Raspberry Pi")
            print("2. Включен ли интерфейс I2C")
            print("3. Правильность адреса датчика")
            return False

    def set_measurement_mode(self, mode='short'):
        """
        Установка режима измерения

        Args:
            mode: 'short' для близких измерений, 'long' для дальних
        """
        if self.sensor:
            if mode == 'short':
                self.sensor.distance_mode = 1
                print("Режим измерения: Short Range (до 1.3м)")
            else:
                self.sensor.distance_mode = 2
                print("Режим измерения: Long Range (до 4м)")

    def read_distance(self):
        """
        Чтение расстояния с датчика

        Returns:
            Расстояние в миллиметрах или None при ошибке
        """
        if not self.sensor:
            return None

        try:
            # Проверка готовности данных
            if self.sensor.data_ready:
                # Чтение расстояния в см и конвертация в мм
                distance_cm = self.sensor.distance
                if distance_cm is not None:
                    distance_mm = int(distance_cm * 10)
                    # Очистка прерывания для следующего измерения
                    self.sensor.clear_interrupt()
                    return distance_mm
            return None
        except Exception as e:
            print(f"Ошибка чтения данных: {e}")
            return None

    def run_continuous(self, interval=0.1, show_timestamp=True):
        """
        Циклическое чтение и вывод данных

        Args:
            interval: Интервал между измерениями в секундах
            show_timestamp: Показывать временную метку
        """
        print(f"Начало циклического чтения данных (интервал: {interval}с)")
        print("Для остановки нажмите Ctrl+C")
        print("-" * 50)

        measurement_count = 0
        error_count = 0
        last_distance = None

        try:
            while True:
                distance = self.read_distance()

                if distance is not None:
                    measurement_count += 1

                    # Форматирование вывода
                    output = f"Измерение #{measurement_count:5d}: "

                    if show_timestamp:
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        output += f"[{timestamp}] "

                    # Конвертация в разные единицы
                    distance_cm = distance / 10.0
                    distance_m = distance / 1000.0

                    output += f"Расстояние: {distance:4d} мм | {distance_cm:6.1f} см | {distance_m:5.3f} м"

                    # Добавление визуального индикатора
                    if distance < 100:
                        output += " ⚠️  ОЧЕНЬ БЛИЗКО!"
                    elif distance < 300:
                        output += " 🟡 Близко"
                    elif distance < 1000:
                        output += " 🟢 Средне"
                    else:
                        output += " 🔵 Далеко"

                    # Показ изменения
                    if last_distance is not None:
                        diff = distance - last_distance
                        if abs(diff) > 10:
                            if diff > 0:
                                output += f" ↗ (+{diff}мм)"
                            else:
                                output += f" ↘ ({diff}мм)"

                    print(output)
                    last_distance = distance
                else:
                    # Ждем готовности данных
                    pass

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n" + "-" * 50)
            print("Остановка измерений...")
            print(f"Статистика:")
            print(f"  Всего измерений: {measurement_count}")
            print(f"  Ошибок чтения: {error_count}")
            if measurement_count > 0:
                print(f"  Средняя частота: {measurement_count / (time.time() - self.start_time):.1f} Гц")

    def cleanup(self):
        """Очистка ресурсов и остановка датчика"""
        if self.sensor:
            try:
                self.sensor.stop_ranging()
                print("Датчик остановлен")
            except Exception as e:
                print(f"Ошибка при остановке датчика: {e}")


def main():
    """Главная функция"""
    print("=" * 50)
    print("VL53L1X Distance Sensor Reader (Adafruit)")
    print("Для Raspberry Pi с Python 3.13+")
    print("=" * 50)

    # Создание объекта для работы с датчиком
    reader = VL53L1XAdafruitReader()

    # Инициализация датчика
    if not reader.initialize():
        sys.exit(1)

    # Запись времени старта
    reader.start_time = time.time()

    try:
        # Запуск циклического чтения
        reader.run_continuous(interval=0.1, show_timestamp=True)

    finally:
        # Очистка ресурсов при завершении
        reader.cleanup()
        print("Программа завершена")


if __name__ == "__main__":
    main()