import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import json
import os
from datetime import datetime


class RFIDApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RFID Монитор животноводческой фермы")
        self.geometry("800x600")

        # Данные
        self.animals = {}  # UID -> имя животного
        self.load_animals()

        self.serial_port = None
        self.reader_thread = None
        self.running = False
        self.log_entries = []  # последние 20 событий

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Верхняя панель: выбор порта и подключение
        frame_top = tk.Frame(self)
        frame_top.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(frame_top, text="COM-порт:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(frame_top, textvariable=self.port_var,
                                       values=self.get_ports(), width=10)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self.port_combo.bind('<Button-1>', lambda e: self.refresh_ports())

        self.btn_connect = tk.Button(frame_top, text="Подключиться",
                                     command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        self.btn_open = tk.Button(frame_top, text="Открыть ворота",
                                  command=self.send_open, bg="lightgreen",
                                  state=tk.DISABLED)
        self.btn_open.pack(side=tk.LEFT, padx=5)

        # Основная панель: слева список животных, справа журнал
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Левая панель - управление животными
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, width=300)

        tk.Label(left_frame, text="Зарегистрированные животные",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        # Таблица животных
        columns = ('UID', 'Имя')
        self.tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=10)
        self.tree.heading('UID', text='UID')
        self.tree.heading('Имя', text='Имя животного')
        self.tree.column('UID', width=120)
        self.tree.column('Имя', width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Кнопки управления
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Добавить", command=self.add_animal_dialog).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Удалить", command=self.delete_animal).pack(side=tk.LEFT, padx=2)

        # Правая панель - журнал событий
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame, width=400)

        tk.Label(right_frame, text="Журнал событий (последние 20)",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        self.log_listbox = tk.Listbox(right_frame, height=15)
        self.log_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статусная строка внизу
        self.status_label = tk.Label(self, text="Статус: не подключено",
                                     bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_animal_list()

    # ---------- Работа с COM-портом ----------
    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["Нет портов"]

    def refresh_ports(self):
        self.port_combo['values'] = self.get_ports()

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        if not port or port == "Нет портов":
            messagebox.showerror("Ошибка", "Выберите корректный COM-порт")
            return
        try:
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.reader_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.reader_thread.start()
            self.btn_connect.config(text="Отключиться")
            self.btn_open.config(state=tk.NORMAL)
            self.status_label.config(text=f"Подключено к {port}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")

    def disconnect(self):
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.btn_connect.config(text="Подключиться")
        self.btn_open.config(state=tk.DISABLED)
        self.status_label.config(text="Отключено")

    def read_serial(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                if line:
                    self.after(0, self.process_line, line)
            except Exception as e:
                print("Ошибка чтения:", e)
                break

    def send_command(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(cmd.encode())
        else:
            print("Порт не открыт")

    # ---------- Обработка данных от Arduino ----------
    def process_line(self, line):
        if line.startswith("UID:"):
            uid = line[4:]  # например "DE:AD:BE:EF"
            name = self.animals.get(uid)
            if name:
                self.send_command('O')
                status = f"РАЗРЕШЁН: {name} ({uid})"
            else:
                self.send_command('D')
                status = f"ЗАПРЕЩЁН: неизвестное животное ({uid})"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{timestamp}] {status}"
            self.add_log_entry(entry)

    def send_open(self):
        self.send_command('O')
        self.status_label.config(text="Команда открытия отправлена")

    def add_log_entry(self, entry):
        self.log_entries.append(entry)
        if len(self.log_entries) > 20:
            self.log_entries.pop(0)
        self.log_listbox.delete(0, tk.END)
        for e in self.log_entries:
            self.log_listbox.insert(tk.END, e)

    # ---------- Работа с базой животных (JSON) ----------
    def load_animals(self):
        filename = "animals.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.animals = json.load(f)
            except:
                self.animals = {}
        else:
            self.animals = {}

    def save_animals(self):
        with open("animals.json", 'w', encoding='utf-8') as f:
            json.dump(self.animals, f, ensure_ascii=False, indent=2)

    def refresh_animal_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for uid, name in self.animals.items():
            self.tree.insert('', tk.END, values=(uid, name))

    def add_animal_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добавить животное")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="UID метки (HEX, например DE:AD:BE:EF):").pack(pady=5)
        uid_entry = tk.Entry(dialog, width=30)
        uid_entry.pack(pady=5)

        tk.Label(dialog, text="Имя животного:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)

        def save():
            uid = uid_entry.get().strip().upper()
            name = name_entry.get().strip()
            if not uid or not name:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            if uid in self.animals:
                messagebox.showerror("Ошибка", "Животное с таким UID уже существует")
                return
            self.animals[uid] = name
            self.save_animals()
            self.refresh_animal_list()
            self.send_command('A')  # звуковое подтверждение на Arduino
            dialog.destroy()

        tk.Button(dialog, text="Сохранить", command=save).pack(pady=10)

    def delete_animal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите животное для удаления")
            return
        item = self.tree.item(selected[0])
        uid = item['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить животное {item['values'][1]}?"):
            del self.animals[uid]
            self.save_animals()
            self.refresh_animal_list()

    def on_close(self):
        self.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = RFIDApp()
    app.mainloop()