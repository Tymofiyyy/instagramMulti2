# -*- coding: utf-8 -*-
"""
Instagram Bot Pro v3.0 - Сучасний GUI з повним функціоналом
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import asyncio
import queue

try:
    from config import BotConfig
    from automation_engine import InstagramAutomation
    from data_manager_final import DataManager
    from browser_manager import BrowserFactory
except ImportError as e:
    print(f"Помилка імпорту: {e}")


class ModernStyle:
    """Сучасна темна тема оформлення"""
    
    COLORS = {
        'primary': '#6366f1',
        'primary_dark': '#4f46e5',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'background': '#0f172a',
        'surface': '#1e293b',
        'card': '#334155',
        'border': '#475569',
        'text': '#f1f5f9',
        'text_secondary': '#94a3b8',
        'sidebar': '#1e293b',
        'sidebar_active': '#6366f1',
    }
    
    FONTS = {
        'title': ('Segoe UI', 24, 'bold'),
        'heading': ('Segoe UI', 14, 'bold'),
        'body': ('Segoe UI', 11),
        'small': ('Segoe UI', 9),
        'button': ('Segoe UI', 10, 'bold')
    }


class AnimatedButton(tk.Button):
    """Анімована кнопка"""
    
    def __init__(self, parent, **kwargs):
        self.default_bg = kwargs.get('bg', ModernStyle.COLORS['primary'])
        self.hover_bg = kwargs.get('hover_bg', ModernStyle.COLORS['primary_dark'])
        
        if 'hover_bg' in kwargs:
            del kwargs['hover_bg']
        
        super().__init__(parent, **kwargs)
        
        self.configure(
            relief='flat',
            borderwidth=0,
            font=ModernStyle.FONTS['button'],
            fg='white',
            bg=self.default_bg,
            cursor='hand2',
            padx=15,
            pady=8
        )
        
        self.bind('<Enter>', lambda e: self.configure(bg=self.hover_bg))
        self.bind('<Leave>', lambda e: self.configure(bg=self.default_bg))


class GlassCard(tk.Frame):
    """Скляна картка"""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=ModernStyle.COLORS['card'],
            relief='flat',
            bd=1,
            highlightbackground=ModernStyle.COLORS['border'],
            highlightthickness=1
        )
        
        if title:
            title_frame = tk.Frame(self, bg=ModernStyle.COLORS['card'])
            title_frame.pack(fill='x', padx=20, pady=(20, 10))
            
            title_label = tk.Label(
                title_frame,
                text=title,
                font=ModernStyle.FONTS['heading'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text']
            )
            title_label.pack(anchor='w')


class ChainBuilderWidget(tk.Frame):
    """Віджет для створення ланцюжка дій"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.chain = []
        self.action_widgets = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        header = tk.Label(
            self,
            text="🔗 Конструктор ланцюжка дій",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Кнопки додавання дій
        actions_frame = tk.Frame(self, bg=ModernStyle.COLORS['surface'])
        actions_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            actions_frame,
            text="Доступні дії:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        buttons_frame = tk.Frame(actions_frame, bg=ModernStyle.COLORS['surface'])
        buttons_frame.pack(fill='x', pady=5)
        
        # Кнопки дій
        action_buttons = [
            ("👤 Підписка", "follow", self.add_follow_action),
            ("❤️ Лайк постів", "like_posts", self.add_like_posts_action),
            ("📖 Перегляд сторіс", "view_stories", self.add_view_stories_action),
            ("💖 Лайк сторіс", "like_stories", self.add_like_stories_action),
            ("💬 Відповідь на сторіс", "reply_stories", self.add_reply_stories_action),
            ("📩 Приватне повідомлення", "send_dm", self.add_send_dm_action),
            ("🔄 Затримка", "delay", self.add_delay_action)
        ]
        
        for i, (text, action_type, command) in enumerate(action_buttons):
            btn = AnimatedButton(
                buttons_frame,
                text=text,
                command=command,
                bg=ModernStyle.COLORS['primary']
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=2, sticky='ew')
        
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        
        # Поточний ланцюжок
        self.chain_frame = tk.Frame(self, bg=ModernStyle.COLORS['surface'])
        self.chain_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(
            self.chain_frame,
            text="Поточний ланцюжок:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        # Скролюючий контейнер для ланцюжка
        self.canvas = tk.Canvas(
            self.chain_frame,
            bg=ModernStyle.COLORS['background'],
            highlightthickness=0,
            height=300
        )
        scrollbar = ttk.Scrollbar(self.chain_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=ModernStyle.COLORS['background'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопки управління
        control_frame = tk.Frame(self, bg=ModernStyle.COLORS['surface'])
        control_frame.pack(fill='x', padx=20, pady=10)
        
        AnimatedButton(
            control_frame,
            text="💾 Зберегти ланцюжок",
            command=self.save_chain,
            bg=ModernStyle.COLORS['success']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="📂 Завантажити",
            command=self.load_chain,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="🗑️ Очистити",
            command=self.clear_chain,
            bg=ModernStyle.COLORS['error']
        ).pack(side='left', padx=5)
    
    def add_follow_action(self):
        """Додавання дії підписки"""
        self.add_action({
            'type': 'follow',
            'name': 'Підписка на користувача',
            'icon': '👤',
            'enabled': True
        })
    
    def add_like_posts_action(self):
        """Додавання дії лайку постів"""
        dialog = ActionDialog(self, "❤️ Налаштування лайку постів")
        if dialog.result:
            count = dialog.result.get('count', 2)
            self.add_action({
                'type': 'like_posts',
                'name': f'Лайк {count} постів',
                'icon': '❤️',
                'settings': {'count': count},
                'enabled': True
            })
    
    def add_view_stories_action(self):
        """Додавання дії перегляду сторіс"""
        dialog = ActionDialog(self, "📖 Налаштування перегляду сторіс")
        if dialog.result:
            count = dialog.result.get('count', 3)
            self.add_action({
                'type': 'view_stories',
                'name': f'Перегляд {count} сторіс',
                'icon': '📖',
                'settings': {'count': count},
                'enabled': True
            })
    
    def add_like_stories_action(self):
        """Додавання дії лайку сторіс"""
        self.add_action({
            'type': 'like_stories',
            'name': 'Лайк сторіс',
            'icon': '💖',
            'enabled': True
        })
    
    def add_reply_stories_action(self):
        """Додавання дії відповіді на сторіс"""
        self.add_action({
            'type': 'reply_stories',
            'name': 'Відповідь на сторіс',
            'icon': '💬',
            'enabled': True
        })
    
    def add_send_dm_action(self):
        """Додавання дії відправки DM"""
        self.add_action({
            'type': 'send_dm',
            'name': 'Приватне повідомлення',
            'icon': '📩',
            'enabled': True
        })
    
    def add_delay_action(self):
        """Додавання затримки"""
        dialog = ActionDialog(self, "🔄 Налаштування затримки")
        if dialog.result:
            delay = dialog.result.get('delay', 30)
            self.add_action({
                'type': 'delay',
                'name': f'Затримка {delay} сек',
                'icon': '🔄',
                'settings': {'delay': delay},
                'enabled': True
            })
    
    def add_action(self, action):
        """Додавання дії до ланцюжка"""
        self.chain.append(action)
        self.update_chain_display()
    
    def update_chain_display(self):
        """Оновлення відображення ланцюжка"""
        # Очищення
        for widget in self.action_widgets:
            widget.destroy()
        self.action_widgets.clear()
        
        # Створення віджетів для кожної дії
        for i, action in enumerate(self.chain):
            self.create_action_widget(i, action)
    
    def create_action_widget(self, index, action):
        """Створення віджета дії"""
        frame = tk.Frame(self.scrollable_frame, bg=ModernStyle.COLORS['card'])
        frame.pack(fill='x', padx=5, pady=2)
        self.action_widgets.append(frame)
        
        # Номер кроку
        step_label = tk.Label(
            frame,
            text=f"{index + 1}.",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text_secondary'],
            width=3
        )
        step_label.pack(side='left', padx=5)
        
        # Іконка та назва
        info_frame = tk.Frame(frame, bg=ModernStyle.COLORS['card'])
        info_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        tk.Label(
            info_frame,
            text=f"{action['icon']} {action['name']}",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        # Перемикач увімкнення
        enabled_var = tk.BooleanVar(value=action.get('enabled', True))
        enabled_check = tk.Checkbutton(
            frame,
            variable=enabled_var,
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=lambda idx=index, var=enabled_var: self.toggle_action(idx, var.get())
        )
        enabled_check.pack(side='right', padx=5)
        
        # Кнопки управління
        btn_frame = tk.Frame(frame, bg=ModernStyle.COLORS['card'])
        btn_frame.pack(side='right', padx=5)
        
        # Кнопка видалення
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️",
            command=lambda idx=index: self.remove_action(idx),
            bg=ModernStyle.COLORS['error'],
            fg='white',
            relief='flat',
            font=('Arial', 8),
            width=3
        )
        delete_btn.pack(side='right', padx=2)
        
        # Кнопки переміщення
        if index > 0:
            up_btn = tk.Button(
                btn_frame,
                text="↑",
                command=lambda idx=index: self.move_action(idx, -1),
                bg=ModernStyle.COLORS['primary'],
                fg='white',
                relief='flat',
                font=('Arial', 8),
                width=2
            )
            up_btn.pack(side='right', padx=1)
        
        if index < len(self.chain) - 1:
            down_btn = tk.Button(
                btn_frame,
                text="↓",
                command=lambda idx=index: self.move_action(idx, 1),
                bg=ModernStyle.COLORS['primary'],
                fg='white',
                relief='flat',
                font=('Arial', 8),
                width=2
            )
            down_btn.pack(side='right', padx=1)
    
    def toggle_action(self, index, enabled):
        """Перемикання стану дії"""
        if 0 <= index < len(self.chain):
            self.chain[index]['enabled'] = enabled
    
    def remove_action(self, index):
        """Видалення дії"""
        if 0 <= index < len(self.chain):
            self.chain.pop(index)
            self.update_chain_display()
    
    def move_action(self, index, direction):
        """Переміщення дії"""
        new_index = index + direction
        if 0 <= new_index < len(self.chain):
            self.chain[index], self.chain[new_index] = self.chain[new_index], self.chain[index]
            self.update_chain_display()
    
    def clear_chain(self):
        """Очищення ланцюжка"""
        if messagebox.askyesno("Підтвердження", "Очистити весь ланцюжок?"):
            self.chain.clear()
            self.update_chain_display()
    
    def save_chain(self):
        """Збереження ланцюжка"""
        if not self.chain:
            messagebox.showwarning("Попередження", "Ланцюжок порожній")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Зберегти ланцюжок дій"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.chain, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Успіх", f"Ланцюжок збережено: {filename}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти: {e}")
    
    def load_chain(self):
        """Завантаження ланцюжка"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Завантажити ланцюжок дій"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.chain = json.load(f)
                self.update_chain_display()
                messagebox.showinfo("Успіх", f"Ланцюжок завантажено: {filename}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося завантажити: {e}")
    
    def get_chain(self):
        """Отримання поточного ланцюжка"""
        return [action for action in self.chain if action.get('enabled', True)]


class ActionDialog(tk.Toplevel):
    """Діалог налаштування дії"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        self.result = None
        
        self.title(title)
        self.geometry("400x200")
        self.configure(bg=ModernStyle.COLORS['background'])
        self.transient(parent)
        self.grab_set()
        
        # Центрування
        self.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення віджетів діалогу"""
        main_frame = tk.Frame(self, bg=ModernStyle.COLORS['background'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Поле кількості
        tk.Label(
            main_frame,
            text="Кількість:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        self.count_var = tk.StringVar(value="2")
        count_entry = tk.Entry(
            main_frame,
            textvariable=self.count_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        count_entry.pack(fill='x', pady=5)
        
        # Поле затримки (якщо потрібно)
        tk.Label(
            main_frame,
            text="Затримка (секунди):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(10, 0))
        
        self.delay_var = tk.StringVar(value="30")
        delay_entry = tk.Entry(
            main_frame,
            textvariable=self.delay_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        delay_entry.pack(fill='x', pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['background'])
        btn_frame.pack(fill='x', pady=20)
        
        AnimatedButton(
            btn_frame,
            text="OK",
            command=self.ok_clicked,
            bg=ModernStyle.COLORS['success']
        ).pack(side='right', padx=5)
        
        AnimatedButton(
            btn_frame,
            text="Скасувати",
            command=self.cancel_clicked,
            bg=ModernStyle.COLORS['error']
        ).pack(side='right')
    
    def ok_clicked(self):
        """Обробка натискання OK"""
        try:
            count = int(self.count_var.get()) if self.count_var.get() else 1
            delay = int(self.delay_var.get()) if self.delay_var.get() else 30
            
            self.result = {
                'count': max(1, count),
                'delay': max(1, delay)
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректні числа")
    
    def cancel_clicked(self):
        """Обробка скасування"""
        self.destroy()


class TextManagerWidget(tk.Frame):
    """Віджет управління текстами"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.texts = {
            'story_replies': [],
            'direct_messages': []
        }
        
        self.create_widgets()
        self.load_texts()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        header = tk.Label(
            self,
            text="📝 Управління текстами",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Стилізація ttk
        style = ttk.Style()
        style.configure('TNotebook', background=ModernStyle.COLORS['surface'])
        style.configure('TNotebook.Tab', background=ModernStyle.COLORS['card'])
        
        # Вкладка для відповідей на сторіс
        self.stories_frame = tk.Frame(self.notebook, bg=ModernStyle.COLORS['card'])
        self.notebook.add(self.stories_frame, text="Відповіді на сторіс")
        
        # Вкладка для приватних повідомлень
        self.dm_frame = tk.Frame(self.notebook, bg=ModernStyle.COLORS['card'])
        self.notebook.add(self.dm_frame, text="Приватні повідомлення")
        
        # Створення віджетів для кожної вкладки
        self.create_text_tab(self.stories_frame, 'story_replies', 
                           "Тексти для відповідей на сторіс:")
        self.create_text_tab(self.dm_frame, 'direct_messages', 
                           "Тексти для приватних повідомлень:")
    
    def create_text_tab(self, parent, text_type, label):
        """Створення вкладки для текстів"""
        # Заголовок
        tk.Label(
            parent,
            text=label,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', padx=20, pady=(10, 5))
        
        # Фрейм для поля введення та кнопки
        input_frame = tk.Frame(parent, bg=ModernStyle.COLORS['card'])
        input_frame.pack(fill='x', padx=20, pady=5)
        
        # Поле для нового тексту
        text_entry = scrolledtext.ScrolledText(
            input_frame,
            height=3,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text'],
            wrap=tk.WORD
        )
        text_entry.pack(side='left', fill='both', expand=True)
        
        # Кнопка додавання
        add_btn = AnimatedButton(
            input_frame,
            text="➕",
            command=lambda: self.add_text(text_type, text_entry),
            bg=ModernStyle.COLORS['success']
        )
        add_btn.pack(side='right', padx=(10, 0))
        
        # Список існуючих текстів
        tk.Label(
            parent,
            text="Збережені тексти:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', padx=20, pady=(10, 5))
        
        # Скролюючий список
        list_frame = tk.Frame(parent, bg=ModernStyle.COLORS['card'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Створення listbox з кастомним стилем
        listbox = tk.Listbox(
            list_frame,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text'],
            selectbackground=ModernStyle.COLORS['primary'],
            selectforeground='white',
            relief='flat',
            borderwidth=0
        )
        listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Кнопки управління
        control_frame = tk.Frame(parent, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=20, pady=10)
        
        AnimatedButton(
            control_frame,
            text="🗑️ Видалити",
            command=lambda: self.remove_text(text_type, listbox),
            bg=ModernStyle.COLORS['error']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="✏️ Редагувати",
            command=lambda: self.edit_text(text_type, listbox, text_entry),
            bg=ModernStyle.COLORS['warning']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="💾 Зберегти все",
            command=self.save_texts,
            bg=ModernStyle.COLORS['success']
        ).pack(side='right', padx=5)
        
        # Збереження посилань
        setattr(self, f'{text_type}_listbox', listbox)
        setattr(self, f'{text_type}_entry', text_entry)
    
    def add_text(self, text_type, text_entry):
        """Додавання нового тексту"""
        text = text_entry.get('1.0', tk.END).strip()
        if text:
            self.texts[text_type].append(text)
            self.update_listbox(text_type)
            text_entry.delete('1.0', tk.END)
            self.save_texts()
    
    def remove_text(self, text_type, listbox):
        """Видалення тексту"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            self.texts[text_type].pop(index)
            self.update_listbox(text_type)
            self.save_texts()
    
    def edit_text(self, text_type, listbox, text_entry):
        """Редагування тексту"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            current_text = self.texts[text_type][index]
            text_entry.delete('1.0', tk.END)
            text_entry.insert('1.0', current_text)
    
    def update_listbox(self, text_type):
        """Оновлення списку текстів"""
        listbox = getattr(self, f'{text_type}_listbox')
        listbox.delete(0, tk.END)
        
        for i, text in enumerate(self.texts[text_type]):
            # Обмеження довжини відображення
            display_text = text[:50] + "..." if len(text) > 50 else text
            # Заміна переносів рядків на пробіли для відображення
            display_text = display_text.replace('\n', ' ')
            listbox.insert(tk.END, f"{i+1}. {display_text}")
    
    def save_texts(self):
        """Збереження текстів"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/texts.json', 'w', encoding='utf-8') as f:
                json.dump(self.texts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти тексти: {e}")
    
    def load_texts(self):
        """Завантаження збережених текстів"""
        try:
            if os.path.exists('data/texts.json'):
                with open('data/texts.json', 'r', encoding='utf-8') as f:
                    self.texts = json.load(f)
                
                # Оновлення відображення
                for text_type in self.texts:
                    if hasattr(self, f'{text_type}_listbox'):
                        self.update_listbox(text_type)
        except Exception as e:
            print(f"Помилка завантаження текстів: {e}")
    
    def get_texts(self, text_type):
        """Отримання текстів певного типу"""
        return self.texts.get(text_type, [])


class AccountManagerWidget(tk.Frame):
    """Віджет управління акаунтами"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.accounts = []
        self.create_widgets()
        self.load_accounts()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        header = tk.Label(
            self,
            text="👥 Управління акаунтами",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Форма додавання акаунту
        add_frame = GlassCard(self, title="Додати новий акаунт")
        add_frame.pack(fill='x', padx=20, pady=10)
        
        form_frame = tk.Frame(add_frame, bg=ModernStyle.COLORS['card'])
        form_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Поля введення
        fields_frame = tk.Frame(form_frame, bg=ModernStyle.COLORS['card'])
        fields_frame.pack(fill='x')
        
        # Username
        tk.Label(
            fields_frame,
            text="Логін:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=0, sticky='w', pady=2)
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(
            fields_frame,
            textvariable=self.username_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        username_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        # Password
        tk.Label(
            fields_frame,
            text="Пароль:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=1, column=0, sticky='w', pady=2)
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            fields_frame,
            textvariable=self.password_var,
            show='*',
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        password_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # Proxy
        tk.Label(
            fields_frame,
            text="Проксі (опціонально):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=2, column=0, sticky='w', pady=2)
        
        self.proxy_var = tk.StringVar()
        proxy_entry = tk.Entry(
            fields_frame,
            textvariable=self.proxy_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        proxy_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопка додавання
        AnimatedButton(
            form_frame,
            text="➕ Додати акаунт",
            command=self.add_account,
            bg=ModernStyle.COLORS['success']
        ).pack(pady=10)
        
        # Список акаунтів
        list_frame = GlassCard(self, title="Збережені акаунти")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Створення Treeview для відображення акаунтів
        tree_frame = tk.Frame(list_frame, bg=ModernStyle.COLORS['card'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        columns = ('Логін', 'Проксі', 'Статус')
        self.accounts_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=8
        )
        
        # Налаштування колонок
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=150)
        
        # Стилізація Treeview
        style = ttk.Style()
        style.configure("Treeview", 
                       background=ModernStyle.COLORS['background'],
                       foreground=ModernStyle.COLORS['text'],
                       fieldbackground=ModernStyle.COLORS['background'])
        style.configure("Treeview.Heading", 
                       background=ModernStyle.COLORS['card'],
                       foreground=ModernStyle.COLORS['text'])
        
        # Скролбар
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.accounts_tree.pack(side='left', fill='both', expand=True)
        tree_scrollbar.pack(side='right', fill='y')
        
        # Кнопки управління
        control_frame = tk.Frame(list_frame, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        AnimatedButton(
            control_frame,
            text="🗑️ Видалити",
            command=self.remove_account,
            bg=ModernStyle.COLORS['error']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="✏️ Редагувати",
            command=self.edit_account,
            bg=ModernStyle.COLORS['warning']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="📁 Імпорт з файлу",
            command=self.import_accounts,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="💾 Експорт",
            command=self.export_accounts,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='right', padx=5)
    
    def add_account(self):
        """Додавання нового акаунту"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        proxy = self.proxy_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Попередження", "Введіть логін та пароль")
            return
        
        # Перевірка чи акаунт вже існує
        for account in self.accounts:
            if account['username'] == username:
                messagebox.showwarning("Попередження", "Акаунт вже існує")
                return
        
        account = {
            'username': username,
            'password': password,
            'proxy': proxy if proxy else None,
            'status': 'active',
            'added_at': datetime.now().isoformat()
        }
        
        self.accounts.append(account)
        self.update_accounts_display()
        self.save_accounts()
        
        # Очищення полів
        self.username_var.set("")
        self.password_var.set("")
        self.proxy_var.set("")
        
        messagebox.showinfo("Успіх", "Акаунт додано успішно")
    
    def remove_account(self):
        """Видалення акаунту"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть акаунт для видалення")
            return
        
        if messagebox.askyesno("Підтвердження", "Видалити вибраний акаунт?"):
            item = selection[0]
            index = self.accounts_tree.index(item)
            self.accounts.pop(index)
            self.update_accounts_display()
            self.save_accounts()
    
    def edit_account(self):
        """Редагування акаунту"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть акаунт для редагування")
            return
        
        item = selection[0]
        index = self.accounts_tree.index(item)
        account = self.accounts[index]
        
        # Заповнення полів поточними даними
        self.username_var.set(account['username'])
        self.password_var.set(account['password'])
        self.proxy_var.set(account.get('proxy', ''))
        
        # Видалення старого акаунту
        self.accounts.pop(index)
        self.update_accounts_display()
    
    def import_accounts(self):
        """Імпорт акаунтів з файлу"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
            title="Імпорт акаунтів"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                    if isinstance(data, list):
                        imported = 0
                        for account_data in data:
                            if isinstance(account_data, dict) and 'username' in account_data and 'password' in account_data:
                                # Перевірка чи акаунт вже існує
                                exists = any(acc['username'] == account_data['username'] for acc in self.accounts)
                                if not exists:
                                    self.accounts.append({
                                        'username': account_data['username'],
                                        'password': account_data['password'],
                                        'proxy': account_data.get('proxy'),
                                        'status': 'active',
                                        'added_at': datetime.now().isoformat()
                                    })
                                    imported += 1
                else:
                    # Текстовий формат: username:password:proxy
                    lines = f.readlines()
                    imported = 0
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                username = parts[0]
                                password = parts[1]
                                proxy = ':'.join(parts[2:]) if len(parts) > 2 else None
                                
                                # Перевірка чи акаунт вже існує
                                exists = any(acc['username'] == username for acc in self.accounts)
                                if not exists:
                                    self.accounts.append({
                                        'username': username,
                                        'password': password,
                                        'proxy': proxy,
                                        'status': 'active',
                                        'added_at': datetime.now().isoformat()
                                    })
                                    imported += 1
                
                self.update_accounts_display()
                self.save_accounts()
                messagebox.showinfo("Успіх", f"Імпортовано {imported} акаунтів")
                
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося імпортувати: {e}")
    
    def export_accounts(self):
        """Експорт акаунтів"""
        if not self.accounts:
            messagebox.showwarning("Попередження", "Немає акаунтів для експорту")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")],
            title="Експорт акаунтів"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    json.dump(self.accounts, f, indent=2, ensure_ascii=False)
                else:
                    for account in self.accounts:
                        line = f"{account['username']}:{account['password']}"
                        if account.get('proxy'):
                            line += f":{account['proxy']}"
                        f.write(line + '\n')
            
            messagebox.showinfo("Успіх", f"Акаунти експортовано: {filename}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося експортувати: {e}")
    
    def update_accounts_display(self):
        """Оновлення відображення акаунтів"""
        # Очищення таблиці
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Додавання акаунтів
        for account in self.accounts:
            proxy_display = account.get('proxy', 'Немає')[:20] + "..." if account.get('proxy') and len(account.get('proxy', '')) > 20 else account.get('proxy', 'Немає')
            
            self.accounts_tree.insert('', 'end', values=(
                account['username'],
                proxy_display,
                account.get('status', 'active')
            ))
    
    def save_accounts(self):
        """Збереження акаунтів"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/accounts.json', 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти акаунти: {e}")
    
    def load_accounts(self):
        """Завантаження збережених акаунтів"""
        try:
            if os.path.exists('data/accounts.json'):
                with open('data/accounts.json', 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
                self.update_accounts_display()
        except Exception as e:
            print(f"Помилка завантаження акаунтів: {e}")
    
    def get_accounts(self):
        """Отримання списку акаунтів"""
        return self.accounts


class TargetManagerWidget(tk.Frame):
    """Віджет управління цілями"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.targets = []
        self.create_widgets()
        self.load_targets()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        header = tk.Label(
            self,
            text="🎯 Управління цілями",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Форма додавання цілі
        add_frame = GlassCard(self, title="Додати нові цілі")
        add_frame.pack(fill='x', padx=20, pady=10)
        
        form_frame = tk.Frame(add_frame, bg=ModernStyle.COLORS['card'])
        form_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Поле введення
        tk.Label(
            form_frame,
            text="Username (без @):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        self.target_var = tk.StringVar()
        target_entry = tk.Entry(
            form_frame,
            textvariable=self.target_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        target_entry.pack(fill='x', pady=5)
        target_entry.bind('<Return>', lambda e: self.add_target())
        
        # Масове додавання
        tk.Label(
            form_frame,
            text="Або додайте кілька цілей (по одній на рядок):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(10, 0))
        
        self.bulk_text = scrolledtext.ScrolledText(
            form_frame,
            height=4,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text'],
            wrap=tk.WORD
        )
        self.bulk_text.pack(fill='x', pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(form_frame, bg=ModernStyle.COLORS['card'])
        btn_frame.pack(fill='x', pady=10)
        
        AnimatedButton(
            btn_frame,
            text="➕ Додати ціль",
            command=self.add_target,
            bg=ModernStyle.COLORS['success']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            btn_frame,
            text="📝 Додати всі",
            command=self.add_bulk_targets,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='left', padx=5)
        
        # Список цілей
        list_frame = GlassCard(self, title="Збережені цілі")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Listbox для цілей
        targets_frame = tk.Frame(list_frame, bg=ModernStyle.COLORS['card'])
        targets_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.targets_listbox = tk.Listbox(
            targets_frame,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text'],
            selectbackground=ModernStyle.COLORS['primary'],
            selectforeground='white',
            relief='flat',
            borderwidth=0
        )
        self.targets_listbox.pack(side='left', fill='both', expand=True)
        
        targets_scrollbar = ttk.Scrollbar(targets_frame, orient="vertical", command=self.targets_listbox.yview)
        targets_scrollbar.pack(side='right', fill='y')
        self.targets_listbox.configure(yscrollcommand=targets_scrollbar.set)
        
        # Кнопки управління
        control_frame = tk.Frame(list_frame, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        AnimatedButton(
            control_frame,
            text="🗑️ Видалити",
            command=self.remove_target,
            bg=ModernStyle.COLORS['error']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="📁 Імпорт",
            command=self.import_targets,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='left', padx=5)
        
        AnimatedButton(
            control_frame,
            text="💾 Експорт",
            command=self.export_targets,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='right', padx=5)
        
        AnimatedButton(
            control_frame,
            text="🗑️ Очистити все",
            command=self.clear_all_targets,
            bg=ModernStyle.COLORS['error']
        ).pack(side='right', padx=5)
    
    def add_target(self):
        """Додавання цілі"""
        target = self.target_var.get().strip().replace('@', '')
        
        if not target:
            messagebox.showwarning("Попередження", "Введіть username")
            return
        
        if target in self.targets:
            messagebox.showwarning("Попередження", "Ціль вже існує")
            return
        
        self.targets.append(target)
        self.update_targets_display()
        self.save_targets()
        self.target_var.set("")
    
    def add_bulk_targets(self):
        """Масове додавання цілей"""
        text = self.bulk_text.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Попередження", "Введіть цілі")
            return
        
        lines = text.split('\n')
        added = 0
        
        for line in lines:
            target = line.strip().replace('@', '')
            if target and target not in self.targets:
                self.targets.append(target)
                added += 1
        
        if added > 0:
            self.update_targets_display()
            self.save_targets()
            self.bulk_text.delete('1.0', tk.END)
            messagebox.showinfo("Успіх", f"Додано {added} цілей")
        else:
            messagebox.showwarning("Попередження", "Нові цілі не знайдено")
    
    def remove_target(self):
        """Видалення цілі"""
        selection = self.targets_listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть ціль для видалення")
            return
        
        index = selection[0]
        self.targets.pop(index)
        self.update_targets_display()
        self.save_targets()
    
    def clear_all_targets(self):
        """Очищення всіх цілей"""
        if messagebox.askyesno("Підтвердження", "Видалити всі цілі?"):
            self.targets.clear()
            self.update_targets_display()
            self.save_targets()
    
    def import_targets(self):
        """Імпорт цілей з файлу"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
            title="Імпорт цілей"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                    if isinstance(data, list):
                        imported = 0
                        for target in data:
                            target = str(target).strip().replace('@', '')
                            if target and target not in self.targets:
                                self.targets.append(target)
                                imported += 1
                else:
                    lines = f.readlines()
                    imported = 0
                    for line in lines:
                        target = line.strip().replace('@', '')
                        if target and not target.startswith('#') and target not in self.targets:
                            self.targets.append(target)
                            imported += 1
                
                self.update_targets_display()
                self.save_targets()
                messagebox.showinfo("Успіх", f"Імпортовано {imported} цілей")
                
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося імпортувати: {e}")
    
    def export_targets(self):
        """Експорт цілей"""
        if not self.targets:
            messagebox.showwarning("Попередження", "Немає цілей для експорту")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
            title="Експорт цілей"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    json.dump(self.targets, f, indent=2, ensure_ascii=False)
                else:
                    for target in self.targets:
                        f.write(target + '\n')
            
            messagebox.showinfo("Успіх", f"Цілі експортовано: {filename}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося експортувати: {e}")
    
    def update_targets_display(self):
        """Оновлення відображення цілей"""
        self.targets_listbox.delete(0, tk.END)
        for i, target in enumerate(self.targets):
            self.targets_listbox.insert(tk.END, f"{i+1}. @{target}")
    
    def save_targets(self):
        """Збереження цілей"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/targets.json', 'w', encoding='utf-8') as f:
                json.dump(self.targets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти цілі: {e}")
    
    def load_targets(self):
        """Завантаження збережених цілей"""
        try:
            if os.path.exists('data/targets.json'):
                with open('data/targets.json', 'r', encoding='utf-8') as f:
                    self.targets = json.load(f)
                self.update_targets_display()
        except Exception as e:
            print(f"Помилка завантаження цілей: {e}")
    
    def get_targets(self):
        """Отримання списку цілей"""
        return self.targets


class BrowserSettingsWidget(tk.Frame):
    """Віджет налаштувань браузера"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.settings = {
            'browser_type': 'chrome',
            'headless': False,
            'proxy_enabled': True,
            'stealth_mode': True,
            'dolphin_api_url': 'http://localhost:3001/v1.0',
            'dolphin_token': ''
        }
        
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        header = tk.Label(
            self,
            text="🌐 Налаштування браузера",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Вибір типу браузера
        browser_frame = GlassCard(self, title="Тип браузера")
        browser_frame.pack(fill='x', padx=20, pady=10)
        
        content_frame = tk.Frame(browser_frame, bg=ModernStyle.COLORS['card'])
        content_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.browser_var = tk.StringVar(value=self.settings['browser_type'])
        
        # Chrome опція
        chrome_frame = tk.Frame(content_frame, bg=ModernStyle.COLORS['surface'], relief='solid', bd=1)
        chrome_frame.pack(fill='x', pady=5)
        
        chrome_radio = tk.Radiobutton(
            chrome_frame,
            text="🌐 Google Chrome (Playwright)",
            variable=self.browser_var,
            value='chrome',
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['primary'],
            activebackground=ModernStyle.COLORS['surface'],
            command=self.on_browser_change
        )
        chrome_radio.pack(anchor='w', padx=10, pady=10)
        
        chrome_desc = tk.Label(
            chrome_frame,
            text="• Безкоштовний\n• Швидкий та стабільний\n• Автоматичний stealth режим",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_secondary'],
            justify='left'
        )
        chrome_desc.pack(anchor='w', padx=30, pady=(0, 10))
        
        # Dolphin опція
        dolphin_frame = tk.Frame(content_frame, bg=ModernStyle.COLORS['surface'], relief='solid', bd=1)
        dolphin_frame.pack(fill='x', pady=5)
        
        dolphin_radio = tk.Radiobutton(
            dolphin_frame,
            text="🐬 Dolphin Anty Browser",
            variable=self.browser_var,
            value='dolphin',
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['primary'],
            activebackground=ModernStyle.COLORS['surface'],
            command=self.on_browser_change
        )
        dolphin_radio.pack(anchor='w', padx=10, pady=10)
        
        dolphin_desc = tk.Label(
            dolphin_frame,
            text="• Професійний антидетект\n• Автоматичні проксі профілі\n• Найкращий обхід блокувань",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_secondary'],
            justify='left'
        )
        dolphin_desc.pack(anchor='w', padx=30, pady=(0, 10))
        
        # Загальні налаштування
        general_frame = GlassCard(self, title="Загальні налаштування")
        general_frame.pack(fill='x', padx=20, pady=10)
        
        gen_content = tk.Frame(general_frame, bg=ModernStyle.COLORS['card'])
        gen_content.pack(fill='x', padx=20, pady=(0, 20))
        
        # Headless режим
        self.headless_var = tk.BooleanVar(value=self.settings['headless'])
        headless_check = tk.Checkbutton(
            gen_content,
            text="Headless режим (без графічного інтерфейсу)",
            variable=self.headless_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=self.save_settings
        )
        headless_check.pack(anchor='w', pady=5)
        
        # Stealth режим
        self.stealth_var = tk.BooleanVar(value=self.settings['stealth_mode'])
        stealth_check = tk.Checkbutton(
            gen_content,
            text="Stealth режим (обхід детекції)",
            variable=self.stealth_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=self.save_settings
        )
        stealth_check.pack(anchor='w', pady=5)
        
        # Проксі
        self.proxy_var = tk.BooleanVar(value=self.settings['proxy_enabled'])
        proxy_check = tk.Checkbutton(
            gen_content,
            text="Автоматичне використання проксі",
            variable=self.proxy_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=self.save_settings
        )
        proxy_check.pack(anchor='w', pady=5)
        
        # Dolphin налаштування
        self.dolphin_frame = GlassCard(self, title="Налаштування Dolphin Anty")
        self.dolphin_frame.pack(fill='x', padx=20, pady=10)
        
        dolphin_content = tk.Frame(self.dolphin_frame, bg=ModernStyle.COLORS['card'])
        dolphin_content.pack(fill='x', padx=20, pady=(0, 20))
        
        # API URL
        tk.Label(
            dolphin_content,
            text="API URL:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(5, 0))
        
        self.api_url_var = tk.StringVar(value=self.settings['dolphin_api_url'])
        api_url_entry = tk.Entry(
            dolphin_content,
            textvariable=self.api_url_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        api_url_entry.pack(fill='x', pady=5)
        api_url_entry.bind('<KeyRelease>', lambda e: self.save_settings())
        
        # API Token
        tk.Label(
            dolphin_content,
            text="API Token:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(10, 0))
        
        self.api_token_var = tk.StringVar(value=self.settings['dolphin_token'])
        api_token_entry = tk.Entry(
            dolphin_content,
            textvariable=self.api_token_var,
            show='*',
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            insertbackground=ModernStyle.COLORS['text']
        )
        api_token_entry.pack(fill='x', pady=5)
        api_token_entry.bind('<KeyRelease>', lambda e: self.save_settings())
        
        # Кнопка тестування
        AnimatedButton(
            dolphin_content,
            text="🔍 Тест з'єднання",
            command=self.test_dolphin_connection,
            bg=ModernStyle.COLORS['primary']
        ).pack(pady=10)
        
        # Показати/приховати Dolphin налаштування
        self.on_browser_change()
    
    def on_browser_change(self):
        """Обробка зміни типу браузера"""
        browser_type = self.browser_var.get()
        
        if browser_type == 'dolphin':
            self.dolphin_frame.pack(fill='x', padx=20, pady=10)
        else:
            self.dolphin_frame.pack_forget()
        
        self.settings['browser_type'] = browser_type
        self.save_settings()
    
    def test_dolphin_connection(self):
        """Тестування з'єднання з Dolphin"""
        def test_worker():
            try:
                import requests
                
                url = self.api_url_var.get()
                token = self.api_token_var.get()
                
                if not url or not token:
                    messagebox.showerror("Помилка", "Введіть URL та Token")
                    return
                
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.get(f'{url}/browser_profiles', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    messagebox.showinfo("Успіх", "З'єднання з Dolphin API успішне!")
                else:
                    messagebox.showerror("Помилка", f"Помилка API: {response.status_code}")
                    
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося підключитися: {e}")
        
        # Запуск в окремому потоці
        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()
    
    def save_settings(self):
        """Збереження налаштувань"""
        self.settings = {
            'browser_type': self.browser_var.get(),
            'headless': self.headless_var.get(),
            'proxy_enabled': self.proxy_var.get(),
            'stealth_mode': self.stealth_var.get(),
            'dolphin_api_url': self.api_url_var.get(),
            'dolphin_token': self.api_token_var.get()
        }
        
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/browser_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження налаштувань браузера: {e}")
    
    def load_settings(self):
        """Завантаження налаштувань"""
        try:
            if os.path.exists('data/browser_settings.json'):
                with open('data/browser_settings.json', 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                
                # Оновлення інтерфейсу
                self.browser_var.set(self.settings['browser_type'])
                self.headless_var.set(self.settings['headless'])
                self.proxy_var.set(self.settings['proxy_enabled'])
                self.stealth_var.set(self.settings['stealth_mode'])
                self.api_url_var.set(self.settings['dolphin_api_url'])
                self.api_token_var.set(self.settings['dolphin_token'])
                
        except Exception as e:
            print(f"Помилка завантаження налаштувань браузера: {e}")
    
    def get_settings(self):
        """Отримання поточних налаштувань"""
        return self.settings


class WorkerStatusWidget(tk.Frame):
    """Віджет статусу воркера"""
    
    def __init__(self, parent, worker_id, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['card'])
        
        self.worker_id = worker_id
        self.status = 'idle'
        self.stats = {
            'processed_accounts': 0,
            'total_actions': 0,
            'successful_actions': 0,
            'errors': 0
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення віджетів"""
        # Заголовок воркера
        header_frame = tk.Frame(self, bg=ModernStyle.COLORS['card'])
        header_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_dot = tk.Label(
            header_frame,
            text="●",
            font=('Arial', 16),
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_dot.pack(side='left')
        
        tk.Label(
            header_frame,
            text=f"Воркер #{self.worker_id + 1}",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(side='left', padx=(5, 0))
        
        self.status_label = tk.Label(
            header_frame,
            text="Очікування",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_label.pack(side='right')
        
        # Статистика
        stats_frame = tk.Frame(self, bg=ModernStyle.COLORS['card'])
        stats_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        self.stats_labels = {}
        stats_items = [
            ('Акаунтів:', 'processed_accounts'),
            ('Дій:', 'total_actions'),
            ('Успішних:', 'successful_actions'),
            ('Помилок:', 'errors')
        ]
        
        for i, (label_text, stat_key) in enumerate(stats_items):
            row = i // 2
            col = i % 2
            
            item_frame = tk.Frame(stats_frame, bg=ModernStyle.COLORS['card'])
            item_frame.grid(row=row, column=col, sticky='ew', padx=2, pady=1)
            
            tk.Label(
                item_frame,
                text=label_text,
                font=ModernStyle.FONTS['small'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text_secondary']
            ).pack(side='left')
            
            value_label = tk.Label(
                item_frame,
                text="0",
                font=ModernStyle.FONTS['small'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text']
            )
            value_label.pack(side='right')
            
            self.stats_labels[stat_key] = value_label
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
    
    def update_status(self, status, current_account=None):
        """Оновлення статусу воркера"""
        self.status = status
        
        status_colors = {
            'idle': ModernStyle.COLORS['text_secondary'],
            'working': ModernStyle.COLORS['success'],
            'error': ModernStyle.COLORS['error'],
            'paused': ModernStyle.COLORS['warning']
        }
        
        status_texts = {
            'idle': 'Очікування',
            'working': f'Працює: {current_account}' if current_account else 'Активний',
            'error': 'Помилка',
            'paused': 'Пауза'
        }
        
        self.status_dot.configure(fg=status_colors.get(status, status_colors['idle']))
        self.status_label.configure(text=status_texts.get(status, 'Невідомо'))
    
    def update_stats(self, stats):
        """Оновлення статистики воркера"""
        self.stats.update(stats)
        
        for stat_key, value in self.stats.items():
            if stat_key in self.stats_labels:
                self.stats_labels[stat_key].configure(text=str(value))


class InstagramBotGUI:
    """Головний клас GUI"""
    
    def __init__(self, root):
        self.root = root
        self.data_manager = DataManager()
        self.automation_manager = None
        self.worker_widgets = []
        
        self.setup_window()
        self.create_widgets()
        self.load_all_data()
    
    def setup_window(self):
        """Налаштування головного вікна"""
        self.root.title("Instagram Bot Pro v3.0 - Професійна автоматизація")
        self.root.geometry("1600x1000")
        self.root.configure(bg=ModernStyle.COLORS['background'])
        
        # Центрування вікна
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (1000 // 2)
        self.root.geometry(f"1600x1000+{x}+{y}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Створення віджетів інтерфейсу"""
        # Головний контейнер
        main_container = tk.Frame(self.root, bg=ModernStyle.COLORS['background'])
        main_container.pack(fill='both', expand=True)
        
        # Бічна панель
        sidebar = tk.Frame(main_container, bg=ModernStyle.COLORS['sidebar'], width=300)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        logo_frame.pack(fill='x', pady=20)
        
        tk.Label(
            logo_frame,
            text="🤖 Instagram Bot Pro",
            font=ModernStyle.FONTS['title'],
            bg=ModernStyle.COLORS['sidebar'],
            fg=ModernStyle.COLORS['text']
        ).pack()
        
        tk.Label(
            logo_frame,
            text="v3.0 Multi-Worker Edition",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['sidebar'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack()
        
        # Навігація
        nav_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        nav_frame.pack(fill='x', padx=10, pady=20)
        
        self.nav_buttons = {}
        nav_items = [
            ("🏠", "Головна", "main"),
            ("👥", "Акаунти", "accounts"),
            ("🎯", "Цілі", "targets"),
            ("🔗", "Ланцюжок дій", "chain"),
            ("📝", "Тексти", "texts"),
            ("🌐", "Браузер", "browser"),
            ("▶️", "Запуск", "run")
        ]
        
        for icon, text, page in nav_items:
            btn = tk.Button(
                nav_frame,
                text=f"  {icon}  {text}",
                command=lambda p=page: self.show_page(p),
                font=ModernStyle.FONTS['body'],
                bg=ModernStyle.COLORS['sidebar'],
                fg=ModernStyle.COLORS['text'],
                relief='flat',
                anchor='w',
                padx=15,
                pady=10,
                cursor='hand2'
            )
            btn.pack(fill='x', pady=1)
            
            # Hover ефекти
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=ModernStyle.COLORS['sidebar_active']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=ModernStyle.COLORS['sidebar']) if not getattr(b, 'active', False) else None)
            
            self.nav_buttons[page] = btn
        
        # Статус системи
        status_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        status_frame.pack(side='bottom', fill='x', padx=20, pady=20)
        
        tk.Label(
            status_frame,
            text="Статус системи:",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['sidebar'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack(anchor='w')
        
        self.status_label = tk.Label(
            status_frame,
            text="● Готовий до роботи",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['sidebar'],
            fg=ModernStyle.COLORS['success']
        )
        self.status_label.pack(anchor='w', pady=2)
        
        # Область контенту
        self.content_area = tk.Frame(main_container, bg=ModernStyle.COLORS['background'])
        self.content_area.pack(side='right', fill='both', expand=True)
        
        # Створення сторінок
        self.create_pages()
        
        # Показ головної сторінки
        self.show_page("main")
    
    def create_pages(self):
        """Створення всіх сторінок"""
        self.pages = {}
        
        # Головна сторінка
        self.pages["main"] = self.create_main_page()
        
        # Сторінка акаунтів
        self.pages["accounts"] = AccountManagerWidget(self.content_area)
        
        # Сторінка цілей
        self.pages["targets"] = TargetManagerWidget(self.content_area)
        
        # Сторінка ланцюжка дій
        self.pages["chain"] = ChainBuilderWidget(self.content_area)
        
        # Сторінка текстів
        self.pages["texts"] = TextManagerWidget(self.content_area)
        
        # Сторінка браузера
        self.pages["browser"] = BrowserSettingsWidget(self.content_area)
        
        # Сторінка запуску
        self.pages["run"] = self.create_run_page()
    
    def create_main_page(self):
        """Створення головної сторінки"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        # Заголовок
        header = tk.Label(
            page,
            text="🏠 Панель управління",
            font=ModernStyle.FONTS['title'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=20)
        
        # Статистичні картки
        stats_frame = tk.Frame(page, bg=ModernStyle.COLORS['background'])
        stats_frame.pack(fill='x', padx=20, pady=20)
        
        # Картки статистики
        cards_data = [
            ("👥", "Акаунтів", "0", "accounts_count"),
            ("🎯", "Цілей", "0", "targets_count"),
            ("🔗", "Дій в ланцюжку", "0", "chain_count"),
            ("📝", "Текстів", "0", "texts_count")
        ]
        
        self.stat_labels = {}
        
        for i, (icon, title, value, key) in enumerate(cards_data):
            card = GlassCard(stats_frame)
            card.grid(row=0, column=i, padx=10, sticky='ew')
            
            content = tk.Frame(card, bg=ModernStyle.COLORS['card'])
            content.pack(fill='both', expand=True, padx=20, pady=20)
            
            tk.Label(
                content,
                text=icon,
                font=('Arial', 32),
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['primary']
            ).pack()
            
            value_label = tk.Label(
                content,
                text=value,
                font=ModernStyle.FONTS['title'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text']
            )
            value_label.pack()
            
            tk.Label(
                content,
                text=title,
                font=ModernStyle.FONTS['small'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text_secondary']
            ).pack()
            
            self.stat_labels[key] = value_label
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)
        
        # Швидкі дії
        actions_frame = GlassCard(page, title="Швидкі дії")
        actions_frame.pack(fill='x', padx=20, pady=20)
        
        actions_content = tk.Frame(actions_frame, bg=ModernStyle.COLORS['card'])
        actions_content.pack(fill='x', padx=20, pady=(0, 20))
        
        buttons = [
            ("➕ Додати акаунт", lambda: self.show_page("accounts"), ModernStyle.COLORS['success']),
            ("🎯 Додати ціль", lambda: self.show_page("targets"), ModernStyle.COLORS['primary']),
            ("🔗 Налаштувати дії", lambda: self.show_page("chain"), ModernStyle.COLORS['warning']),
            ("▶️ Запустити бота", lambda: self.show_page("run"), ModernStyle.COLORS['success'])
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            AnimatedButton(
                actions_content,
                text=text,
                command=command,
                bg=color
            ).grid(row=0, column=i, padx=5, sticky='ew')
        
        actions_content.grid_columnconfigure(0, weight=1)
        actions_content.grid_columnconfigure(1, weight=1)
        actions_content.grid_columnconfigure(2, weight=1)
        actions_content.grid_columnconfigure(3, weight=1)
        
        return page
    
    def create_run_page(self):
        """Створення оптимізованої сторінки запуску"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        # Заголовок
        header = tk.Label(
            page,
            text="▶️ Запуск автоматизації",
            font=ModernStyle.FONTS['title'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=(10, 20))
        
        # Головний скролюючий контейнер
        main_canvas = tk.Canvas(page, bg=ModernStyle.COLORS['background'], highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(page, orient="vertical", command=main_canvas.yview)
        scrollable_page = tk.Frame(main_canvas, bg=ModernStyle.COLORS['background'])
        
        scrollable_page.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_page, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Розміщення скролюючого контейнера
        main_canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        main_scrollbar.pack(side="right", fill="y", padx=(0, 20))
        
        # --- КОМПАКТНІ НАЛАШТУВАННЯ ЗАПУСКУ ---
        settings_card = GlassCard(scrollable_page, title="Швидкі налаштування")
        settings_card.pack(fill='x', padx=20, pady=(0, 15))
        
        settings_content = tk.Frame(settings_card, bg=ModernStyle.COLORS['card'])
        settings_content.pack(fill='x', padx=20, pady=(0, 15))
        
        # Компактна сітка налаштувань
        settings_grid = tk.Frame(settings_content, bg=ModernStyle.COLORS['card'])
        settings_grid.pack(fill='x', pady=5)
        
        # Рядок 1: Воркери та Затримка
        tk.Label(
            settings_grid,
            text="Воркери:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
        
        self.workers_var = tk.StringVar(value="3")
        workers_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=10,
            width=8,
            textvariable=self.workers_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        workers_spin.grid(row=0, column=1, sticky='w', padx=(0, 20), pady=5)
        
        tk.Label(
            settings_grid,
            text="Затримка (хв):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=2, sticky='w', padx=(0, 10), pady=5)
        
        self.delay_var = tk.StringVar(value="5")
        delay_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=60,
            width=8,
            textvariable=self.delay_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        delay_spin.grid(row=0, column=3, sticky='w', pady=5)
        
        # Рядок 2: Режим роботи
        tk.Label(
            settings_grid,
            text="Режим:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=5)
        
        self.mode_var = tk.StringVar(value="continuous")
        mode_combo = ttk.Combobox(
            settings_grid,
            textvariable=self.mode_var,
            values=["continuous", "single_round"],
            state="readonly",
            width=15
        )
        mode_combo.grid(row=1, column=1, columnspan=2, sticky='w', pady=5)
        
        # Налаштування сітки
        settings_grid.grid_columnconfigure(1, weight=1)
        settings_grid.grid_columnconfigure(3, weight=1)
        
        # --- КНОПКИ УПРАВЛІННЯ (ЗАВЖДИ ВИДИМІ) ---
        control_card = GlassCard(scrollable_page, title="Управління")
        control_card.pack(fill='x', padx=20, pady=(0, 15))
        
        control_content = tk.Frame(control_card, bg=ModernStyle.COLORS['card'])
        control_content.pack(fill='x', padx=20, pady=(0, 15))
        
        # Основні кнопки в один рядок
        main_buttons_frame = tk.Frame(control_content, bg=ModernStyle.COLORS['card'])
        main_buttons_frame.pack(fill='x', pady=(0, 10))
        
        self.start_btn = AnimatedButton(
            main_buttons_frame,
            text="▶️ Запустити",
            command=self.start_automation,
            bg=ModernStyle.COLORS['success']
        )
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = AnimatedButton(
            main_buttons_frame,
            text="⏹️ Зупинити",
            command=self.stop_automation,
            bg=ModernStyle.COLORS['error'],
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        self.pause_btn = AnimatedButton(
            main_buttons_frame,
            text="⏸️ Пауза",
            command=self.pause_automation,
            bg=ModernStyle.COLORS['warning'],
            state='disabled'
        )
        self.pause_btn.pack(side='left')
        
        # Додаткові кнопки
        extra_buttons_frame = tk.Frame(control_content, bg=ModernStyle.COLORS['card'])
        extra_buttons_frame.pack(fill='x')
        
        AnimatedButton(
            extra_buttons_frame,
            text="🔄 Перезапустити воркери",
            command=self.restart_workers,
            bg=ModernStyle.COLORS['primary']
        ).pack(side='left', padx=(0, 10))
        
        AnimatedButton(
            extra_buttons_frame,
            text="📊 Статистика",
            command=lambda: self.show_page("statistics"),
            bg=ModernStyle.COLORS['info']
        ).pack(side='left')
        
        # --- КОМПАКТНИЙ СТАТУС ВОРКЕРІВ ---
        workers_card = GlassCard(scrollable_page, title="Статус воркерів")
        workers_card.pack(fill='x', padx=20, pady=(0, 15))
        
        # Контейнер з фіксованою висотою
        workers_container = tk.Frame(workers_card, bg=ModernStyle.COLORS['card'], height=250)
        workers_container.pack(fill='x', padx=20, pady=(0, 15))
        workers_container.pack_propagate(False)  # Фіксована висота
        
        # Скролюючий контейнер для воркерів
        workers_canvas = tk.Canvas(
            workers_container,
            bg=ModernStyle.COLORS['card'],
            highlightthickness=0,
            height=230
        )
        workers_scrollbar = ttk.Scrollbar(workers_container, orient="vertical", command=workers_canvas.yview)
        self.workers_container = tk.Frame(workers_canvas, bg=ModernStyle.COLORS['card'])
        
        self.workers_container.bind(
            "<Configure>",
            lambda e: workers_canvas.configure(scrollregion=workers_canvas.bbox("all"))
        )
        
        workers_canvas.create_window((0, 0), window=self.workers_container, anchor="nw")
        workers_canvas.configure(yscrollcommand=workers_scrollbar.set)
        
        workers_canvas.pack(side="left", fill="both", expand=True)
        workers_scrollbar.pack(side="right", fill="y")
        
        # Створення компактних віджетів воркерів
        self.create_compact_worker_widgets(3)
        
        # --- ШВИДКА СТАТИСТИКА ---
        stats_card = GlassCard(scrollable_page, title="Швидка статистика")
        stats_card.pack(fill='x', padx=20, pady=(0, 20))
        
        stats_content = tk.Frame(stats_card, bg=ModernStyle.COLORS['card'])
        stats_content.pack(fill='x', padx=20, pady=(0, 15))
        
        # Компактна статистика в сітці
        stats_grid = tk.Frame(stats_content, bg=ModernStyle.COLORS['card'])
        stats_grid.pack(fill='x')
        
        # Створення статистичних лейблів
        self.quick_stats = {}
        stats_items = [
            ("Акаунти:", "0", "accounts"),
            ("Цілі:", "0", "targets"),
            ("Дії:", "0", "actions"),
            ("Воркери:", "0", "workers")
        ]
        
        for i, (label, value, key) in enumerate(stats_items):
            row, col = i // 2, (i % 2) * 2
            
            tk.Label(
                stats_grid,
                text=label,
                font=ModernStyle.FONTS['small'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text_secondary']
            ).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=2)
            
            value_label = tk.Label(
                stats_grid,
                text=value,
                font=ModernStyle.FONTS['body'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text']
            )
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 30), pady=2)
            
            self.quick_stats[key] = value_label
        
        # Налаштування сітки статистики
        stats_grid.grid_columnconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(3, weight=1)
        
        # Прокрутка колесом миші
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(page)
        
        return page
    
    def create_compact_worker_widgets(self, count):
        """Створення компактних віджетів воркерів"""
        # Очищення існуючих віджетів
        for widget in self.worker_widgets:
            widget.destroy()
        self.worker_widgets.clear()
        
        # Створення нових компактних віджетів
        for i in range(count):
            worker_widget = CompactWorkerStatusWidget(self.workers_container, i)
            worker_widget.pack(fill='x', padx=5, pady=3)
            self.worker_widgets.append(worker_widget)
    
    def restart_workers(self):
        """Перезапуск воркерів"""
        if self.automation_manager and self.automation_manager.is_running():
            messagebox.showwarning("Попередження", "Спочатку зупиніть автоматизацію")
            return
        
        try:
            # Оновлення кількості воркерів
            workers_count = int(self.workers_var.get())
            self.create_compact_worker_widgets(workers_count)
            
            # Оновлення статусу воркерів
            for widget in self.worker_widgets:
                widget.update_status('idle')
                widget.update_stats({})
            
            messagebox.showinfo("Успіх", f"Воркери перезапущені ({workers_count} воркерів)")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка перезапуску воркерів: {e}")


class CompactWorkerStatusWidget(tk.Frame):
    """Компактний віджет статусу воркера"""
    
    def __init__(self, parent, worker_id, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'], relief='flat', bd=1)
        
        self.worker_id = worker_id
        self.status = 'idle'
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення компактних віджетів"""
        # Основний контейнер
        main_frame = tk.Frame(self, bg=ModernStyle.COLORS['surface'])
        main_frame.pack(fill='x', padx=8, pady=6)
        
        # Ліва частина: статус
        left_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['surface'])
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Статус індикатор та назва
        status_frame = tk.Frame(left_frame, bg=ModernStyle.COLORS['surface'])
        status_frame.pack(fill='x')
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=('Arial', 12),
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_dot.pack(side='left')
        
        tk.Label(
            status_frame,
            text=f"Воркер #{self.worker_id + 1}",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        ).pack(side='left', padx=(5, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="Очікування",
            font=('Arial', 9),
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_label.pack(side='right')
        
        # Права частина: компактна статистика
        right_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['surface'])
        right_frame.pack(side='right')
        
        # Статистика в одному рядку
        stats_text = tk.Label(
            right_frame,
            text="Акаунти: 0 | Дії: 0 | Успішно: 0",
            font=('Arial', 8),
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_muted']
        )
        stats_text.pack()
        
        self.stats_label = stats_text
    
    def update_status(self, status, current_account=None):
        """Оновлення статусу воркера"""
        self.status = status
        
        status_colors = {
            'idle': ModernStyle.COLORS['text_secondary'],
            'working': ModernStyle.COLORS['success'],
            'error': ModernStyle.COLORS['error'],
            'paused': ModernStyle.COLORS['warning']
        }
        
        status_texts = {
            'idle': 'Очікування',
            'working': f'{current_account}' if current_account else 'Активний',
            'error': 'Помилка',
            'paused': 'Пауза'
        }
        
        self.status_dot.configure(fg=status_colors.get(status, status_colors['idle']))
        self.status_label.configure(text=status_texts.get(status, 'Невідомо'))
    
    def update_stats(self, stats):
        """Оновлення статистики воркера"""
        accounts = stats.get('processed_accounts', 0)
        total = stats.get('total_actions', 0) 
        successful = stats.get('successful_actions', 0)
        
        stats_text = f"Акаунти: {accounts} | Дії: {total} | Успішно: {successful}"
        self.stats_label.configure(text=stats_text)
    
    def create_worker_widgets(self, count):
        """Створення віджетів воркерів"""
        # Очищення існуючих віджетів
        for widget in self.worker_widgets:
            widget.destroy()
        self.worker_widgets.clear()
        
        # Створення нових віджетів
        for i in range(count):
            worker_widget = WorkerStatusWidget(self.workers_container, i)
            worker_widget.pack(fill='x', padx=10, pady=5)
            self.worker_widgets.append(worker_widget)
    
    def show_page(self, page_name):
        """Показ сторінки"""
        # Приховування всіх сторінок
        for page in self.pages.values():
            page.pack_forget()
        
        # Показ вибраної сторінки
        if page_name in self.pages:
            self.pages[page_name].pack(fill='both', expand=True)
        
        # Оновлення активної кнопки
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == page_name:
                btn.configure(bg=ModernStyle.COLORS['sidebar_active'])
                btn.active = True
            else:
                btn.configure(bg=ModernStyle.COLORS['sidebar'])
                btn.active = False
        
        # Оновлення статистики на головній сторінці
        if page_name == "main":
            self.update_main_stats()
    
    def update_main_stats(self):
        """Оновлення статистики на головній сторінці"""
        try:
            # Отримання даних
            accounts_count = len(self.pages["accounts"].get_accounts())
            targets_count = len(self.pages["targets"].get_targets())
            chain_count = len(self.pages["chain"].get_chain())
            texts_count = len(self.pages["texts"].get_texts('story_replies')) + len(self.pages["texts"].get_texts('direct_messages'))
            
            # Оновлення лейблів
            self.stat_labels["accounts_count"].configure(text=str(accounts_count))
            self.stat_labels["targets_count"].configure(text=str(targets_count))
            self.stat_labels["chain_count"].configure(text=str(chain_count))
            self.stat_labels["texts_count"].configure(text=str(texts_count))
            
        except Exception as e:
            print(f"Помилка оновлення статистики: {e}")
    
    def start_automation(self):
        """Запуск автоматизації"""
        # Перевірка даних
        accounts = self.pages["accounts"].get_accounts()
        targets = self.pages["targets"].get_targets()
        chain = self.pages["chain"].get_chain()
        browser_settings = self.pages["browser"].get_settings()
        
        if not accounts:
            messagebox.showwarning("Попередження", "Додайте хоча б один акаунт")
            return
        
        if not targets:
            messagebox.showwarning("Попередження", "Додайте хоча б одну ціль")
            return
        
        if not chain:
            messagebox.showwarning("Попередження", "Створіть ланцюжок дій")
            return
        
        # Налаштування
        workers_count = int(self.workers_var.get())
        delay_minutes = int(self.delay_var.get())
        mode = self.mode_var.get()
        
        # Створення віджетів воркерів
        self.create_worker_widgets(workers_count)
        
        # Створення менеджера автоматизації
        if not self.automation_manager:
            self.automation_manager = AutomationManager()
        
        # Конфігурація автоматизації
        automation_config = {
            'accounts': accounts,
            'targets': targets,
            'action_chain': chain,
            'browser_settings': browser_settings,
            'workers_count': workers_count,
            'delay_minutes': delay_minutes,
            'mode': mode,
            'texts': {
                'story_replies': self.pages["texts"].get_texts('story_replies'),
                'direct_messages': self.pages["texts"].get_texts('direct_messages')
            }
        }
        
        # Запуск в окремому потоці
        def run_automation():
            try:
                self.automation_manager.start_automation(automation_config, self.update_worker_status)
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка автоматизації: {e}")
                self.stop_automation()
        
        automation_thread = threading.Thread(target=run_automation, daemon=True)
        automation_thread.start()
        
        # Оновлення інтерфейсу
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.pause_btn.configure(state='normal')
        self.status_label.configure(text="● Автоматизація активна", fg=ModernStyle.COLORS['success'])
        
        messagebox.showinfo("Успіх", f"Автоматизація запущена з {workers_count} воркерами")
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        if self.automation_manager:
            self.automation_manager.stop_automation()
        
        # Оновлення статусу воркерів
        for widget in self.worker_widgets:
            widget.update_status('idle')
        
        # Оновлення інтерфейсу
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.pause_btn.configure(state='disabled')
        self.status_label.configure(text="● Готовий до роботи", fg=ModernStyle.COLORS['success'])
        
        messagebox.showinfo("Інформація", "Автоматизація зупинена")
    
    def pause_automation(self):
        """Пауза автоматизації"""
        if self.automation_manager:
            self.automation_manager.pause_automation()
        
        # Оновлення статусу воркерів
        for widget in self.worker_widgets:
            if widget.status == 'working':
                widget.update_status('paused')
        
        self.status_label.configure(text="● На паузі", fg=ModernStyle.COLORS['warning'])
        messagebox.showinfo("Інформація", "Автоматизація поставлена на паузу")
    
    def update_worker_status(self, worker_id, status, account=None, stats=None):
        """Оновлення статусу воркера"""
        try:
            if worker_id < len(self.worker_widgets):
                self.worker_widgets[worker_id].update_status(status, account)
                if stats:
                    self.worker_widgets[worker_id].update_stats(stats)
        except Exception as e:
            print(f"Помилка оновлення статусу воркера: {e}")
    
    def load_all_data(self):
        """Завантаження всіх збережених даних"""
        try:
            # Дані завантажуються автоматично в кожному віджеті
            self.update_main_stats()
        except Exception as e:
            print(f"Помилка завантаження даних: {e}")
    
    def on_closing(self):
        """Обробка закриття програми"""
        if self.automation_manager and self.automation_manager.is_running():
            if messagebox.askyesno("Підтвердження", "Автоматизація активна. Зупинити і вийти?"):
                self.stop_automation()
                self.root.destroy()
        else:
            if messagebox.askyesno("Підтвердження", "Закрити програму?"):
                self.root.destroy()


# Допоміжні класи

class DataManager:
    """Менеджер даних"""
    
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_data(self, filename, data):
        """Збереження даних"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Помилка збереження {filename}: {e}")
            return False
    
    def load_data(self, filename):
        """Завантаження даних"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Помилка завантаження {filename}: {e}")
        return None


class AutomationManager:
    """Менеджер автоматизації"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.workers = []
    
    def start_automation(self, config, status_callback):
        """Запуск автоматизації"""
        self.running = True
        self.paused = False
        
        # Тут буде логіка запуску воркерів
        # Поки що симуляція роботи
        import time
        
        workers_count = config['workers_count']
        accounts = config['accounts']
        targets = config['targets']
        
        for worker_id in range(workers_count):
            if worker_id < len(accounts):
                account = accounts[worker_id]
                status_callback(worker_id, 'working', account['username'])
                
                # Симуляція роботи
                for i, target in enumerate(targets):
                    if not self.running:
                        break
                    
                    while self.paused:
                        time.sleep(1)
                    
                    status_callback(worker_id, 'working', f"{account['username']} -> {target}")
                    time.sleep(2)  # Симуляція затримки
                    
                    # Оновлення статистики
                    stats = {
                        'processed_accounts': 1,
                        'total_actions': i + 1,
                        'successful_actions': i + 1,
                        'errors': 0
                    }
                    status_callback(worker_id, 'working', account['username'], stats)
                
                status_callback(worker_id, 'idle')
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        self.running = False
        self.paused = False
    
    def pause_automation(self):
        """Пауза автоматизації"""
        self.paused = True
    
    def is_running(self):
        """Перевірка чи працює автоматизація"""
        return self.running


def main():
    """Головна функція"""
    root = tk.Tk()
    app = InstagramBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()