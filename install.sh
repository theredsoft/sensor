#!/bin/bash

# Скрипт установки для Raspberry Pi Sensors
# Запуск: bash install.sh

echo "======================================"
echo "Установка Raspberry Pi Sensors"
echo "======================================"

# Проверка, что скрипт запущен на Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Предупреждение: Похоже, это не Raspberry Pi"
    read -p "Продолжить установку? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Обновление системы
echo "1. Обновление системы..."
sudo apt update

# Установка необходимых пакетов
echo "2. Установка системных пакетов..."
sudo apt install -y python3-pip i2c-tools python3-smbus git

# Включение I2C
echo "3. Включение интерфейса I2C..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    echo "I2C включен. Требуется перезагрузка."
    REBOOT_REQUIRED=true
fi

# Добавление пользователя в группу i2c
echo "4. Добавление пользователя в группу i2c..."
sudo usermod -a -G i2c $USER

# Установка Python зависимостей
echo "5. Установка Python библиотек..."

# Проверка версии Debian/Raspberry Pi OS для определения метода установки
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    # Новая версия с PEP 668 (externally-managed-environment)
    echo "Обнаружена новая версия Python с защитой системных пакетов."
    echo "Выберите метод установки:"
    echo "1. Использовать виртуальное окружение (рекомендуется)"
    echo "2. Установить через apt (если доступно)"
    echo "3. Принудительная установка pip (может нарушить систему)"
    read -p "Ваш выбор (1-3): " -n 1 -r install_choice
    echo

    case $install_choice in
        1)
            echo "Создание виртуального окружения..."
            # Установка python3-venv если не установлен
            sudo apt install -y python3-venv python3-full

            # Создание виртуального окружения
            python3 -m venv venv

            # Активация и установка
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt

            echo ""
            echo "✅ Библиотеки установлены в виртуальное окружение"
            echo "Для запуска скриптов используйте:"
            echo "  source venv/bin/activate"
            echo "  sudo venv/bin/python vl53l1x_sensor_reader.py"

            # Создание скрипта запуска
            cat > run_sensor.sh << 'EOF'
#!/bin/bash
# Скрипт запуска датчика с виртуальным окружением
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/vl53l1x_sensor_reader.py" "$@"
EOF
            chmod +x run_sensor.sh

            echo "Или используйте скрипт-обертку:"
            echo "  ./run_sensor.sh"
            ;;

        2)
            echo "Попытка установки через apt..."
            # VL53L1X обычно недоступен через apt, поэтому используем pipx
            sudo apt install -y pipx python3-smbus
            pipx install vl53l1x

            if [ $? -ne 0 ]; then
                echo "⚠️  Пакет недоступен через apt"
                echo "Используйте виртуальное окружение (вариант 1)"
            fi
            ;;

        3)
            echo "⚠️  ВНИМАНИЕ: Принудительная установка может нарушить систему!"
            read -p "Вы уверены? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pip3 install --break-system-packages -r requirements.txt
            else
                echo "Установка отменена"
                exit 1
            fi
            ;;

        *)
            echo "Неверный выбор"
            exit 1
            ;;
    esac
else
    # Старая версия без защиты
    pip3 install -r requirements.txt
fi

# Проверка подключения датчика
echo "6. Проверка I2C устройств..."
echo "Обнаруженные I2C устройства:"
sudo i2cdetect -y 1

echo ""
echo "======================================"
echo "Установка завершена!"
echo "======================================"

# Проверка наличия датчика VL53L1X (адрес 0x29)
if sudo i2cdetect -y 1 | grep -q " 29 "; then
    echo "✅ Датчик VL53L1X обнаружен на адресе 0x29"
    echo ""
    echo "Для запуска используйте:"
    echo "  sudo python3 vl53l1x_sensor_reader.py"
else
    echo "⚠️  Датчик VL53L1X не обнаружен"
    echo "Проверьте подключение:"
    echo "  VIN → 3.3V (Pin 1)"
    echo "  GND → GND (Pin 6)"
    echo "  SCL → GPIO3 (Pin 5)"
    echo "  SDA → GPIO2 (Pin 3)"
fi

if [ "$REBOOT_REQUIRED" = true ]; then
    echo ""
    echo "⚠️  Требуется перезагрузка для активации I2C"
    echo "Выполните: sudo reboot"
fi