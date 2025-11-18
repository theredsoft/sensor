#!/bin/bash

# Быстрая установка VL53L1X для Raspberry Pi
# Автоматически создает виртуальное окружение для новых версий OS

echo "======================================"
echo "Быстрая установка VL53L1X Sensor"
echo "======================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода ошибок
error_exit() {
    echo -e "${RED}Ошибка: $1${NC}" >&2
    exit 1
}

# Функция для вывода успеха
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Функция для вывода предупреждения
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Обновление системы
echo "1. Обновление системы..."
sudo apt update || error_exit "Не удалось обновить список пакетов"

# 2. Установка необходимых пакетов
echo "2. Установка системных пакетов..."
sudo apt install -y python3-pip python3-venv python3-full i2c-tools python3-smbus git || error_exit "Не удалось установить пакеты"

# 3. Включение I2C
echo "3. Проверка и включение I2C..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null && ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
    warning_msg "I2C не включен. Включаю..."

    # Определение пути к config.txt (разный в зависимости от версии)
    if [ -f /boot/firmware/config.txt ]; then
        CONFIG_FILE="/boot/firmware/config.txt"
    else
        CONFIG_FILE="/boot/config.txt"
    fi

    echo "dtparam=i2c_arm=on" | sudo tee -a $CONFIG_FILE > /dev/null
    REBOOT_REQUIRED=true
    success_msg "I2C включен в $CONFIG_FILE"
else
    success_msg "I2C уже включен"
fi

# 4. Добавление пользователя в группу i2c
echo "4. Добавление пользователя в группу i2c..."
sudo usermod -a -G i2c $USER || warning_msg "Не удалось добавить пользователя в группу i2c"

# 5. Создание виртуального окружения и установка библиотек
echo "5. Установка Python библиотек..."

# Всегда используем виртуальное окружение для безопасности
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv || error_exit "Не удалось создать виртуальное окружение"
fi

# Активация и установка
echo "Установка библиотек в виртуальное окружение..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install vl53l1x smbus2 || error_exit "Не удалось установить Python библиотеки"
deactivate

success_msg "Библиотеки установлены"

# 6. Создание скриптов запуска
echo "6. Создание скриптов запуска..."

# Основной скрипт запуска
cat > run_sensor.sh << 'EOF'
#!/bin/bash
# Запуск датчика VL53L1X
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Проверка наличия виртуального окружения
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Ошибка: Виртуальное окружение не найдено"
    echo "Запустите quick_install.sh для установки"
    exit 1
fi

# Запуск с правами sudo используя Python из виртуального окружения
sudo "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/vl53l1x_sensor_reader.py" "$@"
EOF
chmod +x run_sensor.sh

# Расширенный скрипт запуска
cat > run_advanced.sh << 'EOF'
#!/bin/bash
# Запуск расширенной версии датчика VL53L1X
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Проверка наличия виртуального окружения
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Ошибка: Виртуальное окружение не найдено"
    echo "Запустите quick_install.sh для установки"
    exit 1
fi

# Запуск с правами sudo используя Python из виртуального окружения
sudo "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/vl53l1x_advanced.py" "$@"
EOF
chmod +x run_advanced.sh

success_msg "Скрипты запуска созданы"

# 7. Проверка датчика
echo ""
echo "7. Проверка подключения датчика..."
echo "Сканирование I2C устройств:"

# Проверка I2C
i2c_result=$(sudo i2cdetect -y 1 2>/dev/null)
if echo "$i2c_result" | grep -q " 29 "; then
    success_msg "Датчик VL53L1X обнаружен на адресе 0x29"
    SENSOR_FOUND=true
else
    warning_msg "Датчик VL53L1X НЕ обнаружен"
    echo ""
    echo "Проверьте подключение:"
    echo "  VL53L1X  →  Raspberry Pi"
    echo "  ─────────────────────────"
    echo "  VIN      →  3.3V (Pin 1)"
    echo "  GND      →  GND  (Pin 6)"
    echo "  SCL      →  SCL  (Pin 5)"
    echo "  SDA      →  SDA  (Pin 3)"
    SENSOR_FOUND=false
fi

# 8. Итоговая информация
echo ""
echo "======================================"
echo "Установка завершена!"
echo "======================================"

if [ "$SENSOR_FOUND" = true ]; then
    echo ""
    success_msg "Система готова к работе!"
    echo ""
    echo "Для запуска датчика используйте:"
    echo "  ${GREEN}./run_sensor.sh${NC}          - простой режим"
    echo "  ${GREEN}./run_advanced.sh${NC}        - расширенный режим"
    echo "  ${GREEN}./run_advanced.sh --help${NC} - справка по параметрам"
    echo ""
    echo "Примеры использования:"
    echo "  ./run_sensor.sh"
    echo "  ./run_advanced.sh --mode 2 --display detailed"
    echo "  ./run_advanced.sh --display json > data.jsonl"
else
    echo ""
    warning_msg "Датчик не подключен, но программное обеспечение установлено"
    echo "После подключения датчика запустите скрипты как указано выше"
fi

if [ "$REBOOT_REQUIRED" = true ]; then
    echo ""
    warning_msg "ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА для активации I2C"
    echo "Выполните: ${YELLOW}sudo reboot${NC}"
fi

echo ""