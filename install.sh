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
pip3 install -r requirements.txt

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