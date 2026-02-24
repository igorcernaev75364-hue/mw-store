# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта
COPY . .

# Указываем порт, который будет использовать приложение
EXPOSE 8080

# Запускаем приложение через gunicorn (для продакшена)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app