#!/usr/bin/env python3
"""
VL53L1X Advanced Distance Sensor Reader
Расширенная версия с дополнительными функциями
"""

import time
import sys
import argparse
import signal
import json
from datetime import datetime
from collections import deque
import statistics

try:
    import VL53L1X
except ImportError:
    print("Ошибка: Библиотека VL53L1X не установлена.")
    print("Установите её командой: pip3 install vl53l1x")
    sys.exit(1)


class AdvancedVL53L1XReader:
    """Расширенный класс для работы с датчиком VL53L1X"""

    # Константы для режимов измерения
    RANGE_SHORT = 1  # До 1.3 метров, высокая точность
    RANGE_MEDIUM = 2  # До 3 метров, средняя точность
    RANGE_LONG = 3  # До 4 метров, низкая точность

    def __init__(self, i2c_bus=1, i2c_address=0x29, history_size=100):
        """
        Инициализация датчика с расширенными возможностями

        Args:
            i2c_bus: Номер шины I2C
            i2c_address: Адрес датчика на шине I2C
            history_size: Размер буфера для хранения истории измерений
        """
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.sensor = None
        self.history = deque(maxlen=history_size)
        self.start_time = None
        self.measurement_count = 0
        self.error_count = 0
        self.min_distance = float('inf')
        self.max_distance = 0
        self.running = False

    def initialize(self, mode=RANGE_SHORT, timing_budget=20):
        """
        Инициализация датчика с настройками

        Args:
            mode: Режим измерения расстояния
            timing_budget: Время измерения в мс (20-500)
        """
        try:
            print(f"Инициализация VL53L1X...")
            print(f"  I2C шина: {self.i2c_bus}")
            print(f"  I2C адрес: 0x{self.i2c_address:02X}")

            self.sensor = VL53L1X.VL53L1X(i2c_bus=self.i2c_bus, i2c_address=self.i2c_address)
            self.sensor.open()

            # Настройка времени измерения (влияет на точность)
            # Чем больше timing_budget, тем выше точность, но медленнее измерение
            self.sensor.set_timing_budget(timing_budget)

            # Настройка межизмерительного периода
            # Должен быть больше timing_budget
            self.sensor.set_inter_measurement_period(timing_budget + 10)

            # Запуск измерений
            self.sensor.start_ranging(mode)

            mode_names = {
                self.RANGE_SHORT: "Short (до 1.3м)",
                self.RANGE_MEDIUM: "Medium (до 3м)",
                self.RANGE_LONG: "Long (до 4м)"
            }
            print(f"  Режим: {mode_names.get(mode, 'Unknown')}")
            print(f"  Timing Budget: {timing_budget} мс")
            print("Датчик готов к работе!")
            print("-" * 60)

            self.start_time = datetime.now()
            return True

        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            return False

    def read_with_stats(self):
        """
        Чтение расстояния с вычислением статистики

        Returns:
            Словарь с данными измерения и статистикой
        """
        if not self.sensor:
            return None

        try:
            distance = self.sensor.get_distance()
            self.measurement_count += 1

            # Обновление статистики
            if distance > 0:  # Игнорируем нулевые значения
                self.history.append(distance)
                self.min_distance = min(self.min_distance, distance)
                self.max_distance = max(self.max_distance, distance)

            # Вычисление статистики
            stats = {}
            if len(self.history) > 0:
                stats['current'] = distance
                stats['average'] = statistics.mean(self.history)
                stats['median'] = statistics.median(self.history)
                if len(self.history) > 1:
                    stats['std_dev'] = statistics.stdev(self.history)
                else:
                    stats['std_dev'] = 0
                stats['min'] = self.min_distance
                stats['max'] = self.max_distance
                stats['count'] = self.measurement_count
                stats['errors'] = self.error_count

            return stats

        except Exception as e:
            self.error_count += 1
            return None

    def calculate_velocity(self, window_size=5):
        """
        Вычисление скорости изменения расстояния

        Args:
            window_size: Размер окна для вычисления скорости

        Returns:
            Скорость в мм/с или None
        """
        if len(self.history) < window_size:
            return None

        recent = list(self.history)[-window_size:]
        velocities = []

        for i in range(1, len(recent)):
            velocity = recent[i] - recent[i-1]
            velocities.append(velocity)

        return statistics.mean(velocities) if velocities else 0

    def detect_object_state(self, distance):
        """
        Определение состояния объекта на основе расстояния

        Args:
            distance: Текущее расстояние в мм

        Returns:
            Строка с описанием состояния
        """
        if distance < 50:
            return "КРИТИЧЕСКИ БЛИЗКО", "🔴"
        elif distance < 100:
            return "ОЧЕНЬ БЛИЗКО", "🟠"
        elif distance < 300:
            return "БЛИЗКО", "🟡"
        elif distance < 800:
            return "СРЕДНЕ", "🟢"
        elif distance < 1500:
            return "ДАЛЕКО", "🔵"
        else:
            return "ОЧЕНЬ ДАЛЕКО", "⚪"

    def run_with_display_modes(self, mode='standard', interval=0.1):
        """
        Запуск с различными режимами отображения

        Args:
            mode: 'standard', 'detailed', 'compact', 'json'
            interval: Интервал между измерениями
        """
        self.running = True
        print(f"Режим отображения: {mode.upper()}")
        print("Для остановки нажмите Ctrl+C\n")

        try:
            while self.running:
                stats = self.read_with_stats()

                if stats:
                    if mode == 'standard':
                        self.display_standard(stats)
                    elif mode == 'detailed':
                        self.display_detailed(stats)
                    elif mode == 'compact':
                        self.display_compact(stats)
                    elif mode == 'json':
                        self.display_json(stats)

                time.sleep(interval)

        except KeyboardInterrupt:
            self.print_summary()

    def display_standard(self, stats):
        """Стандартное отображение"""
        distance = stats['current']
        state, emoji = self.detect_object_state(distance)
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"[{timestamp}] Расстояние: {distance:4d} мм "
              f"({distance/10:6.1f} см, {distance/1000:5.3f} м) "
              f"{emoji} {state}")

    def display_detailed(self, stats):
        """Детальное отображение со статистикой"""
        distance = stats['current']
        state, emoji = self.detect_object_state(distance)
        velocity = self.calculate_velocity()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(f"\n[{timestamp}] Измерение #{stats['count']}")
        print(f"  Текущее:  {distance:4d} мм {emoji} {state}")
        print(f"  Среднее:  {stats['average']:6.1f} мм")
        print(f"  Медиана:  {stats['median']:6.1f} мм")
        print(f"  Ст.откл.: {stats['std_dev']:6.1f} мм")
        print(f"  Мин/Макс: {stats['min']:4d}/{stats['max']:4d} мм")

        if velocity is not None:
            direction = "приближается" if velocity < 0 else "удаляется" if velocity > 0 else "неподвижен"
            print(f"  Скорость: {abs(velocity):6.1f} мм/изм ({direction})")

    def display_compact(self, stats):
        """Компактное отображение в одну строку"""
        d = stats['current']
        avg = stats['average']
        state, emoji = self.detect_object_state(d)
        print(f"#{stats['count']:5d} | {d:4d}mm | Avg:{avg:6.1f}mm | {emoji} {state}")

    def display_json(self, stats):
        """Вывод в формате JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'measurement': stats['count'],
            'distance_mm': stats['current'],
            'average_mm': round(stats['average'], 1),
            'std_dev': round(stats['std_dev'], 1),
            'min_mm': stats['min'],
            'max_mm': stats['max']
        }
        print(json.dumps(data))

    def print_summary(self):
        """Вывод итоговой статистики"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        else:
            duration = 0

        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        print(f"Время работы:        {duration:.1f} сек")
        print(f"Всего измерений:     {self.measurement_count}")
        print(f"Ошибок:              {self.error_count}")

        if self.measurement_count > 0:
            success_rate = ((self.measurement_count - self.error_count) / self.measurement_count) * 100
            print(f"Успешность:          {success_rate:.1f}%")
            print(f"Частота измерений:   {self.measurement_count/duration:.1f} Гц")

        if len(self.history) > 0:
            print(f"\nСтатистика расстояний:")
            print(f"  Минимум:           {self.min_distance} мм")
            print(f"  Максимум:          {self.max_distance} мм")
            print(f"  Среднее:           {statistics.mean(self.history):.1f} мм")
            print(f"  Медиана:           {statistics.median(self.history):.1f} мм")
            if len(self.history) > 1:
                print(f"  Ст. отклонение:    {statistics.stdev(self.history):.1f} мм")

    def cleanup(self):
        """Остановка датчика и очистка ресурсов"""
        self.running = False
        if self.sensor:
            try:
                self.sensor.stop_ranging()
                self.sensor.close()
                print("\nДатчик остановлен")
            except Exception as e:
                print(f"Ошибка при остановке: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\nПолучен сигнал завершения...")
    sys.exit(0)


def main():
    """Главная функция с аргументами командной строки"""
    parser = argparse.ArgumentParser(description='VL53L1X Distance Sensor Reader')

    parser.add_argument('--bus', type=int, default=1,
                       help='I2C bus number (default: 1)')
    parser.add_argument('--address', type=lambda x: int(x, 0), default=0x29,
                       help='I2C address (default: 0x29)')
    parser.add_argument('--mode', type=int, choices=[1, 2, 3], default=1,
                       help='Range mode: 1=Short, 2=Medium, 3=Long (default: 1)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Measurement interval in seconds (default: 0.1)')
    parser.add_argument('--display', choices=['standard', 'detailed', 'compact', 'json'],
                       default='standard', help='Display mode (default: standard)')
    parser.add_argument('--timing', type=int, default=20,
                       help='Timing budget in ms, 20-500 (default: 20)')
    parser.add_argument('--history', type=int, default=100,
                       help='History buffer size (default: 100)')

    args = parser.parse_args()

    # Установка обработчика сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("VL53L1X Advanced Distance Sensor Reader")
    print("=" * 60)

    # Создание и инициализация датчика
    reader = AdvancedVL53L1XReader(
        i2c_bus=args.bus,
        i2c_address=args.address,
        history_size=args.history
    )

    if not reader.initialize(mode=args.mode, timing_budget=args.timing):
        sys.exit(1)

    try:
        # Запуск измерений
        reader.run_with_display_modes(
            mode=args.display,
            interval=args.interval
        )
    finally:
        reader.cleanup()


if __name__ == "__main__":
    main()