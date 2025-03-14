import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import colorchooser
import calendar
import os
import sys
import json
import webbrowser
import tempfile
from jinja2 import Environment, FileSystemLoader

# Создаём главное окно
root = tk.Tk()
root.title("Генератор календаря мероприятий")
root.geometry("1000x700")
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
current_file = None
last_temp_file = None
default_colors = {
    "html_bg": "#f4f7fc",         # Фон страницы (body)
    "html_fg": "#37474f",         # Цвет текста страницы (p, calendar-day)
    "html_header": "#2c3e50",     # Цвет заголовка (h1 в .header)
    "calendar_bg": "#ffffff",     # Фон календаря (#calendar)
    "event_fg": "#37474f",        # Цвет текста мероприятий (p в .event-item)
    "active_day_bg": "#1e88e5",   # Фон активных дней (.calendar-day.active, упрощённый цвет)
    "inactive_day_bg": "#f0f0f0", # Фон неактивных дней (.calendar-day.inactive)
    "weekday_bg": "#42a5f5",      # Фон дней недели (.calendar-weekday, упрощённый цвет)
    "weekday_fg": "#ffffff",      # Цвет текста дней недели (.calendar-weekday)
    "event_border": "#ffb74d",    # Цвет полоски мероприятий (.event-item border-left)
    "button_bg": "#1e88e5",       # Фон кнопки (#back-to-top)
    "button_fg": "#ffffff"        # Цвет текста кнопки (#back-to-top)
}
colors = default_colors.copy()

# Словарь месяцев
months = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}


# Валидация ввода только цифр
def validate_numeric_input(P):
    return P.isdigit() or P == ""


vcmd = (root.register(validate_numeric_input), '%P')


# Добавление мероприятия
def add_event():
    """Добавляет новое мероприятие в список с проверкой корректности даты."""
    date = date_entry.get()
    title = title_entry.get()
    time = time_entry.get()
    place = place_entry.get()
    info = info_entry.get()
    if not (date and title):
        status_label.config(text="Ошибка: заполните дату и название!")
        return
    try:
        date_int = int(date)
        if date_int < 1 or date_int > 31:
            status_label.config(text="Ошибка: дата должна быть от 1 до 31!")
            return
        events.append({"date": date_int, "title": title, "time": time, "place": place, "info": info})
        status_label.config(text=f"Добавлено: {date} - {title}")
        clear_entries()
        update_event_list()
    except ValueError:
        status_label.config(text="Ошибка: дата должна быть числом!")


# Очистка полей ввода
def clear_entries():
    """Очищает все поля ввода."""
    date_entry.delete(0, tk.END)
    title_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)
    place_entry.delete(0, tk.END)
    info_entry.delete(0, tk.END)


# Обновление списка мероприятий
def update_event_list():
    """Обновляет список мероприятий в виджете с сортировкой по дате."""
    event_listbox.delete(0, tk.END)
    sorted_events = sorted(events, key=lambda x: x["date"])
    for event in sorted_events:
        event_listbox.insert(tk.END, f"{event['date']} - {event['title']} ({event['place']})")


# Редактирование мероприятия
def edit_event(event=None):
    """Открывает выбранное мероприятие для редактирования."""
    selected = event_listbox.curselection()
    if not selected:
        messagebox.showwarning("Предупреждение", "Выберите мероприятие для редактирования!")
        return
    index = selected[0]
    event_data = events[index]

    clear_entries()
    date_entry.insert(0, event_data["date"])
    title_entry.insert(0, event_data["title"])
    time_entry.insert(0, event_data["time"])
    place_entry.insert(0, event_data["place"])
    info_entry.insert(0, event_data["info"])

    # Удаляем старую кнопку "Сохранить изменения", если она есть
    for widget in button_frame_input.winfo_children():
        if widget != add_button and widget.cget("text") == "Сохранить изменения":
            widget.destroy()

    # Скрываем кнопку "Добавить мероприятие"
    add_button.pack_forget()

    # Создаём новую кнопку "Сохранить изменения"
    save_button = ttk.Button(button_frame_input, text="Сохранить изменения",
                             command=lambda: save_edit(index, save_button))
    save_button.pack(side=tk.LEFT, padx=5)


def save_edit(index, button):
    """Сохраняет отредактированное мероприятие."""
    new_date = date_entry.get()
    new_title = title_entry.get()
    new_time = time_entry.get()
    new_place = place_entry.get()
    new_info = info_entry.get()
    if not (new_date and new_title):
        status_label.config(text="Ошибка: заполните дату и название!")
        return
    try:
        new_date_int = int(new_date)
        if new_date_int < 1 or new_date_int > 31:
            status_label.config(text="Ошибка: дата должна быть от 1 до 31!")
            return
        events[index] = {"date": new_date_int, "title": new_title, "time": new_time, "place": new_place,
                         "info": new_info}
        status_label.config(text=f"Отредактировано: {new_date} - {new_title}")
        clear_entries()
        update_event_list()
        button.pack_forget()
        add_button.pack(side=tk.LEFT, padx=5)
    except ValueError:
        status_label.config(text="Ошибка: дата должна быть числом!")


# Удаление мероприятия
def delete_event():
    """Удаляет выбранное мероприятие из списка."""
    selected = event_listbox.curselection()
    if not selected:
        messagebox.showwarning("Предупреждение", "Выберите мероприятие для удаления!")
        return
    index = selected[0]
    del events[index]
    update_event_list()
    status_label.config(text="Мероприятие удалено")


# Предпросмотр календаря
def update_preview():
    """Генерирует предпросмотр календаря во временном файле, заменяя предыдущий файл."""
    global last_temp_file
    if not events:
        messagebox.showwarning("Предупреждение", "Добавьте хотя бы одно мероприятие!")
        return
    year = year_var.get()
    month = month_var.get()
    if not year or not month:
        messagebox.showwarning("Предупреждение", "Введите год и месяц для предпросмотра!")
        return
    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            messagebox.showwarning("Ошибка", "Месяц должен быть от 1 до 12!")
            return

        if last_temp_file and os.path.exists(last_temp_file):
            tmp_path = last_temp_file
        else:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            tmp_path = tmp_file.name
            tmp_file.close()
            last_temp_file = tmp_path

        generate_html(tmp_path, open_in_browser=False)
        webbrowser.open(f"file://{os.path.abspath(tmp_path)}")
        status_label.config(text=f"Предпросмотр открыт: {tmp_path}")
    except ValueError:
        messagebox.showerror("Ошибка", "Год и месяц должны быть числами!")
    except FileNotFoundError:
        messagebox.showerror("Ошибка", "Не найден шаблон calendar_template.html в папке templates!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть предпросмотр: {str(e)}")


# Генерация календаря
def generate_calendar():
    """Генерирует календарь с фиксированным именем файла."""
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
        generate_html(f"calendar_{year}_{month}.html")
    except Exception as e:
        status_label.config(text=f"Ошибка: {str(e)}")


# Генерация календаря с выбором пути
def generate_calendar_as():
    """Генерирует календарь с выбором пути сохранения."""
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
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if file_path:
            generate_html(file_path)
    except Exception as e:
        status_label.config(text=f"Ошибка: {str(e)}")


# Генерация HTML-файла
def generate_html(file_path, open_in_browser=False):
    """Генерирует HTML-файл на основе данных календаря."""
    year = int(year_var.get())
    month = int(month_var.get())
    month_name = months[month]
    days_in_month = calendar.monthrange(year, month)[1]
    start_day = calendar.monthrange(year, month)[0]
    libraries = sorted(set(event["place"] for event in events if event["place"]))

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    templates_path = os.path.join(base_path, 'templates')
    if not os.path.exists(templates_path):
        raise FileNotFoundError(f"Папка templates не найдена по пути: {templates_path}")
    env = Environment(loader=FileSystemLoader(templates_path), autoescape=True)
    template = env.get_template('calendar_template.html')

    output = template.render(
        year=year,
        month_name=month_name,
        events=sorted(events, key=lambda x: x["date"]),
        libraries=libraries,
        start_day=start_day,
        days_in_month=days_in_month,
        header_title=header_title,
        filter_text=filter_text,
        bg_color=colors["html_bg"],
        fg_color=colors["html_fg"],
        header_color=colors["html_header"],
        calendar_bg=colors["calendar_bg"],
        event_fg=colors["event_fg"],
        active_day_bg=colors["active_day_bg"],
        inactive_day_bg=colors["inactive_day_bg"],
        weekday_bg=colors["weekday_bg"],
        weekday_fg=colors["weekday_fg"],
        event_border=colors["event_border"],
        button_bg=colors["button_bg"],
        button_fg=colors["button_fg"]
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(output)
    status_label.config(text=f"Календарь сохранён как {os.path.basename(file_path)}")
    if open_in_browser:
        webbrowser.open(f"file://{os.path.abspath(file_path)}")


# Настройки календаря
def configure_calendar():
    """Открывает окно настроек для изменения параметров и цветов."""
    config_window = tk.Toplevel(root)
    config_window.title("Настройки")
    config_window.geometry("450x700")
    config_window.configure(bg="#e0e8f0")
    config_window.resizable(False, False)

    notebook = ttk.Notebook(config_window)
    notebook.pack(pady=10, padx=10, fill="both", expand=True)

    # Вкладка "Общие настройки"
    general_frame = ttk.Frame(notebook, padding="10")
    notebook.add(general_frame, text="Общие")

    ttk.Label(general_frame, text="Заголовок:", font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=5, pady=5,
                                                                                     sticky="e")
    header_entry = ttk.Entry(general_frame, width=40)
    header_entry.insert(0, header_title)
    header_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(general_frame, text="Текст фильтра:", font=("Helvetica", 11, "bold")).grid(row=1, column=0, padx=5,
                                                                                         pady=5, sticky="e")
    filter_entry = ttk.Entry(general_frame, width=40)
    filter_entry.insert(0, filter_text)
    filter_entry.grid(row=1, column=1, padx=5, pady=5)

    # Вкладка "Цвета страницы"
    page_frame = ttk.Frame(notebook, padding="10")
    notebook.add(page_frame, text="Цвета страницы")

    ttk.Label(page_frame, text="Цвет фона страницы:", font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=5,
                                                                                           pady=5, sticky="e")
    bg_color_label = tk.Label(page_frame, bg=colors["html_bg"], width=2, height=1, borderwidth=1, relief="solid")
    bg_color_label.grid(row=0, column=1, padx=5, pady=5)
    bg_button = ttk.Button(page_frame, text="Изменить",
                           command=lambda: choose_color("html_bg", bg_button, bg_color_label))
    bg_button.grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(page_frame, text="Цвет текста страницы:", font=("Helvetica", 11, "bold")).grid(row=1, column=0, padx=5,
                                                                                             pady=5, sticky="e")
    fg_color_label = tk.Label(page_frame, bg=colors["html_fg"], width=2, height=1, borderwidth=1, relief="solid")
    fg_color_label.grid(row=1, column=1, padx=5, pady=5)
    fg_button = ttk.Button(page_frame, text="Изменить",
                           command=lambda: choose_color("html_fg", fg_button, fg_color_label))
    fg_button.grid(row=1, column=2, padx=5, pady=5)

    ttk.Label(page_frame, text="Цвет заголовка:", font=("Helvetica", 11, "bold")).grid(row=2, column=0, padx=5, pady=5,
                                                                                       sticky="e")
    header_color_label = tk.Label(page_frame, bg=colors["html_header"], width=2, height=1, borderwidth=1,
                                  relief="solid")
    header_color_label.grid(row=2, column=1, padx=5, pady=5)
    header_button = ttk.Button(page_frame, text="Изменить",
                               command=lambda: choose_color("html_header", header_button, header_color_label))
    header_button.grid(row=2, column=2, padx=5, pady=5)

    ttk.Label(page_frame, text="Цвет кнопки:", font=("Helvetica", 11, "bold")).grid(row=3, column=0, padx=5, pady=5,
                                                                                    sticky="e")
    button_bg_color_label = tk.Label(page_frame, bg=colors["button_bg"], width=2, height=1, borderwidth=1,
                                     relief="solid")
    button_bg_color_label.grid(row=3, column=1, padx=5, pady=5)
    button_bg_button = ttk.Button(page_frame, text="Изменить",
                                  command=lambda: choose_color("button_bg", button_bg_button, button_bg_color_label))
    button_bg_button.grid(row=3, column=2, padx=5, pady=5)

    ttk.Label(page_frame, text="Текст кнопки:", font=("Helvetica", 11, "bold")).grid(row=4, column=0, padx=5, pady=5,
                                                                                     sticky="e")
    button_fg_color_label = tk.Label(page_frame, bg=colors["button_fg"], width=2, height=1, borderwidth=1,
                                     relief="solid")
    button_fg_color_label.grid(row=4, column=1, padx=5, pady=5)
    button_fg_button = ttk.Button(page_frame, text="Изменить",
                                  command=lambda: choose_color("button_fg", button_fg_button, button_fg_color_label))
    button_fg_button.grid(row=4, column=2, padx=5, pady=5)

    # Вкладка "Цвета календаря"
    calendar_frame = ttk.Frame(notebook, padding="10")
    notebook.add(calendar_frame, text="Цвета календаря")

    ttk.Label(calendar_frame, text="Фон календаря:", font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=5,
                                                                                          pady=5, sticky="e")
    cal_bg_color_label = tk.Label(calendar_frame, bg=colors["calendar_bg"], width=2, height=1, borderwidth=1,
                                  relief="solid")
    cal_bg_color_label.grid(row=0, column=1, padx=5, pady=5)
    cal_bg_button = ttk.Button(calendar_frame, text="Изменить",
                               command=lambda: choose_color("calendar_bg", cal_bg_button, cal_bg_color_label))
    cal_bg_button.grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Цвет текста мероприятий:", font=("Helvetica", 11, "bold")).grid(row=1, column=0,
                                                                                                    padx=5, pady=5,
                                                                                                    sticky="e")
    event_fg_color_label = tk.Label(calendar_frame, bg=colors["event_fg"], width=2, height=1, borderwidth=1,
                                    relief="solid")
    event_fg_color_label.grid(row=1, column=1, padx=5, pady=5)
    event_fg_button = ttk.Button(calendar_frame, text="Изменить",
                                 command=lambda: choose_color("event_fg", event_fg_button, event_fg_color_label))
    event_fg_button.grid(row=1, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Фон активных дней:", font=("Helvetica", 11, "bold")).grid(row=2, column=0, padx=5,
                                                                                              pady=5, sticky="e")
    active_day_bg_color_label = tk.Label(calendar_frame, bg=colors["active_day_bg"], width=2, height=1, borderwidth=1,
                                         relief="solid")
    active_day_bg_color_label.grid(row=2, column=1, padx=5, pady=5)
    active_day_bg_button = ttk.Button(calendar_frame, text="Изменить",
                                      command=lambda: choose_color("active_day_bg", active_day_bg_button,
                                                                   active_day_bg_color_label))
    active_day_bg_button.grid(row=2, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Фон неактивных дней:", font=("Helvetica", 11, "bold")).grid(row=3, column=0, padx=5,
                                                                                                pady=5, sticky="e")
    inactive_day_bg_color_label = tk.Label(calendar_frame, bg=colors["inactive_day_bg"], width=2, height=1,
                                           borderwidth=1, relief="solid")
    inactive_day_bg_color_label.grid(row=3, column=1, padx=5, pady=5)
    inactive_day_bg_button = ttk.Button(calendar_frame, text="Изменить",
                                        command=lambda: choose_color("inactive_day_bg", inactive_day_bg_button,
                                                                     inactive_day_bg_color_label))
    inactive_day_bg_button.grid(row=3, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Фон дней недели:", font=("Helvetica", 11, "bold")).grid(row=4, column=0, padx=5,
                                                                                            pady=5, sticky="e")
    weekday_bg_color_label = tk.Label(calendar_frame, bg=colors["weekday_bg"], width=2, height=1, borderwidth=1,
                                      relief="solid")
    weekday_bg_color_label.grid(row=4, column=1, padx=5, pady=5)
    weekday_bg_button = ttk.Button(calendar_frame, text="Изменить",
                                   command=lambda: choose_color("weekday_bg", weekday_bg_button,
                                                                weekday_bg_color_label))
    weekday_bg_button.grid(row=4, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Текст дней недели:", font=("Helvetica", 11, "bold")).grid(row=5, column=0, padx=5,
                                                                                              pady=5, sticky="e")
    weekday_fg_color_label = tk.Label(calendar_frame, bg=colors["weekday_fg"], width=2, height=1, borderwidth=1,
                                      relief="solid")
    weekday_fg_color_label.grid(row=5, column=1, padx=5, pady=5)
    weekday_fg_button = ttk.Button(calendar_frame, text="Изменить",
                                   command=lambda: choose_color("weekday_fg", weekday_fg_button,
                                                                weekday_fg_color_label))
    weekday_fg_button.grid(row=5, column=2, padx=5, pady=5)

    ttk.Label(calendar_frame, text="Полоска мероприятий:", font=("Helvetica", 11, "bold")).grid(row=6, column=0, padx=5,
                                                                                                pady=5, sticky="e")
    event_border_color_label = tk.Label(calendar_frame, bg=colors["event_border"], width=2, height=1, borderwidth=1,
                                        relief="solid")
    event_border_color_label.grid(row=6, column=1, padx=5, pady=5)
    event_border_button = ttk.Button(calendar_frame, text="Изменить",
                                     command=lambda: choose_color("event_border", event_border_button,
                                                                  event_border_color_label))
    event_border_button.grid(row=6, column=2, padx=5, pady=5)

    # Кнопки управления
    button_frame = ttk.Frame(config_window)
    button_frame.pack(pady=10)
    ttk.Button(button_frame, text="Сохранить",
               command=lambda: save_config(config_window, header_entry, filter_entry)).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Сбросить цвета", command=reset_colors).pack(side=tk.LEFT, padx=5)


def choose_color(key, button, color_label):
    """Выбирает цвет для указанного элемента и обновляет индикатор."""
    color = colorchooser.askcolor(title=f"Выберите цвет для {key}", initialcolor=colors[key])[1]
    if color:
        colors[key] = color
        color_label.config(bg=color)
        button.focus_set()


def save_config(window, header_entry, filter_entry):
    """Сохраняет настройки из окна конфигурации."""
    global header_title, filter_text
    header_title = header_entry.get()
    filter_text = filter_entry.get()
    window.destroy()
    status_label.config(text="Настройки сохранены")


def reset_colors():
    """Сбрасывает цвета до значений по умолчанию."""
    global colors
    colors = default_colors.copy()
    status_label.config(text="Цвета сброшены по умолчанию")
    # Если окно настроек открыто, обновляем индикаторы
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel) and window.winfo_exists():
            for notebook in window.winfo_children():
                if isinstance(notebook, ttk.Notebook):
                    for frame in notebook.winfo_children():
                        for widget in frame.winfo_children():
                            if isinstance(widget, tk.Label) and widget.cget("width") == 2:
                                key = widget.grid_info()["row"]
                                if frame == notebook.winfo_children()[1]:  # page_frame
                                    keys = ["html_bg", "html_fg", "html_header", "button_bg", "button_fg"]
                                elif frame == notebook.winfo_children()[2]:  # calendar_frame
                                    keys = ["calendar_bg", "event_fg", "active_day_bg", "inactive_day_bg", "weekday_bg",
                                            "weekday_fg", "event_border"]
                                widget.config(bg=colors[keys[key]])


# Работа с проектом
def new_project():
    """Создаёт новый проект."""
    global events, current_file
    events.clear()
    year_var.set("")
    month_var.set("")
    clear_entries()
    update_event_list()
    current_file = None
    root.title("Генератор календаря мероприятий")
    status_label.config(text="Создан новый проект")


def open_project():
    """Открывает существующий проект из JSON-файла."""
    global events, current_file, header_title, filter_text, colors
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            year_var.set(data.get("year", ""))
            month_var.set(data.get("month", ""))
            events.clear()
            events.extend(data.get("events", []))
            header_title = data.get("header_title", "Афиша мероприятий")
            filter_text = data.get("filter_text", "Фильтр по библиотекам:")
            colors.update(data.get("colors", default_colors))
            clear_entries()
            update_event_list()
            current_file = file_path
            root.title(f"Генератор календаря мероприятий - {os.path.basename(file_path)}")
            status_label.config(text=f"Открыт проект: {os.path.basename(file_path)}")
    except json.JSONDecodeError:
        messagebox.showerror("Ошибка", "Некорректный формат JSON-файла!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть проект: {str(e)}")


def save_project():
    """Сохраняет текущий проект."""
    global current_file
    if current_file:
        save_to_file(current_file)
    else:
        save_project_as()


def save_project_as():
    """Сохраняет проект с выбором пути."""
    global current_file
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        save_to_file(file_path)
        current_file = file_path
        root.title(f"Генератор календаря мероприятий - {os.path.basename(file_path)}")
        status_label.config(text=f"Проект сохранён как: {os.path.basename(file_path)}")


def save_to_file(file_path):
    """Сохраняет данные проекта в файл."""
    data = {
        "year": year_var.get(),
        "month": month_var.get(),
        "events": events,
        "header_title": header_title,
        "filter_text": filter_text,
        "colors": colors
    }
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        status_label.config(text=f"Проект сохранён: {os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить проект: {str(e)}")


def exit_app():
    """Закрывает приложение и удаляет временный файл предпросмотра."""
    global last_temp_file
    if last_temp_file and os.path.exists(last_temp_file):
        try:
            os.remove(last_temp_file)
            status_label.config(text=f"Временный файл {last_temp_file} удалён")
        except Exception as e:
            status_label.config(text=f"Ошибка удаления временного файла: {str(e)}")
    root.quit()


# Обработка клавиш
def handle_keypress(event):
    """Обрабатывает сочетания клавиш для копирования, вставки и выделения."""
    widget = root.focus_get()
    if not (isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry)):
        return
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
        elif event.keycode == 65:  # Ctrl+A
            widget.select_range(0, tk.END)
            return "break"


root.bind_all("<KeyPress>", handle_keypress)
root.bind("<Control-n>", lambda e: new_project())
root.bind("<Control-o>", lambda e: open_project())
root.bind("<Control-s>", lambda e: save_project())

# Создание меню
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Файл", menu=file_menu)
file_menu.add_command(label="Новый проект", command=new_project, accelerator="Ctrl+N")
file_menu.add_command(label="Открыть проект", command=open_project, accelerator="Ctrl+O")
file_menu.add_command(label="Сохранить проект", command=save_project, accelerator="Ctrl+S")
file_menu.add_command(label="Сохранить как...", command=save_project_as)
file_menu.add_separator()
file_menu.add_command(label="Генерация календаря", command=generate_calendar)
file_menu.add_command(label="Генерация календаря в...", command=generate_calendar_as)
file_menu.add_command(label="Настройки", command=configure_calendar)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=exit_app)

# Интерфейс
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill="both", expand=True)

# Секция ввода даты
date_frame = ttk.LabelFrame(main_frame, text="Дата и месяц", padding="10")
date_frame.pack(fill="x", pady=(0, 10))
ttk.Label(date_frame, text="Год:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
year_entry = ttk.Entry(date_frame, textvariable=year_var, width=20, validate="key", validatecommand=vcmd)
year_entry.grid(row=0, column=1, padx=10, pady=5)
ttk.Label(date_frame, text="Месяц (1-12):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
month_entry = ttk.Entry(date_frame, textvariable=month_var, width=20, validate="key", validatecommand=vcmd)
month_entry.grid(row=1, column=1, padx=10, pady=5)

# Секция ввода мероприятий
input_frame = ttk.LabelFrame(main_frame, text="Добавление мероприятия", padding="10")
input_frame.pack(fill="x", pady=10)
ttk.Label(input_frame, text="Дата:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
date_entry = ttk.Entry(input_frame, width=30, validate="key", validatecommand=vcmd)
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

# Кнопки управления в input_frame
button_frame_input = ttk.Frame(input_frame)
button_frame_input.grid(row=7, column=0, columnspan=2, pady=10)
add_button = ttk.Button(button_frame_input, text="Добавить мероприятие", command=add_event)
add_button.pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame_input, text="Очистить", command=clear_entries).pack(side=tk.LEFT, padx=5)

# Кнопка предпросмотра
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill="x", pady=10)
ttk.Button(button_frame, text="Предпросмотр", command=update_preview).pack(side=tk.LEFT, padx=5)

# Статус
status_label = ttk.Label(main_frame, text="Готов к работе", anchor="center", font=("Helvetica", 10, "italic"))
status_label.pack(pady=10)

# Секция списка мероприятий
event_frame = ttk.LabelFrame(main_frame, text="Список мероприятий", padding="10")
event_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
event_listbox = tk.Listbox(event_frame, height=15, width=40, font=("Helvetica", 11), bg="#ffffff", fg="#333333",
                           relief="flat", borderwidth=1)
event_listbox.pack(fill="both", expand=True, pady=(0, 10))

# Кнопки в event_frame
event_button_frame = ttk.Frame(event_frame)
event_button_frame.pack(fill="x", pady=5)
edit_button = ttk.Button(event_button_frame, text="Редактировать выбранное", command=edit_event)
edit_button.pack(side=tk.LEFT, padx=5)
ttk.Button(event_button_frame, text="Удалить выбранное", command=delete_event).pack(side=tk.LEFT, padx=5)

event_listbox.bind("<Double-Button-1>", edit_event)

# Запуск
root.mainloop()