# Импорт необходимых библиотек
import numpy as np
import tensorflow as tf
import pandas as pd
import pretty_midi
from IPython import display
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import json
from datetime import datetime
import sys
import tempfile
import subprocess

class MusicPlayer:
    """Класс для воспроизведения MIDI через системный плеер"""
    
    def __init__(self, parent, midi_object, filename="Сгенерированная музыка", saved_file_path=None):
        self.parent = parent
        self.midi_object = midi_object
        self.filename = filename
        self.saved_file_path = saved_file_path  # Путь к сохраненному файлу
        self.is_playing = False
        self.current_position = 0
        self.total_duration = 0
        self.temp_file = None
        
        # Создаем окно плеера
        self.player_window = tk.Toplevel(parent)
        self.player_window.title("🎵 Музыкальный плеер")
        self.player_window.geometry("500x250")
        self.player_window.configure(bg='#2b2b2b')
        self.player_window.resizable(False, False)
        
        # Иконка (если есть)
        try:
            icon_path = os.path.dirname(os.path.abspath(__file__)) + '/Images/icon.png'
            if os.path.exists(icon_path):
                icon_image = tk.PhotoImage(file=icon_path)
                self.player_window.iconphoto(True, icon_image)
        except:
            pass
        
        self.setup_player_ui()
        self.prepare_audio()
        
        # Обработка закрытия окна
        self.player_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_player_ui(self):
        """Создает интерфейс плеера"""
        
        # Заголовок с названием трека
        title_frame = ttk.Frame(self.player_window)
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        self.title_label = ttk.Label(
            title_frame, 
            text=self.filename,
            style='Title.TLabel',
            font=('Arial', 14, 'bold')
        )
        self.title_label.pack()
        
        # Информация о треке
        self.info_label = ttk.Label(
            title_frame,
            text="Загрузка...",
            style='Custom.TLabel',
            font=('Arial', 9)
        )
        self.info_label.pack(pady=(5, 0))
        
        # Прогресс бар
        progress_frame = ttk.Frame(self.player_window)
        progress_frame.pack(fill='x', padx=20, pady=20)
        
        # Временные метки
        time_frame = ttk.Frame(progress_frame)
        time_frame.pack(fill='x', pady=(0, 5))
        
        self.current_time_label = ttk.Label(
            time_frame,
            text="0:00",
            style='Custom.TLabel'
        )
        self.current_time_label.pack(side='left')
        
        self.total_time_label = ttk.Label(
            time_frame,
            text="0:00",
            style='Custom.TLabel'
        )
        self.total_time_label.pack(side='right')
        
        # Шкала воспроизведения
        self.progress_scale = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient='horizontal'
        )
        self.progress_scale.pack(fill='x')
        self.progress_scale.config(state='disabled')  # Отключаем перемотку для системного плеера
        
        # Кнопки управления
        controls_frame = ttk.Frame(self.player_window)
        controls_frame.pack(pady=15)
        
        self.play_button = ttk.Button(
            controls_frame,
            text="▶ Воспроизвести",
            command=self.play,
            width=20
        )
        self.play_button.pack(side='left', padx=5)
        
        self.open_folder_button = ttk.Button(
            controls_frame,
            text="📁 Открыть папку",
            command=self.open_saved_folder,
            width=20
        )
        self.open_folder_button.pack(side='left', padx=5)
        
        # Отключаем кнопку, если файл не сохранен
        if not self.saved_file_path or not os.path.exists(self.saved_file_path):
            self.open_folder_button.config(state='disabled')
            self.open_folder_button.config(text="📁 Файл не сохранён")
        
        # Статус
        self.status_label = ttk.Label(
            self.player_window,
            text="Готов к воспроизведению",
            style='Custom.TLabel',
            font=('Arial', 9)
        )
        self.status_label.pack(pady=(0, 10))
    
    def prepare_audio(self):
        """Подготавливает аудио для воспроизведения"""
        try:
            # Создаем временный файл
            self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
            self.temp_path = self.temp_file.name
            self.temp_file.close()
            
            # Сохраняем MIDI
            self.midi_object.write(self.temp_path)
            
            # Получаем длительность
            self.total_duration = self.midi_object.get_end_time()
            
            # Обновляем информацию
            minutes = int(self.total_duration // 60)
            seconds = int(self.total_duration % 60)
            self.total_time_label.config(text=f"{minutes}:{seconds:02d}")
            
            # Получаем количество нот
            total_notes = sum(len(instrument.notes) for instrument in self.midi_object.instruments)
            
            self.info_label.config(
                text=f"Нот: {total_notes} | Длительность: {minutes}:{seconds:02d}"
            )
            
            self.status_label.config(text="✅ Готов к воспроизведению")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подготовить аудио:\n{str(e)}")
            self.player_window.destroy()
    
    def play(self):
        """Начинает воспроизведение через системный плеер"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.temp_path)
            else:  # Linux/Mac
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.run(['open', self.temp_path])
                else:
                    subprocess.run(['xdg-open', self.temp_path])
            
            self.is_playing = True
            self.play_button.config(state='disabled')
            self.status_label.config(text="▶ Файл открыт в системном плеере")
            
            # Запускаем симуляцию прогресса
            self.simulate_progress()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось воспроизвести:\n{str(e)}")
    
    def simulate_progress(self):
        """Симулирует прогресс воспроизведения"""
        if not self.is_playing:
            return
        
        try:
            self.current_position += 0.1
            
            if self.current_position <= self.total_duration:
                progress = (self.current_position / self.total_duration) * 100
                self.progress_scale.set(progress)
                
                minutes = int(self.current_position // 60)
                seconds = int(self.current_position % 60)
                self.current_time_label.config(text=f"{minutes}:{seconds:02d}")
                
                # Продолжаем обновление
                self.player_window.after(100, self.simulate_progress)
            else:
                # Воспроизведение закончилось
                self.is_playing = False
                self.play_button.config(state='normal')
                self.status_label.config(text="✅ Воспроизведение завершено")
                
        except Exception as e:
            print(f"Ошибка обновления прогресса: {e}")
    
    def open_saved_folder(self):
        """Открывает папку с сохраненным файлом"""
        if not self.saved_file_path:
            messagebox.showwarning("Предупреждение", 
                                "Файл ещё не сохранён!\n\n"
                                "Сгенерируйте музыку, она автоматически сохранится в папку Outputs.")
            return
        
        if not os.path.exists(self.saved_file_path):
            messagebox.showerror("Ошибка", 
                            f"Файл не найден:\n{self.saved_file_path}\n\n"
                            f"Возможно, он был удалён или перемещён.")
            return
        
        try:
            import subprocess  # Импортируем здесь для всех веток
            folder = os.path.dirname(self.saved_file_path)
            
            if os.name == 'nt':  # Windows
                # Открываем проводник и выделяем файл
                subprocess.run(['explorer', '/select,', os.path.normpath(self.saved_file_path)])
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', '-R', self.saved_file_path])
            else:  # Linux
                # Просто открываем папку
                subprocess.run(['xdg-open', folder])
            
            self.status_label.config(text=f"📁 Открыта папка: {os.path.basename(folder)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.is_playing = False
        
        # Удаляем временный файл
        try:
            if self.temp_file and os.path.exists(self.temp_path):
                # Даем время системному плееру открыть файл
                self.player_window.after(1000, lambda: self.cleanup_temp_file())
        except:
            pass
        
        self.player_window.destroy()
    
    def cleanup_temp_file(self):
        """Отложенная очистка временного файла"""
        try:
            if os.path.exists(self.temp_path):
                os.remove(self.temp_path)
        except:
            pass  # Файл может быть занят плеером

class MusicGeneratorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 Генератор музыки с нейросетью")
        self.root.geometry(f'1000x700')
        icon_image = tk.PhotoImage(file=os.path.dirname(os.path.abspath(__file__)) + '\Images\icon.png')
        self.root.iconphoto(True, icon_image)
        self.root.configure(bg='#2b2b2b')

        self.model = None
        self.model_path = ""
        self.generated_notes = None
        self.generated_midi = None
        self.generated_filename = ""
        self.generated_instrument = 0

        # Переменные для оркестра
        self.orchestra_instruments = [] # Список выбранных инструментов
        self.orchestra_parts = {} # Сгенерированные партии для каждого инструмента
        self.drum_patterns = { # Паттерны для ударных
            'kick': [36], 
            'snare': [38, 40], 
            'hihat': [42, 44], 
            'crash': [49, 57], 
            'ride': [51]
        }

        # Музыкальные константы
        self.SCALES = {
            'C Major': [60, 62, 64, 65, 67, 69, 71],
            'A Minor': [57, 59, 60, 62, 64, 65, 67],
            'G Major': [67, 69, 71, 72, 74, 76, 78],
            'E Minor': [64, 66, 67, 69, 71, 72, 74],
            'F Major': [65, 67, 69, 70, 72, 74, 76],
            'D Minor': [62, 64, 65, 67, 69, 70, 72],
            'Bb Major': [70, 72, 74, 75, 77, 79, 81],
            'Chromatic': list(range(60, 73))
        }

        self.INSTRUMENTS = {
            0: 'Acoustic Grand Piano', 1: 'Bright Acoustic Piano', 2: 'Electric Grand Piano',
            24: 'Acoustic Guitar (nylon)', 25: 'Acoustic Guitar (steel)', 26: 'Electric Guitar (jazz)',
            27: 'Electric Guitar (clean)', 32: 'Acoustic Bass', 33: 'Electric Bass (finger)',
            40: 'Violin', 41: 'Viola', 42: 'Cello', 56: 'Trumpet', 57: 'Trombone',
            64: 'Soprano Sax', 65: 'Alto Sax', 73: 'Flute', 80: 'Lead 1 (square)', 81: 'Lead 2 (sawtooth)'
        }

        self.RHYTHMS = {
            'Медленно': {'step_min': 0.8, 'step_max': 2.0, 'duration_min': 1.0, 'duration_max': 3.0},
            'Умеренно': {'step_min': 0.4, 'step_max': 1.2, 'duration_min': 0.6, 'duration_max': 2.0},
            'Быстро': {'step_min': 0.2, 'step_max': 0.8, 'duration_min': 0.3, 'duration_max': 1.5},
            'Пользовательский': {'step_min': 0.1, 'step_max': 4.0, 'duration_min': 0.1, 'duration_max': 4.0}
        }

        self.setup_ui()

    def setup_ui(self):
        # Стиль для виджетов
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#2b2b2b', foreground='white')
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), background='#2b2b2b', foreground='white')
        style.configure('Custom.TLabel', background='#2b2b2b', foreground='white')

        # Главный заголовок
        title_label = ttk.Label(self.root, text="🎵 Генератор музыки с нейросетью", style='Title.TLabel')
        title_label.pack(pady=10)

        # Создание notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Вкладка 1: Загрузка модели
        self.setup_model_tab(notebook)

        # Вкладка 2: Настройки генерации
        self.setup_generation_tab(notebook)

        # Вкладка 3: Расширенные настройки
        self.setup_advanced_tab(notebook)

        # Вкладка 4: Пресеты
        self.setup_presets_tab(notebook)

        # Кнопки управления
        self.setup_control_buttons()

        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_label = ttk.Label(self.root, textvariable=self.status_var, style='Custom.TLabel')
        status_label.pack(pady=5)

    def update_model_info(self, text):
        """Обновляет информацию о модели в текстовом поле"""
        self.model_info_text.config(state='normal')  # Временно разрешаем редактирование
        self.model_info_text.delete(1.0, tk.END)     # Очищаем содержимое
        self.model_info_text.insert(1.0, text)       # Вставляем новый текст
        self.model_info_text.config(state='disabled') # Снова блокируем редактирование

    def setup_model_tab(self, notebook):
        model_frame = ttk.Frame(notebook)
        notebook.add(model_frame, text="📁 Модель")

        # Загрузка модели
        ttk.Label(model_frame, text="Загрузка модели:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)

        model_frame_inner = ttk.Frame(model_frame)
        model_frame_inner.pack(fill='x', padx=10, pady=5)

        self.model_path_var = tk.StringVar()
        ttk.Entry(model_frame_inner, textvariable=self.model_path_var, width=60).pack(side='left', fill='x', expand=True)
        ttk.Button(model_frame_inner, text="Обзор", command=self.load_model).pack(side='right', padx=(5, 0))

        # Информация о модели (теперь только для чтения)
        self.model_info_text = tk.Text(model_frame, height=20, bg='#3b3b3b', fg='white', wrap='word', state='disabled')
        scrollbar_model = ttk.Scrollbar(model_frame, orient="vertical", command=self.model_info_text.yview)
        self.model_info_text.configure(yscrollcommand=scrollbar_model.set)

        self.model_info_text.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=5)
        scrollbar_model.pack(side='right', fill='y', pady=5)

    def setup_generation_tab(self, notebook):
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="🎵 Генерация")

        # Основные параметры
        ttk.Label(gen_frame, text="Основные параметры:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5) 

        # Инструмент
        instrument_frame = ttk.Frame(gen_frame)
        instrument_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(instrument_frame, text="Инструмент:", style='Custom.TLabel').pack(side='left')
        self.instrument_var = tk.StringVar()
        instrument_combo = ttk.Combobox(instrument_frame, textvariable=self.instrument_var, width=30)
        instrument_combo['values'] = [f"{k}: {v}" for k, v in self.INSTRUMENTS.items()]
        instrument_combo.set("0: Acoustic Grand Piano")
        instrument_combo.pack(side='right')

        # Тип партии
        track_frame = ttk.Frame(gen_frame)
        track_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(track_frame, text="Тип партии:", style='Custom.TLabel').pack(side='left')
        self.track_type_var = tk.StringVar(value="melody")
        track_combo = ttk.Combobox(track_frame, textvariable=self.track_type_var, width=20)
        track_combo['values'] = ["melody", "bass", "chords", "orchestra", "custom"]
        track_combo.bind('<<ComboboxSelected>>', self.on_track_type_change)
        track_combo.pack(side='right')

        # Фрейм для настроек оркестра (изначально скрыт)
        self.orchestra_frame = ttk.LabelFrame(gen_frame, text="🎼 Настройки оркестра")
        self.setup_orchestra_controls()

        # Тональность
        key_frame = ttk.Frame(gen_frame)
        key_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(key_frame, text="Тональность:", style='Custom.TLabel').pack(side='left')
        self.key_var = tk.StringVar(value="C Major")
        key_combo = ttk.Combobox(key_frame, textvariable=self.key_var, width=15)
        key_combo['values'] = list(self.SCALES.keys())
        key_combo.pack(side='right')

        # Количество нот
        notes_frame = ttk.Frame(gen_frame)
        notes_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(notes_frame, text="Количество нот:", style='Custom.TLabel').pack(side='left')
        self.num_notes_var = tk.IntVar(value=200)
        notes_spin = ttk.Spinbox(notes_frame, from_=50, to=1000, textvariable=self.num_notes_var, width=10)
        notes_spin.pack(side='right')

        # Температура
        temp_frame = ttk.Frame(gen_frame)
        temp_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(temp_frame, text="Температура (креативность):", style='Custom.TLabel').pack(side='left')
        self.temperature_var = tk.DoubleVar(value=1.0)
        temp_scale = ttk.Scale(temp_frame, from_=0.3, to=2.0, orient='horizontal', 
                               variable=self.temperature_var, length=200)
        temp_scale.pack(side='right')
        self.temp_label = ttk.Label(temp_frame, text="1.0", style='Custom.TLabel')
        self.temp_label.pack(side='right', padx=(5, 0))
        temp_scale.configure(command=self.update_temp_label)

    def setup_orchestra_controls(self):
        """Создает элементы управления оркестром"""

        # Список инструментов оркестра
        instruments_frame = ttk.Frame(self.orchestra_frame)
        instruments_frame.pack(fill='both', expand=True, padx=5, pady=5)

        ttk.Label(instruments_frame, text="Инструменты оркестра:", style='Heading.TLabel').pack(anchor='w')

        # Фрейм для списка и кнопок
        list_frame = ttk.Frame(instruments_frame)
        list_frame.pack(fill='both', expand=True, pady=5)

        # Список выбранных инструментов
        self.orchestra_listbox = tk.Listbox(list_frame, height=6, bg='#3b3b3b', fg='white')
        scrollbar_orch = ttk.Scrollbar(list_frame, orient="vertical", command=self.orchestra_listbox.yview)
        self.orchestra_listbox.configure(yscrollcommand=scrollbar_orch.set)

        self.orchestra_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_orch.pack(side='right', fill='y')

        # Кнопки управления инструментами
        buttons_frame = ttk.Frame(instruments_frame)
        buttons_frame.pack(fill='x', pady=5)

        ttk.Button(buttons_frame, text="➕ Добавить инструмент", 
                   command=self.add_orchestra_instrument).pack(side='left', padx=2)
        ttk.Button(buttons_frame, text="🥁 Добавить ударные", 
                   command=self.add_drums).pack(side='left', padx=2)
        ttk.Button(buttons_frame, text="❌ Удалить", 
                   command=self.remove_orchestra_instrument).pack(side='left', padx=2)
        ttk.Button(buttons_frame, text="🔄 Очистить все", 
                   command=self.clear_orchestra_instruments).pack(side='left', padx=2)

        # Настройки генерации для каждого инструмента
        settings_frame = ttk.Frame(self.orchestra_frame)
        settings_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(settings_frame, text="Количество нот на инструмент:", style='Custom.TLabel').pack(side='left')
        self.notes_per_instrument = tk.IntVar(value=150)
        ttk.Spinbox(settings_frame, from_=50, to=500, textvariable=self.notes_per_instrument, width=8).pack(side='right')

    def on_track_type_change(self, event=None):
        """Показывает/скрывает настройки оркестра"""
        if self.track_type_var.get() == "orchestra":
            self.orchestra_frame.pack(fill='x', padx=10, pady=5)
            if not self.orchestra_instruments:
                self.add_default_orchestra()
        else:
            self.orchestra_frame.pack_forget()

    def add_default_orchestra(self):
        """Добавляет базовый состав оркестра"""
        default_instruments = [
            (48, "String Ensemble 1", "strings"),
            (0, "Acoustic Grand Piano", "piano"),
            (56, "Trumpet", "brass"),
            (40, "Violin", "strings"),
            (33, "Electric Bass (finger)", "bass")
        ]

        for program, name, role in default_instruments:
            self.orchestra_instruments.append({
                'program': program,
                'name': name,
                'role': role,
                'is_drum': False
            })

        self.update_orchestra_listbox()

    def add_orchestra_instrument(self):
        """Добавляет инструмент в оркестр"""
        # Создаем диалог выбора инструмента
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор инструмента")
        dialog.geometry("500x400")
        dialog.configure(bg='#2b2b2b')

        # Список всех инструментов
        ttk.Label(dialog, text="Выберите инструмент:", style='Heading.TLabel').pack(pady=5)

        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=5)

        instruments_listbox = tk.Listbox(listbox_frame, bg='#3b3b3b', fg='white')
        scrollbar_dialog = ttk.Scrollbar(listbox_frame, orient="vertical", command=instruments_listbox.yview)
        instruments_listbox.configure(yscrollcommand=scrollbar_dialog.set)

        # Заполняем список инструментов
        for program, name in self.INSTRUMENTS.items():
            instruments_listbox.insert(tk.END, f"{program}: {name}")

        instruments_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_dialog.pack(side='right', fill='y')

        # Выбор роли инструмента
        role_frame = ttk.Frame(dialog)
        role_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(role_frame, text="Роль в оркестре:", style='Custom.TLabel').pack(side='left')
        role_var = tk.StringVar(value="melody")
        role_combo = ttk.Combobox(role_frame, textvariable=role_var, width=15)
        role_combo['values'] = ["melody", "harmony", "bass", "rhythm", "solo"]
        role_combo.pack(side='right')

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        def add_selected():
            selection = instruments_listbox.curselection()
            if selection:
                item = instruments_listbox.get(selection[0])
                program = int(item.split(':')[0])
                name = item.split(': ', 1)[1]

                self.orchestra_instruments.append({
                    'program': program,
                    'name': name,
                    'role': role_var.get(),
                    'is_drum': False
                })

                self.update_orchestra_listbox()
                dialog.destroy()

        ttk.Button(button_frame, text="Добавить", command=add_selected).pack(side='right', padx=2)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side='right', padx=2)

    def add_drums(self):
        """Добавляет ударную установку"""
        drum_kit = [
            {'program': 0, 'name': 'Kick Drum', 'role': 'drums', 'drum_notes': [36], 'velocity': 120},
            {'program': 0, 'name': 'Snare Drum', 'role': 'drums', 'drum_notes': [38, 40], 'velocity': 110},
            {'program': 0, 'name': 'Hi-Hat', 'role': 'drums', 'drum_notes': [42, 44], 'velocity': 100},
            {'program': 0, 'name': 'Crash Cymbal', 'role': 'drums', 'drum_notes': [49, 57], 'velocity': 110},
        ]

        for drum in drum_kit:
            drum_safe = {
                'program': int(drum.get('program', 0)),
                'name': str(drum.get('name', 'Drum')),
                'role': str(drum.get('role', 'drums')),
                'is_drum': True,
                'drum_notes': list(drum.get('drum_notes', [36])),
                'velocity': int(drum.get('velocity', 100))
            }
            self.orchestra_instruments.append(drum_safe)

        self.update_orchestra_listbox()

    def remove_orchestra_instrument(self):
        """Удаляет выбранный инструмент"""
        selection = self.orchestra_listbox.curselection()
        if selection:
            del self.orchestra_instruments[selection[0]]
            self.update_orchestra_listbox()

    def clear_orchestra_instruments(self):
        """Очищает список инструментов"""
        self.orchestra_instruments = []
        self.update_orchestra_listbox()

    def update_orchestra_listbox(self):
        """Обновляет отображение списка инструментов"""
        self.orchestra_listbox.delete(0, tk.END)
        for i, instrument in enumerate(self.orchestra_instruments):
            role_icon = {
                "melody": "🎵",
                "harmony": "🎼",
                "bass": "🎸",
                "rhythm": "🥁",
                "solo": "⭐",
                "drums": "🥁"
            }.get(instrument['role'], "🎶")
            drum_mark = " [Drums]" if instrument.get('is_drum', False) else ""
            self.orchestra_listbox.insert(tk.END, f"{role_icon} {instrument['name']}{drum_mark}")

    def setup_advanced_tab(self, notebook):
        adv_frame = ttk.Frame(notebook)
        notebook.add(adv_frame, text="⚙️ Расширенные")

        # Ритмические параметры
        ttk.Label(adv_frame, text="Ритмические параметры:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)

        # Темп
        tempo_frame = ttk.Frame(adv_frame)
        tempo_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(tempo_frame, text="Темп:", style='Custom.TLabel').pack(side='left')
        self.tempo_var = tk.StringVar(value="Умеренно")
        tempo_combo = ttk.Combobox(tempo_frame, textvariable=self.tempo_var, width=15)
        tempo_combo['values'] = list(self.RHYTHMS.keys())
        tempo_combo.pack(side='right')

        # Диапазон высот
        ttk.Label(adv_frame, text="Диапазон высот:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=(10,5))

        pitch_frame = ttk.Frame(adv_frame)
        pitch_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(pitch_frame, text="От:", style='Custom.TLabel').pack(side='left')
        self.pitch_min_var = tk.IntVar(value=48)
        ttk.Spinbox(pitch_frame, from_=24, to=108, textvariable=self.pitch_min_var, width=5).pack(side='left', padx=(5,0))
        ttk.Label(pitch_frame, text="До:", style='Custom.TLabel').pack(side='left', padx=(20,0))
        self.pitch_max_var = tk.IntVar(value=84)
        ttk.Spinbox(pitch_frame, from_=24, to=108, textvariable=self.pitch_max_var, width=5).pack(side='left', padx=(5,0))

        # Музыкальные правила
        ttk.Label(adv_frame, text="Музыкальные правила:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=(10,5))

        rules_frame = ttk.Frame(adv_frame)
        rules_frame.pack(fill='x', padx=10, pady=2)

        self.use_scale_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rules_frame, text="Следовать тональности", variable=self.use_scale_var).pack(anchor='w')

        self.smooth_melody_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rules_frame, text="Плавная мелодия", variable=self.smooth_melody_var).pack(anchor='w')

        self.quantize_rhythm_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rules_frame, text="Квантизация ритма", variable=self.quantize_rhythm_var).pack(anchor='w')

        # Семпл для затравки
        ttk.Label(adv_frame, text="Семпл для затравки:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=(10,5))

        seed_frame = ttk.Frame(adv_frame)
        seed_frame.pack(fill='x', padx=10, pady=2)

        self.seed_type_var = tk.StringVar(value="random")
        ttk.Radiobutton(seed_frame, text="Случайный", variable=self.seed_type_var, value="random").pack(anchor='w')
        ttk.Radiobutton(seed_frame, text="Из MIDI файла", variable=self.seed_type_var, value="midi").pack(anchor='w')
        ttk.Radiobutton(seed_frame, text="Пользовательский", variable=self.seed_type_var, value="custom").pack(anchor='w')

        self.seed_file_var = tk.StringVar()
        seed_file_frame = ttk.Frame(adv_frame)
        seed_file_frame.pack(fill='x', padx=20, pady=2)
        ttk.Entry(seed_file_frame, textvariable=self.seed_file_var, width=40).pack(side='left', fill='x', expand=True)
        ttk.Button(seed_file_frame, text="Обзор", command=self.load_seed_file).pack(side='right')

    def setup_presets_tab(self, notebook):
        presets_frame = ttk.Frame(notebook)
        notebook.add(presets_frame, text="🎼 Пресеты")

        # Готовые пресеты
        ttk.Label(presets_frame, text="Готовые пресеты:", style='Heading.TLabel').pack(anchor='w', padx=10, pady=5)

        presets_list_frame = ttk.Frame(presets_frame)
        presets_list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Список пресетов
        self.presets_listbox = tk.Listbox(presets_list_frame, height=8, bg='#3b3b3b', fg='white')
        scrollbar = ttk.Scrollbar(presets_list_frame, orient="vertical", command=self.presets_listbox.yview)
        self.presets_listbox.configure(yscrollcommand=scrollbar.set)

        self.presets_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Кнопки управления пресетами
        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(preset_buttons_frame, text="Применить пресет", 
                   command=self.apply_preset).pack(side='left', padx=2)
        ttk.Button(preset_buttons_frame, text="Сохранить текущие настройки", 
                   command=self.save_preset).pack(side='left', padx=2)
        ttk.Button(preset_buttons_frame, text="Удалить пресет", 
                   command=self.delete_preset).pack(side='left', padx=2)

        # Предопределенные пресеты
        self.default_presets = {
            "🎹 Классическое пианино": {
                "instrument": "0: Acoustic Grand Piano",
                "track_type": "melody",
                "key": "C Major",
                "num_notes": 300,
                "temperature": 0.8,
                "tempo": "Умеренно",
                "pitch_min": 60,
                "pitch_max": 84,
                "use_scale": True,
                "smooth_melody": True,
                "quantize_rhythm": True
            },
            "🎸 Блюзовая гитара": {
                "instrument": "27: Electric Guitar (clean)",
                "track_type": "melody",
                "key": "A Minor",
                "num_notes": 250,
                "temperature": 1.2,
                "tempo": "Умеренно",
                "pitch_min": 48,
                "pitch_max": 72,
                "use_scale": True,
                "smooth_melody": True,
                "quantize_rhythm": False
            },
            "🎺 Джазовая труба": {
                "instrument": "56: Trumpet",
                "track_type": "melody",
                "key": "Bb Major",
                "num_notes": 200,
                "temperature": 1.1,
                "tempo": "Быстро",
                "pitch_min": 60,
                "pitch_max": 96,
                "use_scale": False,
                "smooth_melody": False,
                "quantize_rhythm": True
            },
            "🎻 Лирическая скрипка": {
                "instrument": "40: Violin",
                "track_type": "melody",
                "key": "G Major",
                "num_notes": 350,
                "temperature": 0.9,
                "tempo": "Медленно",
                "pitch_min": 67,
                "pitch_max": 108,
                "use_scale": True,
                "smooth_melody": True,
                "quantize_rhythm": True
            },
            "🎸 Бас-гитара": {
                "instrument": "33: Electric Bass (finger)",
                "track_type": "bass",
                "key": "E Minor",
                "num_notes": 150,
                "temperature": 0.7,
                "tempo": "Умеренно",
                "pitch_min": 24,
                "pitch_max": 48,
                "use_scale": True,
                "smooth_melody": False,
                "quantize_rhythm": True
            },
            "🎹 Аккордовое сопровождение": {
                "instrument": "0: Acoustic Grand Piano",
                "track_type": "chords",
                "key": "F Major",
                "num_notes": 100,
                "temperature": 0.6,
                "tempo": "Медленно",
                "pitch_min": 48,
                "pitch_max": 72,
                "use_scale": True,
                "smooth_melody": False,
                "quantize_rhythm": True
            },
            "🎷 Саксофон соло": {
                "instrument": "65: Alto Sax",
                "track_type": "melody",
                "key": "D Minor",
                "num_notes": 280,
                "temperature": 1.3,
                "tempo": "Умеренно",
                "pitch_min": 55,
                "pitch_max": 84,
                "use_scale": False,
                "smooth_melody": True,
                "quantize_rhythm": False
            },
            "💫 Электронный синтез": {
                "instrument": "80: Lead 1 (square)",
                "track_type": "melody",
                "key": "Chromatic",
                "num_notes": 400,
                "temperature": 1.5,
                "tempo": "Быстро",
                "pitch_min": 36,
                "pitch_max": 96,
                "use_scale": False,
                "smooth_melody": False,
                "quantize_rhythm": True
            },
            "🎼 Симфонический оркестр": {
                "instrument": "48: String Ensemble 1",
                "track_type": "orchestra",
                "key": "C Major",
                "num_notes": 500,
                "temperature": 0.9,
                "tempo": "Умеренно",
                "pitch_min": 36,
                "pitch_max": 108,
                "use_scale": True,
                "smooth_melody": True,
                "quantize_rhythm": True
            },
            "🎭 Драматический оркестр": {
                "instrument": "49: String Ensemble 2",
                "track_type": "orchestra",
                "key": "D Minor",
                "num_notes": 600,
                "temperature": 1.1,
                "tempo": "Медленно",
                "pitch_min": 24,
                "pitch_max": 108,
                "use_scale": True,
                "smooth_melody": True,
                "quantize_rhythm": True
            },
            "🌟 Торжественный марш": {
                "instrument": "61: Brass Section",
                "track_type": "orchestra",
                "key": "Bb Major",
                "num_notes": 400,
                "temperature": 0.8,
                "tempo": "Умеренно",
                "pitch_min": 48,
                "pitch_max": 96,
                "use_scale": True,
                "smooth_melody": False,
                "quantize_rhythm": True
            }
        }

        self.load_presets()

    def setup_control_buttons(self):
        # Кнопки управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=10)

        # Генерация
        generate_frame = ttk.Frame(control_frame)
        generate_frame.pack(side='left', fill='x', expand=True)

        self.generate_button = ttk.Button(generate_frame, text="🎵 Генерировать музыку", 
                                         command=self.generate_music, width=30)
        self.generate_button.pack(side='left', padx=2)

        self.play_button = ttk.Button(generate_frame, text="🔊 Воспроизвести", 
                                     command=self.play_music, width=20)
        self.play_button.pack(side='left', padx=2)

        self.save_button = ttk.Button(generate_frame, text="💾 Сохранить как...", 
                                     command=self.save_music, width=20)
        self.save_button.pack(side='left', padx=2)

        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, mode='determinate', maximum=100)
        self.progress.pack(fill='x', padx=10, pady=5)

    def update_temp_label(self, value):
        self.temp_label.config(text=f"{float(value):.1f}")

    def get_output_path(self):
        """Создает и возвращает путь к папке для сохранения файлов"""
        # Получаем путь к директории, где находится скрипт
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Создаем путь к папке Outputs
        outputs_dir = os.path.join(script_dir, 'Outputs')
        
        # Получаем текущую дату в формате ДД.ММ.ГГГГ
        current_date = datetime.now().strftime('%d.%m.%Y')
        
        # Создаем путь к папке с датой
        date_dir = os.path.join(outputs_dir, current_date)
        
        # Создаем папки, если их не существует
        os.makedirs(date_dir, exist_ok=True)
        
        return date_dir

    def generate_unique_filename(self, base_dir, prefix="music", extension=".mid"):
        """Генерирует уникальное имя файла"""
        timestamp = datetime.now().strftime('%H-%M-%S')
        counter = 1
        
        while True:
            if counter == 1:
                filename = f"{prefix}_{timestamp}{extension}"
            else:
                filename = f"{prefix}_{timestamp}_{counter}{extension}"
            
            filepath = os.path.join(base_dir, filename)
            
            if not os.path.exists(filepath):
                return filepath
            
            counter += 1

    def load_model_safe_gui(self, model_path):
        """Безопасная загрузка модели для GUI"""
        custom_objects = {
            'mse': tf.keras.losses.MeanSquaredError(),
            'keras.metrics.mse': tf.keras.metrics.MeanSquaredError(),
            'sparse_categorical_crossentropy': tf.keras.losses.SparseCategoricalCrossentropy(),
            'accuracy': tf.keras.metrics.Accuracy(),
        }

        try:
            # Первая попытка - с пользовательскими объектами
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
            return model, "✅ Модель загружена с полной функциональностью"
        except Exception as e1:
            try:
                # Вторая попытка - без компиляции
                model = tf.keras.models.load_model(model_path, compile=False)
                return model, "⚠️ Модель загружена без компиляции"
            except Exception as e2:
                raise Exception(f"Не удалось загрузить модель.\nОшибка 1: {str(e1)[:100]}...\nОшибка 2: {str(e2)[:100]}...")

    def load_model(self):
        """Обновленная функция загрузки модели с обработкой ошибок"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл модели",
            filetypes=[("H5 files", "*.h5"), ("All files", "*.*")]
        )
        if file_path:
            self.model_path_var.set(file_path)
            self.model_path = file_path

            # Показываем прогресс
            self.status_var.set("Загрузка модели...")
            self.progress.start()

            def load_in_thread():
                try:
                    model, status = self.load_model_safe_gui(file_path)
                    self.model = model
                    
                    # Получаем информацию о модели
                    info_text = f"📁 Путь: {file_path}\n\n"
                    info_text += f"🔧 Статус: {status}\n\n"
                    info_text += f"📊 Архитектура модели:\n"
                    info_text += f"  • Количество слоёв: {len(model.layers)}\n"
                    
                    # Информация о входе и выходе
                    try:
                        info_text += f"  • Входная форма: {model.input_shape}\n"
                        info_text += f"  • Выходная форма: {model.output_shape}\n"
                    except:
                        info_text += f"  • Входная/выходная форма: недоступна\n"
                    
                    # Параметры модели
                    try:
                        total_params = model.count_params()
                        info_text += f"  • Всего параметров: {total_params:,}\n"
                    except:
                        info_text += f"  • Параметры: недоступно\n"
                    
                    info_text += f"\n📝 Слои модели:\n"
                    for i, layer in enumerate(model.layers[:10]):  # Показываем первые 10 слоев
                        info_text += f"  {i+1}. {layer.__class__.__name__}"
                        try:
                            info_text += f" - {layer.output_shape}\n"
                        except:
                            info_text += "\n"
                    
                    if len(model.layers) > 10:
                        info_text += f"  ... и ещё {len(model.layers) - 10} слоёв\n"
                    
                    # Обновляем UI
                    self.root.after(0, lambda: self.update_model_info(info_text))
                    self.root.after(0, lambda: self.status_var.set("✅ Модель успешно загружена"))
                    self.root.after(0, lambda: messagebox.showinfo("Успех", "Модель успешно загружена!"))
                    
                except Exception as e:
                    error_msg = f"Ошибка загрузки модели:\n{str(e)}"
                    self.root.after(0, lambda: self.update_model_info(error_msg))
                    self.root.after(0, lambda: self.status_var.set("❌ Ошибка загрузки модели"))
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", error_msg))
                
                finally:
                    self.root.after(0, self.progress.stop)

            thread = threading.Thread(target=load_in_thread, daemon=True)
            thread.start()

    def generate_music(self):
        if self.model is None:
            messagebox.showerror("Ошибка", "Сначала загрузите модель!")
            return

        self.status_var.set("Генерация музыки...")
        self.generate_button.config(state='disabled')
        self.progress['value'] = 0

        def generate_in_thread():
            try:
                # Определяем тип генерации
                track_type = self.track_type_var.get()
                
                if track_type == "orchestra":
                    # Генерация оркестра
                    self.generate_orchestra()
                else:
                    # Обычная генерация
                    # Получаем параметры
                    instrument_str = self.instrument_var.get()
                    instrument = int(instrument_str.split(':')[0])
                    
                    num_notes = self.num_notes_var.get()
                    temperature = self.temperature_var.get()
                    key = self.key_var.get()
                    tempo = self.tempo_var.get()
                    
                    # Генерируем ноты
                    self.progress['value'] = 30
                    self.generated_notes = self.generate_notes_with_model(
                        num_notes, temperature, key, tempo, track_type
                    )
                    
                    # Создаем MIDI
                    self.progress['value'] = 60
                    self.generated_midi = self.notes_to_midi(
                        self.generated_notes, instrument, track_type
                    )
                    
                    self.generated_instrument = instrument
                
                # Автоматически сохраняем файл
                self.progress['value'] = 80
                output_dir = self.get_output_path()
                
                # Генерируем имя файла на основе параметров
                track_name = track_type if track_type != "orchestra" else "orchestra"
                instrument_name = self.instrument_var.get().split(': ')[1].replace(' ', '_') if track_type != "orchestra" else "ensemble"
                key_name = self.key_var.get().replace(' ', '_')
                
                prefix = f"{track_name}_{instrument_name}_{key_name}"
                self.generated_filename = self.generate_unique_filename(output_dir, prefix)
                
                # Сохраняем MIDI файл
                self.generated_midi.write(self.generated_filename)
                
                self.progress['value'] = 100
                self.status_var.set(f"✅ Музыка сгенерирована и сохранена: {os.path.basename(self.generated_filename)}")
                
                messagebox.showinfo("Успех", 
                    f"Музыка успешно сгенерирована!\n\n"
                    f"Сохранено в:\n{self.generated_filename}\n\n"
                    f"Количество нот: {num_notes if track_type != 'orchestra' else 'множество'}\n"
                    f"Инструмент: {self.instrument_var.get()}\n"
                    f"Тональность: {key}")

            except Exception as e:
                self.status_var.set("❌ Ошибка при генерации")
                messagebox.showerror("Ошибка", f"Не удалось сгенерировать музыку:\n{str(e)}")
            
            finally:
                self.generate_button.config(state='normal')
                self.progress['value'] = 0

        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

    def play_music(self):
        """Открывает плеер для воспроизведения музыки"""
        if self.generated_midi is None:
            messagebox.showerror("Ошибка", "Сначала сгенерируйте музыку!")
            return
        
        try:
            # Получаем название файла
            if hasattr(self, 'generated_filename') and self.generated_filename:
                filename = os.path.basename(self.generated_filename)
                saved_path = self.generated_filename
            else:
                filename = "Сгенерированная музыка"
                saved_path = None
            
            # Создаем и открываем плеер с передачей пути к сохраненному файлу
            player = MusicPlayer(self.root, self.generated_midi, filename, saved_path)
            
            self.status_var.set("🔊 Плеер открыт")
            
        except Exception as e:
            messagebox.showerror("Ошибка воспроизведения", 
                            f"Не удалось открыть плеер:\n{str(e)}\n\n"
                            f"Попробуйте сохранить файл и открыть его вручную.")
            self.status_var.set("❌ Ошибка при открытии плеера")

    def save_music(self):
        """Сохраняет сгенерированную музыку с выбором пути"""
        if self.generated_midi is None:
            messagebox.showerror("Ошибка", "Сначала сгенерируйте музыку!")
            return

        # Определяем начальное имя файла и директорию
        if hasattr(self, 'generated_filename') and self.generated_filename:
            initial_filename = os.path.basename(self.generated_filename)
            initial_dir = os.path.dirname(self.generated_filename)
        else:
            initial_filename = "generated_music.mid"
            initial_dir = self.get_output_path()

        # Открываем диалог сохранения файла
        file_path = filedialog.asksaveasfilename(
            title="💾 Сохранить музыку как",
            defaultextension=".mid",
            initialfile=initial_filename,
            initialdir=initial_dir,
            filetypes=[
                ("MIDI файлы", "*.mid *.midi"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Создаем директорию, если её не существует
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Сохраняем MIDI файл
                self.generated_midi.write(file_path)
                
                # Получаем информацию о файле
                file_size = os.path.getsize(file_path)
                file_size_kb = file_size / 1024
                
                # Показываем подробное сообщение об успехе
                messagebox.showinfo(
                    "✅ Успешно сохранено", 
                    f"Музыка успешно сохранена!\n\n"
                    f"📁 Путь:\n{file_path}\n\n"
                    f"📊 Размер: {file_size_kb:.2f} КБ ({file_size} байт)\n"
                    f"🎵 Формат: MIDI"
                )
                
                self.status_var.set(f"✅ Сохранено: {os.path.basename(file_path)}")
                
                # Обновляем текущее имя файла
                self.generated_filename = file_path
                
                # Спрашиваем, открыть ли папку с файлом
                if messagebox.askyesno("Открыть папку?", "Хотите открыть папку с сохранённым файлом?"):
                    self.open_file_location(file_path)
                
            except PermissionError:
                messagebox.showerror(
                    "Ошибка доступа", 
                    f"Нет прав для сохранения в эту папку:\n{os.path.dirname(file_path)}\n\n"
                    f"Выберите другое расположение."
                )
                self.status_var.set("❌ Ошибка: нет прав доступа")
            except Exception as e:
                messagebox.showerror(
                    "Ошибка сохранения", 
                    f"Не удалось сохранить файл:\n\n{str(e)}"
                )
                self.status_var.set("❌ Ошибка при сохранении")
        else:
            self.status_var.set("Сохранение отменено")

    def open_file_location(self, file_path):
        """Открывает папку с файлом в проводнике"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(os.path.dirname(file_path))
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', os.path.dirname(file_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', os.path.dirname(file_path)])
        except Exception as e:
            print(f"Не удалось открыть папку: {e}")

    def load_seed_file(self):
        """Загрузка MIDI файла для затравки"""
        file_path = filedialog.askopenfilename(
            title="Выберите MIDI файл",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")]
        )
        if file_path:
            self.seed_file_var.set(file_path)

    def load_presets(self):
        """Загружает пресеты в список"""
        self.presets_listbox.delete(0, tk.END)
        
        # Добавляем предопределенные пресеты
        for preset_name in self.default_presets.keys():
            self.presets_listbox.insert(tk.END, preset_name)
        
        # Пытаемся загрузить пользовательские пресеты
        try:
            presets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
                    for preset_name in user_presets.keys():
                        if preset_name not in self.default_presets:
                            self.presets_listbox.insert(tk.END, f"👤 {preset_name}")
        except Exception as e:
            print(f"Не удалось загрузить пользовательские пресеты: {e}")

    def apply_preset(self):
        """Применяет выбранный пресет"""
        selection = self.presets_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пресет для применения")
            return
        
        preset_name = self.presets_listbox.get(selection[0])
        
        # Убираем эмодзи пользовательского пресета
        if preset_name.startswith("👤 "):
            preset_name = preset_name[2:]
        
        # Получаем настройки пресета
        preset = None
        if preset_name in self.default_presets:
            preset = self.default_presets[preset_name]
        else:
            # Загружаем из пользовательских
            try:
                presets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')
                with open(presets_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
                    if preset_name in user_presets:
                        preset = user_presets[preset_name]
            except:
                pass
        
        if preset:
            # Применяем настройки
            self.instrument_var.set(preset['instrument'])
            self.track_type_var.set(preset['track_type'])
            self.key_var.set(preset['key'])
            self.num_notes_var.set(preset['num_notes'])
            self.temperature_var.set(preset['temperature'])
            self.tempo_var.set(preset['tempo'])
            self.pitch_min_var.set(preset['pitch_min'])
            self.pitch_max_var.set(preset['pitch_max'])
            self.use_scale_var.set(preset['use_scale'])
            self.smooth_melody_var.set(preset['smooth_melody'])
            self.quantize_rhythm_var.set(preset['quantize_rhythm'])
            
            # Обновляем отображение температуры
            self.update_temp_label(preset['temperature'])
            
            # Обрабатываем изменение типа трека
            self.on_track_type_change()
            
            self.status_var.set(f"✅ Применён пресет: {preset_name}")
            messagebox.showinfo("Успех", f"Пресет '{preset_name}' успешно применён!")
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить пресет")

    def save_preset(self):
        """Сохраняет текущие настройки как пресет"""
        preset_name = simpledialog.askstring("Сохранить пресет", 
                                            "Введите название пресета:",
                                            parent=self.root)
        
        if not preset_name:
            return
        
        # Создаем словарь с текущими настройками
        preset = {
            "instrument": self.instrument_var.get(),
            "track_type": self.track_type_var.get(),
            "key": self.key_var.get(),
            "num_notes": self.num_notes_var.get(),
            "temperature": self.temperature_var.get(),
            "tempo": self.tempo_var.get(),
            "pitch_min": self.pitch_min_var.get(),
            "pitch_max": self.pitch_max_var.get(),
            "use_scale": self.use_scale_var.get(),
            "smooth_melody": self.smooth_melody_var.get(),
            "quantize_rhythm": self.quantize_rhythm_var.get()
        }
        
        try:
            presets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')
            
            # Загружаем существующие пресеты
            user_presets = {}
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
            
            # Добавляем новый пресет
            user_presets[preset_name] = preset
            
            # Сохраняем
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(user_presets, f, indent=4, ensure_ascii=False)
            
            # Обновляем список
            self.load_presets()
            
            self.status_var.set(f"✅ Пресет '{preset_name}' сохранён")
            messagebox.showinfo("Успех", f"Пресет '{preset_name}' успешно сохранён!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить пресет:\n{str(e)}")

    def delete_preset(self):
        """Удаляет выбранный пользовательский пресет"""
        selection = self.presets_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пресет для удаления")
            return
        
        preset_name = self.presets_listbox.get(selection[0])
        
        # Проверяем, что это пользовательский пресет
        if not preset_name.startswith("👤 "):
            messagebox.showwarning("Предупреждение", 
                                 "Невозможно удалить предустановленный пресет")
            return
        
        preset_name = preset_name[2:]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Вы уверены, что хотите удалить пресет '{preset_name}'?"):
            try:
                presets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.json')
                
                with open(presets_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
                
                if preset_name in user_presets:
                    del user_presets[preset_name]
                    
                    with open(presets_file, 'w', encoding='utf-8') as f:
                        json.dump(user_presets, f, indent=4, ensure_ascii=False)
                    
                    self.load_presets()
                    self.status_var.set(f"✅ Пресет '{preset_name}' удалён")
                    messagebox.showinfo("Успех", f"Пресет '{preset_name}' удалён")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить пресет:\n{str(e)}")

    # Заглушки для функций генерации (необходимо реализовать в соответствии с вашей моделью)
    def generate_notes_with_model(self, num_notes, temperature, key, tempo, track_type):
        """Генерирует ноты с помощью модели"""
        # Здесь должна быть ваша логика генерации нот
        # Это заглушка - замените на реальную реализацию
        notes = []
        scale = self.SCALES[key]
        rhythm_params = self.RHYTHMS[tempo]
        
        current_time = 0
        for i in range(num_notes):
            pitch = np.random.choice(scale)
            start = current_time
            duration = np.random.uniform(rhythm_params['duration_min'], rhythm_params['duration_max'])
            step = np.random.uniform(rhythm_params['step_min'], rhythm_params['step_max'])
            velocity = np.random.randint(60, 100)
            
            notes.append({
                'pitch': pitch,
                'start': start,
                'end': start + duration,
                'velocity': velocity
            })
            
            current_time += step
        
        return notes

    def notes_to_midi(self, notes, instrument_program, track_type):
        """Конвертирует ноты в MIDI объект"""
        midi = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=instrument_program)
        
        for note_data in notes:
            note = pretty_midi.Note(
                velocity=note_data['velocity'],
                pitch=note_data['pitch'],
                start=note_data['start'],
                end=note_data['end']
            )
            instrument.notes.append(note)
        
        midi.instruments.append(instrument)
        return midi

    def generate_orchestra(self):
        """Генерирует оркестровую композицию"""
        if not self.orchestra_instruments:
            messagebox.showerror("Ошибка", 
                               "Добавьте инструменты в оркестр перед генерацией!")
            return
        
        try:
            # Создаем MIDI объект
            self.generated_midi = pretty_midi.PrettyMIDI()
            
            # Получаем общие параметры
            key = self.key_var.get()
            tempo = self.tempo_var.get()
            temperature = self.temperature_var.get()
            notes_per_inst = self.notes_per_instrument.get()
            
            # Генерируем партию для каждого инструмента
            for inst_data in self.orchestra_instruments:
                is_drum = inst_data.get('is_drum', False)
                
                if is_drum:
                    # Создаем ударный инструмент
                    drum_instrument = pretty_midi.Instrument(
                        program=inst_data['program'],
                        is_drum=True
                    )
                    
                    # Генерируем паттерн ударных
                    drum_notes = self.generate_drum_pattern(
                        inst_data.get('drum_notes', [36]),
                        inst_data.get('velocity', 100),
                        notes_per_inst
                    )
                    
                    for note_data in drum_notes:
                        note = pretty_midi.Note(
                            velocity=note_data['velocity'],
                            pitch=note_data['pitch'],
                            start=note_data['start'],
                            end=note_data['end']
                        )
                        drum_instrument.notes.append(note)
                    
                    self.generated_midi.instruments.append(drum_instrument)
                    
                else:
                    # Создаем обычный инструмент
                    instrument = pretty_midi.Instrument(program=inst_data['program'])
                    
                    # Генерируем ноты в зависимости от роли
                    role = inst_data.get('role', 'melody')
                    notes = self.generate_notes_with_model(
                        notes_per_inst,
                        temperature,
                        key,
                        tempo,
                        role
                    )
                    
                    for note_data in notes:
                        note = pretty_midi.Note(
                            velocity=note_data['velocity'],
                            pitch=note_data['pitch'],
                            start=note_data['start'],
                            end=note_data['end']
                        )
                        instrument.notes.append(note)
                    
                    self.generated_midi.instruments.append(instrument)
            
            self.status_var.set("✅ Оркестровая композиция сгенерирована")
            
        except Exception as e:
            raise Exception(f"Ошибка генерации оркестра: {str(e)}")

    def generate_drum_pattern(self, drum_notes, velocity, num_hits):
        """Генерирует паттерн для ударных инструментов"""
        pattern = []
        current_time = 0
        beat_duration = 0.5  # Длительность одного удара
        
        for i in range(num_hits):
            # Выбираем случайную ноту из доступных
            pitch = np.random.choice(drum_notes)
            
            pattern.append({
                'pitch': pitch,
                'start': current_time,
                'end': current_time + beat_duration,
                'velocity': velocity + np.random.randint(-10, 10)
            })
            
            # Варьируем ритм
            current_time += np.random.choice([0.25, 0.5, 1.0])
        
        return pattern

    def run(self):
        """Запускает приложение"""
        self.root.mainloop()


# Точка входа в программу
if __name__ == "__main__":
    app = MusicGeneratorGUI()
    app.run()