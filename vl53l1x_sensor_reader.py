#!/usr/bin/env python3
"""
VL53L1X Distance Sensor Reader for Raspberry Pi 5
Циклическое чтение данных с датчика расстояния VL53L1X и вывод в консоль
"""

import time
import sys
from datetime import datetime

try:
    import VL53L1X
except ImportError:
    print("Ошибка: Библиотека VL53L1X не установлена.")
    print("Установите её командой: pip3 install vl53l1x")
    sys.exit(1)


class VL53L1XReader:
    """Класс для работы с датчиком VL53L1X"""

    def __init__(self, i2c_bus=1, i2c_address=0x29):
        """
        Инициализация датчика

        Args:
            i2c_bus: Номер шины I2C (обычно 1 для Raspberry Pi)
            i2c_address: Адрес датчика на шине I2C (по умолчанию 0x29)
        """
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.sensor = None

    def initialize(self):
        """Инициализация и настройка датчика"""
        try:
            print(f"Инициализация датчика VL53L1X на шине I2C-{self.i2c_bus}, адрес: 0x{self.i2c_address:02X}")

            # Создание объекта датчика
            self.sensor = VL53L1X.VL53L1X(i2c_bus=self.i2c_bus, i2c_address=self.i2c_address)

            # Открытие соединения с датчиком
            self.sensor.open()

            # Запуск измерений
            self.sensor.start_ranging(mode=1)  # mode=1: Short Range, mode=2: Medium Range, mode=3: Long Range

            print("Датчик успешно инициализирован")
            print("Режим измерения: Short Range (до 1.3м)")
            print("-" * 50)

            return True

        except Exception as e:
            print(f"Ошибка при инициализации датчика: {e}")
            print("Проверьте:")
            print("1. Подключение датчика к Raspberry Pi (SDA, SCL, VCC, GND)")
            print("2. Включен ли интерфейс I2C (sudo raspi-config)")
            print("3. Правильность адреса датчика (i2cdetect -y 1)")
            return False

    def set_measurement_mode(self, mode):
        """
        Установка режима измерения

        Args:
            mode: 1 - Short Range (до 1.3м)
                  2 - Medium Range (до 3м)
                  3 - Long Range (до 4м)
        """
        if self.sensor:
            self.sensor.stop_ranging()
            self.sensor.start_ranging(mode)

            mode_names = {1: "Short Range", 2: "Medium Range", 3: "Long Range"}
            print(f"Режим измерения изменён на: {mode_names.get(mode, 'Unknown')}")

    def read_distance(self):
        """
        Чтение расстояния с датчика

        Returns:
            Расстояние в миллиметрах или None при ошибке
        """
        if not self.sensor:
            return None

        try:
            distance_mm = self.sensor.get_distance()
            return distance_mm
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

        try:
            while True:
                distance = self.read_distance()
                measurement_count += 1

                if distance is not None:
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

                    print(output)
                else:
                    error_count += 1
                    print(f"Измерение #{measurement_count:5d}: Ошибка чтения (всего ошибок: {error_count})")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n" + "-" * 50)
            print("Остановка измерений...")
            print(f"Статистика:")
            print(f"  Всего измерений: {measurement_count}")
            print(f"  Ошибок чтения: {error_count}")
            print(f"  Успешных измерений: {measurement_count - error_count}")
            if measurement_count > 0:
                success_rate = ((measurement_count - error_count) / measurement_count) * 100
                print(f"  Процент успешных: {success_rate:.1f}%")

    def cleanup(self):
        """Очистка ресурсов и остановка датчика"""
        if self.sensor:
            try:
                self.sensor.stop_ranging()
                self.sensor.close()
                print("Датчик остановлен и закрыт")
            except Exception as e:
                print(f"Ошибка при остановке датчика: {e}")


def main():
    """Главная функция"""
    print("=" * 50)
    print("VL53L1X Distance Sensor Reader")
    print("Для Raspberry Pi 5")
    print("=" * 50)

    # Создание объекта для работы с датчиком
    reader = VL53L1XReader(i2c_bus=1, i2c_address=0x29)

    # Инициализация датчика
    if not reader.initialize():
        sys.exit(1)

    try:
        # Запуск циклического чтения
        # interval - интервал между измерениями в секундах
        # Можно изменить на нужное значение (например, 0.5 для измерения каждые полсекунды)
        reader.run_continuous(interval=0.1, show_timestamp=True)

    finally:
        # Очистка ресурсов при завершении
        reader.cleanup()
        print("Программа завершена")


if __name__ == "__main__":
    main()