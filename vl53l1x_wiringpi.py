#!/usr/bin/env python3
"""
VL53L1X Distance Sensor - WiringPi версия
Использует библиотеку wiringPi для работы с I2C
"""

import time
import sys
from datetime import datetime

try:
    import wiringpi
except ImportError:
    print("Ошибка: Библиотека wiringPi не установлена.")
    print("Установите её командами:")
    print("  pip install wiringpi")
    print("или")
    print("  sudo apt install python3-wiringpi")
    sys.exit(1)


class VL53L1XWiringPi:
    """Драйвер VL53L1X на основе WiringPi"""

    # I2C адрес датчика
    DEFAULT_ADDRESS = 0x29

    # Основные регистры VL53L1X (16-битные адреса)
    SOFT_RESET = 0x0000
    FIRMWARE_SYSTEM_STATUS = 0x0010
    IDENTIFICATION_MODEL_ID = 0x010F

    # Регистры управления
    SYSTEM_INTERRUPT_CLEAR = 0x0086
    SYSTEM_MODE_START = 0x0087
    SYSTEM_SEQUENCE_CONFIG = 0x0001

    # Регистры статуса
    GPIO_TIO_HV_STATUS = 0x0031
    RESULT_RANGE_STATUS = 0x0089
    RESULT_FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0 = 0x0096

    # Регистры конфигурации
    RANGE_CONFIG_VCSEL_PERIOD_A = 0x0060
    RANGE_CONFIG_VCSEL_PERIOD_B = 0x0063
    RANGE_CONFIG_TIMEOUT_MACROP_A = 0x005E
    RANGE_CONFIG_TIMEOUT_MACROP_B = 0x0061
    RANGE_CONFIG_VALID_PHASE_HIGH = 0x0069
    SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0046

    # Настройки дальности
    SD_CONFIG_WOI_SD0 = 0x0078
    SD_CONFIG_WOI_SD1 = 0x007A
    SD_CONFIG_INITIAL_PHASE_SD0 = 0x007C
    SD_CONFIG_INITIAL_PHASE_SD1 = 0x007E

    def __init__(self, i2c_bus=1, address=DEFAULT_ADDRESS):
        """
        Инициализация датчика

        Args:
            i2c_bus: Номер шины I2C (обычно 1 для Raspberry Pi)
            address: I2C адрес датчика
        """
        self.address = address
        self.i2c_bus = i2c_bus
        self.i2c_handle = None

    def open(self):
        """Открытие I2C соединения через WiringPi"""
        try:
            # Инициализация WiringPi
            wiringpi.wiringPiSetup()

            # Открываем I2C устройство
            self.i2c_handle = wiringpi.wiringPiI2CSetup(self.address)

            if self.i2c_handle < 0:
                print(f"✗ Не удалось открыть I2C устройство на адресе 0x{self.address:02X}")
                return False

            print(f"✓ I2C устройство открыто (handle: {self.i2c_handle})")

            # Проверка ID датчика
            model_id = self.read_reg16(self.IDENTIFICATION_MODEL_ID)
            if model_id == 0xEACC:
                print(f"✓ Датчик VL53L1X обнаружен (ID: 0x{model_id:04X})")
                return True
            else:
                print(f"⚠ Неизвестный датчик (ID: 0x{model_id:04X})")
                return False

        except Exception as e:
            print(f"✗ Ошибка открытия I2C: {e}")
            return False

    def write_reg8(self, reg, value):
        """Запись 8-битного значения в 16-битный регистр"""
        try:
            # Для 16-битного адреса регистра
            # Сначала записываем старший байт адреса
            wiringpi.wiringPiI2CWriteReg8(self.i2c_handle, (reg >> 8) & 0xFF, reg & 0xFF)
            # Затем записываем данные
            wiringpi.wiringPiI2CWrite(self.i2c_handle, value)
        except Exception as e:
            pass

    def write_reg16(self, reg, value):
        """Запись 16-битного значения в 16-битный регистр"""
        try:
            # Записываем адрес
            wiringpi.wiringPiI2CWriteReg8(self.i2c_handle, (reg >> 8) & 0xFF, reg & 0xFF)
            # Записываем данные (big-endian)
            wiringpi.wiringPiI2CWrite(self.i2c_handle, (value >> 8) & 0xFF)
            wiringpi.wiringPiI2CWrite(self.i2c_handle, value & 0xFF)
        except Exception as e:
            pass

    def read_reg8(self, reg):
        """Чтение 8-битного значения из 16-битного регистра"""
        try:
            # Записываем адрес регистра
            wiringpi.wiringPiI2CWriteReg8(self.i2c_handle, (reg >> 8) & 0xFF, reg & 0xFF)
            # Читаем данные
            return wiringpi.wiringPiI2CRead(self.i2c_handle) & 0xFF
        except Exception as e:
            return 0

    def read_reg16(self, reg):
        """Чтение 16-битного значения из 16-битного регистра"""
        try:
            # Записываем адрес регистра
            wiringpi.wiringPiI2CWriteReg8(self.i2c_handle, (reg >> 8) & 0xFF, reg & 0xFF)
            # Читаем 2 байта
            high = wiringpi.wiringPiI2CRead(self.i2c_handle) & 0xFF
            low = wiringpi.wiringPiI2CRead(self.i2c_handle) & 0xFF
            return (high << 8) | low
        except Exception as e:
            return 0

    def init_sensor(self):
        """Инициализация датчика VL53L1X"""
        print("Инициализация датчика...")

        # Программный сброс
        self.write_reg8(self.SOFT_RESET, 0x00)
        time.sleep(0.01)
        self.write_reg8(self.SOFT_RESET, 0x01)
        time.sleep(0.01)

        # Ждем загрузки прошивки
        print("Ожидание загрузки прошивки...")
        for i in range(100):
            status = self.read_reg8(self.FIRMWARE_SYSTEM_STATUS)
            if status & 0x01:
                print(f"✓ Прошивка загружена (попытка {i+1})")
                break
            time.sleep(0.01)
        else:
            print("⚠ Таймаут загрузки прошивки")

        # Базовая конфигурация
        # Настройки VCSEL (лазера)
        self.write_reg8(self.RANGE_CONFIG_VCSEL_PERIOD_A, 0x09)
        self.write_reg8(self.RANGE_CONFIG_VCSEL_PERIOD_B, 0x0D)

        # Настройки валидности фазы
        self.write_reg8(self.RANGE_CONFIG_VALID_PHASE_HIGH, 0xC8)

        # Настройки окна детектирования
        self.write_reg16(self.SD_CONFIG_WOI_SD0, 0x0001)
        self.write_reg16(self.SD_CONFIG_WOI_SD1, 0x0001)
        self.write_reg8(self.SD_CONFIG_INITIAL_PHASE_SD0, 0x00)
        self.write_reg8(self.SD_CONFIG_INITIAL_PHASE_SD1, 0x00)

        # Timing budget (время измерения)
        self.write_reg16(self.RANGE_CONFIG_TIMEOUT_MACROP_A, 0x00D6)
        self.write_reg16(self.RANGE_CONFIG_TIMEOUT_MACROP_B, 0x00D6)

        # Настройка прерываний
        self.write_reg8(self.SYSTEM_INTERRUPT_CONFIG_GPIO, 0x01)

        # Очистка прерывания
        self.write_reg8(self.SYSTEM_INTERRUPT_CLEAR, 0x01)

        print("✓ Датчик инициализирован")

    def start_ranging(self):
        """Запуск непрерывных измерений"""
        # Очистка прерывания
        self.write_reg8(self.SYSTEM_INTERRUPT_CLEAR, 0x01)

        # Запуск измерений (0x40 = ranging mode)
        self.write_reg8(self.SYSTEM_MODE_START, 0x40)

        # Небольшая задержка для первого измерения
        time.sleep(0.05)

    def stop_ranging(self):
        """Остановка измерений"""
        self.write_reg8(self.SYSTEM_MODE_START, 0x00)

    def get_distance(self):
        """
        Получение расстояния в миллиметрах

        Returns:
            Расстояние в мм или None при ошибке
        """
        try:
            # Проверяем готовность данных
            gpio_status = self.read_reg8(self.GPIO_TIO_HV_STATUS)

            if not (gpio_status & 0x01):
                return None  # Данные не готовы

            # Читаем статус измерения
            range_status = self.read_reg8(self.RESULT_RANGE_STATUS)

            # Читаем результат измерения
            distance = self.read_reg16(self.RESULT_FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0)

            # Очищаем прерывание для следующего измерения
            self.write_reg8(self.SYSTEM_INTERRUPT_CLEAR, 0x01)

            # Проверка валидности
            if distance > 0 and distance < 8000:
                # Проверяем статус (биты 4-7 должны быть 0 для валидного измерения)
                if (range_status >> 4) & 0x0F == 0:
                    return distance

            return None

        except Exception as e:
            return None

    def close(self):
        """Закрытие соединения"""
        if self.i2c_handle is not None:
            self.stop_ranging()
            print("✓ Датчик остановлен")


def main():
    print("=" * 50)
    print("VL53L1X Distance Sensor - WiringPi версия")
    print("=" * 50)

    # Создаем объект датчика
    sensor = VL53L1XWiringPi(i2c_bus=1, address=0x29)

    # Открываем соединение
    if not sensor.open():
        print("\n⚠ Проблемы с подключением датчика!")
        print("\nПроверьте:")
        print("1. Подключение:")
        print("   VIN → 3.3V (Pin 1)")
        print("   GND → GND (Pin 6)")
        print("   SCL → GPIO3/SCL (Pin 5)")
        print("   SDA → GPIO2/SDA (Pin 3)")
        print("\n2. Включен ли I2C:")
        print("   sudo raspi-config")
        print("   Interface Options → I2C → Enable")
        print("\n3. Установлена ли библиотека WiringPi:")
        print("   pip install wiringpi")
        sys.exit(1)

    # Инициализируем датчик
    sensor.init_sensor()

    # Запускаем измерения
    sensor.start_ranging()

    print("\nНачало измерений (Ctrl+C для остановки)...")
    print("-" * 50)

    count = 0
    errors = 0
    history = []
    last_distance = 0

    try:
        while True:
            distance = sensor.get_distance()

            if distance is not None:
                count += 1
                history.append(distance)

                # Храним последние 10 измерений
                if len(history) > 10:
                    history.pop(0)

                # Вычисляем среднее
                avg = sum(history) / len(history)

                # Изменение
                delta = distance - last_distance if last_distance > 0 else 0
                delta_str = f"Δ{delta:+4d}" if abs(delta) > 5 else "     "

                # Форматированный вывод
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] #{count:4d}: {distance:4d} мм "
                      f"({distance/10:5.1f} см, {distance/1000:5.3f} м) "
                      f"Avg:{avg:6.1f} {delta_str}", end="")

                # Визуальная шкала
                bars = min(int(distance / 100), 40)
                print(" |" + "█" * bars)

                # Индикатор близости
                if distance < 100:
                    print("          ⚠️  ОЧЕНЬ БЛИЗКО!")
                elif distance < 300:
                    print("          ⚡ Близко")

                last_distance = distance
            else:
                errors += 1
                if errors % 20 == 0:
                    print(f"⚠ Ожидание данных... (пропусков: {errors})")

            # Частота опроса ~20 Гц
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print("Статистика:")
        print(f"  Измерений: {count}")
        print(f"  Пропусков: {errors}")
        if count > 0:
            print(f"  Успешность: {count/(count+errors)*100:.1f}%")
            if history:
                print(f"  Последнее: {history[-1]} мм")
                print(f"  Среднее: {sum(history)/len(history):.1f} мм")
                print(f"  Мин/Макс: {min(history)}/{max(history)} мм")

    finally:
        sensor.close()
        print("\n✓ Программа завершена")


if __name__ == "__main__":
    main()