/*
 * VL53L1X Distance Sensor - WiringPi C версия
 * Компилировать: gcc -o vl53l1x_wiringpi vl53l1x_wiringpi.c -lwiringPi
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <wiringPi.h>
#include <wiringPiI2C.h>

// I2C адрес датчика
#define VL53L1X_ADDRESS 0x29

// Основные регистры VL53L1X
#define SOFT_RESET                      0x0000
#define FIRMWARE_SYSTEM_STATUS          0x0010
#define IDENTIFICATION_MODEL_ID         0x010F
#define SYSTEM_INTERRUPT_CLEAR          0x0086
#define SYSTEM_MODE_START               0x0087
#define GPIO_TIO_HV_STATUS             0x0031
#define RESULT_RANGE_STATUS            0x0089
#define RESULT_DISTANCE                0x0096

// Регистры конфигурации
#define RANGE_CONFIG_VCSEL_PERIOD_A    0x0060
#define RANGE_CONFIG_VCSEL_PERIOD_B    0x0063
#define RANGE_CONFIG_TIMEOUT_MACROP_A  0x005E
#define RANGE_CONFIG_TIMEOUT_MACROP_B  0x0061
#define RANGE_CONFIG_VALID_PHASE_HIGH  0x0069
#define SYSTEM_INTERRUPT_CONFIG_GPIO   0x0046

// Дескриптор I2C устройства
int fd;

// Функция записи в 16-битный регистр (8-битное значение)
void writeReg8(int fd, unsigned short reg, unsigned char value) {
    // Записываем старший байт адреса
    wiringPiI2CWriteReg8(fd, (reg >> 8) & 0xFF, reg & 0xFF);
    // Записываем значение
    wiringPiI2CWrite(fd, value);
}

// Функция записи в 16-битный регистр (16-битное значение)
void writeReg16(int fd, unsigned short reg, unsigned short value) {
    // Записываем адрес
    wiringPiI2CWriteReg8(fd, (reg >> 8) & 0xFF, reg & 0xFF);
    // Записываем данные (big-endian)
    wiringPiI2CWrite(fd, (value >> 8) & 0xFF);
    wiringPiI2CWrite(fd, value & 0xFF);
}

// Функция чтения из 16-битного регистра (8-битное значение)
unsigned char readReg8(int fd, unsigned short reg) {
    // Записываем адрес регистра
    wiringPiI2CWriteReg8(fd, (reg >> 8) & 0xFF, reg & 0xFF);
    // Читаем данные
    return wiringPiI2CRead(fd) & 0xFF;
}

// Функция чтения из 16-битного регистра (16-битное значение)
unsigned short readReg16(int fd, unsigned short reg) {
    unsigned char high, low;
    // Записываем адрес регистра
    wiringPiI2CWriteReg8(fd, (reg >> 8) & 0xFF, reg & 0xFF);
    // Читаем 2 байта
    high = wiringPiI2CRead(fd) & 0xFF;
    low = wiringPiI2CRead(fd) & 0xFF;
    return (high << 8) | low;
}

// Инициализация датчика
int initSensor(int fd) {
    unsigned short model_id;
    int i;

    printf("Инициализация VL53L1X...\n");

    // Проверка ID датчика
    model_id = readReg16(fd, IDENTIFICATION_MODEL_ID);
    if (model_id == 0xEACC) {
        printf("✓ Датчик VL53L1X обнаружен (ID: 0x%04X)\n", model_id);
    } else {
        printf("✗ Неизвестный датчик (ID: 0x%04X)\n", model_id);
        return -1;
    }

    // Программный сброс
    writeReg8(fd, SOFT_RESET, 0x00);
    usleep(10000); // 10ms
    writeReg8(fd, SOFT_RESET, 0x01);
    usleep(10000); // 10ms

    // Ждем загрузки прошивки
    printf("Ожидание загрузки прошивки...\n");
    for (i = 0; i < 100; i++) {
        if (readReg8(fd, FIRMWARE_SYSTEM_STATUS) & 0x01) {
            printf("✓ Прошивка загружена (попытка %d)\n", i + 1);
            break;
        }
        usleep(10000); // 10ms
    }

    if (i >= 100) {
        printf("✗ Таймаут загрузки прошивки\n");
        return -1;
    }

    // Базовая конфигурация
    writeReg8(fd, RANGE_CONFIG_VCSEL_PERIOD_A, 0x09);
    writeReg8(fd, RANGE_CONFIG_VCSEL_PERIOD_B, 0x0D);
    writeReg8(fd, RANGE_CONFIG_VALID_PHASE_HIGH, 0xC8);

    // Timing budget
    writeReg16(fd, RANGE_CONFIG_TIMEOUT_MACROP_A, 0x00D6);
    writeReg16(fd, RANGE_CONFIG_TIMEOUT_MACROP_B, 0x00D6);

    // Настройка прерываний
    writeReg8(fd, SYSTEM_INTERRUPT_CONFIG_GPIO, 0x01);
    writeReg8(fd, SYSTEM_INTERRUPT_CLEAR, 0x01);

    printf("✓ Датчик инициализирован\n");
    return 0;
}

// Запуск измерений
void startRanging(int fd) {
    writeReg8(fd, SYSTEM_INTERRUPT_CLEAR, 0x01);
    writeReg8(fd, SYSTEM_MODE_START, 0x40);
    usleep(50000); // 50ms для первого измерения
}

// Остановка измерений
void stopRanging(int fd) {
    writeReg8(fd, SYSTEM_MODE_START, 0x00);
}

// Получение расстояния
int getDistance(int fd) {
    unsigned char gpio_status, range_status;
    unsigned short distance;

    // Проверяем готовность данных
    gpio_status = readReg8(fd, GPIO_TIO_HV_STATUS);
    if (!(gpio_status & 0x01)) {
        return -1; // Данные не готовы
    }

    // Читаем статус измерения
    range_status = readReg8(fd, RESULT_RANGE_STATUS);

    // Читаем результат
    distance = readReg16(fd, RESULT_DISTANCE);

    // Очищаем прерывание
    writeReg8(fd, SYSTEM_INTERRUPT_CLEAR, 0x01);

    // Проверка валидности
    if (distance > 0 && distance < 8000) {
        // Проверяем статус
        if (((range_status >> 4) & 0x0F) == 0) {
            return distance;
        }
    }

    return -1;
}

// Визуализация расстояния
void printDistance(int distance, int count) {
    time_t now;
    struct tm *tm_info;
    char time_str[20];
    int bars, i;

    // Получаем текущее время
    time(&now);
    tm_info = localtime(&now);
    strftime(time_str, 20, "%H:%M:%S", tm_info);

    // Выводим данные
    printf("[%s] #%4d: %4d мм (%.1f см, %.3f м) ",
           time_str, count, distance,
           distance / 10.0, distance / 1000.0);

    // Визуальная шкала
    bars = distance / 100;
    if (bars > 40) bars = 40;
    printf("|");
    for (i = 0; i < bars; i++) {
        printf("█");
    }

    // Индикаторы близости
    if (distance < 100) {
        printf(" ⚠️ ОЧЕНЬ БЛИЗКО!");
    } else if (distance < 300) {
        printf(" ⚡ Близко");
    }

    printf("\n");
    fflush(stdout);
}

int main() {
    int distance;
    int count = 0;
    int errors = 0;
    int sum = 0;
    int min_dist = 9999;
    int max_dist = 0;

    printf("==========================================\n");
    printf("VL53L1X Distance Sensor - WiringPi C\n");
    printf("==========================================\n\n");

    // Инициализация WiringPi
    if (wiringPiSetup() == -1) {
        printf("✗ Ошибка инициализации WiringPi\n");
        return 1;
    }

    // Открываем I2C устройство
    fd = wiringPiI2CSetup(VL53L1X_ADDRESS);
    if (fd == -1) {
        printf("✗ Не удалось открыть I2C устройство\n");
        printf("\nПроверьте:\n");
        printf("1. Подключение датчика:\n");
        printf("   VIN → 3.3V (Pin 1)\n");
        printf("   GND → GND (Pin 6)\n");
        printf("   SCL → GPIO3 (Pin 5)\n");
        printf("   SDA → GPIO2 (Pin 3)\n");
        printf("2. Включен ли I2C:\n");
        printf("   sudo raspi-config → Interface Options → I2C\n");
        printf("3. Запустите с правами root:\n");
        printf("   sudo ./vl53l1x_wiringpi\n");
        return 1;
    }

    printf("✓ I2C устройство открыто (fd: %d)\n", fd);

    // Инициализация датчика
    if (initSensor(fd) != 0) {
        printf("✗ Ошибка инициализации датчика\n");
        return 1;
    }

    // Запуск измерений
    startRanging(fd);

    printf("\nНачало измерений (Ctrl+C для остановки)...\n");
    printf("------------------------------------------\n");

    // Основной цикл измерений
    while (1) {
        distance = getDistance(fd);

        if (distance > 0) {
            count++;
            sum += distance;

            if (distance < min_dist) min_dist = distance;
            if (distance > max_dist) max_dist = distance;

            printDistance(distance, count);
        } else {
            errors++;
            if (errors % 20 == 0) {
                printf("⚠ Ожидание данных... (пропусков: %d)\n", errors);
            }
        }

        usleep(50000); // 50ms = 20Hz
    }

    // Завершение (не достигается из-за бесконечного цикла)
    stopRanging(fd);
    close(fd);

    return 0;
}