#!/bin/bash

# Скрипт установки WiringPi для работы с VL53L1X
# Поддерживает как старые, так и новые версии Raspberry Pi OS

echo "========================================"
echo "Установка WiringPi для VL53L1X"
echo "========================================"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для вывода
error_msg() { echo -e "${RED}✗ $1${NC}"; }
success_msg() { echo -e "${GREEN}✓ $1${NC}"; }
warning_msg() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Определение архитектуры системы
ARCH=$(uname -m)
echo "Архитектура системы: $ARCH"

# Определение версии ОС
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_VERSION=$VERSION_ID
    OS_NAME=$PRETTY_NAME
    echo "ОС: $OS_NAME"
fi

echo ""
echo "1. Установка системной библиотеки WiringPi..."
echo "----------------------------------------------"

# Попытка установки через apt
if command -v apt &> /dev/null; then
    echo "Попытка установки через apt..."
    sudo apt update

    # Для новых версий Raspberry Pi OS библиотека может быть недоступна через apt
    if sudo apt install -y wiringpi 2>/dev/null; then
        success_msg "WiringPi установлен через apt"
    else
        warning_msg "WiringPi недоступен через apt, устанавливаем вручную..."

        # Установка из исходников для ARM64/Raspberry Pi 4+
        echo ""
        echo "Установка WiringPi из исходников..."

        # Удаляем старую версию если есть
        if [ -d "WiringPi" ]; then
            rm -rf WiringPi
        fi

        # Клонирование репозитория (неофициальный форк для Pi 4/5)
        git clone https://github.com/WiringPi/WiringPi.git
        cd WiringPi

        # Сборка и установка
        echo "Компиляция WiringPi..."
        ./build

        if [ $? -eq 0 ]; then
            success_msg "WiringPi успешно установлен из исходников"
        else
            error_msg "Ошибка компиляции WiringPi"

            # Альтернативный метод для Raspberry Pi 4/5
            echo ""
            echo "Пробуем альтернативный метод установки..."
            cd ..
            rm -rf WiringPi

            # Загрузка предкомпилированной версии
            if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
                # Для 64-битной системы
                wget https://github.com/WiringPi/WiringPi/releases/download/3.2/wiringpi_3.2_arm64.deb
                sudo dpkg -i wiringpi_3.2_arm64.deb
                rm wiringpi_3.2_arm64.deb
            else
                # Для 32-битной системы
                wget https://github.com/WiringPi/WiringPi/releases/download/3.2/wiringpi_3.2_armhf.deb
                sudo dpkg -i wiringpi_3.2_armhf.deb
                rm wiringpi_3.2_armhf.deb
            fi

            if [ $? -eq 0 ]; then
                success_msg "WiringPi установлен из .deb пакета"
            else
                error_msg "Не удалось установить WiringPi"
            fi
        fi

        cd ..
    fi
fi

# Проверка установки
echo ""
echo "2. Проверка установки WiringPi..."
echo "----------------------------------"

if command -v gpio &> /dev/null; then
    GPIO_VERSION=$(gpio -v | head -n 1)
    success_msg "WiringPi установлен: $GPIO_VERSION"

    # Проверка I2C
    echo ""
    echo "Обнаруженные I2C устройства:"
    gpio i2cdetect
else
    error_msg "Команда gpio не найдена"
fi

echo ""
echo "3. Установка Python библиотеки wiringpi..."
echo "-------------------------------------------"

# Создание виртуального окружения если нужно
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip > /dev/null 2>&1

# Установка Python библиотеки
echo "Установка wiringpi для Python..."

# Для новых версий Python может потребоваться установка из исходников
if ! pip install wiringpi 2>/dev/null; then
    warning_msg "Стандартная установка не удалась, пробуем альтернативы..."

    # Альтернатива 1: установка через системный пакет
    if sudo apt install -y python3-wiringpi 2>/dev/null; then
        success_msg "python3-wiringpi установлен через apt"
    else
        # Альтернатива 2: установка конкретной версии
        pip install wiringpi==2.60.1 || {
            # Альтернатива 3: установка из исходников
            echo "Установка из исходников..."
            git clone https://github.com/WiringPi/WiringPi-Python.git
            cd WiringPi-Python
            python setup.py install
            cd ..
            rm -rf WiringPi-Python
        }
    fi
fi

# Установка smbus2 как запасной вариант
pip install smbus2

deactivate

echo ""
echo "4. Проверка Python библиотеки..."
echo "---------------------------------"

# Тест импорта
venv/bin/python -c "import wiringpi; print('✓ wiringpi успешно импортирован')" 2>/dev/null || {
    warning_msg "Не удалось импортировать wiringpi в Python"
    echo "Попробуйте использовать vl53l1x_minimal.py вместо wiringpi версии"
}

echo ""
echo "5. Создание скриптов запуска..."
echo "--------------------------------"

# Создание скрипта запуска для WiringPi версии
cat > run_wiringpi.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/vl53l1x_wiringpi.py" "$@"
EOF
chmod +x run_wiringpi.sh

success_msg "Скрипт run_wiringpi.sh создан"

echo ""
echo "========================================"
echo "Установка завершена!"
echo "========================================"
echo ""
echo "Для запуска используйте:"
echo "  ./run_wiringpi.sh"
echo "или"
echo "  sudo venv/bin/python vl53l1x_wiringpi.py"
echo ""

# Проверка I2C
echo "Проверка I2C устройств:"
if command -v i2cdetect &> /dev/null; then
    sudo i2cdetect -y 1
else
    warning_msg "i2cdetect не установлен"
    echo "Установите: sudo apt install i2c-tools"
fi

echo ""
echo "Если датчик не обнаружен на адресе 0x29:"
echo "1. Проверьте подключение (3.3V, GND, SDA, SCL)"
echo "2. Включите I2C: sudo raspi-config"
echo "3. Запустите диагностику: bash diagnose.sh"