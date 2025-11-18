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

    # Основные регистры VL53L1X
    SOFT_RESET = 0x0000
    I2C_SLAVE_DEVICE_ADDRESS = 0x0001
    VHV_CONFIG_INIT = 0x0001
    SYSTEM_INTERRUPT_CLEAR = 0x0086
    SYSTEM_MODE_START = 0x0087
    RESULT_RANGE_STATUS = 0x0089
    RESULT_FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0 = 0x0096
    GPIO_HV_MUX_CTRL = 0x0030
    GPIO_TIO_HV_STATUS = 0x0031
    SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0046

    # Регистры для инициализации
    ALGO_PART_TO_PART_RANGE_OFFSET_MM = 0x001E
    MM_CONFIG_OUTER_OFFSET_MM = 0x0022
    RANGE_CONFIG_VCSEL_PERIOD_A = 0x0060
    RANGE_CONFIG_TIMEOUT_MACROP_A = 0x005E
    RANGE_CONFIG_VCSEL_PERIOD_B = 0x0063
    RANGE_CONFIG_TIMEOUT_MACROP_B = 0x0061
    RANGE_CONFIG_VALID_PHASE_HIGH = 0x0069
    PHASECAL_CONFIG_TIMEOUT_MACROP = 0x004B
    SYSTEM_THRESH_HIGH = 0x0072
    SYSTEM_THRESH_LOW = 0x0074
    DSS_CONFIG_MANUAL_EFFECTIVE_SPADS_SELECT = 0x0054
    DSS_CONFIG_ROI_MODE_CONTROL = 0x004D

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
        """Инициализация I2C соединения и датчика"""
        try:
            self.bus = SMBus(self.i2c_bus)
            print(f"I2C шина {self.i2c_bus} открыта")

            # Проверка присутствия датчика
            try:
                # Попытка чтения ID регистра
                model_id = self.read_word(0x010F)
                if model_id == 0xEACC:
                    print(f"Датчик VL53L1X обнаружен на адресе 0x{self.address:02X}")
                else:
                    print(f"Обнаружен неизвестный датчик: ID=0x{model_id:04X}")

                # Базовая инициализация датчика
                self.sensor_init()
                return True
            except Exception as e:
                print(f"Датчик не найден на адресе 0x{self.address:02X}: {e}")
                return False

        except Exception as e:
            print(f"Ошибка открытия I2C: {e}")
            return False

    def sensor_init(self):
        """Базовая инициализация датчика VL53L1X"""
        print("Инициализация датчика...")

        # Сброс датчика
        self.write_byte(self.SOFT_RESET, 0x00)
        time.sleep(0.001)
        self.write_byte(self.SOFT_RESET, 0x01)
        time.sleep(0.1)

        # Базовые настройки для измерения
        # Установка периода измерения
        self.write_word(self.RANGE_CONFIG_TIMEOUT_MACROP_A, 0x001D)
        self.write_word(self.RANGE_CONFIG_TIMEOUT_MACROP_B, 0x0027)

        # Конфигурация прерывания
        self.write_byte(self.SYSTEM_INTERRUPT_CONFIG_GPIO, 0x01)

        # Очистка прерывания
        self.write_byte(self.SYSTEM_INTERRUPT_CLEAR, 0x01)

        print("Датчик инициализирован")

    def write_byte(self, reg, value):
        """Запись байта в регистр"""
        try:
            # Для 16-битных адресов регистров
            if reg > 0xFF:
                # Разделяем на старший и младший байты адреса
                addr_high = (reg >> 8) & 0xFF
                addr_low = reg & 0xFF
                self.bus.write_i2c_block_data(self.address, addr_high, [addr_low, value])
            else:
                self.bus.write_byte_data(self.address, reg, value)
        except Exception as e:
            pass  # Игнорируем ошибки для упрощения

    def write_word(self, reg, value):
        """Запись 16-битного слова в регистр"""
        try:
            # Разделяем значение на два байта
            high_byte = (value >> 8) & 0xFF
            low_byte = value & 0xFF

            if reg > 0xFF:
                # Для 16-битных адресов
                addr_high = (reg >> 8) & 0xFF
                addr_low = reg & 0xFF
                self.bus.write_i2c_block_data(self.address, addr_high, [addr_low, high_byte, low_byte])
            else:
                # Для 8-битных адресов
                self.bus.write_i2c_block_data(self.address, reg, [high_byte, low_byte])
        except Exception as e:
            pass  # Игнорируем ошибки для упрощения

    def read_byte(self, reg):
        """Чтение байта из регистра"""
        try:
            if reg > 0xFF:
                # Для 16-битных адресов
                addr_high = (reg >> 8) & 0xFF
                addr_low = reg & 0xFF
                self.bus.write_byte_data(self.address, addr_high, addr_low)
                return self.bus.read_byte(self.address)
            else:
                return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            return None

    def read_word(self, reg):
        """Чтение 16-битного слова из регистра"""
        try:
            if reg > 0xFF:
                # Для 16-битных адресов
                addr_high = (reg >> 8) & 0xFF
                addr_low = reg & 0xFF
                self.bus.write_byte_data(self.address, addr_high, addr_low)
                data = self.bus.read_i2c_block_data(self.address, 0, 2)
            else:
                # Для 8-битных адресов
                data = self.bus.read_i2c_block_data(self.address, reg, 2)

            # Объединение в 16-битное значение (big-endian)
            return (data[0] << 8) | data[1]
        except Exception as e:
            return None

    def start_measurement(self):
        """Запуск измерения"""
        # Очистка прерывания перед запуском
        self.write_byte(self.SYSTEM_INTERRUPT_CLEAR, 0x01)
        # Установка режима измерения (0x40 = single shot ranging)
        self.write_byte(self.SYSTEM_MODE_START, 0x40)

    def wait_for_data_ready(self, timeout=0.5):
        """Ожидание готовности данных"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Проверяем статус готовности данных
            status = self.read_byte(self.GPIO_TIO_HV_STATUS)
            if status and (status & 0x01):
                return True
            time.sleep(0.01)
        return False

    def get_distance(self):
        """
        Получение расстояния в миллиметрах

        Returns:
            Расстояние в мм или None при ошибке
        """
        try:
            # Запуск измерения
            self.start_measurement()

            # Ожидание готовности данных
            if not self.wait_for_data_ready():
                return None

            # Чтение статуса измерения
            range_status = self.read_byte(self.RESULT_RANGE_STATUS)

            # Чтение результата расстояния
            distance = self.read_word(self.RESULT_FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0)

            # Очистка прерывания для следующего измерения
            self.write_byte(self.SYSTEM_INTERRUPT_CLEAR, 0x01)

            # Проверка валидности данных
            if distance and distance > 0 and distance < 8190:
                # Проверяем статус (биты 4-7 должны быть 0 для валидного измерения)
                if range_status and ((range_status >> 4) & 0x0F) == 0:
                    return distance

            return None

        except Exception as e:
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