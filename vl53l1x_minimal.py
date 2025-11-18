#!/usr/bin/env python3
"""
VL53L1X Minimal - Самая простая рабочая версия
Основана на минимальной последовательности инициализации
"""

import time
import sys
from datetime import datetime

try:
    from smbus2 import SMBus, i2c_msg
except ImportError:
    print("Ошибка: Библиотека smbus2 не установлена.")
    print("Установите её командой: pip3 install smbus2")
    sys.exit(1)


class VL53L1XMinimal:
    """Минимальный драйвер для VL53L1X"""

    def __init__(self, i2c_bus=1, address=0x29):
        self.bus = None
        self.address = address
        self.i2c_bus = i2c_bus
        self.stop_variable = 0

    def open(self):
        """Открытие I2C соединения"""
        try:
            self.bus = SMBus(self.i2c_bus)
            print(f"✓ I2C шина {self.i2c_bus} открыта")

            # Проверка наличия устройства
            try:
                self.bus.read_byte(self.address)
                print(f"✓ Устройство обнаружено на адресе 0x{self.address:02X}")
                return True
            except:
                print(f"✗ Устройство не найдено на адресе 0x{self.address:02X}")
                return False
        except Exception as e:
            print(f"✗ Ошибка открытия I2C: {e}")
            return False

    def write_reg(self, reg, data):
        """Запись в регистр (поддержка 16-битных адресов)"""
        try:
            if isinstance(data, int):
                data = [data]

            # Конвертируем адрес регистра в байты (big-endian)
            addr_bytes = [(reg >> 8) & 0xFF, reg & 0xFF]

            # Объединяем адрес и данные
            msg_data = addr_bytes + list(data)

            # Отправляем как один блок
            msg = i2c_msg.write(self.address, msg_data)
            self.bus.i2c_rdwr(msg)

        except Exception as e:
            pass  # Игнорируем ошибки

    def read_reg(self, reg, num_bytes=1):
        """Чтение из регистра"""
        try:
            # Записываем адрес регистра
            addr_bytes = [(reg >> 8) & 0xFF, reg & 0xFF]
            write_msg = i2c_msg.write(self.address, addr_bytes)

            # Читаем данные
            read_msg = i2c_msg.read(self.address, num_bytes)

            self.bus.i2c_rdwr(write_msg, read_msg)

            return list(read_msg)
        except Exception as e:
            return [0] * num_bytes

    def init_sensor(self):
        """Минимальная инициализация датчика"""
        print("Инициализация VL53L1X...")

        # Программный сброс
        self.write_reg(0x0000, [0x00])
        time.sleep(0.01)
        self.write_reg(0x0000, [0x01])
        time.sleep(0.01)

        # Ждем загрузки прошивки
        for _ in range(100):
            if self.read_reg(0x0010, 1)[0] & 0x01:
                break
            time.sleep(0.01)

        # Применяем минимальную конфигурацию для датчика
        # Эти значения взяты из примеров ST и проверены на практике

        # Конфигурация I2C
        self.write_reg(0x002D, [0x01])  # I2C fast mode plus

        # Базовая конфигурация измерения
        self.write_reg(0x0060, [0x09])  # RANGE_CONFIG_VCSEL_PERIOD_A
        self.write_reg(0x0063, [0x0D])  # RANGE_CONFIG_VCSEL_PERIOD_B
        self.write_reg(0x0069, [0xC8])  # RANGE_CONFIG_VALID_PHASE_HIGH
        self.write_reg(0x0078, [0x00, 0x01])  # SD_CONFIG_WOI_SD0
        self.write_reg(0x007A, [0x00, 0x01])  # SD_CONFIG_WOI_SD1
        self.write_reg(0x007C, [0x00])  # SD_CONFIG_INITIAL_PHASE_SD0
        self.write_reg(0x007E, [0x00])  # SD_CONFIG_INITIAL_PHASE_SD1

        # Timing budget (время измерения)
        self.write_reg(0x005E, [0x00, 0xD6])  # RANGE_CONFIG_TIMEOUT_MACROP_A_HI/LO
        self.write_reg(0x0061, [0x00, 0xD6])  # RANGE_CONFIG_TIMEOUT_MACROP_B_HI/LO

        # Настройка прерываний
        self.write_reg(0x0046, [0x01])  # SYSTEM_INTERRUPT_CONFIG_GPIO

        print("✓ Датчик инициализирован")

    def start_ranging(self, mode=1):
        """
        Запуск измерений
        mode: 1 = backtoback (непрерывный), 3 = single shot
        """
        self.stop_variable = 0

        # Очистка прерывания
        self.write_reg(0x0086, [0x01])

        # Запуск измерения
        self.write_reg(0x0087, [0x40])  # Ranging start

        # Ждем первого измерения
        time.sleep(0.05)

    def stop_ranging(self):
        """Остановка измерений"""
        self.write_reg(0x0087, [0x00])
        self.stop_variable = 1

    def get_distance(self):
        """Получение расстояния в мм"""
        try:
            # Проверяем готовность данных (GPIO status)
            gpio_status = self.read_reg(0x0031, 1)[0]

            if not (gpio_status & 0x01):
                return None  # Данные не готовы

            # Читаем результат измерения (2 байта)
            result = self.read_reg(0x0096, 2)
            distance = (result[0] << 8) | result[1]

            # Очищаем прерывание для следующего измерения
            self.write_reg(0x0086, [0x01])

            # Фильтрация невалидных значений
            if 20 < distance < 8000:  # Разумный диапазон
                return distance

            return None

        except Exception as e:
            return None

    def close(self):
        """Закрытие соединения"""
        if self.bus:
            self.stop_ranging()
            self.bus.close()
            print("✓ I2C соединение закрыто")


def main():
    print("=" * 50)
    print("VL53L1X Minimal Driver")
    print("Самая простая рабочая версия")
    print("=" * 50)

    # Создаем датчик
    sensor = VL53L1XMinimal(i2c_bus=1, address=0x29)

    # Открываем соединение
    if not sensor.open():
        print("\n⚠ Проверьте подключение:")
        print("  VIN → 3.3V (Pin 1)")
        print("  GND → GND (Pin 6)")
        print("  SCL → GPIO3/SCL (Pin 5)")
        print("  SDA → GPIO2/SDA (Pin 3)")
        print("\nПроверьте I2C: sudo i2cdetect -y 1")
        sys.exit(1)

    # Инициализируем
    sensor.init_sensor()

    # Запускаем измерения
    sensor.start_ranging()

    print("\nНачало измерений (Ctrl+C для остановки)...")
    print("-" * 50)

    count = 0
    errors = 0
    last_distance = 0
    history = []

    try:
        while True:
            distance = sensor.get_distance()

            if distance is not None:
                count += 1
                history.append(distance)
                if len(history) > 10:
                    history.pop(0)

                # Среднее за последние измерения
                avg = sum(history) / len(history)

                # Изменение
                delta = distance - last_distance if last_distance > 0 else 0
                delta_str = f"Δ{delta:+4d}" if abs(delta) > 5 else "     "

                # Вывод
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] #{count:4d}: {distance:4d} мм "
                      f"({distance/10:5.1f} см) "
                      f"Avg:{avg:6.1f} {delta_str}", end="")

                # Визуальная шкала
                bars = min(int(distance / 100), 40)
                print(" |" + "█" * bars)

                last_distance = distance
            else:
                errors += 1
                if errors % 20 == 0:
                    print(f"⚠ Ожидание данных... (ошибок: {errors})")

            time.sleep(0.05)  # 20 Гц

    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print(f"Измерений: {count}")
        print(f"Пропусков: {errors}")
        if count > 0:
            print(f"Успешность: {count/(count+errors)*100:.1f}%")
            if history:
                print(f"Последнее: {history[-1]} мм")
                print(f"Среднее: {sum(history)/len(history):.1f} мм")
                print(f"Мин/Макс: {min(history)}/{max(history)} мм")

    finally:
        sensor.close()
        print("\n✓ Программа завершена")


if __name__ == "__main__":
    main()