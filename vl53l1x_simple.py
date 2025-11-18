#!/usr/bin/env python3
"""
VL53L1X Simple I2C Reader - минималистичная версия без сложных зависимостей
Работает напрямую с I2C через smbus2
"""

import time
import sys
from datetime import datetime

try:
    from smbus2 import SMBus
except ImportError:
    print("Ошибка: Библиотека smbus2 не установлена.")
    print("Установите её командой: pip3 install smbus2")
    sys.exit(1)


class VL53L1XSimple:
    """Простой класс для работы с VL53L1X через I2C"""

    # I2C адреса и регистры VL53L1X
    DEFAULT_ADDRESS = 0x29

    # Основные регистры
    SYSTEM__MODE_START = 0x87
    RESULT__RANGE_STATUS = 0x89
    RESULT__FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0 = 0x96
    SYSTEM__INTERRUPT_CLEAR = 0x86
    PHASECAL_CONFIG__TIMEOUT_MACROP = 0x8F
    RANGE_CONFIG__TIMEOUT_MACROP_A_HI = 0x5E
    RANGE_CONFIG__TIMEOUT_MACROP_A_LO = 0x5F
    RANGE_CONFIG__TIMEOUT_MACROP_B_HI = 0x60
    RANGE_CONFIG__TIMEOUT_MACROP_B_LO = 0x61
    RANGE_CONFIG__VCSEL_PERIOD_A = 0x62
    RANGE_CONFIG__VCSEL_PERIOD_B = 0x63

    def __init__(self, i2c_bus=1, address=DEFAULT_ADDRESS):
        """
        Инициализация датчика

        Args:
            i2c_bus: Номер шины I2C (обычно 1 для Raspberry Pi)
            address: I2C адрес датчика (по умолчанию 0x29)
        """
        self.bus = None
        self.address = address
        self.i2c_bus = i2c_bus

    def init(self):
        """Инициализация I2C соединения"""
        try:
            self.bus = SMBus(self.i2c_bus)
            print(f"I2C шина {self.i2c_bus} открыта")

            # Проверка присутствия датчика
            try:
                # Попытка чтения из регистра
                self.bus.read_byte_data(self.address, 0x00)
                print(f"Датчик обнаружен на адресе 0x{self.address:02X}")
                return True
            except:
                print(f"Датчик не найден на адресе 0x{self.address:02X}")
                return False

        except Exception as e:
            print(f"Ошибка открытия I2C: {e}")
            return False

    def write_byte(self, reg, value):
        """Запись байта в регистр"""
        try:
            self.bus.write_byte_data(self.address, reg, value)
        except Exception as e:
            print(f"Ошибка записи в регистр 0x{reg:02X}: {e}")

    def read_byte(self, reg):
        """Чтение байта из регистра"""
        try:
            return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            print(f"Ошибка чтения из регистра 0x{reg:02X}: {e}")
            return None

    def read_word(self, reg):
        """Чтение 16-битного слова из регистра"""
        try:
            # Чтение двух байтов
            data = self.bus.read_i2c_block_data(self.address, reg, 2)
            # Объединение в 16-битное значение (big-endian)
            return (data[0] << 8) | data[1]
        except Exception as e:
            print(f"Ошибка чтения слова из регистра 0x{reg:02X}: {e}")
            return None

    def start_measurement(self):
        """Запуск измерения"""
        # Установка режима измерения (0x40 = single shot)
        self.write_byte(self.SYSTEM__MODE_START, 0x40)

    def get_distance(self):
        """
        Получение расстояния в миллиметрах

        Returns:
            Расстояние в мм или None при ошибке
        """
        try:
            # Запуск измерения
            self.start_measurement()

            # Ожидание готовности данных (простой метод)
            time.sleep(0.05)  # 50мс обычно достаточно

            # Чтение результата
            distance = self.read_word(self.RESULT__FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0)

            # Очистка прерывания для следующего измерения
            self.write_byte(self.SYSTEM__INTERRUPT_CLEAR, 0x01)

            if distance and distance < 8190:  # Максимальное значение
                return distance
            else:
                return None

        except Exception as e:
            print(f"Ошибка измерения: {e}")
            return None

    def close(self):
        """Закрытие I2C соединения"""
        if self.bus:
            self.bus.close()
            print("I2C соединение закрыто")


def run_simple_sensor():
    """Основная функция для запуска датчика"""

    print("=" * 50)
    print("VL53L1X Simple I2C Reader")
    print("Минималистичная версия без сложных зависимостей")
    print("=" * 50)

    # Создание объекта датчика
    sensor = VL53L1XSimple(i2c_bus=1, address=0x29)

    # Инициализация
    if not sensor.init():
        print("Не удалось инициализировать датчик")
        print("\nПроверьте:")
        print("1. Подключение датчика:")
        print("   VIN → 3.3V (Pin 1)")
        print("   GND → GND (Pin 6)")
        print("   SCL → GPIO3 (Pin 5)")
        print("   SDA → GPIO2 (Pin 3)")
        print("2. Включен ли I2C: sudo raspi-config")
        print("3. Видит ли система датчик: sudo i2cdetect -y 1")
        sys.exit(1)

    print("\nНачало измерений...")
    print("Для остановки нажмите Ctrl+C")
    print("-" * 50)

    measurement_count = 0
    error_count = 0
    last_distance = None

    try:
        while True:
            # Получение расстояния
            distance = sensor.get_distance()

            if distance is not None:
                measurement_count += 1

                # Форматирование вывода
                timestamp = datetime.now().strftime("%H:%M:%S")
                distance_cm = distance / 10.0
                distance_m = distance / 1000.0

                output = f"[{timestamp}] #{measurement_count:4d}: "
                output += f"{distance:4d} мм | {distance_cm:6.1f} см | {distance_m:5.3f} м"

                # Визуальный индикатор
                if distance < 100:
                    output += " [!!!] ОЧЕНЬ БЛИЗКО"
                elif distance < 300:
                    output += " [!!] Близко"
                elif distance < 1000:
                    output += " [!] Средне"
                else:
                    output += " [ ] Далеко"

                # Показ изменения
                if last_distance is not None:
                    diff = distance - last_distance
                    if abs(diff) > 5:
                        if diff > 0:
                            output += f" ↑{diff}"
                        else:
                            output += f" ↓{abs(diff)}"

                print(output)
                last_distance = distance
            else:
                error_count += 1
                if error_count % 10 == 0:
                    print(f"Ошибки чтения: {error_count}")

            # Задержка между измерениями
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print("Остановка измерений")
        print(f"Всего измерений: {measurement_count}")
        print(f"Ошибок: {error_count}")
        if measurement_count > 0:
            print(f"Успешность: {(measurement_count/(measurement_count+error_count)*100):.1f}%")

    finally:
        sensor.close()


if __name__ == "__main__":
    # Проверка прав доступа
    import os
    if os.geteuid() != 0:
        print("Внимание: Может потребоваться запуск с sudo для доступа к I2C")

    run_simple_sensor()