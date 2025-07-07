# -*- coding: utf-8 -*-
"""
Менеджер даних для Instagram Bot Pro v3.0
Централізоване управління всіма даними програми
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil
from pathlib import Path


class DataManager:
    """Централізований менеджер для всіх даних програми"""
    
    def __init__(self):
        self.data_dir = "data"
        self.backups_dir = "backups"
        self.exports_dir = "exports"
        self.logs_dir = "logs"
        
        self.setup_directories()
        self.setup_logging()
        
        # Ініціалізація структур даних
        self.accounts = []
        self.targets = []
        self.action_chain = []
        self.texts = {
            'story_replies': [],
            'direct_messages': []
        }
        self.browser_settings = {
            'browser_type': 'chrome',
            'headless': False,
            'proxy_enabled': True,
            'stealth_mode': True,
            'dolphin_api_url': 'http://localhost:3001/v1.0',
            'dolphin_token': ''
        }
        self.statistics = {
            'total_sessions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'last_run': None
        }
        
        # Завантаження збережених даних
        self.load_all_data()
    
    def setup_directories(self):
        """Створення необхідних директорій"""
        directories = [
            self.data_dir,
            self.backups_dir, 
            self.exports_dir,
            self.logs_dir,
            "samples"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def setup_logging(self):
        """Налаштування логування"""
        log_file = os.path.join(self.logs_dir, "bot.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    # Методи для роботи з акаунтами
    def add_account(self, username: str, password: str, proxy: str = None) -> bool:
        """Додавання нового акаунту"""
        try:
            # Перевірка чи акаунт вже існує
            if any(acc['username'] == username for acc in self.accounts):
                logging.warning(f"Акаунт {username} вже існує")
                return False
            
            account = {
                'username': username,
                'password': password,
                'proxy': proxy,
                'status': 'active',
                'added_at': datetime.now().isoformat(),
                'last_used': None,
                'total_actions': 0,
                'success_rate': 0.0
            }
            
            self.accounts.append(account)
            self.save_accounts()
            
            logging.info(f"Додано акаунт: {username}")
            return True
            
        except Exception as e:
            logging.error(f"Помилка додавання акаунту {username}: {e}")
            return False
    
    def remove_account(self, username: str) -> bool:
        """Видалення акаунту"""
        try:
            self.accounts = [acc for acc in self.accounts if acc['username'] != username]
            self.save_accounts()
            
            logging.info(f"Видалено акаунт: {username}")
            return True
            
        except Exception as e:
            logging.error(f"Помилка видалення акаунту {username}: {e}")
            return False
    
    def get_accounts(self) -> List[Dict]:
        """Отримання списку акаунтів"""
        return self.accounts.copy()
    
    def update_account_stats(self, username: str, actions_count: int, success_rate: float):
        """Оновлення статистики акаунту"""
        for account in self.accounts:
            if account['username'] == username:
                account['last_used'] = datetime.now().isoformat()
                account['total_actions'] += actions_count
                account['success_rate'] = success_rate
                break
        
        self.save_accounts()
    
    # Методи для роботи з цілями
    def add_target(self, target: str) -> bool:
        """Додавання цілі"""
        try:
            target = target.strip().replace('@', '')
            
            if target in self.targets:
                logging.warning(f"Ціль {target} вже існує")
                return False
            
            self.targets.append(target)
            self.save_targets()
            
            logging.info(f"Додано ціль: {target}")
            return True
            
        except Exception as e:
            logging.error(f"Помилка додавання цілі {target}: {e}")
            return False
    
    def remove_target(self, target: str) -> bool:
        """Видалення цілі"""
        try:
            if target in self.targets:
                self.targets.remove(target)
                self.save_targets()
                
                logging.info(f"Видалено ціль: {target}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка видалення цілі {target}: {e}")
            return False
    
    def get_targets(self) -> List[str]:
        """Отримання списку цілей"""
        return self.targets.copy()
    
    def bulk_add_targets(self, targets_list: List[str]) -> int:
        """Масове додавання цілей"""
        added_count = 0
        
        for target in targets_list:
            target = target.strip().replace('@', '')
            if target and target not in self.targets:
                self.targets.append(target)
                added_count += 1
        
        if added_count > 0:
            self.save_targets()
            logging.info(f"Додано {added_count} цілей")
        
        return added_count
    
    # Методи для роботи з ланцюжком дій
    def set_action_chain(self, chain: List[Dict]) -> bool:
        """Встановлення ланцюжка дій"""
        try:
            self.action_chain = chain.copy()
            self.save_action_chain()
            
            logging.info(f"Встановлено ланцюжок з {len(chain)} дій")
            return True
            
        except Exception as e:
            logging.error(f"Помилка встановлення ланцюжка: {e}")
            return False
    
    def get_action_chain(self) -> List[Dict]:
        """Отримання ланцюжка дій"""
        return self.action_chain.copy()
    
    def add_action_to_chain(self, action: Dict) -> bool:
        """Додавання дії до ланцюжка"""
        try:
            self.action_chain.append(action)
            self.save_action_chain()
            
            logging.info(f"Додано дію до ланцюжка: {action.get('name', action.get('type'))}")
            return True
            
        except Exception as e:
            logging.error(f"Помилка додавання дії: {e}")
            return False
    
    # Методи для роботи з текстами
    def add_text(self, text_type: str, text: str) -> bool:
        """Додавання тексту"""
        try:
            if text_type not in self.texts:
                self.texts[text_type] = []
            
            if text not in self.texts[text_type]:
                self.texts[text_type].append(text)
                self.save_texts()
                
                logging.info(f"Додано текст для {text_type}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка додавання тексту: {e}")
            return False
    
    def remove_text(self, text_type: str, index: int) -> bool:
        """Видалення тексту"""
        try:
            if text_type in self.texts and 0 <= index < len(self.texts[text_type]):
                removed_text = self.texts[text_type].pop(index)
                self.save_texts()
                
                logging.info(f"Видалено текст: {removed_text[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка видалення тексту: {e}")
            return False
    
    def get_texts(self, text_type: str) -> List[str]:
        """Отримання текстів певного типу"""
        return self.texts.get(text_type, []).copy()
    
    def get_all_texts(self) -> Dict[str, List[str]]:
        """Отримання всіх текстів"""
        return {key: value.copy() for key, value in self.texts.items()}
    
    # Методи для роботи з налаштуваннями браузера
    def update_browser_settings(self, settings: Dict) -> bool:
        """Оновлення налаштувань браузера"""
        try:
            self.browser_settings.update(settings)
            self.save_browser_settings()
            
            logging.info("Налаштування браузера оновлено")
            return True
            
        except Exception as e:
            logging.error(f"Помилка оновлення налаштувань браузера: {e}")
            return False
    
    def get_browser_settings(self) -> Dict:
        """Отримання налаштувань браузера"""
        return self.browser_settings.copy()
    
    # Методи для роботи зі статистикою
    def update_statistics(self, stats_update: Dict) -> bool:
        """Оновлення статистики"""
        try:
            self.statistics.update(stats_update)
            self.statistics['last_updated'] = datetime.now().isoformat()
            self.save_statistics()
            
            return True
            
        except Exception as e:
            logging.error(f"Помилка оновлення статистики: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Отримання статистики"""
        return self.statistics.copy()
    
    # Методи збереження/завантаження
    def save_accounts(self):
        """Збереження акаунтів"""
        self._save_json_file("accounts.json", self.accounts)
    
    def save_targets(self):
        """Збереження цілей"""
        self._save_json_file("targets.json", self.targets)
    
    def save_action_chain(self):
        """Збереження ланцюжка дій"""
        self._save_json_file("action_chain.json", self.action_chain)
    
    def save_texts(self):
        """Збереження текстів"""
        self._save_json_file("texts.json", self.texts)
    
    def save_browser_settings(self):
        """Збереження налаштувань браузера"""
        self._save_json_file("browser_settings.json", self.browser_settings)
    
    def save_statistics(self):
        """Збереження статистики"""
        self._save_json_file("statistics.json", self.statistics)
    
    def load_all_data(self):
        """Завантаження всіх збережених даних"""
        try:
            self.accounts = self._load_json_file("accounts.json", [])
            self.targets = self._load_json_file("targets.json", [])
            self.action_chain = self._load_json_file("action_chain.json", [])
            self.texts = self._load_json_file("texts.json", {
                'story_replies': [],
                'direct_messages': []
            })
            self.browser_settings = self._load_json_file("browser_settings.json", {
                'browser_type': 'chrome',
                'headless': False,
                'proxy_enabled': True,
                'stealth_mode': True,
                'dolphin_api_url': 'http://localhost:3001/v1.0',
                'dolphin_token': ''
            })
            self.statistics = self._load_json_file("statistics.json", {
                'total_sessions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'last_run': None
            })
            
            logging.info("Всі дані завантажено успішно")
            
        except Exception as e:
            logging.error(f"Помилка завантаження даних: {e}")
    
    def _save_json_file(self, filename: str, data: Any):
        """Збереження JSON файлу"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            # Створення бекапу перед збереженням
            if os.path.exists(filepath):
                backup_path = os.path.join(
                    self.backups_dir, 
                    f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
                )
                shutil.copy2(filepath, backup_path)
            
            # Збереження нових даних
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"Помилка збереження {filename}: {e}")
    
    def _load_json_file(self, filename: str, default: Any = None):
        """Завантаження JSON файлу"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        except Exception as e:
            logging.error(f"Помилка завантаження {filename}: {e}")
        
        return default if default is not None else {}
    
    # Методи імпорту/експорту
    def export_data(self, data_type: str = "all") -> str:
        """Експорт даних"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"export_{data_type}_{timestamp}.json"
            filepath = os.path.join(self.exports_dir, filename)
            
            if data_type == "all":
                export_data = {
                    "accounts": self.accounts,
                    "targets": self.targets,
                    "action_chain": self.action_chain,
                    "texts": self.texts,
                    "browser_settings": self.browser_settings,
                    "statistics": self.statistics,
                    "export_date": datetime.now().isoformat(),
                    "version": "3.0.0"
                }
            elif data_type == "accounts":
                export_data = self.accounts
            elif data_type == "targets":
                export_data = self.targets
            elif data_type == "chain":
                export_data = self.action_chain
            elif data_type == "texts":
                export_data = self.texts
            else:
                raise ValueError(f"Невідомий тип експорту: {data_type}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Дані експортовано: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Помилка експорту {data_type}: {e}")
            return None
    
    def import_data(self, filepath: str, data_type: str = "all") -> bool:
        """Імпорт даних"""
        try:
            if not os.path.exists(filepath):
                logging.error(f"Файл не знайдено: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data_type == "all":
                if isinstance(data, dict):
                    if "accounts" in data:
                        self.accounts = data["accounts"]
                        self.save_accounts()
                    if "targets" in data:
                        self.targets = data["targets"]
                        self.save_targets()
                    if "action_chain" in data:
                        self.action_chain = data["action_chain"]
                        self.save_action_chain()
                    if "texts" in data:
                        self.texts = data["texts"]
                        self.save_texts()
                    if "browser_settings" in data:
                        self.browser_settings = data["browser_settings"]
                        self.save_browser_settings()
                    
                    logging.info("Всі дані імпортовано успішно")
                    return True
            
            elif data_type == "accounts":
                if isinstance(data, list):
                    self.accounts = data
                    self.save_accounts()
                    logging.info(f"Імпортовано {len(data)} акаунтів")
                    return True
            
            elif data_type == "targets":
                if isinstance(data, list):
                    self.targets = data
                    self.save_targets()
                    logging.info(f"Імпортовано {len(data)} цілей")
                    return True
            
            elif data_type == "chain":
                if isinstance(data, list):
                    self.action_chain = data
                    self.save_action_chain()
                    logging.info(f"Імпортовано ланцюжок з {len(data)} дій")
                    return True
            
            elif data_type == "texts":
                if isinstance(data, dict):
                    self.texts = data
                    self.save_texts()
                    logging.info("Тексти імпортовано успішно")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка імпорту {data_type}: {e}")
            return False
    
    def create_full_backup(self) -> str:
        """Створення повного бекапу"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"full_backup_{timestamp}.json"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "version": "3.0.0",
                "accounts": self.accounts,
                "targets": self.targets,
                "action_chain": self.action_chain,
                "texts": self.texts,
                "browser_settings": self.browser_settings,
                "statistics": self.statistics
            }
            
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
            return self.import_data(backup_path, "all")
            
        except Exception as e:
            logging.error(f"Помилка відновлення з бекапу: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups: int = 10):
        """Очищення старих бекапів"""
        try:
            if not os.path.exists(self.backups_dir):
                return
            
            # Отримання всіх файлів бекапів
            backup_files = []
            for filename in os.listdir(self.backups_dir):
                if filename.endswith('.json') or filename.endswith('.backup'):
                    file_path = os.path.join(self.backups_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Сортування за часом створення
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Видалення старих бекапів
            for file_path, _ in backup_files[max_backups:]:
                try:
                    os.remove(file_path)
                    logging.info(f"Видалено старий бекап: {os.path.basename(file_path)}")
                except Exception as e:
                    logging.error(f"Помилка видалення бекапу {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"Помилка очищення бекапів: {e}")
    
    # Методи валідації
    def validate_account(self, account: Dict) -> Dict[str, Any]:
        """Валідація акаунту"""
        errors = []
        warnings = []
        
        # Перевірка логіну
        username = account.get('username', '')
        if not username:
            errors.append("Відсутній логін")
        elif not self._validate_username(username):
            errors.append("Некоректний формат логіну")
        
        # Перевірка паролю
        password = account.get('password', '')
        if not password:
            errors.append("Відсутній пароль")
        elif len(password) < 6:
            warnings.append("Короткий пароль (менше 6 символів)")
        
        # Перевірка проксі
        proxy = account.get('proxy')
        if proxy and not self._validate_proxy(proxy):
            warnings.append("Некоректний формат проксі")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_target(self, target: str) -> bool:
        """Валідація цілі"""
        return self._validate_username(target.replace('@', ''))
    
    def validate_action_chain(self, chain: List[Dict]) -> Dict[str, Any]:
        """Валідація ланцюжка дій"""
        errors = []
        warnings = []
        
        if not chain:
            errors.append("Ланцюжок дій порожній")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Перевірка кожної дії
        valid_action_types = [
            'follow', 'like_posts', 'view_stories', 'like_stories', 
            'reply_stories', 'send_dm', 'delay'
        ]
        
        enabled_count = 0
        
        for i, action in enumerate(chain):
            action_type = action.get('type')
            
            if action.get('enabled', True):
                enabled_count += 1
            
            if action_type not in valid_action_types:
                errors.append(f"Невідомий тип дії в кроці {i+1}: {action_type}")
            
            # Перевірка налаштувань
            settings = action.get('settings', {})
            
            if action_type in ['like_posts', 'view_stories']:
                count = settings.get('count', 1)
                if not isinstance(count, int) or count < 1 or count > 10:
                    warnings.append(f"Некоректна кількість в кроці {i+1}: {count}")
            
            elif action_type == 'delay':
                delay = settings.get('delay', 30)
                if not isinstance(delay, int) or delay < 1:
                    warnings.append(f"Некоректна затримка в кроці {i+1}: {delay}")
        
        if enabled_count == 0:
            errors.append("Немає увімкнених дій в ланцюжку")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_username(self, username: str) -> bool:
        """Валідація username Instagram"""
        import re
        if not username:
            return False
        
        # Instagram username правила
        pattern = r'^[a-zA-Z0-9._]{1,30}'
        return bool(re.match(pattern, username))
    
    def _validate_proxy(self, proxy: str) -> bool:
        """Валідація проксі"""
        import re
        if not proxy:
            return False
        
        patterns = [
            r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}',  # ip:port
            r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:\w+:\w+',  # ip:port:user:pass
            r'^[\w\.-]+:\d{1,5}',  # domain:port
            r'^[\w\.-]+:\d{1,5}:\w+:\w+' # domain:port:user:pass
        ]
        
        return any(re.match(pattern, proxy) for pattern in patterns)
    
    # Методи отримання статистики
    def get_summary_stats(self) -> Dict[str, Any]:
        """Отримання загальної статистики"""
        return {
            'accounts_count': len(self.accounts),
            'targets_count': len(self.targets),
            'chain_actions_count': len([a for a in self.action_chain if a.get('enabled', True)]),
            'total_texts_count': sum(len(texts) for texts in self.texts.values()),
            'story_replies_count': len(self.texts.get('story_replies', [])),
            'direct_messages_count': len(self.texts.get('direct_messages', [])),
            'browser_type': self.browser_settings.get('browser_type', 'chrome'),
            'proxy_enabled': self.browser_settings.get('proxy_enabled', False),
            'last_backup': self._get_last_backup_date(),
            'data_directory_size': self._get_directory_size(self.data_dir)
        }
    
    def _get_last_backup_date(self) -> Optional[str]:
        """Отримання дати останнього бекапу"""
        try:
            if not os.path.exists(self.backups_dir):
                return None
            
            backup_files = [
                f for f in os.listdir(self.backups_dir) 
                if f.startswith('full_backup_') and f.endswith('.json')
            ]
            
            if not backup_files:
                return None
            
            # Знаходження найновішого бекапу
            latest_backup = max(
                backup_files,
                key=lambda f: os.path.getmtime(os.path.join(self.backups_dir, f))
            )
            
            backup_path = os.path.join(self.backups_dir, latest_backup)
            backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
            
            return backup_time.isoformat()
            
        except Exception:
            return None
    
    def _get_directory_size(self, directory: str) -> int:
        """Отримання розміру директорії в байтах"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception:
            return 0
    
    # Методи для швидкого доступу
    def get_active_accounts(self) -> List[Dict]:
        """Отримання активних акаунтів"""
        return [acc for acc in self.accounts if acc.get('status') == 'active']
    
    def get_enabled_actions(self) -> List[Dict]:
        """Отримання увімкнених дій з ланцюжка"""
        return [action for action in self.action_chain if action.get('enabled', True)]
    
    def has_sufficient_data_for_automation(self) -> Dict[str, Any]:
        """Перевірка чи достатньо даних для запуску автоматизації"""
        issues = []
        
        if not self.accounts:
            issues.append("Немає доданих акаунтів")
        elif not self.get_active_accounts():
            issues.append("Немає активних акаунтів")
        
        if not self.targets:
            issues.append("Немає цілей для автоматизації")
        
        if not self.action_chain:
            issues.append("Не створено ланцюжок дій")
        elif not self.get_enabled_actions():
            issues.append("Немає увімкнених дій в ланцюжку")
        
        # Перевірка текстів для дій що їх потребують
        enabled_actions = self.get_enabled_actions()
        needs_story_replies = any(a.get('type') == 'reply_stories' for a in enabled_actions)
        needs_dm_texts = any(a.get('type') == 'send_dm' for a in enabled_actions)
        
        if needs_story_replies and not self.texts.get('story_replies'):
            issues.append("Для відповідей на сторіс потрібні тексти")
        
        if needs_dm_texts and not self.texts.get('direct_messages'):
            issues.append("Для приватних повідомлень потрібні тексти")
        
        # Перевірка налаштувань Dolphin якщо вибрано
        if self.browser_settings.get('browser_type') == 'dolphin':
            if not self.browser_settings.get('dolphin_api_url'):
                issues.append("Не налаштовано URL API Dolphin")
            if not self.browser_settings.get('dolphin_token'):
                issues.append("Не налаштовано токен API Dolphin")
        
        return {
            'ready': len(issues) == 0,
            'issues': issues
        }
    
    # Методи автоматичного обслуговування
    def perform_maintenance(self):
        """Автоматичне обслуговування"""
        try:
            # Очищення старих бекапів
            self.cleanup_old_backups(10)
            
            # Створення автоматичного бекапу раз на день
            last_backup = self._get_last_backup_date()
            if not last_backup:
                self.create_full_backup()
            else:
                last_backup_time = datetime.fromisoformat(last_backup.replace('Z', '+00:00').replace('+00:00', ''))
                if (datetime.now() - last_backup_time).days >= 1:
                    self.create_full_backup()
            
            logging.info("Автоматичне обслуговування виконано")
            
        except Exception as e:
            logging.error(f"Помилка автоматичного обслуговування: {e}")


# Експорт головного класу
__all__ = ['DataManager']