# Raspberry Pi Sensors Collection

Коллекция скриптов для работы с различными датчиками на Raspberry Pi.

## Быстрый старт

```bash
# Клонирование репозитория на Raspberry Pi
git clone https://github.com/theredsoft/sensor.git
cd sensor

# Автоматическая установка (рекомендуется для новых версий OS)
bash quick_install.sh

# Запуск датчика после установки
./run_sensor.sh

# Или расширенная версия
./run_advanced.sh --help
```

### ⚠️ Важно для новых версий Raspberry Pi OS (Bookworm и новее)

Начиная с Debian 12 (Bookworm), система защищает системные пакеты Python (PEP 668).
Используйте `quick_install.sh` который автоматически создаст виртуальное окружение.

## Поддерживаемые датчики

### VL53L1X Distance Sensor
Лазерный датчик расстояния с диапазоном измерения до 4 метров.

## Требования
- Raspberry Pi 5 (или другая модель)
- Датчик VL53L1X
- Python 3.7+
- Включенный интерфейс I2C

## Установка

### 1. Подключение датчика

Подключите датчик VL53L1X к Raspberry Pi:

| VL53L1X | Raspberry Pi GPIO |
|---------|-------------------|
| VIN     | 3.3V (Pin 1)     |
| GND     | GND (Pin 6)      |
| SCL     | GPIO3/SCL (Pin 5)|
| SDA     | GPIO2/SDA (Pin 3)|

### 2. Включение I2C

```bash
# Включите I2C через raspi-config
sudo raspi-config
# Выберите: Interface Options -> I2C -> Enable

# Или через командную строку
sudo raspi-config nonint do_i2c 0
```

### 3. Установка зависимостей

#### Автоматическая установка (рекомендуется):
```bash
# Запустите скрипт быстрой установки
bash quick_install.sh
```

#### Ручная установка:
```bash
# Обновление системы
sudo apt update

# Установка инструментов I2C
sudo apt install -y python3-pip python3-venv i2c-tools python3-smbus

# Проверка подключения датчика (должен показать адрес 0x29)
sudo i2cdetect -y 1

# Для новых версий OS (Bookworm+) - создание виртуального окружения
python3 -m venv venv
source venv/bin/activate
pip install vl53l1x

# Для старых версий OS - прямая установка
pip3 install vl53l1x
```

## Использование

### Простой скрипт (vl53l1x_sensor_reader.py)

Базовое циклическое чтение данных:

```bash
# Запуск с правами суперпользователя (требуется для доступа к I2C)
sudo python3 vl53l1x_sensor_reader.py
```

Особенности:
- Простой вывод расстояния в мм, см и метрах
- Визуальные индикаторы расстояния
- Временные метки измерений
- Статистика при завершении

### Расширенный скрипт (vl53l1x_advanced.py)

Продвинутые функции с параметрами командной строки:

```bash
# Запуск с параметрами по умолчанию
sudo python3 vl53l1x_advanced.py

# Режим дальнего измерения с детальным выводом
sudo python3 vl53l1x_advanced.py --mode 3 --display detailed

# Быстрые измерения (каждые 50мс) в компактном режиме
sudo python3 vl53l1x_advanced.py --interval 0.05 --display compact

# JSON вывод для интеграции с другими программами
sudo python3 vl53l1x_advanced.py --display json

# Высокая точность (больший timing budget)
sudo python3 vl53l1x_advanced.py --timing 100 --mode 1

# Полный список параметров
sudo python3 vl53l1x_advanced.py --help
```

#### Параметры командной строки:

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| --bus | Номер шины I2C | 1 |
| --address | Адрес датчика I2C | 0x29 |
| --mode | Режим: 1=Short, 2=Medium, 3=Long | 1 |
| --interval | Интервал измерений (сек) | 0.1 |
| --display | Режим отображения: standard, detailed, compact, json | standard |
| --timing | Timing budget в мс (20-500) | 20 |
| --history | Размер буфера истории | 100 |

### Режимы измерения расстояния

1. **Short Range (mode=1)**
   - Дальность: до 1.3 метров
   - Высокая точность
   - Быстрое измерение

2. **Medium Range (mode=2)**
   - Дальность: до 3 метров
   - Средняя точность
   - Умеренная скорость

3. **Long Range (mode=3)**
   - Дальность: до 4 метров
   - Низкая точность
   - Медленное измерение

### Режимы отображения

1. **standard** - Стандартный вывод с временной меткой
2. **detailed** - Подробная статистика и скорость изменения
3. **compact** - Компактный однострочный вывод
4. **json** - JSON формат для программной обработки

## Примеры использования

### Мониторинг парковочного места
```bash
sudo python3 vl53l1x_advanced.py --mode 2 --interval 1 --display standard
```

### Детектор движения
```bash
sudo python3 vl53l1x_advanced.py --mode 1 --interval 0.05 --display detailed
```

### Логирование данных в файл
```bash
sudo python3 vl53l1x_advanced.py --display json --interval 1 > distance_log.jsonl
```

### Интеграция с другими скриптами
```python
import subprocess
import json

# Запуск датчика и чтение JSON данных
process = subprocess.Popen(
    ['sudo', 'python3', 'vl53l1x_advanced.py', '--display', 'json'],
    stdout=subprocess.PIPE,
    text=True
)

for line in process.stdout:
    data = json.loads(line)
    distance = data['distance_mm']
    # Обработка данных
    print(f"Получено расстояние: {distance} мм")
```

## Устранение неполадок

### Ошибка "externally-managed-environment" при установке

Эта ошибка появляется в новых версиях Raspberry Pi OS (Bookworm и новее):
```
error: externally-managed-environment
× This environment is externally managed
```

**Решение:**
```bash
# Используйте скрипт быстрой установки
bash quick_install.sh

# Или создайте виртуальное окружение вручную
python3 -m venv venv
source venv/bin/activate
pip install vl53l1x

# Запуск с виртуальным окружением
sudo venv/bin/python vl53l1x_sensor_reader.py
```

### Датчик не обнаруживается
```bash
# Проверка подключения
i2cdetect -y 1
# Должен показать 29 на позиции 0x29
```

### Ошибка "Permission denied"
```bash
# Добавьте пользователя в группу i2c
sudo usermod -a -G i2c $USER
# Перезайдите в систему

# Или запускайте с sudo
sudo python3 vl53l1x_sensor_reader.py
```

### Нестабильные показания
- Увеличьте timing budget: `--timing 100`
- Используйте режим Short Range для близких объектов
- Убедитесь, что датчик надёжно закреплён
- Проверьте качество соединений

## Дополнительная информация

- [Документация VL53L1X Python](https://github.com/pimoroni/vl53l1x-python)
- [Datasheet VL53L1X](https://www.st.com/resource/en/datasheet/vl53l1x.pdf)
- [Raspberry Pi I2C Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c)

## Лицензия
MIT