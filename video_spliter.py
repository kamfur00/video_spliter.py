#!/usr/bin/env python3
"""
Video Splitter - разделяет видео на части по 2 часа максимально
Поддерживает форматы: mp4, avi, mkv, mov, flv, webm
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional


class VideoSplitter:
    """Класс для разделения видеофайлов на части"""

    def __init__(self, input_path: str, max_duration: int = 7200):
        self.input_path = Path(input_path)
        self.max_duration = max_duration

        if not self.input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {input_path}")

        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg не установлен. Установите FFmpeg: https://ffmpeg.org/")

    def _check_ffmpeg(self) -> bool:
        """Проверяет наличие FFmpeg в системе"""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _get_video_duration(self) -> float:
        """
        Получает длительность видео в секундах

        Returns:
            float: длительность в секундах
        """
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(self.input_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            raise RuntimeError(f"Ошибка при получении длительности видео: {e}")

    def _clean_filename(self, filename: str) -> str:
        """
        Очищает имя файла от недопустимых символов

        Args:
            filename: исходное имя файла

        Returns:
            str: очищенное имя файла
        """
        # Заменяем недопустимые символы на подчеркивания
        # Для Windows: \ / : * ? " < > |
        # Для Unix: / и \0
        invalid_chars = r'[<>:"/\\|?*]'
        clean_name = re.sub(invalid_chars, '_', filename)
        # Убираем точки в начале и конце
        clean_name = clean_name.strip('.')
        return clean_name

    def _calculate_parts(self, duration: float) -> List[Tuple[float, float]]:
        """
        Рассчитывает временные отрезки для каждой части

        Args:
            duration: общая длительность видео в секундах

        Returns:
            list: список кортежей (начало_в_секундах, конец_в_секундах)
        """
        if duration <= self.max_duration:
            return [(0, duration)]

        parts = []
        start = 0

        while start < duration:
            end = min(start + self.max_duration, duration)
            parts.append((start, end))
            start = end

        return parts

    def _get_output_filename(self, part_num: int, total_parts: int) -> str:
        """
        Генерирует имя выходного файла в формате [Name]++"1.mp4

        Args:
            part_num: номер части (начиная с 1)
            total_parts: общее количество частей

        Returns:
            str: имя выходного файла
        """
        # Получаем чистое имя без расширения
        stem = self.input_path.stem
        # Очищаем от недопустимых символов
        clean_stem = self._clean_filename(stem)
        extension = self.input_path.suffix

        # Если после очистки имя стало пустым, используем "video"
        if not clean_stem:
            clean_stem = "video"

        # Формат: Name.1.mp4 
        return f"{clean_stem}.{part_num}{extension}"

    def split_video(self, output_dir: Optional[str] = None) -> List[str]:
        """
        Разделяет видео на части

        Args:
            output_dir: директория для сохранения частей

        Returns:
            list: список путей к созданным файлам
        """
        # Получаем длительность
        print(f"📹 Анализ видео: {self.input_path.name}")
        duration = self._get_video_duration()

        print(f"⏱️  Длительность: {duration / 60:.1f} минут ({duration:.1f} секунд)")

        # Рассчитываем части
        parts = self._calculate_parts(duration)
        total_parts = len(parts)

        print(f"✂️  Будет создано частей: {total_parts}")
        print(f"⏰ Максимальная длительность части: {self.max_duration / 3600} час(ов)\n")

        # Определяем выходную директорию
        output_dir = Path(output_dir) if output_dir else self.input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        # Разделяем видео
        for idx, (start, end) in enumerate(parts, 1):
            part_duration = end - start
            output_file = output_dir / self._get_output_filename(idx, total_parts)

            print(f"🔪 Создание части {idx}/{total_parts}...")
            print(f"   ⏱️  Длительность: {part_duration / 60:.1f} минут")
            print(f"   📁 Сохранение: {output_file.name}")

            # Проверяем, не существует ли уже файл
            if output_file.exists():
                print(f"   ⚠️  Файл уже существует, будет перезаписан")

            # Команда FFmpeg для вырезания части
            cmd = [
                'ffmpeg',
                '-i', str(self.input_path),
                '-ss', str(start),
                '-t', str(part_duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',  # Перезаписывать существующие файлы
                str(output_file)
            ]

            try:
                # Запускаем команду с подавлением вывода (или без, для отладки)
                result = subprocess.run(cmd,
                                        capture_output=True,
                                        text=True)

                if result.returncode != 0:
                    # Если ошибка, пробуем альтернативный метод с перекодированием
                    print(f"   ⚠️  Ошибка при копировании, пробуем перекодирование...")

                    cmd_reencode = [
                        'ffmpeg',
                        '-i', str(self.input_path),
                        '-ss', str(start),
                        '-t', str(part_duration),
                        '-c:v', 'libx264',  # Перекодируем видео
                        '-c:a', 'aac',  # Перекодируем аудио
                        '-y',
                        str(output_file)
                    ]

                    result = subprocess.run(cmd_reencode,
                                            capture_output=True,
                                            text=True)

                    if result.returncode != 0:
                        print(f"   ❌ Ошибка FFmpeg:")
                        print(f"   {result.stderr[-500:]}")  # Показываем последние 500 символов ошибки
                        raise RuntimeError(f"Не удалось создать часть {idx}")

                created_files.append(str(output_file))
                print(f"   ✅ Готово! (Размер: {output_file.stat().st_size / (1024 * 1024):.1f} MB)\n")

            except Exception as e:
                print(f"   ❌ Критическая ошибка: {e}")
                raise

        return created_files


def main():
    """Основная функция"""

    print("=" * 50)
    print("🎬 Video Splitter v2.0")
    print("=" * 50)
    print()

    # Проверка аргументов
    if len(sys.argv) < 2:
        print("Использование: python video_splitter.py <путь_к_видео> [макс_часов]")
        print("\nПримеры:")
        print("  python video_splitter.py video.mp4")
        print("  python video_splitter.py '2.1.mp4'")
        print("  python video_splitter.py video.avi 1.5")
        sys.exit(1)

    input_path = sys.argv[1]

    # Парсим максимальную длительность
    max_hours = 2.0
    if len(sys.argv) >= 3:
        try:
            max_hours = float(sys.argv[2])
            if max_hours <= 0:
                print(f"❌ Ошибка: длительность должна быть больше 0")
                sys.exit(1)
        except ValueError:
            print(f"❌ Ошибка: '{sys.argv[2]}' не является числом")
            sys.exit(1)

    max_duration = int(max_hours * 3600)

    try:
        # Создаем сплиттер
        splitter = VideoSplitter(input_path, max_duration)

        # Разделяем видео
        output_files = splitter.split_video()

        # Выводим результат
        print("=" * 50)
        print("✅ Разделение завершено успешно!")
        print(f"📁 Создано файлов: {len(output_files)}")
        print("\nСозданные файлы:")
        for file in output_files:
            file_path = Path(file)
            file_size = file_path.stat().st_size / (1024 * 1024)
            print(f"  📄 {file_path.name} ({file_size:.1f} MB)")

    except FileNotFoundError as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
