# -*- coding: utf-8 -*-
"""
Instagram Bot Pro v3.0 - Оптимізований GUI з розподілом воркерів
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
    from automation_engine import MultiWorkerManager, InstagramAutomation # Реальна автоматизація
    from data_manager_final import DataManager
    from browser_manager import BrowserFactory
    REAL_AUTOMATION = True
except ImportError as e:
    print(f"Помилка імпорту реальної автоматизації: {e}")
    print("Використовується симуляція")
    REAL_AUTOMATION = False


class ModernStyle:
    """Сучасна темна тема оформлення"""
    
    COLORS = {
        'primary': '#6366f1',
        'primary_dark': '#4f46e5',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#3b82f6',
        'background': '#0f172a',
        'surface': '#1e293b',
        'card': '#334155',
        'border': '#475569',
        'text': '#f1f5f9',
        'text_secondary': '#94a3b8',
        'text_muted': '#64748b',
        'sidebar': '#1e293b',
        'sidebar_active': '#6366f1',
    }
    
    FONTS = {
        'title': ('Segoe UI', 18, 'bold'),
        'heading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'button': ('Segoe UI', 9, 'bold')
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
            padx=12,
            pady=6
        )
        
        self.bind('<Enter>', lambda e: self.configure(bg=self.hover_bg))
        self.bind('<Leave>', lambda e: self.configure(bg=self.default_bg))


class GlassCard(tk.Frame):
    """Скляна картка з оптимізованими розмірами"""
    
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
            title_frame.pack(fill='x', padx=15, pady=(10, 5))
            
            title_label = tk.Label(
                title_frame,
                text=title,
                font=ModernStyle.FONTS['heading'],
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['text']
            )
            title_label.pack(anchor='w')


class ActionDialog(tk.Toplevel):
    """Покращений діалог налаштування дії"""
    
    def __init__(self, parent, title, action_type=""):
        super().__init__(parent)
        self.result = None
        self.action_type = action_type
        
        self.title(title)
        self.geometry("350x250")
        self.configure(bg=ModernStyle.COLORS['background'])
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        # Центрування
        self.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення віджетів діалогу"""
        main_frame = tk.Frame(self, bg=ModernStyle.COLORS['background'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Налаштування в залежності від типу дії
        if self.action_type in ['like_posts', 'view_stories']:
            self.create_count_settings(main_frame)
        elif self.action_type == 'like_stories':
            self.create_like_stories_settings(main_frame)
        elif self.action_type == 'delay':
            self.create_delay_settings(main_frame)
        else:
            self.create_general_settings(main_frame)
        
        # Кнопки
        btn_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['background'])
        btn_frame.pack(fill='x', pady=(15, 0))
        
        AnimatedButton(
            btn_frame,
            text="Скасувати",
            command=self.cancel_clicked,
            bg=ModernStyle.COLORS['error']
        ).pack(side='left')
        
        AnimatedButton(
            btn_frame,
            text="OK",
            command=self.ok_clicked,
            bg=ModernStyle.COLORS['success']
        ).pack(side='right')
    
    def create_count_settings(self, parent):
        """Налаштування для дій з кількістю"""
        title = "лайків постів" if self.action_type == 'like_posts' else "переглядів сторіс"
        max_count = 5 if self.action_type == 'like_posts' else 10
        
        tk.Label(
            parent,
            text=f"Кількість {title}:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(0, 5))
        
        self.count_var = tk.IntVar(value=2 if self.action_type == 'like_posts' else 3)
        count_frame = tk.Frame(parent, bg=ModernStyle.COLORS['background'])
        count_frame.pack(fill='x', pady=5)
        
        count_spin = tk.Spinbox(
            count_frame,
            from_=1,
            to=max_count,
            width=10,
            textvariable=self.count_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        count_spin.pack(side='left')
        
        tk.Label(
            count_frame,
            text=f"(макс. {max_count})",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack(side='left', padx=(10, 0))
    
    def create_like_stories_settings(self, parent):
        """Налаштування для лайків сторіс"""
        tk.Label(
            parent,
            text="Кількість лайків сторіс:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(0, 5))
        
        self.count_var = tk.IntVar(value=2)
        count_frame = tk.Frame(parent, bg=ModernStyle.COLORS['background'])
        count_frame.pack(fill='x', pady=5)
        
        count_spin = tk.Spinbox(
            count_frame,
            from_=1,
            to=5,
            width=10,
            textvariable=self.count_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        count_spin.pack(side='left')
        
        tk.Label(
            count_frame,
            text="(макс. 5)",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack(side='left', padx=(10, 0))
        
        # Попередження
        warning_frame = tk.Frame(parent, bg=ModernStyle.COLORS['warning'], relief='solid', bd=1)
        warning_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(
            warning_frame,
            text="⚠️ Лайків сторіс не може бути більше\nніж переглядів сторіс в ланцюжку",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['warning'],
            fg='white',
            justify='center'
        ).pack(pady=8)
    
    def create_delay_settings(self, parent):
        """Налаштування затримки"""
        tk.Label(
            parent,
            text="Затримка (секунди):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w', pady=(0, 5))
        
        self.delay_var = tk.IntVar(value=30)
        delay_frame = tk.Frame(parent, bg=ModernStyle.COLORS['background'])
        delay_frame.pack(fill='x', pady=5)
        
        delay_spin = tk.Spinbox(
            delay_frame,
            from_=5,
            to=300,
            width=10,
            textvariable=self.delay_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        delay_spin.pack(side='left')
        
        tk.Label(
            delay_frame,
            text="(5-300 сек)",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack(side='left', padx=(10, 0))
    
    def create_general_settings(self, parent):
        """Загальні налаштування"""
        tk.Label(
            parent,
            text="Дія буде додана з стандартними\nналаштуваннями",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text'],
            justify='center'
        ).pack(expand=True)
    
    def ok_clicked(self):
        """Обробка натискання OK"""
        try:
            if self.action_type in ['like_posts', 'view_stories', 'like_stories']:
                count = self.count_var.get()
                self.result = {'count': count}
            elif self.action_type == 'delay':
                delay = self.delay_var.get()
                self.result = {'delay': delay}
            else:
                self.result = {}
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Помилка", f"Некоректні дані: {e}")
    
    def cancel_clicked(self):
        """Обробка скасування"""
        self.destroy()


class ChainBuilderWidget(tk.Frame):
    """Оптимізований віджет для створення ланцюжка дій"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['surface'])
        
        self.chain = []
        self.action_widgets = []
        
        # Спроба автозавантаження
        if not self.load_chain_from_data():
            print("Створено новий порожній ланцюжок")
        
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
        header.pack(pady=(10, 5))
        
        # Компактні кнопки дій
        actions_frame = tk.Frame(self, bg=ModernStyle.COLORS['surface'])
        actions_frame.pack(fill='x', padx=15, pady=5)
        
        tk.Label(
            actions_frame,
            text="Доступні дії:",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        buttons_frame = tk.Frame(actions_frame, bg=ModernStyle.COLORS['surface'])
        buttons_frame.pack(fill='x', pady=(5, 0))
        
        # Компактні кнопки дій
        action_buttons = [
            ("👤 Підписка", "follow", self.add_follow_action),
            ("❤️ Лайк постів", "like_posts", self.add_like_posts_action),
            ("📖 Перегляд сторіс", "view_stories", self.add_view_stories_action),
            ("💖 Лайк сторіс", "like_stories", self.add_like_stories_action),
            ("💬 Відповідь", "reply_stories", self.add_reply_stories_action),
            ("📩 DM", "send_dm", self.add_send_dm_action),
            ("🔄 Затримка", "delay", self.add_delay_action)
        ]
        
        for i, (text, action_type, command) in enumerate(action_buttons):
            btn = AnimatedButton(
                buttons_frame,
                text=text,
                command=command,
                bg=ModernStyle.COLORS['primary']
            )
            btn.grid(row=i//4, column=i%4, padx=3, pady=2, sticky='ew')
        
        # Налаштування сітки
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Поточний ланцюжок з оптимізованим розміром
        chain_card = GlassCard(self, title="Поточний ланцюжок")
        chain_card.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Скролюючий контейнер з обмеженою висотою
        chain_container = tk.Frame(chain_card, bg=ModernStyle.COLORS['card'])
        chain_container.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        self.canvas = tk.Canvas(
            chain_container,
            bg=ModernStyle.COLORS['background'],
            highlightthickness=0,
            height=200  # Обмежена висота
        )
        scrollbar = ttk.Scrollbar(chain_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=ModernStyle.COLORS['background'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Компактні кнопки управління
        control_frame = tk.Frame(chain_card, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        AnimatedButton(
            control_frame,
            text="💾 Зберегти",
            command=self.save_chain,
            bg=ModernStyle.COLORS['success']
        ).pack(side='left', padx=(0, 5))
        
        AnimatedButton(
            control_frame,
            text="📂 Завантажити",
            command=self.load_chain,
            bg=ModernStyle.COLORS['info']
        ).pack(side='left', padx=(0, 5))
        
        AnimatedButton(
            control_frame,
            text="🗑️ Очистити",
            command=self.clear_chain,
            bg=ModernStyle.COLORS['error']
        ).pack(side='right')
    
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
        dialog = ActionDialog(self, "❤️ Налаштування лайку постів", "like_posts")
        self.wait_window(dialog)
        
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
        dialog = ActionDialog(self, "📖 Налаштування перегляду сторіс", "view_stories")
        self.wait_window(dialog)
        
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
        """Додавання дії лайку сторіс з перевіркою"""
        # Перевірка кількості переглядів сторіс в ланцюжку
        view_stories_count = 0
        for action in self.chain:
            if action.get('type') == 'view_stories' and action.get('enabled', True):
                view_stories_count = max(view_stories_count, action.get('settings', {}).get('count', 0))
        
        if view_stories_count == 0:
            messagebox.showwarning(
                "Попередження", 
                "Спочатку додайте 'Перегляд сторіс' в ланцюжок.\nЛайків сторіс не може бути більше ніж переглядів."
            )
            return
        
        dialog = ActionDialog(self, "💖 Налаштування лайку сторіс", "like_stories")
        self.wait_window(dialog)
        
        if dialog.result:
            count = dialog.result.get('count', 2)
            
            # Перевірка ліміту
            if count > view_stories_count:
                messagebox.showwarning(
                    "Попередження", 
                    f"Кількість лайків сторіс ({count}) не може перевищувати\nкількість переглядів сторіс ({view_stories_count})"
                )
                return
            
            self.add_action({
                'type': 'like_stories',
                'name': f'Лайк {count} сторіс',
                'icon': '💖',
                'settings': {'count': count},
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
        dialog = ActionDialog(self, "🔄 Налаштування затримки", "delay")
        self.wait_window(dialog)
        
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
        print(f"Додано дію: {action.get('name', action.get('type'))}")
        print(f"Загальна кількість дій в ланцюжку: {len(self.chain)}")
        self.update_chain_display()
        
        # Автоматичне збереження
        self.save_chain_to_data()
    
    def update_chain_display(self):
        """Оновлення відображення ланцюжка"""
        # Очищення
        for widget in self.action_widgets:
            widget.destroy()
        self.action_widgets.clear()
        
        # Створення компактних віджетів для кожної дії
        for i, action in enumerate(self.chain):
            self.create_compact_action_widget(i, action)
    
    def create_compact_action_widget(self, index, action):
        """Створення компактного віджета дії"""
        frame = tk.Frame(self.scrollable_frame, bg=ModernStyle.COLORS['card'], relief='solid', bd=1)
        frame.pack(fill='x', padx=3, pady=2)
        self.action_widgets.append(frame)
        
        # Основний контейнер
        main_container = tk.Frame(frame, bg=ModernStyle.COLORS['card'])
        main_container.pack(fill='x', padx=8, pady=6)
        
        # Номер кроку
        step_label = tk.Label(
            main_container,
            text=f"{index + 1}.",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text_secondary'],
            width=3
        )
        step_label.pack(side='left')
        
        # Іконка та назва
        info_frame = tk.Frame(main_container, bg=ModernStyle.COLORS['card'])
        info_frame.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        tk.Label(
            info_frame,
            text=f"{action['icon']} {action['name']}",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(anchor='w')
        
        # Кнопки управління
        btn_frame = tk.Frame(main_container, bg=ModernStyle.COLORS['card'])
        btn_frame.pack(side='right')
        
        # Перемикач увімкнення
        enabled_var = tk.BooleanVar(value=action.get('enabled', True))
        enabled_check = tk.Checkbutton(
            btn_frame,
            variable=enabled_var,
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=lambda idx=index, var=enabled_var: self.toggle_action(idx, var.get())
        )
        enabled_check.pack(side='right', padx=2)
        
        # Кнопка видалення
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️",
            command=lambda idx=index: self.remove_action(idx),
            bg=ModernStyle.COLORS['error'],
            fg='white',
            relief='flat',
            font=('Arial', 8),
            width=3,
            height=1
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
                width=2,
                height=1
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
                width=2,
                height=1
            )
            down_btn.pack(side='right', padx=1)
    
    def toggle_action(self, index, enabled):
        """Перемикання стану дії"""
        if 0 <= index < len(self.chain):
            self.chain[index]['enabled'] = enabled
            action_name = self.chain[index].get('name', self.chain[index].get('type'))
            status = "увімкнено" if enabled else "вимкнено"
            print(f"Дію '{action_name}' {status}")
            self.save_chain_to_data()
    
    def remove_action(self, index):
        """Видалення дії"""
        if 0 <= index < len(self.chain):
            removed = self.chain.pop(index)
            print(f"Видалено дію: {removed.get('name', removed.get('type'))}")
            self.update_chain_display()
            self.save_chain_to_data()
    
    def move_action(self, index, direction):
        """Переміщення дії"""
        new_index = index + direction
        if 0 <= new_index < len(self.chain):
            self.chain[index], self.chain[new_index] = self.chain[new_index], self.chain[index]
            self.update_chain_display()
    
    def save_chain_to_data(self):
        """Автоматичне збереження ланцюжка в data/action_chain.json"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/action_chain.json', 'w', encoding='utf-8') as f:
                json.dump(self.chain, f, indent=2, ensure_ascii=False)
            print(f"Автоматично збережено ланцюжок з {len(self.chain)} дій")
        except Exception as e:
            print(f"Помилка автозбереження ланцюжка: {e}")
    
    def load_chain_from_data(self):
        """Автоматичне завантаження ланцюжка з data/action_chain.json"""
        try:
            if os.path.exists('data/action_chain.json'):
                with open('data/action_chain.json', 'r', encoding='utf-8') as f:
                    self.chain = json.load(f)
                print(f"Автоматично завантажено ланцюжок з {len(self.chain)} дій")
                self.update_chain_display()
                return True
        except Exception as e:
            print(f"Помилка автозавантаження ланцюжка: {e}")
        return False
    
    def clear_chain(self):
        """Очищення ланцюжка"""
        if messagebox.askyesno("Підтвердження", "Очистити весь ланцюжок?"):
            self.chain.clear()
            self.update_chain_display()
            self.save_chain_to_data()
            print("Ланцюжок очищено")
    
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
        """Отримання поточного ланцюжка - тільки увімкнені дії"""
        enabled_actions = [action for action in self.chain if action.get('enabled', True)]
        print(f"ChainBuilder: повертаю {len(enabled_actions)} увімкнених дій з {len(self.chain)} загальних")
        
        if enabled_actions:
            for i, action in enumerate(enabled_actions):
                print(f"  Увімкнена дія {i+1}: {action.get('name', action.get('type'))}")
        
        return enabled_actions


class WorkerConfigWidget(tk.Frame):
    """Віджет конфігурації воркера з вибором акаунту"""
    
    def __init__(self, parent, worker_id, accounts, targets, chain, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=ModernStyle.COLORS['card'], relief='solid', bd=1)
        
        self.worker_id = worker_id
        self.accounts = accounts
        self.targets = targets
        self.chain = chain
        
        self.selected_account = None
        self.selected_targets = []
        self.enabled = True
        
        self.create_widgets()
    
    def create_widgets(self):
        """Створення віджетів конфігурації воркера"""
        # Заголовок воркера
        header_frame = tk.Frame(self, bg=ModernStyle.COLORS['card'])
        header_frame.pack(fill='x', padx=10, pady=(8, 5))
        
        # Перемикач увімкнення воркера
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = tk.Checkbutton(
            header_frame,
            variable=self.enabled_var,
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text'],
            selectcolor=ModernStyle.COLORS['surface'],
            command=self.on_enabled_change
        )
        enabled_check.pack(side='left')
        
        tk.Label(
            header_frame,
            text=f"Воркер #{self.worker_id + 1}",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).pack(side='left', padx=(5, 0))
        
        # Статус
        self.status_label = tk.Label(
            header_frame,
            text="Налаштування",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_label.pack(side='right')
        
        # Контейнер налаштувань
        self.config_frame = tk.Frame(self, bg=ModernStyle.COLORS['card'])
        self.config_frame.pack(fill='x', padx=10, pady=(0, 8))
        
        # Вибір акаунту
        tk.Label(
            self.config_frame,
            text="Акаунт:",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=0, sticky='w', pady=2)
        
        self.account_var = tk.StringVar()
        account_combo = ttk.Combobox(
            self.config_frame,
            textvariable=self.account_var,
            values=[acc['username'] for acc in self.accounts],
            state="readonly",
            width=15
        )
        account_combo.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=2)
        account_combo.bind('<<ComboboxSelected>>', self.on_account_change)
        
        # Автовибір акаунту
        if self.worker_id < len(self.accounts):
            account_combo.set(self.accounts[self.worker_id]['username'])
            self.selected_account = self.accounts[self.worker_id]
        
        # Кількість цілей
        tk.Label(
            self.config_frame,
            text="Цілі (макс):",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=1, column=0, sticky='w', pady=2)
        
        self.targets_count_var = tk.IntVar(value=min(10, len(self.targets)))
        targets_spin = tk.Spinbox(
            self.config_frame,
            from_=1,
            to=len(self.targets) if self.targets else 1,
            width=8,
            textvariable=self.targets_count_var,
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text']
        )
        targets_spin.grid(row=1, column=1, sticky='w', padx=(5, 0), pady=2)
        
        # Налаштування сітки
        self.config_frame.grid_columnconfigure(1, weight=1)
    
    def on_enabled_change(self):
        """Обробка зміни стану увімкнення"""
        self.enabled = self.enabled_var.get()
        
        # Увімкнення/вимкнення налаштувань
        state = 'normal' if self.enabled else 'disabled'
        for widget in self.config_frame.winfo_children():
            if isinstance(widget, (ttk.Combobox, tk.Spinbox)):
                widget.configure(state=state)
        
        # Оновлення статусу
        if self.enabled:
            self.status_label.configure(text="Готовий", fg=ModernStyle.COLORS['success'])
        else:
            self.status_label.configure(text="Вимкнено", fg=ModernStyle.COLORS['text_secondary'])
    
    def on_account_change(self, event=None):
        """Обробка зміни акаунту"""
        username = self.account_var.get()
        self.selected_account = next((acc for acc in self.accounts if acc['username'] == username), None)
    
    def get_config(self):
        """Отримання конфігурації воркера"""
        if not self.enabled:
            return None
        
        targets_count = self.targets_count_var.get()
        selected_targets = self.targets[:targets_count] if self.targets else []
        
        return {
            'worker_id': self.worker_id,
            'enabled': self.enabled,
            'account': self.selected_account,
            'targets': selected_targets,
            'chain': self.chain,
            'targets_count': targets_count
        }


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
        main_frame.pack(fill='x', padx=8, pady=4)
        
        # Ліва частина: статус
        left_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['surface'])
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Статус індикатор та назва
        status_frame = tk.Frame(left_frame, bg=ModernStyle.COLORS['surface'])
        status_frame.pack(fill='x')
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=('Arial', 10),
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
            font=('Arial', 8),
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_secondary']
        )
        self.status_label.pack(side='right')
        
        # Права частина: компактна статистика
        right_frame = tk.Frame(main_frame, bg=ModernStyle.COLORS['surface'])
        right_frame.pack(side='right')
        
        # Статистика в одному рядку
        self.stats_label = tk.Label(
            right_frame,
            text="Цілі: 0 | Дії: 0 | Успішно: 0",
            font=('Arial', 7),
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text_muted']
        )
        self.stats_label.pack()
    
    def update_status(self, status, current_target=None, account=None):
        """Оновлення статусу воркера"""
        self.status = status
        
        status_colors = {
            'idle': ModernStyle.COLORS['text_secondary'],
            'working': ModernStyle.COLORS['success'],
            'error': ModernStyle.COLORS['error'],
            'paused': ModernStyle.COLORS['warning'],
            'disabled': ModernStyle.COLORS['text_muted']
        }
        
        status_texts = {
            'idle': 'Очікування',
            'working': f'{current_target}' if current_target else 'Активний',
            'error': 'Помилка',
            'paused': 'Пауза',
            'disabled': 'Вимкнено'
        }
        
        self.status_dot.configure(fg=status_colors.get(status, status_colors['idle']))
        self.status_label.configure(text=status_texts.get(status, 'Невідомо'))
    
    def update_stats(self, stats):
        """Оновлення статистики воркера"""
        targets = stats.get('processed_targets', 0)
        total = stats.get('total_actions', 0) 
        successful = stats.get('successful_actions', 0)
        
        stats_text = f"Цілі: {targets} | Дії: {total} | Успішно: {successful}"
        self.stats_label.configure(text=stats_text)


class InstagramBotGUI:
    """Головний клас GUI з оптимізованими розмірами"""
    
    def __init__(self, root):
        self.root = root
        self.data_manager = DataManager()
        self.automation_manager = None
        self.worker_widgets = []
        self.worker_configs = []
        
        self.setup_window()
        self.create_widgets()
        self.load_all_data()
    
    def setup_window(self):
        """Налаштування головного вікна з оптимізованими розмірами"""
        self.root.title("Instagram Bot Pro v3.0 - Професійна автоматизація")
        self.root.geometry("1400x800")  # Зменшений розмір
        self.root.configure(bg=ModernStyle.COLORS['background'])
        self.root.minsize(1200, 700)  # Мінімальний розмір
        
        # Центрування вікна
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1400x800+{x}+{y}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Створення віджетів інтерфейсу"""
        # Головний контейнер
        main_container = tk.Frame(self.root, bg=ModernStyle.COLORS['background'])
        main_container.pack(fill='both', expand=True)
        
        # Компактна бічна панель
        sidebar = tk.Frame(main_container, bg=ModernStyle.COLORS['sidebar'], width=250)  # Зменшена ширина
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Компактний логотип
        logo_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        logo_frame.pack(fill='x', pady=15)
        
        tk.Label(
            logo_frame,
            text="🤖 Instagram Bot Pro",
            font=ModernStyle.FONTS['heading'],  # Зменшений шрифт
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
        
        # Компактна навігація
        nav_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        nav_frame.pack(fill='x', padx=8, pady=15)
        
        self.nav_buttons = {}
        nav_items = [
            ("🏠", "Головна", "main"),
            ("👥", "Акаунти", "accounts"),
            ("🎯", "Цілі", "targets"),
            ("🔗", "Ланцюжок", "chain"),
            ("📝", "Тексти", "texts"),
            ("🌐", "Браузер", "browser"),
            ("▶️", "Запуск", "run")
        ]
        
        for icon, text, page in nav_items:
            btn = tk.Button(
                nav_frame,
                text=f"  {icon}  {text}",
                command=lambda p=page: self.show_page(p),
                font=ModernStyle.FONTS['small'],  # Зменшений шрифт
                bg=ModernStyle.COLORS['sidebar'],
                fg=ModernStyle.COLORS['text'],
                relief='flat',
                anchor='w',
                padx=12,
                pady=6,  # Зменшений відступ
                cursor='hand2'
            )
            btn.pack(fill='x', pady=1)
            
            # Hover ефекти
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=ModernStyle.COLORS['sidebar_active']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=ModernStyle.COLORS['sidebar']) if not getattr(b, 'active', False) else None)
            
            self.nav_buttons[page] = btn
        
        # Компактний статус системи
        status_frame = tk.Frame(sidebar, bg=ModernStyle.COLORS['sidebar'])
        status_frame.pack(side='bottom', fill='x', padx=15, pady=15)
        
        tk.Label(
            status_frame,
            text="Статус:",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['sidebar'],
            fg=ModernStyle.COLORS['text_secondary']
        ).pack(anchor='w')
        
        self.status_label = tk.Label(
            status_frame,
            text="● Готовий",
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
        
        # Сторінка акаунтів (використаємо спрощену версію)
        self.pages["accounts"] = self.create_accounts_page()
        
        # Сторінка цілей (використаємо спрощену версію)
        self.pages["targets"] = self.create_targets_page()
        
        # Сторінка ланцюжка дій
        self.pages["chain"] = ChainBuilderWidget(self.content_area)
        
        # Сторінка текстів (використаємо спрощену версію)
        self.pages["texts"] = self.create_texts_page()
        
        # Сторінка браузера (використаємо спрощену версію)
        self.pages["browser"] = self.create_browser_page()
        
        # Сторінка запуску
        self.pages["run"] = self.create_run_page()
    
    def create_main_page(self):
        """Створення компактної головної сторінки"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        # Компактний заголовок
        header = tk.Label(
            page,
            text="🏠 Панель управління",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=15)
        
        # Компактні статистичні картки
        stats_frame = tk.Frame(page, bg=ModernStyle.COLORS['background'])
        stats_frame.pack(fill='x', padx=15, pady=10)
        
        # Картки статистики в сітці 2x2
        cards_data = [
            ("👥", "Акаунтів", "0", "accounts_count"),
            ("🎯", "Цілей", "0", "targets_count"),
            ("🔗", "Дій", "0", "chain_count"),
            ("📝", "Текстів", "0", "texts_count")
        ]
        
        self.stat_labels = {}
        
        for i, (icon, title, value, key) in enumerate(cards_data):
            row, col = i // 2, i % 2
            
            card = GlassCard(stats_frame)
            card.grid(row=row, column=col, padx=8, pady=5, sticky='ew')
            
            content = tk.Frame(card, bg=ModernStyle.COLORS['card'])
            content.pack(fill='both', expand=True, padx=15, pady=10)
            
            tk.Label(
                content,
                text=icon,
                font=('Arial', 24),  # Зменшений розмір іконки
                bg=ModernStyle.COLORS['card'],
                fg=ModernStyle.COLORS['primary']
            ).pack()
            
            value_label = tk.Label(
                content,
                text=value,
                font=ModernStyle.FONTS['heading'],
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
        
        # Компактні швидкі дії
        actions_frame = GlassCard(page, title="Швидкі дії")
        actions_frame.pack(fill='x', padx=15, pady=15)
        
        actions_content = tk.Frame(actions_frame, bg=ModernStyle.COLORS['card'])
        actions_content.pack(fill='x', padx=15, pady=(0, 15))
        
        buttons = [
            ("➕ Додати акаунт", lambda: self.show_page("accounts"), ModernStyle.COLORS['success']),
            ("🎯 Додати ціль", lambda: self.show_page("targets"), ModernStyle.COLORS['primary']),
            ("🔗 Налаштувати дії", lambda: self.show_page("chain"), ModernStyle.COLORS['warning']),
            ("▶️ Запустити бота", lambda: self.show_page("run"), ModernStyle.COLORS['success'])
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            row, col = i // 2, i % 2
            AnimatedButton(
                actions_content,
                text=text,
                command=command,
                bg=color
            ).grid(row=row, column=col, padx=5, pady=3, sticky='ew')
        
        actions_content.grid_columnconfigure(0, weight=1)
        actions_content.grid_columnconfigure(1, weight=1)
        
        return page
    
    def create_run_page(self):
        """Створення оптимізованої сторінки запуску з розподілом воркерів"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        # Заголовок
        header = tk.Label(
            page,
            text="▶️ Запуск автоматизації",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=(10, 15))
        
        # Скролюючий контейнер
        canvas = tk.Canvas(page, bg=ModernStyle.COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernStyle.COLORS['background'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(15, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 15))
        
        # Швидкі налаштування
        settings_card = GlassCard(scrollable_frame, title="Налаштування запуску")
        settings_card.pack(fill='x', padx=15, pady=(0, 10))
        
        settings_content = tk.Frame(settings_card, bg=ModernStyle.COLORS['card'])
        settings_content.pack(fill='x', padx=15, pady=(0, 10))
        
        # Сітка налаштувань
        settings_grid = tk.Frame(settings_content, bg=ModernStyle.COLORS['card'])
        settings_grid.pack(fill='x', pady=5)
        
        # Кількість воркерів
        tk.Label(
            settings_grid,
            text="Воркери:",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=3)
        
        self.workers_var = tk.IntVar(value=3)
        workers_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=10,
            width=8,
            textvariable=self.workers_var,
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['surface'],
            fg=ModernStyle.COLORS['text'],
            command=self.update_worker_configs
        )
        workers_spin.grid(row=0, column=1, sticky='w', padx=(0, 20), pady=3)
        
        # Затримка між акаунтами
        tk.Label(
            settings_grid,
            text="Затримка (хв):",
            font=ModernStyle.FONTS['body'],
            bg=ModernStyle.COLORS['card'],
            fg=ModernStyle.COLORS['text']
        ).grid(row=0, column=2, sticky='w', padx=(0, 10), pady=3)
        
        self.delay_var = tk.IntVar(value=5)
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
        delay_spin.grid(row=0, column=3, sticky='w', pady=3)
        
        # Режим роботи  
        mode_frame = tk.Frame(settings_grid, bg=ModernStyle.COLORS['card'])
        mode_frame.grid(row=1, column=1, columnspan=2, sticky='w', pady=3)
        
        self.mode_var = tk.StringVar(value="continuous")
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["continuous", "single_round"],
            state="readonly",
            width=15
        )
        mode_combo.pack(side='left')
        
        # Індикатор режиму автоматизації
        mode_indicator = tk.Label(
            mode_frame,
            text="🎭 СИМУЛЯЦІЯ" if not REAL_AUTOMATION else "🤖 РЕАЛЬНА РОБОТА",
            font=ModernStyle.FONTS['small'],
            bg=ModernStyle.COLORS['warning'] if not REAL_AUTOMATION else ModernStyle.COLORS['success'],
            fg='white',
            padx=8,
            pady=2
        )
        mode_indicator.pack(side='left', padx=(10, 0))
        
        # Кнопка оновлення конфігурації
        AnimatedButton(
            settings_grid,
            text="🔄 Оновити конфігурацію",
            command=self.update_worker_configs,
            bg=ModernStyle.COLORS['info']
        ).grid(row=1, column=3, sticky='w', padx=(10, 0), pady=3)
        
        # Кнопки управління
        control_card = GlassCard(scrollable_frame, title="Управління")
        control_card.pack(fill='x', padx=15, pady=(0, 10))
        
        control_content = tk.Frame(control_card, bg=ModernStyle.COLORS['card'])
        control_content.pack(fill='x', padx=15, pady=(0, 10))
        
        buttons_frame = tk.Frame(control_content, bg=ModernStyle.COLORS['card'])
        buttons_frame.pack(fill='x')
        
        self.start_btn = AnimatedButton(
            buttons_frame,
            text="▶️ Запустити",
            command=self.start_automation,
            bg=ModernStyle.COLORS['success']
        )
        self.start_btn.pack(side='left', padx=(0, 8))
        
        self.stop_btn = AnimatedButton(
            buttons_frame,
            text="⏹️ Зупинити",
            command=self.stop_automation,
            bg=ModernStyle.COLORS['error'],
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 8))
        
        self.pause_btn = AnimatedButton(
            buttons_frame,
            text="⏸️ Пауза",
            command=self.pause_automation,
            bg=ModernStyle.COLORS['warning'],
            state='disabled'
        )
        self.pause_btn.pack(side='left')
        
        # Конфігурація воркерів
        workers_card = GlassCard(scrollable_frame, title="Конфігурація воркерів")
        workers_card.pack(fill='x', padx=15, pady=(0, 10))
        
        # Контейнер для конфігурацій воркерів
        self.workers_config_container = tk.Frame(workers_card, bg=ModernStyle.COLORS['card'])
        self.workers_config_container.pack(fill='x', padx=15, pady=(0, 10))
        
        # Статус воркерів
        status_card = GlassCard(scrollable_frame, title="Статус воркерів")
        status_card.pack(fill='x', padx=15, pady=(0, 15))
        
        # Контейнер для статусу воркерів
        status_container = tk.Frame(status_card, bg=ModernStyle.COLORS['card'], height=200)
        status_container.pack(fill='x', padx=15, pady=(0, 10))
        status_container.pack_propagate(False)
        
        status_canvas = tk.Canvas(
            status_container,
            bg=ModernStyle.COLORS['card'],
            highlightthickness=0,
            height=180
        )
        status_scrollbar = ttk.Scrollbar(status_container, orient="vertical", command=status_canvas.yview)
        self.workers_status_container = tk.Frame(status_canvas, bg=ModernStyle.COLORS['card'])
        
        self.workers_status_container.bind(
            "<Configure>",
            lambda e: status_canvas.configure(scrollregion=status_canvas.bbox("all"))
        )
        
        status_canvas.create_window((0, 0), window=self.workers_status_container, anchor="nw")
        status_canvas.configure(yscrollcommand=status_scrollbar.set)
        
        status_canvas.pack(side="left", fill="both", expand=True)
        status_scrollbar.pack(side="right", fill="y")
        
        # Ініціалізація конфігурації воркерів
        self.update_worker_configs()
        
        # Прокрутка колесом миші
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(page)
        
        return page
    
    def update_worker_configs(self):
        """Оновлення конфігурації воркерів"""
        try:
            # Отримання даних
            accounts = self.get_accounts_data()
            targets = self.get_targets_data()
            chain = self.get_chain_data()
            workers_count = self.workers_var.get()
            
            print(f"Оновлення воркерів: {len(accounts)} акаунтів, {workers_count} воркерів")  # Для відлагодження
            
            # Очищення існуючих конфігурацій
            for widget in self.worker_configs:
                widget.destroy()
            self.worker_configs.clear()
            
            # Очищення статусних віджетів
            for widget in self.worker_widgets:
                widget.destroy()
            self.worker_widgets.clear()
            
            # Створення нових конфігурацій воркерів
            for i in range(workers_count):
                # Конфігурація воркера
                worker_config = WorkerConfigWidget(
                    self.workers_config_container, 
                    i, 
                    accounts, 
                    targets, 
                    chain
                )
                worker_config.pack(fill='x', pady=3)
                self.worker_configs.append(worker_config)
                
                # Статус воркера
                worker_status = CompactWorkerStatusWidget(self.workers_status_container, i)
                worker_status.pack(fill='x', pady=2)
                self.worker_widgets.append(worker_status)
            
            # Повідомлення якщо немає достатньо акаунтів
            if len(accounts) < workers_count:
                messagebox.showwarning(
                    "Попередження",
                    f"Кількість акаунтів ({len(accounts)}) менша за кількість воркерів ({workers_count}).\n"
                    f"Деякі воркери будуть вимкнені."
                )
        
        except Exception as e:
            print(f"Помилка оновлення конфігурації: {e}")  # Для відлагодження
            messagebox.showerror("Помилка", f"Помилка оновлення конфігурації: {e}")
    
    def get_accounts_data(self):
        """Отримання даних акаунтів"""
        try:
            # Спробуємо отримати з головного об'єкта
            if hasattr(self, 'accounts') and self.accounts:
                print(f"Отримано {len(self.accounts)} акаунтів з головного об'єкта")
                return self.accounts
            
            # Якщо немає, спробуємо з сторінки
            if hasattr(self.pages.get("accounts"), 'accounts'):
                accounts = self.pages["accounts"].accounts
                print(f"Отримано {len(accounts)} акаунтів зі сторінки")
                return accounts
            
            # Якщо і це не працює, завантажимо напряму
            if os.path.exists('data/accounts.json'):
                with open('data/accounts.json', 'r', encoding='utf-8') as f:
                    accounts = json.load(f)
                    print(f"Завантажено {len(accounts)} акаунтів з файлу")
                    return accounts
            
            print("Акаунти не знайдено")
            return []
        except Exception as e:
            print(f"Помилка отримання акаунтів: {e}")
            return []
    
    def get_targets_data(self):
        """Отримання даних цілей"""
        try:
            # Спробуємо отримати з головного об'єкта
            if hasattr(self, 'targets') and self.targets:
                print(f"Отримано {len(self.targets)} цілей з головного об'єкта")
                return self.targets
            
            # Якщо немає, спробуємо з сторінки
            if hasattr(self.pages.get("targets"), 'targets'):
                targets = self.pages["targets"].targets
                print(f"Отримано {len(targets)} цілей зі сторінки")
                return targets
            
            # Якщо і це не працює, завантажимо напряму
            if os.path.exists('data/targets.json'):
                with open('data/targets.json', 'r', encoding='utf-8') as f:
                    targets = json.load(f)
                    print(f"Завантажено {len(targets)} цілей з файлу")
                    return targets
            
            print("Цілі не знайдено")
            return []
        except Exception as e:
            print(f"Помилка отримання цілей: {e}")
            return []
    
    def get_chain_data(self):
        """Отримання даних ланцюжка"""
        try:
            # Спробуємо отримати з сторінки ланцюжка
            if hasattr(self.pages.get("chain"), 'get_chain'):
                chain = self.pages["chain"].get_chain()
                print(f"Отримано ланцюжок з {len(chain)} дій зі сторінки")
                if chain:
                    for i, action in enumerate(chain):
                        print(f"  Дія {i+1}: {action.get('name', action.get('type'))}")
                return chain
            
            # Якщо не знайшли, спробуємо напряму з об'єкта
            if hasattr(self.pages.get("chain"), 'chain'):
                chain = self.pages["chain"].chain
                enabled_chain = [action for action in chain if action.get('enabled', True)]
                print(f"Отримано ланцюжок з {len(enabled_chain)} увімкнених дій з об'єкта")
                return enabled_chain
            
            # Спробуємо завантажити з файлу
            if os.path.exists('data/action_chain.json'):
                with open('data/action_chain.json', 'r', encoding='utf-8') as f:
                    chain = json.load(f)
                    enabled_chain = [action for action in chain if action.get('enabled', True)]
                    print(f"Завантажено ланцюжок з {len(enabled_chain)} дій з файлу")
                    return enabled_chain
            
            print("❌ Ланцюжок дій не знайдено")
            return []
        except Exception as e:
            print(f"❌ Помилка отримання ланцюжка: {e}")
            return []
    
    def create_accounts_page(self):
        """Створення спрощеної сторінки акаунтів"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        header = tk.Label(
            page,
            text="👥 Управління акаунтами",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Форма додавання
        add_card = GlassCard(page, title="Додати акаунт")
        add_card.pack(fill='x', padx=15, pady=10)
        
        form_frame = tk.Frame(add_card, bg=ModernStyle.COLORS['card'])
        form_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        # Поля введення в сітці
        fields_frame = tk.Frame(form_frame, bg=ModernStyle.COLORS['card'])
        fields_frame.pack(fill='x', pady=5)
        
        tk.Label(fields_frame, text="Логін:", **self.label_style()).grid(row=0, column=0, sticky='w')
        self.username_var = tk.StringVar()
        tk.Entry(fields_frame, textvariable=self.username_var, **self.entry_style()).grid(row=0, column=1, sticky='ew', padx=5)
        
        tk.Label(fields_frame, text="Пароль:", **self.label_style()).grid(row=0, column=2, sticky='w', padx=(10, 0))
        self.password_var = tk.StringVar()
        tk.Entry(fields_frame, textvariable=self.password_var, show='*', **self.entry_style()).grid(row=0, column=3, sticky='ew', padx=5)
        
        tk.Label(fields_frame, text="Проксі:", **self.label_style()).grid(row=1, column=0, sticky='w')
        self.proxy_var = tk.StringVar()
        tk.Entry(fields_frame, textvariable=self.proxy_var, **self.entry_style()).grid(row=1, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        
        fields_frame.grid_columnconfigure(1, weight=1)
        fields_frame.grid_columnconfigure(3, weight=1)
        
        AnimatedButton(
            form_frame,
            text="➕ Додати акаунт",
            command=self.add_account,
            bg=ModernStyle.COLORS['success']
        ).pack(pady=10)
        
        # Список акаунтів
        list_card = GlassCard(page, title="Збережені акаунти")
        list_card.pack(fill='both', expand=True, padx=15, pady=10)
        
        list_frame = tk.Frame(list_card, bg=ModernStyle.COLORS['card'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Treeview для акаунтів
        columns = ('Логін', 'Проксі', 'Статус')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=120)
        
        # Стилізація Treeview
        style = ttk.Style()
        style.configure("Treeview", 
                       background=ModernStyle.COLORS['background'],
                       foreground=ModernStyle.COLORS['text'],
                       fieldbackground=ModernStyle.COLORS['background'])
        style.configure("Treeview.Heading", 
                       background=ModernStyle.COLORS['card'],
                       foreground=ModernStyle.COLORS['text'])
        
        scrollbar_acc = ttk.Scrollbar(list_frame, orient="vertical", command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar_acc.set)
        
        self.accounts_tree.pack(side='left', fill='both', expand=True)
        scrollbar_acc.pack(side='right', fill='y')
        
        # Кнопки управління
        control_frame = tk.Frame(list_card, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        AnimatedButton(control_frame, text="🗑️ Видалити", command=self.remove_account, bg=ModernStyle.COLORS['error']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="📁 Імпорт", command=self.import_accounts, bg=ModernStyle.COLORS['info']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="🧹 Очистити все", command=self.clear_all_accounts, bg=ModernStyle.COLORS['error']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="💾 Експорт", command=self.export_accounts, bg=ModernStyle.COLORS['info']).pack(side='right', padx=5)
        
        # Ініціалізація даних
        self.accounts = []
        self.load_accounts()  # Завантаження відразу після створення віджетів
        
        return page
    
    def create_targets_page(self):
        """Створення спрощеної сторінки цілей"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        header = tk.Label(
            page,
            text="🎯 Управління цілями",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Форма додавання
        add_card = GlassCard(page, title="Додати цілі")
        add_card.pack(fill='x', padx=15, pady=10)
        
        form_frame = tk.Frame(add_card, bg=ModernStyle.COLORS['card'])
        form_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        # Одна ціль
        tk.Label(form_frame, text="Username:", **self.label_style()).pack(anchor='w')
        self.target_var = tk.StringVar()
        target_entry = tk.Entry(form_frame, textvariable=self.target_var, **self.entry_style())
        target_entry.pack(fill='x', pady=5)
        target_entry.bind('<Return>', lambda e: self.add_target())
        
        # Масове додавання
        tk.Label(form_frame, text="Кілька цілей (по одній на рядок):", **self.label_style()).pack(anchor='w', pady=(10, 0))
        self.bulk_text = scrolledtext.ScrolledText(form_frame, height=4, **self.text_style())
        self.bulk_text.pack(fill='x', pady=5)
        
        buttons_frame = tk.Frame(form_frame, bg=ModernStyle.COLORS['card'])
        buttons_frame.pack(fill='x', pady=10)
        
        AnimatedButton(buttons_frame, text="➕ Додати", command=self.add_target, bg=ModernStyle.COLORS['success']).pack(side='left', padx=5)
        AnimatedButton(buttons_frame, text="📝 Додати всі", command=self.add_bulk_targets, bg=ModernStyle.COLORS['primary']).pack(side='left', padx=5)
        
        # Список цілей
        list_card = GlassCard(page, title="Збережені цілі")
        list_card.pack(fill='both', expand=True, padx=15, pady=10)
        
        list_frame = tk.Frame(list_card, bg=ModernStyle.COLORS['card'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        self.targets_listbox = tk.Listbox(list_frame, **self.listbox_style())
        targets_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.targets_listbox.yview)
        self.targets_listbox.configure(yscrollcommand=targets_scrollbar.set)
        
        self.targets_listbox.pack(side='left', fill='both', expand=True)
        targets_scrollbar.pack(side='right', fill='y')
        
        # Кнопки управління
        control_frame = tk.Frame(list_card, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        AnimatedButton(control_frame, text="🗑️ Видалити", command=self.remove_target, bg=ModernStyle.COLORS['error']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="📁 Імпорт", command=self.import_targets, bg=ModernStyle.COLORS['info']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="🧹 Очистити все", command=self.clear_all_targets, bg=ModernStyle.COLORS['error']).pack(side='left', padx=5)
        AnimatedButton(control_frame, text="💾 Експорт", command=self.export_targets, bg=ModernStyle.COLORS['info']).pack(side='right', padx=5)
        
        # Ініціалізація даних
        self.targets = []
        self.load_targets()  # Завантаження відразу після створення віджетів
        
        return page
    
    def create_texts_page(self):
        """Створення спрощеної сторінки текстів"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        header = tk.Label(
            page,
            text="📝 Управління текстами",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Notebook для вкладок
        notebook = ttk.Notebook(page)
        notebook.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Вкладка сторіс
        stories_frame = tk.Frame(notebook, bg=ModernStyle.COLORS['card'])
        notebook.add(stories_frame, text="Відповіді на сторіс")
        
        # Вкладка DM
        dm_frame = tk.Frame(notebook, bg=ModernStyle.COLORS['card'])
        notebook.add(dm_frame, text="Приватні повідомлення")
        
        # Створення вмісту вкладок
        self.create_texts_tab(stories_frame, 'story_replies')
        self.create_texts_tab(dm_frame, 'direct_messages')
        
        # Ініціалізація даних
        self.texts = {'story_replies': [], 'direct_messages': []}
        self.load_texts()
        
        return page
    
    def create_browser_page(self):
        """Створення спрощеної сторінки браузера"""
        page = tk.Frame(self.content_area, bg=ModernStyle.COLORS['background'])
        
        header = tk.Label(
            page,
            text="🌐 Налаштування браузера",
            font=ModernStyle.FONTS['heading'],
            bg=ModernStyle.COLORS['background'],
            fg=ModernStyle.COLORS['text']
        )
        header.pack(pady=10)
        
        # Вибір браузера
        browser_card = GlassCard(page, title="Тип браузера")
        browser_card.pack(fill='x', padx=15, pady=10)
        
        browser_content = tk.Frame(browser_card, bg=ModernStyle.COLORS['card'])
        browser_content.pack(fill='x', padx=15, pady=(0, 15))
        
        self.browser_var = tk.StringVar(value='chrome')
        
        chrome_frame = tk.Frame(browser_content, bg=ModernStyle.COLORS['surface'], relief='solid', bd=1)
        chrome_frame.pack(fill='x', pady=5)
        
        tk.Radiobutton(
            chrome_frame,
            text="🌐 Google Chrome (безкоштовний)",
            variable=self.browser_var,
            value='chrome',
            **self.radio_style()
        ).pack(anchor='w', padx=10, pady=8)
        
        dolphin_frame = tk.Frame(browser_content, bg=ModernStyle.COLORS['surface'], relief='solid', bd=1)
        dolphin_frame.pack(fill='x', pady=5)
        
        tk.Radiobutton(
            dolphin_frame,
            text="🐬 Dolphin Anty (професійний)",
            variable=self.browser_var,
            value='dolphin',
            **self.radio_style()
        ).pack(anchor='w', padx=10, pady=8)
        
        # Загальні налаштування
        settings_card = GlassCard(page, title="Налаштування")
        settings_card.pack(fill='x', padx=15, pady=10)
        
        settings_content = tk.Frame(settings_card, bg=ModernStyle.COLORS['card'])
        settings_content.pack(fill='x', padx=15, pady=(0, 15))
        
        self.headless_var = tk.BooleanVar()
        self.stealth_var = tk.BooleanVar(value=True)
        self.proxy_enabled_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(settings_content, text="Headless режим", variable=self.headless_var, **self.check_style()).pack(anchor='w', pady=2)
        tk.Checkbutton(settings_content, text="Stealth режим", variable=self.stealth_var, **self.check_style()).pack(anchor='w', pady=2)
        tk.Checkbutton(settings_content, text="Використовувати проксі", variable=self.proxy_enabled_var, **self.check_style()).pack(anchor='w', pady=2)
        
        # Ініціалізація даних
        self.browser_settings = {}
        self.load_browser_settings()
        
        return page
    
    def create_texts_tab(self, parent, text_type):
        """Створення вкладки текстів"""
        # Поле введення
        input_frame = tk.Frame(parent, bg=ModernStyle.COLORS['card'])
        input_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(input_frame, text="Новий текст:", **self.label_style()).pack(anchor='w')
        
        entry_frame = tk.Frame(input_frame, bg=ModernStyle.COLORS['card'])
        entry_frame.pack(fill='x', pady=5)
        
        text_entry = scrolledtext.ScrolledText(entry_frame, height=3, **self.text_style())
        text_entry.pack(side='left', fill='both', expand=True)
        
        AnimatedButton(
            entry_frame,
            text="➕",
            command=lambda: self.add_text(text_type, text_entry),
            bg=ModernStyle.COLORS['success']
        ).pack(side='right', padx=(10, 0))
        
        # Список текстів
        tk.Label(input_frame, text="Збережені тексти:", **self.label_style()).pack(anchor='w', pady=(10, 0))
        
        list_frame = tk.Frame(input_frame, bg=ModernStyle.COLORS['card'])
        list_frame.pack(fill='both', expand=True, pady=5)
        
        listbox = tk.Listbox(list_frame, **self.listbox_style())
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Кнопки управління
        control_frame = tk.Frame(input_frame, bg=ModernStyle.COLORS['card'])
        control_frame.pack(fill='x', pady=10)
        
        AnimatedButton(
            control_frame,
            text="🗑️ Видалити",
            command=lambda: self.remove_text(text_type, listbox),
            bg=ModernStyle.COLORS['error']
        ).pack(side='left', padx=5)
        
        # Збереження посилань
        setattr(self, f'{text_type}_listbox', listbox)
        setattr(self, f'{text_type}_entry', text_entry)
    
    # Стилі для віджетів
    def label_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['card'],
            'fg': ModernStyle.COLORS['text']
        }
    
    def entry_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['surface'],
            'fg': ModernStyle.COLORS['text'],
            'insertbackground': ModernStyle.COLORS['text']
        }
    
    def text_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['surface'],
            'fg': ModernStyle.COLORS['text'],
            'insertbackground': ModernStyle.COLORS['text'],
            'wrap': tk.WORD
        }
    
    def listbox_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['background'],
            'fg': ModernStyle.COLORS['text'],
            'selectbackground': ModernStyle.COLORS['primary'],
            'selectforeground': 'white',
            'relief': 'flat',
            'borderwidth': 0
        }
    
    def radio_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['surface'],
            'fg': ModernStyle.COLORS['text'],
            'selectcolor': ModernStyle.COLORS['primary'],
            'activebackground': ModernStyle.COLORS['surface']
        }
    
    def check_style(self):
        return {
            'font': ModernStyle.FONTS['body'],
            'bg': ModernStyle.COLORS['card'],
            'fg': ModernStyle.COLORS['text'],
            'selectcolor': ModernStyle.COLORS['surface']
        }
    
    # Методи для роботи з даними
    def add_account(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        proxy = self.proxy_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Попередження", "Введіть логін та пароль")
            return
        
        if any(acc['username'] == username for acc in self.accounts):
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
        
        print(f"Додано акаунт: {username}")  # Для відлагодження
        messagebox.showinfo("Успіх", "Акаунт додано")
    
    def clear_all_accounts(self):
        """Очищення всіх акаунтів"""
        if not self.accounts:
            messagebox.showinfo("Інформація", "Список акаунтів вже порожній")
            return
        
        if messagebox.askyesno(
            "Підтвердження", 
            f"Видалити всі {len(self.accounts)} акаунтів?\n\nЦю дію неможливо скасувати!"
        ):
            self.accounts.clear()
            self.update_accounts_display()
            self.save_accounts()
            
            # Оновлення конфігурації воркерів якщо ми на сторінці запуску
            try:
                if hasattr(self, 'update_worker_configs'):
                    self.update_worker_configs()
            except:
                pass
            
            messagebox.showinfo("Успіх", "Всі акаунти видалено")
    
    def remove_account(self):
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть акаунт")
            return
        
        if messagebox.askyesno("Підтвердження", "Видалити акаунт?"):
            index = self.accounts_tree.index(selection[0])
            self.accounts.pop(index)
            self.update_accounts_display()
            self.save_accounts()
    
    def add_target(self):
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
        text = self.bulk_text.get('1.0', tk.END).strip()
        if not text:
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
    
    def clear_all_targets(self):
        """Очищення всіх цілей"""
        if not self.targets:
            messagebox.showinfo("Інформація", "Список цілей вже порожній")
            return
        
        if messagebox.askyesno(
            "Підтвердження", 
            f"Видалити всі {len(self.targets)} цілей?\n\nЦю дію неможливо скасувати!"
        ):
            self.targets.clear()
            self.update_targets_display()
            self.save_targets()
            
            # Оновлення конфігурації воркерів якщо ми на сторінці запуску
            try:
                if hasattr(self, 'update_worker_configs'):
                    self.update_worker_configs()
            except:
                pass
            
            messagebox.showinfo("Успіх", "Всі цілі видалено")
    
    def remove_target(self):
        selection = self.targets_listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть ціль")
            return
        
        index = selection[0]
        self.targets.pop(index)
        self.update_targets_display()
        self.save_targets()
    
    def add_text(self, text_type, text_entry):
        text = text_entry.get('1.0', tk.END).strip()
        if not text:
            return
        
        self.texts[text_type].append(text)
        self.update_texts_display(text_type)
        self.save_texts()
        text_entry.delete('1.0', tk.END)
    
    def remove_text(self, text_type, listbox):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть текст")
            return
        
        index = selection[0]
        self.texts[text_type].pop(index)
        self.update_texts_display(text_type)
        self.save_texts()
    
    # Методи оновлення відображення
    def update_accounts_display(self):
        # Очищення таблиці
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        print(f"Оновлення відображення для {len(self.accounts)} акаунтів")  # Для відлагодження
        
        # Додавання акаунтів
        for account in self.accounts:
            proxy_display = (account.get('proxy', 'Немає') or 'Немає')
            if len(proxy_display) > 15:
                proxy_display = proxy_display[:15] + "..."
            
            self.accounts_tree.insert('', 'end', values=(
                account['username'],
                proxy_display,
                account.get('status', 'active')
            ))
    
    def update_targets_display(self):
        self.targets_listbox.delete(0, tk.END)
        for i, target in enumerate(self.targets):
            self.targets_listbox.insert(tk.END, f"{i+1}. @{target}")
    
    def update_texts_display(self, text_type):
        listbox = getattr(self, f'{text_type}_listbox', None)
        if listbox:
            listbox.delete(0, tk.END)
            for i, text in enumerate(self.texts[text_type]):
                display_text = text[:40] + "..." if len(text) > 40 else text
                display_text = display_text.replace('\n', ' ')
                listbox.insert(tk.END, f"{i+1}. {display_text}")
    
    # Методи збереження/завантаження
    def save_accounts(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/accounts.json', 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти акаунти: {e}")
    
    def load_accounts(self):
        try:
            if os.path.exists('data/accounts.json'):
                with open('data/accounts.json', 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
                print(f"Завантажено {len(self.accounts)} акаунтів")  # Для відлагодження
                self.update_accounts_display()
            else:
                print("Файл accounts.json не знайдено")  # Для відлагодження
                self.accounts = []
        except Exception as e:
            print(f"Помилка завантаження акаунтів: {e}")
            self.accounts = []
    
    def save_targets(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/targets.json', 'w', encoding='utf-8') as f:
                json.dump(self.targets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти цілі: {e}")
    
    def load_targets(self):
        try:
            if os.path.exists('data/targets.json'):
                with open('data/targets.json', 'r', encoding='utf-8') as f:
                    self.targets = json.load(f)
                self.update_targets_display()
        except Exception as e:
            print(f"Помилка завантаження цілей: {e}")
    
    def save_texts(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/texts.json', 'w', encoding='utf-8') as f:
                json.dump(self.texts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти тексти: {e}")
    
    def load_texts(self):
        try:
            if os.path.exists('data/texts.json'):
                with open('data/texts.json', 'r', encoding='utf-8') as f:
                    self.texts = json.load(f)
                for text_type in self.texts:
                    self.update_texts_display(text_type)
        except Exception as e:
            print(f"Помилка завантаження текстів: {e}")
    
    def save_browser_settings(self):
        try:
            self.browser_settings = {
                'browser_type': self.browser_var.get(),
                'headless': self.headless_var.get(),
                'stealth_mode': self.stealth_var.get(),
                'proxy_enabled': self.proxy_enabled_var.get()
            }
            os.makedirs('data', exist_ok=True)
            with open('data/browser_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.browser_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження налаштувань браузера: {e}")
    
    def load_browser_settings(self):
        try:
            if os.path.exists('data/browser_settings.json'):
                with open('data/browser_settings.json', 'r', encoding='utf-8') as f:
                    self.browser_settings = json.load(f)
                    
                self.browser_var.set(self.browser_settings.get('browser_type', 'chrome'))
                self.headless_var.set(self.browser_settings.get('headless', False))
                self.stealth_var.set(self.browser_settings.get('stealth_mode', True))
                self.proxy_enabled_var.set(self.browser_settings.get('proxy_enabled', True))
        except Exception as e:
            print(f"Помилка завантаження налаштувань браузера: {e}")
    
    # Методи імпорту/експорту
    def import_accounts(self):
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
    
    def import_targets(self):
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
    
    # Методи управління автоматизацією
    def start_automation(self):
        """Запуск автоматизації з розподіленими воркерами"""
        try:
            # Збереження налаштувань браузера
            self.save_browser_settings()
            
            # Перевірка наявності даних
            accounts = self.accounts
            targets = self.targets
            chain = self.pages["chain"].get_chain()
            
            if not accounts:
                messagebox.showwarning("Попередження", "Додайте хоча б один акаунт")
                return
            
            if not targets:
                messagebox.showwarning("Попередження", "Додайте хоча б одну ціль")
                return
            
            if not chain:
                messagebox.showwarning("Попередження", "Створіть ланцюжок дій")
                return
            
            # Отримання конфігурацій воркерів
            worker_configs = []
            for worker_config in self.worker_configs:
                config = worker_config.get_config()
                if config:  # Тільки увімкнені воркери
                    worker_configs.append(config)
            
            if not worker_configs:
                messagebox.showwarning("Попередження", "Увімкніть хоча б один воркер")
                return
            
            # Перевірка що у всіх воркерів є акаунти
            for config in worker_configs:
                if not config['account']:
                    messagebox.showwarning("Попередження", f"Воркер #{config['worker_id'] + 1} не має акаунту")
                    return
            
            # Налаштування автоматизації
            automation_config = {
                'worker_configs': worker_configs,
                'browser_settings': self.browser_settings,
                'delay_minutes': self.delay_var.get(),
                'mode': self.mode_var.get(),
                'texts': self.texts
            }
            
            # Створення менеджера автоматизації
            if not self.automation_manager:
                self.automation_manager = AutomationManager()
            
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
            
            # Оновлення статусу воркерів
            for i, config in enumerate(worker_configs):
                if i < len(self.worker_widgets):
                    account_name = config['account']['username']
                    self.worker_widgets[i].update_status('working', f"Підготовка", account_name)
            
            messagebox.showinfo("Успіх", f"Автоматизація запущена з {len(worker_configs)} воркерами")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка запуску автоматизації: {e}")
    
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
        self.status_label.configure(text="● Готовий", fg=ModernStyle.COLORS['success'])
        
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
    
    def update_worker_status(self, worker_id, status, current_target=None, account=None, stats=None):
        """Оновлення статусу воркера"""
        try:
            if worker_id < len(self.worker_widgets):
                self.worker_widgets[worker_id].update_status(status, current_target, account)
                if stats:
                    self.worker_widgets[worker_id].update_stats(stats)
        except Exception as e:
            print(f"Помилка оновлення статусу воркера {worker_id}: {e}")
    
    # Методи навігації
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
            accounts_count = len(self.accounts)
            targets_count = len(self.targets)
            chain_count = len(self.pages["chain"].get_chain())
            texts_count = len(self.texts.get('story_replies', [])) + len(self.texts.get('direct_messages', []))
            
            self.stat_labels["accounts_count"].configure(text=str(accounts_count))
            self.stat_labels["targets_count"].configure(text=str(targets_count))
            self.stat_labels["chain_count"].configure(text=str(chain_count))
            self.stat_labels["texts_count"].configure(text=str(texts_count))
            
        except Exception as e:
            print(f"Помилка оновлення статистики: {e}")
    
    def load_all_data(self):
        """Завантаження всіх збережених даних"""
        try:
            self.load_accounts()
            self.load_targets()
            self.load_texts()
            self.load_browser_settings()
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
    
    # Методи для отримання даних (для сумісності)
    def get_accounts(self):
        return self.accounts
    
    def get_targets(self):
        return self.targets
    
    def get_texts(self, text_type):
        return self.texts.get(text_type, [])


# Допоміжні класи

class DataManager:
    """Спрощений менеджер даних"""
    
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)


class RealAutomationManager:
    """РЕАЛЬНИЙ менеджер автоматизації з браузерами"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.manager = None
        print("🤖 Ініціалізовано RealAutomationManager")
    
    def start_automation(self, config, status_callback):
        """Запуск РЕАЛЬНОЇ автоматизації"""
        print("🚀 Запуск РЕАЛЬНОЇ автоматизації з браузерами!")
        
        self.running = True
        self.paused = False
        
        try:
            # Створення MultiWorkerManager
            self.manager = MultiWorkerManager()
            
            # Перетворення конфігурації GUI в формат для automation_engine
            worker_configs = config['worker_configs']
            browser_settings = config.get('browser_settings', {})
            texts = config.get('texts', {})
            
            # Формування конфігурації для кожного воркера
            automation_configs = []
            
            for worker_config in worker_configs:
                account = worker_config['account']
                targets = worker_config['targets']
                chain = worker_config['chain']
                
                # Конфігурація для automation_engine
                automation_config = {
                    'accounts': [account],  # Один акаунт на воркер
                    'targets': targets,
                    'action_chain': chain,
                    'texts': texts,
                    'workers_count': 1,  # Кожен воркер - окремий процес
                    'delay_minutes': config.get('delay_minutes', 5),
                    'mode': config.get('mode', 'continuous'),
                    'browser_settings': {
                        'type': browser_settings.get('browser_type', 'chrome'),
                        'headless': browser_settings.get('headless', False),
                        'stealth_mode': browser_settings.get('stealth_mode', True),
                        'proxy_enabled': browser_settings.get('proxy_enabled', True),
                        'timeout': 30000
                    },
                    'selectors': BotConfig().get_selectors() if REAL_AUTOMATION else {},
                    'action_delays': BotConfig().get_action_delays() if REAL_AUTOMATION else {},
                    'safety_limits': BotConfig().get_safety_limits() if REAL_AUTOMATION else {}
                }
                
                automation_configs.append(automation_config)
                
                print(f"🔧 Конфігурація воркера {worker_config['worker_id']+1}:")
                print(f"   👤 Акаунт: {account['username']}")
                print(f"   🎯 Цілі: {len(targets)}")
                print(f"   🔗 Дії: {len(chain)}")
                print(f"   🌐 Браузер: {browser_settings.get('browser_type', 'chrome')}")
            
            # Запуск автоматизації для кожного воркера
            def worker_callback(worker_id, status, account_name=None, target=None, stats=None):
                """Проксі для callback GUI"""
                if account_name and target:
                    status_callback(worker_id, status, target, account_name, stats)
                elif account_name:
                    status_callback(worker_id, status, "Обробка", account_name, stats)
                else:
                    status_callback(worker_id, status)
            
            # Запуск кожного воркера в окремому потоці
            import asyncio
            
            async def run_real_automation():
                tasks = []
                
                for i, auto_config in enumerate(automation_configs):
                    print(f"🚀 Запуск воркера {i+1}...")
                    
                    # Створення автоматизації для воркера
                    automation = InstagramAutomation(auto_config)
                    
                    # Запуск автоматизації
                    task = asyncio.create_task(
                        automation.run_account_automation(
                            auto_config['accounts'][0],
                            auto_config['targets'],
                            auto_config['action_chain'],
                            auto_config['texts'],
                            i,
                            worker_callback
                        )
                    )
                    tasks.append(task)
                
                # Очікування завершення всіх воркерів
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                print("🏁 Всі воркери завершили роботу")
                self.running = False
                
                return results
            
            # Запуск в окремому потоці
            def sync_runner():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(run_real_automation())
                    loop.close()
                    print("✅ Автоматизація завершена успішно")
                except Exception as e:
                    print(f"💥 Помилка в реальній автоматизації: {e}")
                    self.running = False
                    raise e
            
            # Запуск в окремому потоці
            automation_thread = threading.Thread(target=sync_runner, daemon=True)
            automation_thread.start()
            
            print(f"🎬 Запущено {len(automation_configs)} реальних воркерів!")
            
        except Exception as e:
            print(f"💥 Помилка запуску реальної автоматизації: {e}")
            self.running = False
            raise e
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        print("🛑 Зупинка реальної автоматизації")
        self.running = False
        self.paused = False
        
        if self.manager:
            self.manager.stop_automation()
    
    def pause_automation(self):
        """Пауза автоматизації"""
        print("⏸️ Пауза реальної автоматизації")
        self.paused = True
        
        if self.manager:
            self.manager.pause_automation()
    
    def is_running(self):
        """Перевірка чи працює автоматизація"""
        return self.running


class AutomationManager:
    """Менеджер автоматизації з розподілом воркерів"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.workers = []
        print("🏭 Ініціалізовано AutomationManager")
    
    def start_automation(self, config, status_callback):
        """Запуск автоматизації з розподіленими воркерами"""
        print("🚀 AutomationManager.start_automation() викликано")
        
        self.running = True
        self.paused = False
        
        worker_configs = config['worker_configs']
        delay_minutes = config['delay_minutes']
        
        print(f"⚙️ Конфігурація: {len(worker_configs)} воркерів, затримка {delay_minutes} хв")
        
        import time
        
        try:
            # Симуляція роботи кожного воркера
            for worker_config in worker_configs:
                if not self.running:
                    print("🛑 Автоматизація зупинена")
                    break
                
                worker_id = worker_config['worker_id']
                account = worker_config['account']
                targets = worker_config['targets']
                chain = worker_config['chain']
                
                print(f"👤 Воркер {worker_id+1}: {account['username']} -> {len(targets)} цілей")
                
                status_callback(worker_id, 'working', "Підготовка", account['username'])
                time.sleep(1)  # Симуляція підготовки
                
                # Симуляція роботи з цілями
                for i, target in enumerate(targets):
                    if not self.running:
                        print(f"🛑 Воркер {worker_id+1} зупинено")
                        break
                    
                    while self.paused:
                        print(f"⏸️ Воркер {worker_id+1} на паузі")
                        time.sleep(1)
                    
                    print(f"🎯 Воркер {worker_id+1}: обробка цілі {target}")
                    status_callback(worker_id, 'working', target, account['username'])
                    
                    # Симуляція виконання дій
                    for j, action in enumerate(chain):
                        if not self.running:
                            break
                        
                        print(f"🔄 Воркер {worker_id+1}: дія {action.get('name', action.get('type'))}")
                        time.sleep(0.5)  # Симуляція затримки дії
                        
                        # Оновлення статистики
                        stats = {
                            'processed_targets': i + 1,
                            'total_actions': (i * len(chain)) + j + 1,
                            'successful_actions': (i * len(chain)) + j + 1,
                            'errors': 0
                        }
                        status_callback(worker_id, 'working', target, account['username'], stats)
                    
                    # Затримка між цілями
                    if i < len(targets) - 1:
                        print(f"⏱️ Воркер {worker_id+1}: затримка між цілями")
                        time.sleep(2)
                
                # Затримка між акаунтами
                if worker_config != worker_configs[-1]:
                    delay_seconds = min(delay_minutes * 10, 30)  # Максимум 30 сек для демо
                    print(f"⏱️ Воркер {worker_id+1}: затримка {delay_seconds} сек")
                    time.sleep(delay_seconds)
                
                print(f"✅ Воркер {worker_id+1} завершено")
                status_callback(worker_id, 'idle')
            
            print("🏁 Всі воркери завершили роботу")
            self.running = False
            
        except Exception as e:
            print(f"💥 Помилка в AutomationManager: {e}")
            self.running = False
            raise e
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        print("🛑 Зупинка автоматизації")
        self.running = False
        self.paused = False
    
    def pause_automation(self):
        """Пауза автоматизації"""
        print("⏸️ Пауза автоматизації")
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
