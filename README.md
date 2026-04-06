# Установка и использование:
1. Установите FFmpeg:
Windows:

bash
Через chocolatey
choco install ffmpeg

Или скачайте с официального сайта https://ffmpeg.org/download.html
macOS:

bash
brew install ffmpeg
Linux (Ubuntu/Debian):

bash
sudo apt update
sudo apt install ffmpeg
2. Использование скрипта:
bash
# Базовое использование (части по 2 часа)
python video_spliter.py video.mp4

# Указать другую максимальную длительность (1.5 часа)
python video_spliter.py video.avi 1.5

# Полный путь к файлу
python video_spliter.py "C:/Videos/my_movie.mkv"

bash
$ python video_spliter.py "Big Movie.mp4"

Особенности скрипта:
Быстрое разделение - использует -c copy для копирования потоков без перекодирования

Автоматическое определение формата - работает с MP4, AVI, MKV, MOV, FLV, WEBM

Интеллектуальная нумерация - автоматически определяет количество цифр (01, 02 или 1, 2)

Обработка ошибок - проверяет наличие FFmpeg и корректность входных данных

Информативный вывод - показывает прогресс и детали каждой части

Скрипт готов к использованию в production-среде и обрабатывает видео любого размера!
