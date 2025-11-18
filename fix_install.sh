#!/bin/bash

# Скрипт исправления проблемы с установкой VL53L1X на Python 3.13
# Использует альтернативные методы установки

echo "======================================"
echo "Исправление установки VL53L1X"
echo "для Python 3.13+"
echo "======================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка версии Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Обнаружена версия Python: $PYTHON_VERSION"

# Установка системных пакетов
echo ""
echo "1. Установка системных пакетов..."
sudo apt update
sudo apt install -y build-essential python3-dev python3-venv python3-pip git i2c-tools

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    echo ""
    echo "2. Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

echo ""
echo "3. Обновление pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "4. Выберите метод установки:"
echo ""
echo "1. Установка из исходников с патчем (рекомендуется)"
echo "2. Использовать Adafruit библиотеку (альтернатива)"
echo "3. Установить более старую версию VL53L1X"
echo "4. Попробовать все методы автоматически"
echo ""
read -p "Ваш выбор (1-4): " -n 1 -r choice
echo ""

case $choice in
    1)
        echo "Метод 1: Установка из исходников с патчем..."

        # Клонирование и патч
        if [ -d "vl53l1x-python" ]; then
            rm -rf vl53l1x-python
        fi

        git clone https://github.com/pimoroni/vl53l1x-python.git
        cd vl53l1x-python

        # Применение патча для usleep
        echo "Применение патча для Python 3.13..."
        cat > platform_patch.patch << 'EOF'
--- a/api/platform/vl53l1_platform.c
+++ b/api/platform/vl53l1_platform.c
@@ -1,3 +1,4 @@
+#define _GNU_SOURCE
 #include "vl53l1_platform.h"
 #include <string.h>
 #include <time.h>
EOF

        patch -p1 < platform_patch.patch 2>/dev/null || {
            # Альтернативный метод патча
            sed -i '1i#define _GNU_SOURCE' api/platform/vl53l1_platform.c
        }

        # Установка
        pip install .
        INSTALL_SUCCESS=$?
        cd ..

        if [ $INSTALL_SUCCESS -eq 0 ]; then
            echo -e "${GREEN}✅ Установка успешна!${NC}"
            echo "Используйте: vl53l1x_sensor_reader.py"
        else
            echo -e "${RED}Ошибка установки${NC}"
        fi
        ;;

    2)
        echo "Метод 2: Установка Adafruit библиотеки..."

        # Установка системных зависимостей для lgpio
        echo "Установка системных зависимостей..."
        sudo apt install -y python3-lgpio || {
            # Если lgpio недоступен через apt, компилируем из исходников
            echo "Компиляция lgpio из исходников..."
            wget http://abyz.me.uk/lg/lg.tar.gz
            tar -xzf lg.tar.gz
            cd lg
            make
            sudo make install
            cd ..
            rm -rf lg lg.tar.gz
        }

        pip install RPi.GPIO adafruit-circuitpython-vl53l1x lgpio

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Установка успешна!${NC}"
            echo "Используйте: vl53l1x_adafruit.py"
        else
            echo -e "${RED}Ошибка установки${NC}"
        fi
        ;;

    3)
        echo "Метод 3: Установка старой версии..."

        # Пробуем разные версии
        pip install vl53l1x==0.0.4 || pip install vl53l1x==0.0.3

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Установка успешна!${NC}"
        else
            echo -e "${RED}Ошибка установки${NC}"
        fi
        ;;

    4)
        echo "Метод 4: Автоматический поиск рабочего метода..."

        # Попытка 1: Стандартная установка
        echo "Попытка 1: Стандартная установка..."
        if pip install vl53l1x 2>/dev/null; then
            echo -e "${GREEN}✅ Стандартная установка успешна!${NC}"
        else
            # Попытка 2: Из исходников с патчем
            echo "Попытка 2: Компиляция из исходников..."

            if [ -d "vl53l1x-python" ]; then
                rm -rf vl53l1x-python
            fi

            git clone https://github.com/pimoroni/vl53l1x-python.git 2>/dev/null
            cd vl53l1x-python
            sed -i '1i#define _GNU_SOURCE' api/platform/vl53l1_platform.c 2>/dev/null

            if pip install . 2>/dev/null; then
                echo -e "${GREEN}✅ Установка из исходников успешна!${NC}"
                cd ..
            else
                cd ..
                # Попытка 3: Adafruit
                echo "Попытка 3: Adafruit библиотека..."
                if pip install adafruit-circuitpython-vl53l1x 2>/dev/null; then
                    echo -e "${GREEN}✅ Adafruit библиотека установлена!${NC}"
                    echo -e "${YELLOW}Используйте vl53l1x_adafruit.py для работы${NC}"
                else
                    echo -e "${RED}❌ Все методы не удались${NC}"
                    echo "Попробуйте использовать Python 3.11 или ниже"
                fi
            fi
        fi
        ;;

    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac

# Установка дополнительных библиотек
echo ""
echo "5. Установка дополнительных библиотек..."
pip install smbus2 2>/dev/null

# Создание скриптов запуска
echo ""
echo "6. Создание скриптов запуска..."

# Проверка какая библиотека установлена
if python3 -c "import VL53L1X" 2>/dev/null; then
    MAIN_SCRIPT="vl53l1x_sensor_reader.py"
    ADVANCED_SCRIPT="vl53l1x_advanced.py"
elif python3 -c "import adafruit_vl53l1x" 2>/dev/null; then
    MAIN_SCRIPT="vl53l1x_adafruit.py"
    ADVANCED_SCRIPT="vl53l1x_adafruit.py"
else
    echo -e "${RED}Ни одна библиотека не установлена${NC}"
    exit 1
fi

cat > run.sh << EOF
#!/bin/bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
sudo "\$SCRIPT_DIR/venv/bin/python" "\$SCRIPT_DIR/$MAIN_SCRIPT" "\$@"
EOF
chmod +x run.sh

# Создание дополнительного скрипта для простой версии
cat > run_simple.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
sudo "\$SCRIPT_DIR/venv/bin/python" "\$SCRIPT_DIR/vl53l1x_simple.py" "\$@"
EOF
chmod +x run_simple.sh

deactivate

echo ""
echo "======================================"
echo -e "${GREEN}Установка завершена!${NC}"
echo "======================================"
echo ""
echo "Для запуска используйте:"
echo "  ./run.sh"
echo ""
echo "Или активируйте виртуальное окружение:"
echo "  source venv/bin/activate"
echo "  sudo venv/bin/python $MAIN_SCRIPT"
echo ""