import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import calendar
import os
import sys
import webbrowser
from jinja2 import Environment, FileSystemLoader

# Создаём главное окно
root = tk.Tk()
root.title("Генератор календаря мероприятий")
root.geometry("1000x650")
root.resizable(True, True)
root.configure(bg="#e0e8f0")

# Применяем современную тему и кастомизируем стиль
style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", padding=10, font=("Helvetica", 11, "bold"), background="#4CAF50", foreground="white")
style.map("TButton", background=[('active', '#45a049')], foreground=[('active', 'white')])
style.configure("TLabel", font=("Helvetica", 11), background="#e0e8f0", foreground="#333333")
style.configure("TFrame", background="#e0e8f0")
style.configure("TEntry", font=("Helvetica", 11))

# Переменные
year_var = tk.StringVar()
month_var = tk.StringVar()
events = []
header_title = "Афиша мероприятий"
filter_text = "Фильтр по библиотекам:"

# Словарь месяцев
months = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# Функция добавления мероприятия
def add_event():
    date = date_entry.get()
    title = title_entry.get()
    time = time_entry.get()
    place = place_entry.get()
    info = info_entry.get()
    if date and title:
        try:
            date_int = int(date)
            events.append({"date": date_int, "title": title, "time": time, "place": place, "info": info})
            status_label.config(text=f"Добавлено: {date} - {title}")
            clear_entries()
            update_event_list()
        except ValueError:
            status_label.config(text="Ошибка: дата должна быть числом!")
    else:
        status_label.config(text="Ошибка: заполните дату и название!")

# Функция очистки полей ввода
def clear_entries():
    date_entry.delete(0, tk.END)
    title_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)
    place_entry.delete(0, tk.END)
    info_entry.delete(0, tk.END)

# Функция обновления списка мероприятий
def update_event_list():
    event_listbox.delete(0, tk.END)
    for i, event in enumerate(events):
        event_listbox.insert(tk.END, f"{event['date']} - {event['title']} ({event['place']})")

# Функция редактирования выбранного мероприятия
def edit_event(event=None):
    selected = event_listbox.curselection()
    if not selected:
        messagebox.showwarning("Предупреждение", "Выберите мероприятие для редактирования!")
        return
    index = selected[0]
    event_data = events[index]

    date_entry.delete(0, tk.END)
    date_entry.insert(0, event_data["date"])
    title_entry.delete(0, tk.END)
    title_entry.insert(0, event_data["title"])
    time_entry.delete(0, tk.END)
    time_entry.insert(0, event_data["time"])
    place_entry.delete(0, tk.END)
    place_entry.insert(0, event_data["place"])
    info_entry.delete(0, tk.END)
    info_entry.insert(0, event_data["info"])

    add_button.grid_remove()
    save_button = ttk.Button(input_frame, text="Сохранить изменения", command=lambda: save_edit(save_button))
    save_button.grid(row=7, column=0, columnspan=2, pady=10)

    def save_edit(button):
        new_date = date_entry.get()
        new_title = title_entry.get()
        new_time = time_entry.get()
        new_place = place_entry.get()
        new_info = info_entry.get()
        if new_date and new_title:
            try:
                new_date_int = int(new_date)
                events[index] = {"date": new_date_int, "title": new_title, "time": new_time, "place": new_place, "info": new_info}
                status_label.config(text=f"Отредактировано: {new_date} - {new_title}")
                clear_entries()
                update_event_list()
                button.grid_remove()
                add_button.grid(row=7, column=0, columnspan=2, pady=10)
            except ValueError:
                status_label.config(text="Ошибка: дата должна быть числом!")
        else:
            status_label.config(text="Ошибка: заполните дату и название!")

# Функция предпросмотра в браузере
def update_preview():
    if not events:
        messagebox.showwarning("Предупреждение", "Добавьте хотя бы одно мероприятие для предпросмотра!")
        return
    year = year_var.get()
    month = month_var.get()
    if not year or not month:
        status_label.config(text="Введите год и месяц для предпросмотра")
        return
    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            status_label.config(text="Месяц должен быть от 1 до 12")
            return

        month_name = months[month]
        days_in_month = calendar.monthrange(year, month)[1]
        start_day = calendar.monthrange(year, month)[0]
        libraries = sorted(set(event["place"] for event in events))

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        templates_path = os.path.join(base_path, 'templates')
        env = Environment(loader=FileSystemLoader(templates_path))
        template = env.get_template('calendar_template.html')

        output = template.render(
            year=year,
            month_name=month_name,
            events=events,
            libraries=libraries,
            start_day=start_day,
            days_in_month=days_in_month,
            header_title=header_title,
            filter_text=filter_text
        )

        preview_file = "preview.html"
        with open(preview_file, "w", encoding="utf-8") as f:
            f.write(output)

        webbrowser.open(f"file://{os.path.abspath(preview_file)}")

    except Exception as e:
        status_label.config(text=f"Ошибка предпросмотра: {str(e)}")

# Функция настроек
def configure_calendar():
    config_window = tk.Toplevel(root)
    config_window.title("Настройки")
    config_window.geometry("400x200")
    config_window.configure(bg="#e0e8f0")

    ttk.Label(config_window, text="Заголовок:", font=("Helvetica", 11)).pack(pady=10)
    header_entry = ttk.Entry(config_window, width=40, font=("Helvetica", 11))
    header_entry.insert(0, header_title)
    header_entry.pack(pady=5)

    ttk.Label(config_window, text="Текст фильтра:", font=("Helvetica", 11)).pack(pady=10)
    filter_entry = ttk.Entry(config_window, width=40, font=("Helvetica", 11))
    filter_entry.insert(0, filter_text)
    filter_entry.pack(pady=5)

    def save_config():
        global header_title, filter_text
        header_title = header_entry.get()
        filter_text = filter_entry.get()
        config_window.destroy()
        status_label.config(text="Настройки сохранены")

    ttk.Button(config_window, text="Сохранить", command=save_config).pack(pady=15)

# Функция генерации календаря
def generate_calendar():
    year = year_var.get()
    month = month_var.get()
    if not year or not month:
        status_label.config(text="Ошибка: введите год и месяц!")
        return
    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            status_label.config(text="Ошибка: месяц должен быть от 1 до 12")
            return

        month_name = months[month]
        days_in_month = calendar.monthrange(year, month)[1]
        start_day = calendar.monthrange(year, month)[0]
        libraries = sorted(set(event["place"] for event in events))

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        templates_path = os.path.join(base_path, 'templates')
        env = Environment(loader=FileSystemLoader(templates_path))
        template = env.get_template('calendar_template.html')

        output = template.render(
            year=year,
            month_name=month_name,
            events=events,
            libraries=libraries,
            start_day=start_day,
            days_in_month=days_in_month,
            header_title=header_title,
            filter_text=filter_text
        )

        filename = f"calendar_{year}_{month}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
        status_label.config(text=f"Календарь сохранён как {filename}")

    except Exception as e:
        status_label.config(text=f"Ошибка: {str(e)}")

# Функции для работы с буфером обмена
def handle_keypress(event):
    widget = root.focus_get()
    if not (isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry)):
        return  # Обрабатываем только поля ввода

    # Проверяем, нажат ли Control (event.state & 0x4 — бит для Control)
    if event.state & 0x4:  # Control pressed
        if event.keycode == 67:  # Ctrl+C
            try:
                selected_text = widget.get()[widget.index("sel.first"):widget.index("sel.last")]
                root.clipboard_clear()
                root.clipboard_append(selected_text)
            except tk.TclError:
                pass
            return "break"
        elif event.keycode == 86:  # Ctrl+V
            try:
                clipboard_text = root.clipboard_get()
                widget.insert(tk.INSERT, clipboard_text)
            except tk.TclError:
                pass
            return "break"
        elif event.keycode == 88:  # Ctrl+X
            try:
                selected_text = widget.get()[widget.index("sel.first"):widget.index("sel.last")]
                root.clipboard_clear()
                root.clipboard_append(selected_text)
                widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            return "break"

# Привязка события <KeyPress> для перехвата всех нажатий клавиш
root.bind_all("<KeyPress>", handle_keypress)
# Альтернативные комбинации для Windows
root.bind_all("<Control-Insert>", lambda e: handle_paste(e))
root.bind_all("<Shift-Insert>", lambda e: handle_paste(e))
root.bind_all("<Shift-Delete>", lambda e: handle_cut(e))

def handle_paste(event):
    widget = root.focus_get()
    if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry):
        try:
            clipboard_text = root.clipboard_get()
            widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass
    return "break"

def handle_cut(event):
    widget = root.focus_get()
    if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry):
        try:
            selected_text = widget.get()[widget.index("sel.first"):widget.index("sel.last")]
            root.clipboard_clear()
            root.clipboard_append(selected_text)
            widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
    return "break"

# Интерфейс
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill="both", expand=True)

# Секция ввода даты
date_frame = ttk.LabelFrame(main_frame, text="Дата и месяц", padding="10")
date_frame.pack(fill="x", pady=(0, 10))
ttk.Label(date_frame, text="Год:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
year_entry = ttk.Entry(date_frame, textvariable=year_var, width=20)
year_entry.grid(row=0, column=1, padx=10, pady=5)
ttk.Label(date_frame, text="Месяц (1-12):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
month_entry = ttk.Entry(date_frame, textvariable=month_var, width=20)
month_entry.grid(row=1, column=1, padx=10, pady=5)

# Секция ввода мероприятий
input_frame = ttk.LabelFrame(main_frame, text="Добавление мероприятия", padding="10")
input_frame.pack(fill="x", pady=10)
ttk.Label(input_frame, text="Дата:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
date_entry = ttk.Entry(input_frame, width=30)
date_entry.grid(row=0, column=1, padx=10, pady=5)
ttk.Label(input_frame, text="Название:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
title_entry = ttk.Entry(input_frame, width=30)
title_entry.grid(row=1, column=1, padx=10, pady=5)
ttk.Label(input_frame, text="Время:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
time_entry = ttk.Entry(input_frame, width=30)
time_entry.grid(row=2, column=1, padx=10, pady=5)
ttk.Label(input_frame, text="Место:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
place_entry = ttk.Entry(input_frame, width=30)
place_entry.grid(row=3, column=1, padx=10, pady=5)
ttk.Label(input_frame, text="Описание:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
info_entry = ttk.Entry(input_frame, width=30)
info_entry.grid(row=4, column=1, padx=10, pady=5)

# Кнопки управления
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill="x", pady=10)
add_button = ttk.Button(input_frame, text="Добавить мероприятие", command=add_event)
add_button.grid(row=7, column=0, columnspan=2, pady=10)
ttk.Button(button_frame, text="Предпросмотр", command=update_preview).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Генерация календаря", command=generate_calendar).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Настройки", command=configure_calendar).pack(side=tk.LEFT, padx=5)

# Статус
status_label = ttk.Label(main_frame, text="Готов к работе", anchor="center", font=("Helvetica", 10, "italic"))
status_label.pack(pady=10)

# Секция списка мероприятий
event_frame = ttk.LabelFrame(main_frame, text="Список мероприятий", padding="10")
event_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
event_listbox = tk.Listbox(event_frame, height=20, width=40, font=("Helvetica", 11), bg="#ffffff", fg="#333333", relief="flat", borderwidth=1)
event_listbox.pack(fill="both", expand=True)
event_listbox.bind("<Double-Button-1>", edit_event)
ttk.Button(event_frame, text="Редактировать выбранное", command=edit_event).pack(pady=10)

# Запуск
root.mainloop()