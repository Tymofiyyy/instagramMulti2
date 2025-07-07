# -*- coding: utf-8 -*-
"""
Розширений менеджер конфігурації для Instagram Bot v3.0
Збереження налаштувань, ланцюжків дій, акаунтів та текстів
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil
from pathlib import Path


class BotConfig:
    """Клас для управління конфігурацією бота з автозбереженням"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.data_dir = "data"
        self.backup_dir = "backups"
        
        # Створення необхідних директорій
        for directory in [self.data_dir, self.backup_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Завантаження конфігурації з файлу"""
        default_config = self.get_default_config()
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # Злиття з дефолтними значеннями
                merged_config = self.merge_configs(default_config, loaded_config)
                return merged_config
            else:
                # Створення стандартного файлу конфігурації
                self.save_config(default_config)
                logging.info(f"Створено стандартний файл конфігурації: {self.config_file}")
                
        except Exception as e:
            logging.error(f"Помилка завантаження конфігурації: {e}")
            logging.info("Використовуємо стандартну конфігурацію")
        
        return default_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """Стандартна конфігурація"""
        return {
            "version": "3.0.0",
            "created_at": datetime.now().isoformat(),
            
            # Налаштування браузера
            "browser_settings": {
                "type": "chrome",  # chrome, dolphin
                "headless": False,
                "stealth_mode": True,
                "auto_close": True,
                "timeout": 30000,
                "mobile_emulation": True
            },
            
            # Налаштування Dolphin
            "dolphin_settings": {
                "api_url": "http://localhost:3001/v1.0",
                "token": "",
                "auto_create_profiles": True,
                "auto_assign_proxy": True
            },
            
            # Ліміти безпеки
            "safety_limits": {
                "max_accounts": 50,
                "max_parallel_workers": 10,
                "daily_action_limit": 100,
                "hourly_action_limit": 20,
                "max_errors_per_account": 3,
                "cooldown_after_error": 1800  # 30 хвилин
            },
            
            # Затримки (секунди)
            "action_delays": {
                "like_post": [2, 5],
                "view_story": [1, 3],
                "like_story": [1, 2],
                "reply_story": [3, 6],
                "send_dm": [5, 10],
                "follow": [3, 7],
                "between_actions": [5, 15],
                "between_targets": [30, 90],
                "between_accounts": [300, 600],  # 5-10 хвилин
                "page_load": [2, 5]
            },
            
            # User Agents для обходу детекції
            "user_agents": [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            ],
            
            # Роздільна здатність екрану
            "screen_resolutions": [
                [375, 812],  # iPhone X/11/12/13
                [414, 896],  # iPhone XR/11/12/13 Pro Max
                [390, 844],  # iPhone 12/13 mini
                [360, 640],  # Samsung Galaxy S
                [412, 869]   # Pixel
            ],
            
            # Селектори для Playwright
            "selectors": {
                "login": {
                    "username_field": "input[name='username']",
                    "password_field": "input[name='password']",
                    "login_button": "button[type='submit']",
                    "save_info_not_now": "text=Not Now",
                    "turn_on_notifications": "text=Not Now"
                },
                "posts": {
                    "post_links": "article a[href*='/p/']",
                    "like_button": "[aria-label='Like']",
                    "liked_button": "[aria-label='Unlike']",
                    "close_button": "[aria-label='Close']"
                },
                "stories": {
                    "story_ring": "canvas",
                    "story_container": "[role='dialog']",
                    "like_button": "[aria-label='Like']",
                    "reply_field": "textarea[placeholder*='message']",
                    "send_button": "button[type='submit']",
                    "next_button": "[aria-label='Next']",
                    "close_story": "[aria-label='Close']"
                },
                "follow": {
                    "follow_button": "text=Follow",
                    "following_button": "text=Following",
                    "unfollow_button": "text=Unfollow"
                },
                "direct": {
                    "new_message_button": "[aria-label*='New message']",
                    "search_field": "input[placeholder*='Search']",
                    "message_field": "textarea[placeholder*='Message']",
                    "send_button": "button[type='submit']"
                }
            },
            
            # Налаштування логування
            "logging": {
                "level": "INFO",
                "file": "logs/instagram_bot.log",
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5
            }
        }
    
    def merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Злиття конфігурацій з пріоритетом завантаженої"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self.merge_configs(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def save_config(self, config: Dict[str, Any] = None):
        """Збереження конфігурації з backup"""
        if config is None:
            config = self.config
        
        try:
            # Створення backup поточної конфігурації
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_dir, f"config_backup_{timestamp}.json")
                shutil.copy2(self.config_file, backup_file)
            
            # Збереження нової конфігурації
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Конфігурація збережена: {self.config_file}")
            
        except Exception as e:
            logging.error(f"Помилка збереження конфігурації: {e}")
    
    def get(self, key: str, default=None):
        """Отримання значення з конфігурації"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Встановлення значення в конфігурації"""
        keys = key.split('.')
        config = self.config
        
        # Навігація до батьківського елемента
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Встановлення значення
        config[keys[-1]] = value
        self.save_config()
    
    def get_browser_settings(self) -> Dict[str, Any]:
        """Отримання налаштувань браузера"""
        return self.config.get('browser_settings', {})
    
    def get_dolphin_settings(self) -> Dict[str, Any]:
        """Отримання налаштувань Dolphin"""
        return self.config.get('dolphin_settings', {})
    
    def get_safety_limits(self) -> Dict[str, Any]:
        """Отримання лімітів безпеки"""
        return self.config.get('safety_limits', {})
    
    def get_action_delays(self) -> Dict[str, List[int]]:
        """Отримання затримок дій"""
        return self.config.get('action_delays', {})
    
    def get_selectors(self) -> Dict[str, Any]:
        """Отримання селекторів"""
        return self.config.get('selectors', {})


class DataPersistence:
    """Клас для збереження даних програми"""
    
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Створення директорії для даних"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save_accounts(self, accounts: List[Dict]) -> bool:
        """Збереження акаунтів"""
        return self._save_json_file("accounts.json", accounts)
    
    def load_accounts(self) -> List[Dict]:
        """Завантаження акаунтів"""
        return self._load_json_file("accounts.json", [])
    
    def save_targets(self, targets: List[str]) -> bool:
        """Збереження цілей"""
        return self._save_json_file("targets.json", targets)
    
    def load_targets(self) -> List[str]:
        """Завантаження цілей"""
        return self._load_json_file("targets.json", [])
    
    def save_action_chain(self, chain: List[Dict]) -> bool:
        """Збереження ланцюжка дій"""
        return self._save_json_file("action_chain.json", chain)
    
    def load_action_chain(self) -> List[Dict]:
        """Завантаження ланцюжка дій"""
        return self._load_json_file("action_chain.json", [])
    
    def save_texts(self, texts: Dict[str, List[str]]) -> bool:
        """Збереження текстів"""
        return self._save_json_file("texts.json", texts)
    
    def load_texts(self) -> Dict[str, List[str]]:
        """Завантаження текстів"""
        return self._load_json_file("texts.json", {
            "story_replies": [],
            "direct_messages": []
        })
    
    def save_browser_settings(self, settings: Dict) -> bool:
        """Збереження налаштувань браузера"""
        return self._save_json_file("browser_settings.json", settings)
    
    def load_browser_settings(self) -> Dict:
        """Завантаження налаштувань браузера"""
        return self._load_json_file("browser_settings.json", {
            "browser_type": "chrome",
            "headless": False,
            "proxy_enabled": True,
            "stealth_mode": True
        })
    
    def save_statistics(self, stats: Dict) -> bool:
        """Збереження статистики"""
        stats["last_updated"] = datetime.now().isoformat()
        return self._save_json_file("statistics.json", stats)
    
    def load_statistics(self) -> Dict:
        """Завантаження статистики"""
        return self._load_json_file("statistics.json", {
            "total_accounts_processed": 0,
            "total_actions_performed": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "last_run": None,
            "session_history": []
        })
    
    def save_session_log(self, session_data: Dict) -> bool:
        """Збереження логу сесії"""
        session_data["timestamp"] = datetime.now().isoformat()
        
        # Завантаження існуючих логів
        logs = self._load_json_file("session_logs.json", [])
        logs.append(session_data)
        
        # Обмеження кількості логів (останні 100 сесій)
        if len(logs) > 100:
            logs = logs[-100:]
        
        return self._save_json_file("session_logs.json", logs)
    
    def load_session_logs(self) -> List[Dict]:
        """Завантаження логів сесій"""
        return self._load_json_file("session_logs.json", [])
    
    def export_data(self, export_type: str, filename: str = None) -> str:
        """Експорт даних"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"export_{export_type}_{timestamp}.json"
        
        filepath = os.path.join("exports", filename)
        os.makedirs("exports", exist_ok=True)
        
        try:
            if export_type == "all":
                data = {
                    "accounts": self.load_accounts(),
                    "targets": self.load_targets(),
                    "action_chain": self.load_action_chain(),
                    "texts": self.load_texts(),
                    "browser_settings": self.load_browser_settings(),
                    "statistics": self.load_statistics(),
                    "export_date": datetime.now().isoformat()
                }
            elif export_type == "accounts":
                data = self.load_accounts()
            elif export_type == "targets":
                data = self.load_targets()
            elif export_type == "chain":
                data = self.load_action_chain()
            elif export_type == "texts":
                data = self.load_texts()
            else:
                raise ValueError(f"Невідомий тип експорту: {export_type}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            logging.error(f"Помилка експорту {export_type}: {e}")
            return None
    
    def import_data(self, filepath: str, import_type: str) -> bool:
        """Імпорт даних"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if import_type == "accounts":
                return self.save_accounts(data)
            elif import_type == "targets":
                return self.save_targets(data)
            elif import_type == "chain":
                return self.save_action_chain(data)
            elif import_type == "texts":
                return self.save_texts(data)
            elif import_type == "all":
                success = True
                if "accounts" in data:
                    success &= self.save_accounts(data["accounts"])
                if "targets" in data:
                    success &= self.save_targets(data["targets"])
                if "action_chain" in data:
                    success &= self.save_action_chain(data["action_chain"])
                if "texts" in data:
                    success &= self.save_texts(data["texts"])
                return success
            else:
                raise ValueError(f"Невідомий тип імпорту: {import_type}")
                
        except Exception as e:
            logging.error(f"Помилка імпорту {import_type}: {e}")
            return False
    
    def backup_all_data(self) -> str:
        """Створення повного бекапу всіх даних"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"full_backup_{timestamp}.json"
        
        try:
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "version": "3.0.0",
                "accounts": self.load_accounts(),
                "targets": self.load_targets(),
                "action_chain": self.load_action_chain(),
                "texts": self.load_texts(),
                "browser_settings": self.load_browser_settings(),
                "statistics": self.load_statistics(),
                "session_logs": self.load_session_logs()
            }
            
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Створено повний бекап: {backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"Помилка створення бекапу: {e}")
            return None
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Відновлення з бекапу"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            success = True
            
            if "accounts" in backup_data:
                success &= self.save_accounts(backup_data["accounts"])
            if "targets" in backup_data:
                success &= self.save_targets(backup_data["targets"])
            if "action_chain" in backup_data:
                success &= self.save_action_chain(backup_data["action_chain"])
            if "texts" in backup_data:
                success &= self.save_texts(backup_data["texts"])
            if "browser_settings" in backup_data:
                success &= self.save_browser_settings(backup_data["browser_settings"])
            
            if success:
                logging.info(f"Дані відновлено з бекапу: {backup_path}")
            
            return success
            
        except Exception as e:
            logging.error(f"Помилка відновлення з бекапу: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups: int = 10):
        """Очищення старих бекапів"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                return
            
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('full_backup_') and filename.endswith('.json'):
                    file_path = os.path.join(backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Сортування за часом модифікації
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Видалення старих бекапів
            for file_path, _ in backup_files[max_backups:]:
                try:
                    os.remove(file_path)
                    logging.info(f"Видалено старий бекап: {file_path}")
                except Exception as e:
                    logging.error(f"Помилка видалення бекапу {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"Помилка очищення бекапів: {e}")
    
    def _save_json_file(self, filename: str, data: Any) -> bool:
        """Збереження JSON файлу"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Помилка збереження {filename}: {e}")
            return False
    
    def _load_json_file(self, filename: str, default: Any = None) -> Any:
        """Завантаження JSON файлу"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Помилка завантаження {filename}: {e}")
        
        return default if default is not None else {}


class SettingsValidator:
    """Валідатор налаштувань"""
    
    @staticmethod
    def validate_account(account: Dict) -> Dict[str, Any]:
        """Валідація акаунту"""
        errors = []
        warnings = []
        
        # Перевірка обов'язкових полів
        if not account.get('username'):
            errors.append("Відсутній логін")
        elif not SettingsValidator._validate_username(account['username']):
            errors.append("Некоректний формат логіну")
        
        if not account.get('password'):
            errors.append("Відсутній пароль")
        elif len(account['password']) < 6:
            warnings.append("Короткий пароль (менше 6 символів)")
        
        # Перевірка проксі
        if account.get('proxy'):
            if not SettingsValidator._validate_proxy(account['proxy']):
                warnings.append("Некоректний формат проксі")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_target(target: str) -> bool:
        """Валідація цілі"""
        return SettingsValidator._validate_username(target)
    
    @staticmethod
    def validate_action_chain(chain: List[Dict]) -> Dict[str, Any]:
        """Валідація ланцюжка дій"""
        errors = []
        warnings = []
        
        if not chain:
            errors.append("Ланцюжок дій порожній")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        enabled_actions = [action for action in chain if action.get('enabled', True)]
        
        if not enabled_actions:
            errors.append("Немає увімкнених дій")
        
        # Перевірка типів дій
        valid_action_types = [
            'follow', 'like_posts', 'view_stories', 'like_stories', 
            'reply_stories', 'send_dm', 'delay'
        ]
        
        for i, action in enumerate(chain):
            if action.get('type') not in valid_action_types:
                errors.append(f"Невідомий тип дії в кроці {i+1}: {action.get('type')}")
            
            # Перевірка налаштувань дій
            if action.get('type') in ['like_posts', 'view_stories'] and action.get('settings'):
                count = action['settings'].get('count', 1)
                if not isinstance(count, int) or count < 1 or count > 10:
                    warnings.append(f"Некоректна кількість в кроці {i+1}: {count}")
            
            if action.get('type') == 'delay' and action.get('settings'):
                delay = action['settings'].get('delay', 30)
                if not isinstance(delay, int) or delay < 1:
                    warnings.append(f"Некоректна затримка в кроці {i+1}: {delay}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_browser_settings(settings: Dict) -> Dict[str, Any]:
        """Валідація налаштувань браузера"""
        errors = []
        warnings = []
        
        browser_type = settings.get('browser_type', 'chrome')
        if browser_type not in ['chrome', 'dolphin']:
            errors.append(f"Невідомий тип браузера: {browser_type}")
        
        if browser_type == 'dolphin':
            if not settings.get('dolphin_api_url'):
                errors.append("Не вказано URL API Dolphin")
            if not settings.get('dolphin_token'):
                warnings.append("Не вказано токен API Dolphin")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """Валідація логіну Instagram"""
        import re
        if not username:
            return False
        # Instagram username rules
        pattern = r'^[a-zA-Z0-9._]{1,30}'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def _validate_proxy(proxy: str) -> bool:
        """Валідація проксі"""
        import re
        if not proxy:
            return False
        
        patterns = [
            r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}',  # ip:port
            r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:\w+:\w+',  # ip:port:user:pass
            r'^[\w\.-]+:\d{1,5}',  # domain:port
            r'^[\w\.-]+:\d{1,5}:\w+:\w+'  # domain:port:user:pass'
        ]
    
        return any(re.match(pattern, proxy) for pattern in patterns)


# Допоміжні функції

def setup_logging(level=logging.INFO):
    """Налаштування системи логування"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def create_sample_files():
    """Створення зразків файлів для імпорту"""
    samples_dir = "samples"
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
    
    # Зразок акаунтів
    sample_accounts = [
        {
            "username": "example_user1",
            "password": "example_password1",
            "proxy": "127.0.0.1:8080:user:pass",
            "status": "active"
        },
        {
            "username": "example_user2", 
            "password": "example_password2",
            "proxy": None,
            "status": "active"
        }
    ]
    
    # Зразок цілей
    sample_targets = [
        "target_user1",
        "target_user2",
        "target_user3"
    ]
    
    # Зразок ланцюжка дій
    sample_chain = [
        {
            "type": "like_posts",
            "name": "Лайк 2 постів",
            "icon": "❤️",
            "settings": {"count": 2},
            "enabled": True
        },
        {
            "type": "view_stories",
            "name": "Перегляд 3 сторіс",
            "icon": "📖", 
            "settings": {"count": 3},
            "enabled": True
        },
        {
            "type": "like_stories",
            "name": "Лайк сторіс",
            "icon": "💖",
            "enabled": True
        },
        {
            "type": "delay",
            "name": "Затримка 30 сек",
            "icon": "🔄",
            "settings": {"delay": 30},
            "enabled": True
        }
    ]
    
    # Зразок текстів
    sample_texts = {
        "story_replies": [
            "🔥🔥🔥",
            "❤️",
            "Круто!",
            "👍",
            "Супер!",
            "💯"
        ],
        "direct_messages": [
            "Привіт! Як справи? 😊",
            "Вітаю! Сподобався ваш контент 👍",
            "Доброго дня! Цікавий профіль ✨"
        ]
    }
    
    # Збереження зразків
    try:
        with open(os.path.join(samples_dir, "sample_accounts.json"), 'w', encoding='utf-8') as f:
            json.dump(sample_accounts, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(samples_dir, "sample_targets.json"), 'w', encoding='utf-8') as f:
            json.dump(sample_targets, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(samples_dir, "sample_chain.json"), 'w', encoding='utf-8') as f:
            json.dump(sample_chain, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(samples_dir, "sample_texts.json"), 'w', encoding='utf-8') as f:
            json.dump(sample_texts, f, indent=2, ensure_ascii=False)
        
        print(f"Зразки файлів створено в директорії: {samples_dir}")
        
    except Exception as e:
        print(f"Помилка створення зразків: {e}")


# Експорт основних класів
__all__ = [
    'BotConfig', 'DataPersistence', 'SettingsValidator', 
    'setup_logging', 'create_sample_files'
]