#!/bin/bash

# Скрипт настройки I2C для VL53L1X на Raspberry Pi
# Обрабатывает новую структуру файлов (/boot/firmware/)

echo "======================================"
echo "Настройка I2C для VL53L1X"
echo "======================================"

# Определяем путь к config.txt
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
    echo "✓ Используется новая структура: /boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
    echo "✓ Используется старая структура: /boot/config.txt"
else
    echo "✗ Файл config.txt не найден!"
    exit 1
fi

echo ""
echo "1. Проверка текущих настроек I2C..."

# Проверка включен ли I2C
if grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE"; then
    echo "✓ I2C уже включен"
else
    echo "⚠ I2C не включен. Включаю..."
    echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "✓ I2C включен"
    REBOOT_REQUIRED=true
fi

# Проверка скорости I2C
if grep -q "dtparam=i2c_baudrate=" "$CONFIG_FILE"; then
    CURRENT_SPEED=$(grep "dtparam=i2c_baudrate=" "$CONFIG_FILE" | cut -d'=' -f2)
    echo "✓ Текущая скорость I2C: $CURRENT_SPEED"
else
    echo "⚠ Скорость I2C не задана (используется по умолчанию 100000)"
fi

echo ""
echo "2. Оптимизация для VL53L1X..."

# Рекомендуемые настройки для VL53L1X
read -p "Установить оптимальную скорость I2C 400kHz? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Удаляем старую настройку если есть
    sudo sed -i '/dtparam=i2c_baudrate=/d' "$CONFIG_FILE"
    # Добавляем новую
    echo "dtparam=i2c_baudrate=400000" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "✓ Скорость I2C установлена на 400kHz"
    REBOOT_REQUIRED=true
fi

echo ""
echo "3. Установка прав доступа..."

# Добавляем пользователя в группу i2c
sudo usermod -a -G i2c $USER 2>/dev/null
echo "✓ Пользователь добавлен в группу i2c"

# Загружаем модули I2C
sudo modprobe i2c-dev 2>/dev/null
sudo modprobe i2c-bcm2835 2>/dev/null
echo "✓ Модули I2C загружены"

echo ""
echo "4. Проверка датчика..."

# Сканирование I2C
echo "Сканирование шины I2C..."
sudo i2cdetect -y 1

# Проверка адреса 0x29
if sudo i2cdetect -y 1 | grep -q " 29 "; then
    echo ""
    echo "✅ Датчик VL53L1X обнаружен на адресе 0x29!"
else
    echo ""
    echo "⚠️ Датчик не обнаружен на адресе 0x29"
    echo ""
    echo "Проверьте подключение:"
    echo "┌──────────┬─────────────────┐"
    echo "│ VL53L1X  │ Raspberry Pi    │"
    echo "├──────────┼─────────────────┤"
    echo "│ VIN      │ 3.3V (Pin 1)    │"
    echo "│ GND      │ GND (Pin 6)     │"
    echo "│ SCL      │ GPIO3 (Pin 5)   │"
    echo "│ SDA      │ GPIO2 (Pin 3)   │"
    echo "└──────────┴─────────────────┘"
fi

echo ""
echo "5. Создание правила udev для доступа без sudo..."

# Создаем правило udev
sudo bash -c 'cat > /etc/udev/rules.d/99-i2c.rules' << EOF
SUBSYSTEM=="i2c-dev", MODE="0666"
EOF

sudo udevadm control --reload-rules && sudo udevadm trigger
echo "✓ Правило udev создано"

echo ""
echo "======================================"
echo "Настройка завершена!"
echo "======================================"

if [ "$REBOOT_REQUIRED" = true ]; then
    echo ""
    echo "⚠️ ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА!"
    echo "Выполните: sudo reboot"
else
    echo ""
    echo "✅ Система готова к работе!"
    echo ""
    echo "Теперь можно запускать без sudo:"
    echo "  python3 vl53l1x_minimal.py"
fi