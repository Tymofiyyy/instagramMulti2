# -*- coding: utf-8 -*-
"""
Модуль автоматизації Instagram з підтримкою ланцюжків дій та мультиворкерів
"""

import asyncio
import random
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json

try:
    from playwright.async_api import Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Playwright не встановлено")

from browser_manager import BrowserFactory, SessionManager
from config import BotConfig, DataPersistence


class InstagramAutomation:
    """Клас для автоматизації дій в Instagram"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser_manager = None
        self.selectors = config.get('selectors', {})
        self.action_delays = config.get('action_delays', {})
        self.safety_limits = config.get('safety_limits', {})
        self.running = False
        self.paused = False
        
        self.stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'accounts_processed': 0,
            'current_account': None,
            'current_target': None,
            'start_time': None,
            'errors': []
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def initialize(self):
        """Ініціалізація автоматизації"""
        try:
            # Створення менеджера браузера
            self.browser_manager = BrowserFactory.create_manager(self.config)
            await self.browser_manager.initialize()
            
            logging.info("Instagram автоматизація ініціалізована")
            return True
            
        except Exception as e:
            logging.error(f"Помилка ініціалізації автоматизації: {e}")
            return False
    
    async def cleanup(self):
        """Очищення ресурсів"""
        self.running = False
        
        if self.browser_manager:
            await self.browser_manager.cleanup()
        
        logging.info("Ресурси автоматизації очищено")
    
    async def run_account_automation(self, account: Dict, targets: List[str], 
                                   action_chain: List[Dict], texts: Dict[str, List[str]],
                                   worker_id: int = 0, status_callback: Callable = None):
        """Запуск автоматизації для одного акаунту"""
        account_username = account.get('username')
        self.stats['current_account'] = account_username
        self.stats['start_time'] = datetime.now()
        
        if status_callback:
            status_callback(worker_id, 'working', account_username)
        
        context = None
        page = None
        
        try:
            logging.info(f"Воркер {worker_id}: Початок обробки акаунту {account_username}")
            
            # Створення контексту браузера
            proxy = account.get('proxy')
            context = await self.browser_manager.create_context(account_username, proxy)
            if not context:
                raise Exception(f"Не вдалося створити контекст для {account_username}")
            
            # Створення сторінки
            page = await self.browser_manager.create_page(context)
            if not page:
                raise Exception(f"Не вдалося створити сторінку для {account_username}")
            
            # Вхід в акаунт
            login_success = await self.login_account(page, account)
            if not login_success:
                raise Exception(f"Не вдалося увійти в акаунт {account_username}")
            
            # Обробка цілей
            shuffled_targets = targets.copy()
            random.shuffle(shuffled_targets)
            
            for target in shuffled_targets:
                if not self.running:
                    break
                
                while self.paused:
                    await asyncio.sleep(1)
                
                try:
                    self.stats['current_target'] = target
                    if status_callback:
                        status_callback(worker_id, 'working', f"{account_username} -> {target}")
                    
                    # Виконання ланцюжка дій для цілі
                    await self.execute_action_chain(page, target, action_chain, texts, account_username)
                    
                    # Затримка між цілями
                    if target != shuffled_targets[-1]:  # Не останній target
                        delay = random.uniform(*self.action_delays.get('between_targets', [30, 90]))
                        await self.safe_sleep(delay)
                
                except Exception as e:
                    logging.error(f"Помилка обробки цілі {target} для {account_username}: {e}")
                    self.stats['failed_actions'] += 1
                    self.stats['errors'].append({
                        'account': account_username,
                        'target': target,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            self.stats['accounts_processed'] += 1
            logging.info(f"Воркер {worker_id}: Акаунт {account_username} оброблено успішно")
            
        except Exception as e:
            logging.error(f"Помилка обробки акаунту {account_username}: {e}")
            self.stats['failed_actions'] += 1
            self.stats['errors'].append({
                'account': account_username,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        finally:
            # Закриття ресурсів
            if page:
                try:
                    await page.close()
                except:
                    pass
            
            if context and account_username:
                try:
                    await self.browser_manager.close_context(account_username)
                except:
                    pass
            
            if status_callback:
                status_callback(worker_id, 'idle')
        
        return self.stats.copy()
    
    async def login_account(self, page: Page, account: Dict) -> bool:
        """Вхід в акаунт Instagram"""
        try:
            username = account.get('username')
            password = account.get('password')
            
            if not username or not password:
                logging.error("Не вказано логін або пароль")
                return False
            
            logging.info(f"Вхід в акаунт: {username}")
            
            # Перехід на сторінку входу
            await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
            await self.safe_sleep(random.uniform(2, 4))
            
            # Очікування форми входу
            await page.wait_for_selector(self.selectors['login']['username_field'], timeout=15000)
            
            # Введення логіну
            await page.fill(self.selectors['login']['username_field'], username)
            await self.safe_sleep(random.uniform(0.5, 1.5))
            
            # Введення паролю
            await page.fill(self.selectors['login']['password_field'], password)
            await self.safe_sleep(random.uniform(0.5, 1.5))
            
            # Натискання кнопки входу
            await page.click(self.selectors['login']['login_button'])
            
            # Очікування завантаження
            await self.safe_sleep(random.uniform(3, 5))
            
            # Перевірка успішного входу
            current_url = page.url
            
            if 'instagram.com' in current_url and 'login' not in current_url:
                # Обробка popup'ів після входу
                await self.handle_post_login_popups(page)
                
                logging.info(f"Успішний вхід в акаунт: {username}")
                return True
            else:
                logging.error(f"Неуспішний вхід в акаунт: {username}")
                return False
        
        except Exception as e:
            logging.error(f"Помилка входу в акаунт {username}: {e}")
            return False
    
    async def handle_post_login_popups(self, page: Page):
        """Обробка popup'ів після входу"""
        try:
            # "Save Your Login Info?" popup
            try:
                await page.wait_for_selector(self.selectors['login']['save_info_not_now'], timeout=3000)
                await page.click(self.selectors['login']['save_info_not_now'])
                await self.safe_sleep(1)
            except:
                pass
            
            # "Turn on Notifications" popup
            try:
                await page.wait_for_selector(self.selectors['login']['turn_on_notifications'], timeout=3000)
                await page.click(self.selectors['login']['turn_on_notifications'])
                await self.safe_sleep(1)
            except:
                pass
            
        except Exception as e:
            logging.error(f"Помилка обробки popup'ів: {e}")
    
    async def execute_action_chain(self, page: Page, target: str, action_chain: List[Dict], 
                             texts: Dict[str, List[str]], account_username: str):
     """Виконання ланцюжка дій для цілі з покращеною логікою"""
     try:
        logging.info(f"🎯 Виконання ланцюжка дій для {target} (акаунт: {account_username})")
        
        # Валідація ланцюжка дій
        if not action_chain:
            logging.warning(f"Порожній ланцюжок дій для {target}")
            return
        
        enabled_actions = [action for action in action_chain if action.get('enabled', True)]
        if not enabled_actions:
            logging.warning(f"Немає увімкнених дій для {target}")
            return
        
        # Перехід на профіль цілі з retry логікою
        profile_loaded = await self.navigate_to_profile(page, target)
        if not profile_loaded:
            logging.error(f"Не вдалося завантажити профіль {target}")
            return
        
        # Перевірка існування та доступності профілю
        profile_status = await self.check_profile_status(page, target)
        if profile_status['blocked']:
            logging.warning(f"Профіль {target} заблокований або приватний")
            return
        
        # Збір початкової інформації про профіль
        profile_info = await self.gather_profile_info(page, target)
        logging.info(f"Профіль {target}: {profile_info['posts_count']} постів, {profile_info['followers_count']} фоловерів")
        
        # Виконання ланцюжка дій
        successful_actions = 0
        failed_actions = 0
        
        for i, action in enumerate(enabled_actions):
            if not self.running:
                logging.info("Зупинка виконання ланцюжка через команду stop")
                break
            
            while self.paused:
                await asyncio.sleep(1)
            
            action_type = action.get('type')
            action_name = action.get('name', action_type)
            action_settings = action.get('settings', {})
            
            try:
                logging.info(f"🔄 Дія {i+1}/{len(enabled_actions)}: {action_name}")
                
                # Виконання дії залежно від типу
                action_result = await self.execute_single_action(
                    page, target, action_type, action_settings, texts, account_username, profile_info
                )
                
                if action_result['success']:
                    successful_actions += 1
                    self.stats['successful_actions'] += 1
                    logging.info(f"✅ {action_name} виконано успішно")
                    
                    # Оновлення профільної інформації після певних дій
                    if action_type in ['follow', 'like_posts']:
                        profile_info = await self.update_profile_info(page, profile_info, action_type)
                else:
                    failed_actions += 1
                    self.stats['failed_actions'] += 1
                    logging.warning(f"❌ {action_name} не виконано: {action_result.get('error', 'Невідома помилка')}")
                
                self.stats['total_actions'] += 1
                
                # Динамічна затримка між діями (залежить від типу дії та успішності)
                if i < len(enabled_actions) - 1:  # Не остання дія
                    delay = await self.calculate_action_delay(action_type, action_result['success'])
                    await self.safe_sleep(delay)
                
                # Перевірка на блокування після кожної дії
                if await self.check_for_blocks(page):
                    logging.error(f"Виявлено блокування після дії {action_name}")
                    break
                
            except Exception as e:
                failed_actions += 1
                self.stats['failed_actions'] += 1
                self.stats['total_actions'] += 1
                
                logging.error(f"❌ Помилка виконання дії {action_name}: {e}")
                
                # Спроба відновлення після помилки
                recovery_success = await self.attempt_error_recovery(page, target, e)
                if not recovery_success:
                    logging.error(f"Не вдалося відновитися після помилки для {target}")
                    break
        
        # Фінальна статистика для цілі
        success_rate = (successful_actions / (successful_actions + failed_actions) * 100) if (successful_actions + failed_actions) > 0 else 0
        
        logging.info(f"📊 Завершено обробку {target}: {successful_actions} успішних, {failed_actions} невдалих дій (успішність: {success_rate:.1f}%)")
        
        # Збереження статистики обробки цілі
        await self.save_target_statistics(target, account_username, {
            'successful_actions': successful_actions,
            'failed_actions': failed_actions,
            'success_rate': success_rate,
            'actions_performed': [action.get('name', action.get('type')) for action in enabled_actions],
            'processed_at': datetime.now().isoformat()
        })
        
     except Exception as e:
        logging.error(f"💥 Критична помилка виконання ланцюжка дій для {target}: {e}")
        self.stats['failed_actions'] += 1
        raise


    async def navigate_to_profile(self, page: Page, target: str, max_retries: int = 3) -> bool:
     """Навігація до профілю з retry логікою"""
     for attempt in range(max_retries):
        try:
            logging.debug(f"Спроба {attempt + 1} завантаження профілю {target}")
            
            await page.goto(f'https://www.instagram.com/{target}/', 
                          wait_until='networkidle', 
                          timeout=30000)
            
            # Перевірка успішного завантаження
            await page.wait_for_load_state('domcontentloaded', timeout=10000)
            
            # Додаткова перевірка що це профіль Instagram
            page_title = await page.title()
            if 'Instagram' in page_title or target in page_title:
                await self.safe_sleep(random.uniform(2, 4))
                return True
            
        except Exception as e:
            logging.warning(f"Спроба {attempt + 1} не вдалася для {target}: {e}")
            if attempt < max_retries - 1:
                await self.safe_sleep(random.uniform(3, 6))
            
     return False


    async def check_profile_status(self, page: Page, target: str) -> Dict[str, Any]:
     """Перевірка статусу профілю"""
     try:
        page_content = await page.content()
        
        status = {
            'blocked': False,
            'private': False,
            'not_found': False,
            'suspended': False,
            'reason': None
        }
        
        # Перевірки різних станів профілю
        if "Sorry, this page isn't available" in page_content:
            status['not_found'] = True
            status['blocked'] = True
            status['reason'] = 'Сторінка не знайдена'
            
        elif "This Account is Private" in page_content or "This account is private" in page_content:
            status['private'] = True
            status['blocked'] = True
            status['reason'] = 'Приватний акаунт'
            
        elif "User not found" in page_content:
            status['not_found'] = True
            status['blocked'] = True
            status['reason'] = 'Користувач не знайдений'
            
        elif "temporarily unavailable" in page_content.lower():
            status['suspended'] = True
            status['blocked'] = True
            status['reason'] = 'Акаунт тимчасово недоступний'
        
        return status
        
     except Exception as e:
        logging.error(f"Помилка перевірки статусу профілю {target}: {e}")
        return {'blocked': True, 'reason': f'Помилка перевірки: {e}'}


    async def gather_profile_info(self, page: Page, target: str) -> Dict[str, Any]:
     """Збір інформації про профіль"""
     try:
        profile_info = {
            'username': target,
            'posts_count': 0,
            'followers_count': 0,
            'following_count': 0,
            'has_stories': False,
            'is_verified': False,
            'bio_text': '',
            'is_business': False
        }
        
        # Спроба отримати статистику профілю
        try:
            stats_elements = await page.query_selector_all('main ul li')
            if len(stats_elements) >= 3:
                # Пости
                posts_text = await stats_elements[0].inner_text()
                profile_info['posts_count'] = self.extract_number_from_text(posts_text)
                
                # Фоловери
                followers_text = await stats_elements[1].inner_text()
                profile_info['followers_count'] = self.extract_number_from_text(followers_text)
                
                # Підписки
                following_text = await stats_elements[2].inner_text()
                profile_info['following_count'] = self.extract_number_from_text(following_text)
                
        except Exception as e:
            logging.debug(f"Не вдалося отримати статистику профілю {target}: {e}")
        
        # Перевірка наявності сторіс
        try:
            story_ring = await page.query_selector('canvas')
            if story_ring:
                profile_info['has_stories'] = True
        except:
            pass
        
        # Перевірка верифікації
        try:
            verified_badge = await page.query_selector('[aria-label*="Verified"]')
            if verified_badge:
                profile_info['is_verified'] = True
        except:
            pass
        
        # Отримання біо
        try:
            bio_element = await page.query_selector('main article div div span')
            if bio_element:
                profile_info['bio_text'] = await bio_element.inner_text()
        except:
            pass
        
        return profile_info
        
     except Exception as e:
        logging.error(f"Помилка збору інформації про профіль {target}: {e}")
        return {'username': target}


    async def execute_single_action(self, page: Page, target: str, action_type: str, 
                               settings: Dict, texts: Dict, account_username: str, 
                               profile_info: Dict) -> Dict[str, Any]:
     """Виконання однієї дії з детальним логуванням"""
     action_result = {'success': False, 'error': None, 'details': {}}
    
     try:
        if action_type == 'follow':
            result = await self.follow_user(page, target, account_username)
            action_result['success'] = result
            
        elif action_type == 'like_posts':
            count = settings.get('count', 2)
            result = await self.like_recent_posts(page, target, account_username, count)
            action_result['success'] = result
            action_result['details']['posts_liked'] = count if result else 0
            
        elif action_type == 'view_stories':
            if not profile_info.get('has_stories', False):
                action_result['error'] = 'Немає активних сторіс'
                return action_result
                
            count = settings.get('count', 3)
            result = await self.view_stories(page, target, account_username, count)
            action_result['success'] = result
            action_result['details']['stories_viewed'] = count if result else 0
            
        elif action_type == 'like_stories':
            if not profile_info.get('has_stories', False):
                action_result['error'] = 'Немає активних сторіс'
                return action_result
                
            result = await self.like_stories(page, target, account_username)
            action_result['success'] = result
            
        elif action_type == 'reply_stories':
            if not profile_info.get('has_stories', False):
                action_result['error'] = 'Немає активних сторіс'
                return action_result
                
            story_texts = texts.get('story_replies', [])
            if not story_texts:
                action_result['error'] = 'Немає текстів для відповідей'
                return action_result
                
            result = await self.reply_to_stories(page, target, account_username, story_texts)
            action_result['success'] = result
            
        elif action_type == 'send_dm':
            dm_texts = texts.get('direct_messages', [])
            if not dm_texts:
                action_result['error'] = 'Немає текстів для DM'
                return action_result
                
            result = await self.send_direct_message(page, target, account_username, dm_texts)
            action_result['success'] = result
            
        elif action_type == 'delay':
            delay_seconds = settings.get('delay', 30)
            await self.safe_sleep(delay_seconds)
            action_result['success'] = True
            action_result['details']['delay_duration'] = delay_seconds
            
        else:
            action_result['error'] = f'Невідомий тип дії: {action_type}'
            
     except Exception as e:
        action_result['error'] = str(e)
        logging.error(f"Помилка виконання дії {action_type}: {e}")
    
     return action_result


    async def calculate_action_delay(self, action_type: str, was_successful: bool) -> float:
     """Розрахунок динамічної затримки між діями"""
     base_delays = self.action_delays.get('between_actions', [5, 15])
    
     # Базова затримка
     delay = random.uniform(*base_delays)
    
    # Збільшення затримки для важливих дій
     important_actions = ['follow', 'send_dm', 'reply_stories']
     if action_type in important_actions:
        delay *= 1.5
    
    # Збільшення затримки якщо дія не вдалася (можливе блокування)
     if not was_successful:
        delay *= 2
    
     # Додаткова рандомізація для природності
     delay += random.uniform(-2, 3)
    
     return max(delay, 1)  # Мінімум 1 секунда


    async def check_for_blocks(self, page: Page) -> bool:
     """Перевірка на блокування або лімітування"""
     try:
        page_content = await page.content()
        
        block_indicators = [
            'Try Again Later',
            'Please wait a few minutes',
            'temporarily blocked',
            'unusual activity',
            'We restrict certain activity',
            'Action Blocked',
            'temporary ban'
        ]
        
        for indicator in block_indicators:
            if indicator.lower() in page_content.lower():
                logging.warning(f"Виявлено індикатор блокування: {indicator}")
                return True
        
        # Перевірка на спеціальні діалоги
        dialog = await page.query_selector('[role="dialog"]')
        if dialog:
            dialog_text = await dialog.inner_text()
            if any(indicator.lower() in dialog_text.lower() for indicator in block_indicators):
                return True
        
        return False
        
     except Exception as e:
        logging.error(f"Помилка перевірки блокування: {e}")
        return False


    async def attempt_error_recovery(self, page: Page, target: str, error: Exception) -> bool:
     """Спроба відновлення після помилки"""
     try:
        logging.info(f"Спроба відновлення після помилки для {target}")
        
        # Перевірка чи сторінка ще доступна
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            # Спроба перезавантаження сторінки
            await page.reload(wait_until='networkidle', timeout=15000)
            await self.safe_sleep(random.uniform(3, 6))
        
        # Закриття можливих діалогів
        try:
            close_buttons = await page.query_selector_all('[aria-label="Close"], [aria-label="Закрити"]')
            for button in close_buttons:
                await button.click()
                await self.safe_sleep(1)
        except:
            pass
        
        # Повернення на профіль
        return await self.navigate_to_profile(page, target, max_retries=2)
        
     except Exception as e:
        logging.error(f"Помилка відновлення: {e}")
        return False


    def extract_number_from_text(self, text: str) -> int:
     """Витягування числа з тексту (наприклад, '1,234 posts' -> 1234)"""
     try:
        import re
        # Видалення всіх символів крім цифр та ком
        numbers_only = re.sub(r'[^\d,.]', '', text)
        
        # Обробка скорочень (K, M)
        if 'K' in text.upper():
            base_number = float(numbers_only.replace(',', ''))
            return int(base_number * 1000)
        elif 'M' in text.upper():
            base_number = float(numbers_only.replace(',', ''))
            return int(base_number * 1000000)
        else:
            return int(numbers_only.replace(',', ''))
            
     except:
        return 0


    async def save_target_statistics(self, target: str, account: str, stats: Dict): 
     """Збереження статистики обробки цілі"""
     try:
        # Тут можна додати збереження в базу даних або файл
        stats_entry = {
            'target': target,
            'account': account,
            'timestamp': datetime.now().isoformat(),
            **stats
        }
        
        # Логування для моніторингу
        logging.info(f"📈 Статистика {target}: {stats}")
        
     except Exception as e:
        logging.error(f"Помилка збереження статистики: {e}")


    async def update_profile_info(self, page: Page, profile_info: Dict, action_type: str) -> Dict:
     """Оновлення інформації про профіль після дії"""
     try:
        if action_type == 'follow':
            # Можна перевірити чи змінилася кількість підписників
            pass
        
        # Перевірка чи з'явилися нові сторіс
        if action_type in ['like_posts', 'follow']:
            try:
                story_ring = await page.query_selector('canvas')
                profile_info['has_stories'] = story_ring is not None
            except:
                pass
        
        return profile_info
        
     except Exception as e:
        logging.error(f"Помилка оновлення профільної інформації: {e}")
        return profile_info
    
    async def is_profile_private_or_not_found(self, page: Page) -> bool:
        """Перевірка чи профіль приватний або не існує"""
        try:
            page_content = await page.content()
            
            # Перевірка на помилку 404
            if "Sorry, this page isn't available" in page_content:
                return True
            
            # Перевірка на приватний профіль
            private_indicators = [
                "This Account is Private",
                "Follow to see their photos and videos",
                "This account is private"
            ]
            
            return any(indicator in page_content for indicator in private_indicators)
            
        except Exception:
            return True
    
    async def follow_user(self, page: Page, target: str, account_username: str):
        """Підписка на користувача"""
        try:
            # Пошук кнопки підписки
            follow_button = await page.query_selector(self.selectors['follow']['follow_button'])
            
            if follow_button:
                await follow_button.click()
                await self.safe_sleep(random.uniform(1, 2))
                
                self.stats['successful_actions'] += 1
                self.stats['total_actions'] += 1
                
                logging.info(f"Підписка на {target} виконана")
                return True
            else:
                # Можливо вже підписані
                following_button = await page.query_selector(self.selectors['follow']['following_button'])
                if following_button:
                    logging.info(f"Вже підписані на {target}")
                    return True
                
                logging.warning(f"Кнопка підписки не знайдена для {target}")
                return False
        
        except Exception as e:
            logging.error(f"Помилка підписки на {target}: {e}")
            self.stats['failed_actions'] += 1
            self.stats['total_actions'] += 1
            return False
    
    async def like_recent_posts(self, page: Page, target: str, account_username: str, count: int = 2):
        """Лайк останніх постів"""
        try:
            # Пошук постів
            post_links = await page.query_selector_all(self.selectors['posts']['post_links'])
            
            if not post_links:
                logging.warning(f"Пости не знайдено для {target}")
                return False
            
            posts_to_like = min(count, len(post_links))
            liked_count = 0
            
            for i in range(posts_to_like):
                try:
                    # Відкриття посту
                    await post_links[i].click()
                    await self.safe_sleep(random.uniform(2, 4))
                    
                    # Очікування завантаження посту
                    await page.wait_for_selector(self.selectors['posts']['like_button'], timeout=5000)
                    
                    # Перевірка чи пост вже лайкнуто
                    liked_button = await page.query_selector(self.selectors['posts']['liked_button'])
                    if liked_button:
                        logging.info(f"Пост {i+1} вже лайкнуто")
                        await self.close_post(page)
                        continue
                    
                    # Лайк посту
                    like_button = await page.query_selector(self.selectors['posts']['like_button'])
                    if like_button:
                        await like_button.click()
                        await self.safe_sleep(random.uniform(1, 2))
                        
                        liked_count += 1
                        self.stats['successful_actions'] += 1
                        self.stats['total_actions'] += 1
                        
                        logging.info(f"Лайкнуто пост {i+1} користувача {target}")
                    
                    # Затримка між лайками
                    delay = random.uniform(*self.action_delays.get('like_post', [2, 5]))
                    await self.safe_sleep(delay)
                    
                    # Закриття посту
                    await self.close_post(page)
                    
                except Exception as e:
                    logging.error(f"Помилка лайку посту {i+1} для {target}: {e}")
                    self.stats['failed_actions'] += 1
                    self.stats['total_actions'] += 1
                    
                    # Спроба закрити пост
                    await self.close_post(page)
            
            logging.info(f"Лайкнуто {liked_count}/{posts_to_like} постів для {target}")
            return liked_count > 0
            
        except Exception as e:
            logging.error(f"Помилка лайку постів для {target}: {e}")
            return False
    
    async def close_post(self, page: Page):
        """Закриття відкритого посту"""
        try:
            close_button = await page.query_selector(self.selectors['posts']['close_button'])
            if close_button:
                await close_button.click()
                await self.safe_sleep(1)
            else:
                # Альтернативний спосіб - натискання Escape
                await page.keyboard.press('Escape')
                await self.safe_sleep(1)
        except Exception as e:
            logging.error(f"Помилка закриття посту: {e}")
    
    async def view_stories(self, page: Page, target: str, account_username: str, count: int = 3):
        """Перегляд сторіс"""
        try:
            # Пошук кільця сторіс
            story_ring = await page.query_selector(self.selectors['stories']['story_ring'])
            
            if not story_ring:
                logging.info(f"У користувача {target} немає активних сторіс")
                return False
            
            # Відкриття сторіс
            await story_ring.click()
            await self.safe_sleep(random.uniform(2, 4))
            
            # Очікування завантаження сторіс
            await page.wait_for_selector(self.selectors['stories']['story_container'], timeout=5000)
            
            stories_viewed = 0
            
            for i in range(count):
                try:
                    # Затримка для перегляду
                    view_delay = random.uniform(*self.action_delays.get('view_story', [1, 3]))
                    await self.safe_sleep(view_delay)
                    
                    stories_viewed += 1
                    self.stats['successful_actions'] += 1
                    self.stats['total_actions'] += 1
                    
                    logging.info(f"Переглянуто сторіс {i+1} користувача {target}")
                    
                    # Перехід до наступної сторіс
                    if i < count - 1:
                        next_button = await page.query_selector(self.selectors['stories']['next_button'])
                        if next_button:
                            await next_button.click()
                            await self.safe_sleep(random.uniform(1, 2))
                        else:
                            # Немає більше сторіс
                            break
                
                except Exception as e:
                    logging.error(f"Помилка перегляду сторіс {i+1}: {e}")
                    break
            
            # Закриття сторіс
            await self.close_stories(page)
            
            logging.info(f"Переглянуто {stories_viewed} сторіс для {target}")
            return stories_viewed > 0
            
        except Exception as e:
            logging.error(f"Помилка перегляду сторіс для {target}: {e}")
            return False
    
    async def like_stories(self, page: Page, target: str, account_username: str):
        """Лайк сторіс"""
        try:
            # Пошук кільця сторіс
            story_ring = await page.query_selector(self.selectors['stories']['story_ring'])
            
            if not story_ring:
                logging.info(f"У користувача {target} немає активних сторіс")
                return False
            
            # Відкриття сторіс
            await story_ring.click()
            await self.safe_sleep(random.uniform(2, 4))
            
            # Лайк сторіс
            like_button = await page.query_selector(self.selectors['stories']['like_button'])
            if like_button:
                await like_button.click()
                await self.safe_sleep(random.uniform(1, 2))
                
                self.stats['successful_actions'] += 1
                self.stats['total_actions'] += 1
                
                logging.info(f"Лайкнуто сторіс користувача {target}")
                
                # Закриття сторіс
                await self.close_stories(page)
                return True
            
            # Закриття сторіс
            await self.close_stories(page)
            return False
            
        except Exception as e:
            logging.error(f"Помилка лайку сторіс для {target}: {e}")
            return False
    
    async def reply_to_stories(self, page: Page, target: str, account_username: str, texts: List[str]):
        """Відповідь на сторіс"""
        try:
            if not texts:
                logging.warning("Немає текстів для відповіді на сторіс")
                return False
            
            # Пошук кільця сторіс
            story_ring = await page.query_selector(self.selectors['stories']['story_ring'])
            
            if not story_ring:
                logging.info(f"У користувача {target} немає активних сторіс")
                return False
            
            # Відкриття сторіс
            await story_ring.click()
            await self.safe_sleep(random.uniform(2, 4))
            
            # Пошук поля для відповіді
            reply_field = await page.query_selector(self.selectors['stories']['reply_field'])
            if not reply_field:
                await self.close_stories(page)
                return False
            
            # Вибір випадкового тексту
            message = random.choice(texts)
            
            # Введення повідомлення
            await reply_field.fill(message)
            await self.safe_sleep(random.uniform(1, 2))
            
            # Відправка
            send_button = await page.query_selector(self.selectors['stories']['send_button'])
            if send_button:
                await send_button.click()
                await self.safe_sleep(random.uniform(2, 4))
                
                self.stats['successful_actions'] += 1
                self.stats['total_actions'] += 1
                
                logging.info(f"Відповідь на сторіс {target}: {message}")
                
                # Закриття сторіс
                await self.close_stories(page)
                return True
            
            # Закриття сторіс
            await self.close_stories(page)
            return False
            
        except Exception as e:
            logging.error(f"Помилка відповіді на сторіс {target}: {e}")
            return False
    
    async def send_direct_message(self, page: Page, target: str, account_username: str, texts: List[str]):
        """Відправка приватного повідомлення"""
        try:
            if not texts:
                logging.warning("Немає текстів для приватних повідомлень")
                return False
            
            # Перехід до директ
            await page.goto('https://www.instagram.com/direct/new/')
            await self.safe_sleep(random.uniform(2, 4))
            
            # Пошук користувача
            search_field = await page.query_selector(self.selectors['direct']['search_field'])
            if search_field:
                await search_field.fill(target)
                await self.safe_sleep(random.uniform(1, 2))
                
                # Вибір користувача зі списку
                user_result = await page.query_selector(f'text={target}')
                if user_result:
                    await user_result.click()
                    await self.safe_sleep(1)
                    
                    # Натискання Next
                    next_button = await page.query_selector('text=Next')
                    if next_button:
                        await next_button.click()
                        await self.safe_sleep(2)
                        
                        # Введення повідомлення
                        message_field = await page.query_selector(self.selectors['direct']['message_field'])
                        if message_field:
                            message = random.choice(texts)
                            await message_field.fill(message)
                            await self.safe_sleep(random.uniform(1, 2))
                            
                            # Відправка
                            send_button = await page.query_selector(self.selectors['direct']['send_button'])
                            if send_button:
                                await send_button.click()
                                await self.safe_sleep(random.uniform(2, 4))
                                
                                self.stats['successful_actions'] += 1
                                self.stats['total_actions'] += 1
                                
                                logging.info(f"Відправлено DM до {target}: {message}")
                                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка відправки DM до {target}: {e}")
            self.stats['failed_actions'] += 1
            self.stats['total_actions'] += 1
            return False
    
    async def close_stories(self, page: Page):
        """Закриття сторіс"""
        try:
            # Спроба натиснути кнопку закриття
            close_button = await page.query_selector(self.selectors['stories']['close_story'])
            if close_button:
                await close_button.click()
            else:
                # Альтернативний спосіб - Escape
                await page.keyboard.press('Escape')
            
            await self.safe_sleep(1)
            
        except Exception as e:
            logging.error(f"Помилка закриття сторіс: {e}")
    
    async def safe_sleep(self, duration: float):
        """Безпечна затримка з перевіркою стану"""
        start_time = time.time()
        while time.time() - start_time < duration:
            if not self.running:
                break
            
            while self.paused:
                await asyncio.sleep(0.1)
            
            await asyncio.sleep(0.1)
    
    def stop(self):
        """Зупинка автоматизації"""
        self.running = False
    
    def pause(self):
        """Пауза автоматизації"""
        self.paused = True
    
    def resume(self):
        """Продовження автоматизації"""
        self.paused = False
    
    def get_stats(self) -> Dict:
        """Отримання статистики"""
        stats = self.stats.copy()
        if stats['start_time']:
            stats['duration'] = (datetime.now() - stats['start_time']).total_seconds()
        return stats


class MultiWorkerManager:
    """Менеджер для координації роботи кількох воркерів"""
    
    def __init__(self):
        self.workers = []
        self.running = False
        self.paused = False
        self.config = None
        self.status_callback = None
    
    def start_automation(self, config: Dict[str, Any], status_callback: Callable = None):
        """Запуск мультиворкер автоматизації"""
        self.config = config
        self.status_callback = status_callback
        self.running = True
        self.paused = False
        
        # Запуск в окремому потоці
        import threading
        thread = threading.Thread(target=self._run_automation_sync, daemon=True)
        thread.start()
    
    def _run_automation_sync(self):
        """Синхронний запуск автоматизації"""
        try:
            # Створення нового event loop для потоку
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запуск асинхронної автоматизації
            loop.run_until_complete(self._run_automation_async())
            
        except Exception as e:
            logging.error(f"Помилка мультиворкер автоматизації: {e}")
        finally:
            loop.close()
    
    async def _run_automation_async(self):
        """Асинхронний запуск автоматизації"""
        try:
            accounts = self.config['accounts']
            targets = self.config['targets']
            action_chain = self.config['action_chain']
            texts = self.config['texts']
            workers_count = self.config['workers_count']
            delay_minutes = self.config['delay_minutes']
            mode = self.config['mode']
            
            # Розподіл акаунтів між воркерами
            account_chunks = self._distribute_accounts(accounts, workers_count)
            
            # Створення та запуск воркерів
            tasks = []
            for worker_id, account_chunk in enumerate(account_chunks):
                if account_chunk:  # Якщо є акаунти для воркера
                    task = asyncio.create_task(
                        self._worker_process(
                            worker_id, account_chunk, targets, 
                            action_chain, texts, delay_minutes, mode
                        )
                    )
                    tasks.append(task)
            
            # Очікування завершення всіх воркерів
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logging.info("Мультиворкер автоматизація завершена")
            
        except Exception as e:
            logging.error(f"Помилка асинхронної автоматизації: {e}")
    
    def _distribute_accounts(self, accounts: List[Dict], num_workers: int) -> List[List[Dict]]:
        """Розподіл акаунтів між воркерами"""
        if not accounts:
            return [[] for _ in range(num_workers)]
        
        chunks = []
        chunk_size = len(accounts) // num_workers
        remainder = len(accounts) % num_workers
        
        start = 0
        for i in range(num_workers):
            end = start + chunk_size + (1 if i < remainder else 0)
            if start < len(accounts):
                chunks.append(accounts[start:end])
            else:
                chunks.append([])
            start = end
        
        return chunks
    
    async def _worker_process(self, worker_id: int, accounts: List[Dict], targets: List[str],
                            action_chain: List[Dict], texts: Dict[str, List[str]], 
                            delay_minutes: int, mode: str):
        """Процес одного воркера"""
        try:
            logging.info(f"Воркер {worker_id} запущено з {len(accounts)} акаунтами")
            
            # Створення автоматизації для воркера
            automation_config = {
                'browser_settings': self.config['browser_settings'],
                'selectors': BotConfig().get_selectors(),
                'action_delays': BotConfig().get_action_delays(),
                'safety_limits': BotConfig().get_safety_limits()
            }
            
            async with InstagramAutomation(automation_config) as automation:
                automation.running = True
                
                for account in accounts:
                    if not self.running:
                        break
                    
                    while self.paused:
                        await asyncio.sleep(1)
                    
                    try:
                        # Запуск автоматизації для акаунту
                        stats = await automation.run_account_automation(
                            account, targets, action_chain, texts, 
                            worker_id, self.status_callback
                        )
                        
                        # Затримка між акаунтами
                        if account != accounts[-1]:  # Не останній акаунт
                            delay_seconds = delay_minutes * 60
                            await automation.safe_sleep(delay_seconds)
                    
                    except Exception as e:
                        logging.error(f"Помилка обробки акаунту воркером {worker_id}: {e}")
                        continue
            
            logging.info(f"Воркер {worker_id} завершено")
            
        except Exception as e:
            logging.error(f"Помилка воркера {worker_id}: {e}")
        
        finally:
            if self.status_callback:
                self.status_callback(worker_id, 'idle')
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        self.running = False
        self.paused = False
    
    def pause_automation(self):
        """Пауза автоматизації"""
        self.paused = True
    
    def resume_automation(self):
        """Продовження автоматизації"""
        self.paused = False
    
    def is_running(self) -> bool:
        """Перевірка чи працює автоматизація"""
        return self.running


# Експорт основних класів
__all__ = ['InstagramAutomation', 'MultiWorkerManager']