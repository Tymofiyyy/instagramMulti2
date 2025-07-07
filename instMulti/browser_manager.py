# -*- coding: utf-8 -*-
"""
Менеджер браузерів для Instagram Bot v3.0
Підтримка Chrome (Playwright) та Dolphin Anty з автоматичними проксі
"""

import asyncio
import logging
import random
import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import os

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Playwright не встановлено. Встановіть: pip install playwright")
    print("Після встановлення виконайте: playwright install chromium")


class BaseBrowserManager:
    """Базовий клас для управління браузерами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser_settings = config.get('browser_settings', {})
        self.active_contexts = {}
        self.browser_instance = None
        self.session_manager = SessionManager()
        
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def initialize(self):
        """Ініціалізація браузера"""
        raise NotImplementedError
    
    async def create_context(self, account_username: str, proxy: str = None) -> Optional[BrowserContext]:
        """Створення контексту браузера"""
        raise NotImplementedError
    
    async def create_page(self, context: BrowserContext) -> Optional[Page]:
        """Створення сторінки"""
        raise NotImplementedError
    
    async def cleanup(self):
        """Очищення ресурсів"""
        for context in self.active_contexts.values():
            try:
                await context.close()
            except:
                pass
        
        if self.browser_instance:
            try:
                await self.browser_instance.close()
            except:
                pass


class ChromeBrowserManager(BaseBrowserManager):
    """Менеджер для Chrome браузера через Playwright"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.playwright = None
        
    async def initialize(self):
        """Ініціалізація Playwright та Chrome"""
        try:
            self.playwright = await async_playwright().start()
            
            # Налаштування запуску Chrome
            launch_options = {
                'headless': self.browser_settings.get('headless', False),
                'args': [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions-file-access-check',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--disable-ipc-flooding-protection',
                    '--user-agent=' + self._get_random_user_agent(),
                    '--lang=uk-UA,uk,en-US,en'
                ]
            }
            
            # Додаткові аргументи для stealth режиму
            if self.browser_settings.get('stealth_mode', True):
                launch_options['args'].extend([
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-popup-blocking'
                ])
            
            self.browser_instance = await self.playwright.chromium.launch(**launch_options)
            logging.info("Chrome браузер ініціалізовано через Playwright")
            return True
            
        except Exception as e:
            logging.error(f"Помилка ініціалізації Chrome: {e}")
            return False
    
    async def create_context(self, account_username: str, proxy: str = None) -> Optional[BrowserContext]:
        """Створення контексту Chrome"""
        try:
            if not self.browser_instance:
                await self.initialize()
            
            # Перевірка блокування сесії
            if not await self.session_manager.acquire_session(account_username):
                logging.warning(f"Сесія для {account_username} вже активна")
                return None
            
            # Налаштування контексту
            context_options = {
                'user_agent': self._get_random_user_agent(),
                'viewport': self._get_random_viewport(),
                'locale': random.choice(['uk-UA', 'en-US']),
                'timezone_id': random.choice(['Europe/Kiev', 'Europe/London']),
                'device_scale_factor': random.uniform(1.0, 2.0),
                'is_mobile': True,
                'has_touch': True,
                'extra_http_headers': {
                    'Accept-Language': 'uk-UA,uk;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document'
                }
            }
            
            # Налаштування проксі
            if proxy:
                proxy_config = self._parse_proxy(proxy)
                if proxy_config:
                    context_options['proxy'] = proxy_config
                    logging.info(f"Використовується проксі для {account_username}: {proxy}")
            
            # Створення контексту
            context = await self.browser_instance.new_context(**context_options)
            
            # Застосування stealth налаштувань
            await self._apply_stealth_settings(context)
            
            # Збереження контексту
            self.active_contexts[account_username] = {
                'context': context,
                'proxy': proxy,
                'created_at': datetime.now()
            }
            
            logging.info(f"Створено Chrome контекст для {account_username}")
            return context
            
        except Exception as e:
            logging.error(f"Помилка створення Chrome контексту для {account_username}: {e}")
            await self.session_manager.release_session(account_username)
            return None
    
    async def _apply_stealth_settings(self, context: BrowserContext):
        """Застосування stealth налаштувань"""
        try:
            stealth_script = """
                // Видалення слідів webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Перевизначення navigator.permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Маскування navigator.plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => ({
                        length: 3,
                        0: { name: 'Chrome PDF Plugin' },
                        1: { name: 'Chrome PDF Viewer' },
                        2: { name: 'Native Client' }
                    }),
                });
                
                // Маскування navigator.languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['uk-UA', 'uk', 'en-US', 'en'],
                });
                
                // Маскування navigator.platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Linux armv7l',
                });
                
                // Видалення window.chrome індикаторів автоматизації
                if (window.chrome) {
                    delete window.chrome.runtime;
                }
                
                // Маскування розміру екрану
                Object.defineProperty(screen, 'availHeight', {
                    get: () => window.innerHeight,
                });
                Object.defineProperty(screen, 'availWidth', {
                    get: () => window.innerWidth,
                });
            """
            
            await context.add_init_script(stealth_script)
            
        except Exception as e:
            logging.error(f"Помилка застосування stealth налаштувань: {e}")
    
    def _get_random_user_agent(self) -> str:
        """Отримання випадкового User-Agent"""
        user_agents = self.config.get('user_agents', [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36"
        ])
        return random.choice(user_agents)
    
    def _get_random_viewport(self) -> Dict[str, int]:
        """Отримання випадкової роздільної здатності"""
        resolutions = self.config.get('screen_resolutions', [[375, 812], [414, 896]])
        width, height = random.choice(resolutions)
        return {'width': width, 'height': height}
    
    def _parse_proxy(self, proxy: str) -> Optional[Dict[str, Any]]:
        """Парсинг проксі для Playwright"""
        try:
            parts = proxy.split(':')
            
            if len(parts) == 2:
                # ip:port
                return {
                    'server': f"http://{parts[0]}:{parts[1]}"
                }
            elif len(parts) == 4:
                # ip:port:user:pass
                return {
                    'server': f"http://{parts[0]}:{parts[1]}",
                    'username': parts[2],
                    'password': parts[3]
                }
            
        except Exception as e:
            logging.error(f"Помилка парсингу проксі {proxy}: {e}")
        
        return None
    
    async def create_page(self, context: BrowserContext) -> Optional[Page]:
     """Створення сторінки"""
     try:
        page = await context.new_page()
        
        # Налаштування timeout'ів
        page.set_default_timeout(self.browser_settings.get('timeout', 30000))
        
        # Блокування зайвих ресурсів для швидкості
        await page.route('**/*', self._route_handler)
        
        return page
        
     except Exception as e:
        logging.error(f"❌ Помилка створення сторінки: {e}")
        return None
     
    async def _route_handler(self, route):
        """Обробник маршрутів для оптимізації"""
        try:
            resource_type = route.request.resource_type
            url = route.request.url
            
            # Блокуємо зайві ресурси
            if resource_type in ['image', 'font', 'media'] and 'instagram' not in url:
                await route.abort()
            elif 'ads' in url or 'analytics' in url or 'tracking' in url:
                await route.abort()
            else:
                await route.continue_()
                
        except Exception:
            await route.continue_()
    
    async def close_context(self, account_username: str):
        """Закриття контексту"""
        if account_username in self.active_contexts:
            try:
                context_data = self.active_contexts[account_username]
                await context_data['context'].close()
                del self.active_contexts[account_username]
                await self.session_manager.release_session(account_username)
                logging.info(f"Chrome контекст для {account_username} закрито")
            except Exception as e:
                logging.error(f"Помилка закриття Chrome контексту {account_username}: {e}")


class DolphinBrowserManager(BaseBrowserManager):
    """Менеджер для Dolphin Anty браузера"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.dolphin_settings = config.get('dolphin_settings', {})
        self.api_url = self.dolphin_settings.get('api_url', 'http://localhost:3001/v1.0')
        self.token = self.dolphin_settings.get('token', '')
        self.profiles = {}
        self.playwright = None
        
    async def initialize(self):
        """Ініціалізація Dolphin API"""
        try:
            # Перевірка з'єднання з Dolphin
            if await self._check_dolphin_connection():
                # Ініціалізація Playwright для підключення до профілів
                self.playwright = await async_playwright().start()
                logging.info("Dolphin Anty браузер підключено")
                return True
            else:
                logging.error("Не вдалося підключитися до Dolphin Anty")
                return False
                
        except Exception as e:
            logging.error(f"Помилка ініціалізації Dolphin: {e}")
            return False
    
    async def _check_dolphin_connection(self) -> bool:
        """Перевірка з'єднання з Dolphin API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.token}'}
                async with session.get(f'{self.api_url}/browser_profiles', headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logging.error(f"Помилка з'єднання з Dolphin: {e}")
            return False
    
    async def create_context(self, account_username: str, proxy: str = None) -> Optional[BrowserContext]:
        """Створення контексту через Dolphin профіль"""
        try:
            # Перевірка блокування сесії
            if not await self.session_manager.acquire_session(account_username):
                logging.warning(f"Сесія для {account_username} вже активна")
                return None
            
            # Створення або отримання профілю
            profile_id = await self._get_or_create_profile(account_username, proxy)
            if not profile_id:
                await self.session_manager.release_session(account_username)
                return None
            
            # Запуск профілю
            automation_data = await self._start_profile(profile_id)
            if not automation_data:
                await self.session_manager.release_session(account_username)
                return None
            
            # Підключення до браузера через CDP
            browser = await self.playwright.chromium.connect_over_cdp(automation_data['ws'])
            
            # Отримання першого контексту (Dolphin автоматично створює контекст)
            contexts = browser.contexts
            if not contexts:
                # Якщо контекстів немає, створюємо новий
                context = await browser.new_context()
            else:
                context = contexts[0]
            
            # Збереження контексту
            self.active_contexts[account_username] = {
                'context': context,
                'profile_id': profile_id,
                'browser': browser,
                'proxy': proxy,
                'created_at': datetime.now()
            }
            
            logging.info(f"Створено Dolphin контекст для {account_username}")
            return context
            
        except Exception as e:
            logging.error(f"Помилка створення Dolphin контексту для {account_username}: {e}")
            await self.session_manager.release_session(account_username)
            return None
    
    async def _get_or_create_profile(self, account_username: str, proxy: str = None) -> Optional[str]:
        """Отримання існуючого або створення нового профілю"""
        try:
            profile_name = f"InstagramBot_{account_username}"
            
            # Пошук існуючого профілю
            existing_profile = await self._find_profile_by_name(profile_name)
            if existing_profile:
                profile_id = existing_profile['id']
                
                # Оновлення проксі якщо потрібно
                if proxy and self.dolphin_settings.get('auto_assign_proxy', True):
                    await self._update_profile_proxy(profile_id, proxy)
                
                return profile_id
            
            # Створення нового профілю
            profile_data = {
                'name': profile_name,
                'tags': ['instagram', 'automation', account_username],
                'platform': 'android',
                'browserType': 'anty',
                'mainWebsite': 'instagram.com',
                'userAgent': self._get_random_user_agent(),
                'screen': {
                    'mode': 'real',
                    'resolution': random.choice(self.config.get('screen_resolutions', [[375, 812]]))
                },
                'webRtc': {
                    'mode': 'altered',
                    'ipAddress': None
                },
                'timezone': {
                    'mode': 'auto'
                },
                'locale': {
                    'mode': 'auto'
                },
                'geolocation': {
                    'mode': 'auto'
                },
                'canvas': {
                    'mode': 'real'
                },
                'webGl': {
                    'mode': 'real'
                },
                'clientRects': {
                    'mode': 'real'
                },
                'notes': f'Створено для Instagram автоматизації: {account_username}'
            }
            
            # Додавання проксі якщо вказано
            if proxy:
                proxy_config = self._parse_dolphin_proxy(proxy)
                if proxy_config:
                    profile_data['proxy'] = proxy_config
                    logging.info(f"Додано проксі до профілю {profile_name}: {proxy}")
            
            # Створення профілю
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                
                async with session.post(
                    f'{self.api_url}/browser_profiles',
                    headers=headers,
                    json=profile_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        profile_id = result['id']
                        logging.info(f"Створено Dolphin профіль {profile_id} для {account_username}")
                        return profile_id
                    else:
                        error_text = await response.text()
                        logging.error(f"Помилка створення профілю: {error_text}")
                        return None
            
        except Exception as e:
            logging.error(f"Помилка отримання/створення профілю для {account_username}: {e}")
            return None
    
    async def _find_profile_by_name(self, profile_name: str) -> Optional[Dict]:
        """Пошук профілю за назвою"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.token}'}
                async with session.get(f'{self.api_url}/browser_profiles', headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        profiles = data.get('data', [])
                        
                        for profile in profiles:
                            if profile.get('name') == profile_name:
                                return profile
                        
        except Exception as e:
            logging.error(f"Помилка пошуку профілю {profile_name}: {e}")
        
        return None
    
    async def _update_profile_proxy(self, profile_id: str, proxy: str):
        """Оновлення проксі профілю"""
        try:
            proxy_config = self._parse_dolphin_proxy(proxy)
            if not proxy_config:
                return False
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                
                update_data = {'proxy': proxy_config}
                
                async with session.patch(
                    f'{self.api_url}/browser_profiles/{profile_id}',
                    headers=headers,
                    json=update_data
                ) as response:
                    if response.status == 200:
                        logging.info(f"Оновлено проксі для профілю {profile_id}")
                        return True
                    else:
                        logging.error(f"Помилка оновлення проксі профілю {profile_id}")
                        return False
                        
        except Exception as e:
            logging.error(f"Помилка оновлення проксі: {e}")
            return False
    
    def _parse_dolphin_proxy(self, proxy: str) -> Optional[Dict]:
        """Парсинг проксі для Dolphin"""
        try:
            parts = proxy.split(':')
            
            if len(parts) >= 2:
                proxy_config = {
                    'mode': 'new',
                    'host': parts[0],
                    'port': int(parts[1]),
                    'type': 'http'
                }
                
                if len(parts) >= 4:
                    proxy_config.update({
                        'login': parts[2],
                        'password': parts[3]
                    })
                
                return proxy_config
                
        except Exception as e:
            logging.error(f"Помилка парсингу проксі для Dolphin {proxy}: {e}")
        
        return None
    
    def _get_random_user_agent(self) -> str:
        """Отримання випадкового User-Agent"""
        user_agents = self.config.get('user_agents', [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        ])
        return random.choice(user_agents)
    
    async def _start_profile(self, profile_id: str) -> Optional[Dict]:
        """Запуск профілю Dolphin"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.token}'}
                async with session.get(
                    f'{self.api_url}/browser_profiles/{profile_id}/start',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logging.info(f"Профіль {profile_id} запущено")
                        return data
                    else:
                        error_text = await response.text()
                        logging.error(f"Помилка запуску профілю {profile_id}: {error_text}")
                        return None
                        
        except Exception as e:
            logging.error(f"Помилка запуску профілю {profile_id}: {e}")
            return None
    
    async def create_page(self, context: BrowserContext) -> Optional[Page]:
        """Створення нової сторінки в Dolphin контексті"""
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            # Додаткові налаштування для Instagram
            await page.add_init_script("""
                // Додаткові stealth налаштування для Dolphin
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            return page
            
        except Exception as e:
            logging.error(f"Помилка створення сторінки Dolphin: {e}")
            return None
    
    async def close_context(self, account_username: str):
        """Закриття Dolphin контексту"""
        if account_username in self.active_contexts:
            try:
                context_data = self.active_contexts[account_username]
                profile_id = context_data['profile_id']
                
                # Зупинка профілю
                await self._stop_profile(profile_id)
                
                # Закриття браузера
                await context_data['browser'].close()
                
                del self.active_contexts[account_username]
                await self.session_manager.release_session(account_username)
                logging.info(f"Dolphin контекст для {account_username} закрито")
                
            except Exception as e:
                logging.error(f"Помилка закриття Dolphin контексту {account_username}: {e}")
    
    async def _stop_profile(self, profile_id: str):
        """Зупинка профілю Dolphin"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.token}'}
                async with session.get(
                    f'{self.api_url}/browser_profiles/{profile_id}/stop',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logging.info(f"Профіль {profile_id} зупинено")
                    else:
                        logging.error(f"Помилка зупинки профілю {profile_id}")
                        
        except Exception as e:
            logging.error(f"Помилка зупинки профілю {profile_id}: {e}")


class SessionManager:
    """Менеджер сесій для координації між воркерами"""
    
    def __init__(self):
        self.active_sessions = {}
        self._lock = asyncio.Lock()
    
    async def acquire_session(self, account_username: str) -> bool:
        """Отримання блокування сесії"""
        async with self._lock:
            if account_username in self.active_sessions:
                return False
            
            self.active_sessions[account_username] = {
                'start_time': datetime.now(),
                'session_id': str(uuid.uuid4())
            }
            
            return True
    
    async def release_session(self, account_username: str):
        """Звільнення сесії"""
        async with self._lock:
            if account_username in self.active_sessions:
                del self.active_sessions[account_username]
    
    async def is_session_active(self, account_username: str) -> bool:
        """Перевірка активності сесії"""
        return account_username in self.active_sessions
    
    async def get_active_sessions(self) -> Dict[str, Dict]:
        """Отримання списку активних сесій"""
        return self.active_sessions.copy()


class BrowserFactory:
    """Фабрика для створення менеджерів браузерів"""
    
    @staticmethod
    def create_manager(config: Dict[str, Any]) -> BaseBrowserManager:
        """Створення менеджера браузера відповідно до конфігурації"""
        browser_type = config.get('browser_settings', {}).get('type', 'chrome')
        
        if browser_type == 'chrome':
            return ChromeBrowserManager(config)
        elif browser_type == 'dolphin':
            return DolphinBrowserManager(config)
        else:
            raise ValueError(f"Непідтримуваний тип браузера: {browser_type}")


class ProxyRotator:
    """Клас для ротації проксі"""
    
    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_next_proxy(self) -> Optional[str]:
        """Отримання наступного проксі"""
        if not self.proxy_list:
            return None
        
        attempts = 0
        while attempts < len(self.proxy_list):
            proxy = self.proxy_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxy_list)
            
            if proxy not in self.failed_proxies:
                return proxy
            
            attempts += 1
        
        return None
    
    def mark_proxy_failed(self, proxy: str):
        """Позначити проксі як неробочий"""
        self.failed_proxies.add(proxy)
    
    def reset_failed_proxies(self):
        """Скинути список неробочих проксі"""
        self.failed_proxies.clear()


class BrowserHealthMonitor:
    """Монітор здоров'я браузерів"""
    
    def __init__(self):
        self.health_stats = {}
    
    async def check_browser_health(self, manager: BaseBrowserManager) -> Dict[str, Any]:
        """Перевірка здоров'я браузера"""
        health_data = {
            'active_contexts': len(manager.active_contexts),
            'browser_running': manager.browser_instance is not None,
            'memory_usage': await self._get_memory_usage(),
            'last_check': datetime.now().isoformat()
        }
        
        return health_data
    
    async def _get_memory_usage(self) -> float:
        """Отримання використання пам'яті"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0


# Експорт основних класів
__all__ = [
    'BaseBrowserManager', 'ChromeBrowserManager', 'DolphinBrowserManager',
    'BrowserFactory', 'SessionManager', 'ProxyRotator', 'BrowserHealthMonitor'
]