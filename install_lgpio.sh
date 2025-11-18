#!/bin/bash

# Скрипт установки lgpio для Adafruit библиотек
# Исправляет ошибку: ModuleNotFoundError: No module named 'lgpio'

echo "======================================"
echo "Установка lgpio для Adafruit"
echo "======================================"

# Проверка виртуального окружения
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "Виртуальное окружение не найдено, работаем с системным Python"
fi

echo ""
echo "1. Установка системных зависимостей..."
sudo apt update
sudo apt install -y swig python3-dev python3-setuptools

echo ""
echo "2. Попытка установки lgpio через apt..."
if sudo apt install -y python3-lgpio 2>/dev/null; then
    echo "✅ lgpio установлен через apt"
else
    echo "⚠️  lgpio недоступен через apt, компиляция из исходников..."

    # Установка из исходников
    echo "3. Загрузка и компиляция lgpio..."
    cd /tmp
    wget http://abyz.me.uk/lg/lg.tar.gz
    tar -xzf lg.tar.gz
    cd lg
    make
    sudo make install

    # Установка Python биндингов
    cd SWIG/PYTHON
    python3 setup.py install

    # Очистка
    cd /
    rm -rf /tmp/lg /tmp/lg.tar.gz

    echo "✅ lgpio установлен из исходников"
fi

echo ""
echo "4. Установка Python пакетов..."
pip install lgpio 2>/dev/null || {
    echo "Прямая установка не удалась, пробуем альтернативный метод..."
    pip install rpi-lgpio 2>/dev/null
}

# Установка дополнительных зависимостей
pip install RPi.GPIO 2>/dev/null

echo ""
echo "5. Проверка установки..."
if python3 -c "import lgpio" 2>/dev/null; then
    echo "✅ lgpio успешно установлен и работает!"
else
    echo "⚠️  lgpio не удалось импортировать"
    echo ""
    echo "Альтернативное решение:"
    echo "Используйте vl53l1x_simple.py который работает только с smbus2:"
    echo "  sudo venv/bin/python vl53l1x_simple.py"
fi

if [ -d "venv" ]; then
    deactivate
fi

echo ""
echo "======================================"
echo "Установка завершена"
echo "======================================"
echo ""
echo "Попробуйте запустить:"
echo "  ./run.sh"
echo ""
echo "Или используйте простую версию без Adafruit:"
echo "  sudo venv/bin/python vl53l1x_simple.py"