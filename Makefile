# Makefile для компиляции VL53L1X WiringPi версий

CC = gcc
CFLAGS = -Wall -O2
LIBS = -lwiringPi

# Цель по умолчанию
all: vl53l1x_wiringpi

# Компиляция C версии
vl53l1x_wiringpi: vl53l1x_wiringpi.c
	@echo "Компиляция vl53l1x_wiringpi..."
	$(CC) $(CFLAGS) -o vl53l1x_wiringpi vl53l1x_wiringpi.c $(LIBS)
	@echo "✓ Готово! Запускайте: sudo ./vl53l1x_wiringpi"

# Установка WiringPi
install-wiringpi:
	@echo "Установка WiringPi..."
	bash install_wiringpi.sh

# Установка всех зависимостей
install: install-wiringpi
	@echo "Установка Python зависимостей..."
	python3 -m venv venv || true
	venv/bin/pip install --upgrade pip
	venv/bin/pip install wiringpi smbus2 || echo "Некоторые пакеты могут требовать ручной установки"

# Запуск Python версии
run-python:
	sudo venv/bin/python vl53l1x_wiringpi.py

# Запуск C версии
run-c: vl53l1x_wiringpi
	sudo ./vl53l1x_wiringpi

# Запуск минимальной версии (самая надежная)
run-minimal:
	sudo venv/bin/python vl53l1x_minimal.py

# Диагностика
diagnose:
	bash diagnose.sh

# Очистка
clean:
	rm -f vl53l1x_wiringpi
	rm -f *.o

# Полная очистка
clean-all: clean
	rm -rf venv
	rm -rf __pycache__
	rm -rf *.pyc

.PHONY: all install install-wiringpi run-python run-c run-minimal diagnose clean clean-all

# Помощь
help:
	@echo "VL53L1X Distance Sensor - Makefile"
	@echo "==================================="
	@echo ""
	@echo "Команды:"
	@echo "  make              - Компиляция C версии"
	@echo "  make install      - Установка всех зависимостей"
	@echo "  make run-c        - Запуск C версии"
	@echo "  make run-python   - Запуск Python WiringPi версии"
	@echo "  make run-minimal  - Запуск минимальной версии (рекомендуется)"
	@echo "  make diagnose     - Диагностика подключения"
	@echo "  make clean        - Очистка скомпилированных файлов"
	@echo "  make help         - Показать эту справку"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  1. make install   - установить зависимости"
	@echo "  2. make          - скомпилировать"
	@echo "  3. make run-c    - запустить"