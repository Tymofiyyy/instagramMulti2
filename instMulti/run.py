#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Bot Pro v3.0 - Головний файл запуску
Професійна мультиворкер автоматизація Instagram з Playwright
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# Додавання поточної директорії до шляху
sys.path.append(str(Path(__file__).parent))

def main():
    """Запуск головного GUI"""
    try:
        print("🖥️ Запуск Instagram Bot Pro v3.0...")
        
        # Створення головного вікна
        root = tk.Tk()
        
        # Імпорт та запуск GUI
        from gui import InstagramBotGUI
        app = InstagramBotGUI(root)
        
        print("✅ GUI запущено успішно!")
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ Критична помилка GUI: {e}")
        return False

if __name__ == "__main__":
    main()