import telebot
from telebot import types
import config
from database import Database
from cryptopay import CryptoPay
import threading
import time
import os

# Инициализация
try:
    bot = telebot.TeleBot(config.BOT_TOKEN)
    # Проверяем токен
    bot_info = bot.get_me()
    print(f"✅ Бот успешно подключен: @{bot_info.username}")
except Exception as e:
    print(f"❌ Ошибка подключения к боту: {e}")
    print("Проверьте правильность токена в переменной окружения BOT_TOKEN или config.py")
    raise

db = Database()
crypto_pay = CryptoPay()

# Инициализация админов из config
if config.ADMIN_IDS:
    for admin_id in config.ADMIN_IDS:
        db.add_admin(admin_id)
        print(f"✅ Админ добавлен: {admin_id}")

# Состояния пользователей для обработки ввода
user_states = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def send_video_message(chat_id, video_filename, caption, reply_markup=None):
    """Отправить видео с подписью, если файла нет — fallback на текст."""
    video_path = os.path.join(BASE_DIR, video_filename)
    try:
        # Проверяем существование файла
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Используем InputFile для надежной отправки видео
        video_file = types.InputFile(video_path)
        bot.send_video(
            chat_id,
            video_file,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except FileNotFoundError:
        bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка при отправке видео {video_filename}: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode='HTML')

def get_text(user_id, key):
    """Получить текст на языке пользователя"""
    # Всегда русский язык
    return config.LANGUAGES['RU'].get(key, key)

def create_main_menu(user_id):
    """Создать главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    balance = db.get_balance(user_id)
    markup.add(types.KeyboardButton(f"💰 Баланс: {balance:.2f} USDT"))
    markup.add(types.KeyboardButton("💼 Мой кошелек"))
    markup.add(types.KeyboardButton("✨ Создать сделку"))
    if db.is_admin(user_id):
        markup.add(types.KeyboardButton("🔐 Админ-панель"))
    return markup


@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or None
        
        print(f"Получена команда /start от пользователя {user_id} (@{username})")
        
        # Проверяем, есть ли параметр в команде (ссылка на сделку)
        if message.text and len(message.text.split()) > 1:
            param = message.text.split()[1]
            if param.startswith('deal_'):
                try:
                    deal_id = int(param.split('_')[1])
                    handle_deal_link(message, deal_id)
                    return
                except Exception as e:
                    print(f"Ошибка при обработке ссылки на сделку: {e}")
        
        # Создаем пользователя если его нет (всегда русский язык)
        try:
            user = db.get_user(user_id)
            if not user:
                db.create_user(user_id, username, language='RU')
                print(f"Создан новый пользователь: {user_id}")
        except Exception as e:
            print(f"Ошибка при создании/получении пользователя: {e}")
        
        # Показываем красивое приветствие
        balance = db.get_balance(user_id)
        text = f"""
👋 <b>Добро пожаловать!</b>



💼 <b>Надёжный сервис для безопасных сделок!</b>

✨ <b>Автоматизировано, быстро и без лишних хлопот!</b>

🔹 <b>Комиссия за услугу: 0%</b>

🔹 <b>Поддержка 24/7: @anceIorren</b>

💌 <b>Теперь ваши сделки под защитой! 🛡</b>
        """
        
        send_video_message(message.chat.id, 'start.mp4', text, reply_markup=create_main_menu(user_id))
        print(f"Отправлено главное меню пользователю {user_id}")
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА в start_message: {e}")
        import traceback
        traceback.print_exc()
        try:
            bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуйте еще раз.")
        except:
            print("Не удалось отправить сообщение об ошибке")


@bot.message_handler(func=lambda message: '💰' in message.text and 'Баланс' in message.text)
def handle_balance_button(message):
    user_id = message.from_user.id
    balance = db.get_balance(user_id)
    
    text = f"""
💰 <b>Ваш баланс</b>

💵 <b>Текущий баланс:</b> {balance:.2f} USDT

💡 <b>Как пополнить:</b>
• Администратор может выдать баланс
• Получите средства после продажи сделки
    """
    
    bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')

@bot.message_handler(func=lambda message: '💼' in message.text and 'кошелек' in message.text.lower())
def handle_my_wallet(message):
    user_id = message.from_user.id
    
    # Получаем список кошельков
    wallets = db.get_user_wallets(user_id)
    
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    
    if wallets:
        # Показываем список кошельков
        for wallet in wallets:
            wallet_id, display_name, created_at = wallet
            button_text = f"💼 {display_name} (#{wallet_id})"
            markup.add(types.KeyboardButton(button_text))
    else:
        text = """
💼 <b>Мой кошелек</b>

📦 <b>У вас пока нет кошельков</b>

💡 <b>Создайте кошелек для хранения ваших средств</b>
        """
        markup.add(types.KeyboardButton("➕ Создать кошелек"))
        markup.add(types.KeyboardButton("🏠 Главное меню"))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
        return
    
    markup.add(types.KeyboardButton("➕ Создать кошелек"))
    markup.add(types.KeyboardButton("🏠 Главное меню"))
    
    text = f"""
💼 <b>Мой кошелек</b>

📦 <b>Ваши кошельки:</b> {len(wallets)}

Выберите кошелек, чтобы просмотреть детали и пополнить баланс, или создайте новый:
    """
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: '➕' in message.text and 'кошелек' in message.text.lower())
def handle_add_wallet(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"User_{user_id}"
    
    # Создаем кошелек с именем пользователя
    wallet_id = db.add_wallet(user_id, username)
    
    text = f"""
✅ <b>Кошелек создан успешно!</b>

💼 <b>Название:</b> {username}
🆔 <b>ID кошелька:</b> #{wallet_id}

💡 <b>Теперь вы можете использовать этот кошелек для хранения средств</b>
    """
    
    bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text.startswith('💼 ') and '(#' in message.text)
def handle_wallet_details(message):
    user_id = message.from_user.id
    text_parts = message.text
    
    try:
        start_index = text_parts.rfind('(#')
        end_index = text_parts.rfind(')')
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise ValueError("Invalid wallet format")
        wallet_id = int(text_parts[start_index + 2:end_index])
    except ValueError:
        bot.send_message(message.chat.id, "❌ Не удалось определить выбранный кошелек.", parse_mode='HTML')
        return
    
    wallet = db.get_wallet_by_id(wallet_id)
    if not wallet or wallet[1] != user_id:
        bot.send_message(message.chat.id, "❌ Кошелек не найден или вам не принадлежит.", parse_mode='HTML')
        return
    
    _, _, display_name, created_at = wallet
    balance = db.get_balance(user_id)
    
    text = f"""
💼 <b>Кошелек:</b> {display_name}
🆔 <b>ID кошелька:</b> #{wallet_id}
📅 <b>Создан:</b> {created_at}

💰 <b>Текущий баланс:</b> {balance:.2f} USDT

Нажмите кнопку ниже, чтобы создать счет и пополнить баланс через CryptoBot.
    """
    
    inline_markup = types.InlineKeyboardMarkup(row_width=1)
    inline_markup.add(types.InlineKeyboardButton("➕ Пополнить баланс", callback_data=f"wallet_topup_{wallet_id}"))
    inline_markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    
    bot.send_message(message.chat.id, text, reply_markup=inline_markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text in ['❌ Отмена', 'Назад', 'Back', '🏠 Главное меню'])
def handle_back(message):
    user_id = message.from_user.id
    
    # Очищаем состояние пользователя если он был в процессе создания сделки
    if user_id in user_states:
        del user_states[user_id]
    
    balance = db.get_balance(user_id)
    text = f"""
🏠 <b>Главное меню</b>

💰 <b>Баланс:</b> {balance:.2f} USDT

Выберите действие:
    """
    
    bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    user_id = message.from_user.id
    
    # Проверяем права админа
    if not db.is_admin(user_id):
        text = """
❌ <b>Доступ запрещен</b>

У вас нет прав доступа к админ-панели.
        """
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        return
    
    # Показываем админ-меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("➕ Выдать баланс"))
    markup.add(types.KeyboardButton("➖ Забрать баланс"))
    markup.add(types.KeyboardButton("🏠 Главное меню"))
    
    text = """
🔐 <b>Админ-панель</b>

⚙️ <b>Управление системой</b>

Выберите действие:
    """
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: '➕' in message.text and 'Выдать баланс' in message.text)
def handle_admin_give_balance(message):
    user_id = message.from_user.id
    
    if not db.is_admin(user_id):
        return
    
    user_states[user_id] = {'step': 'admin_give_user_id', 'action': 'give'}
    text = """
➕ <b>Выдача баланса</b>

👤 <b>Шаг 1:</b> Введите ID пользователя

💡 <b>Пример:</b> 123456789
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отмена"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: '➖' in message.text and 'Забрать баланс' in message.text)
def handle_admin_take_balance(message):
    user_id = message.from_user.id
    
    if not db.is_admin(user_id):
        return
    
    user_states[user_id] = {'step': 'admin_take_user_id', 'action': 'take'}
    text = """
➖ <b>Забор баланса</b>

👤 <b>Шаг 1:</b> Введите ID пользователя

💡 <b>Пример:</b> 123456789
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отмена"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: '🔐 Админ-панель' in message.text)
def handle_admin_panel_button(message):
    handle_admin(message)

@bot.message_handler(func=lambda message: '✨' in message.text and 'сделк' in message.text.lower())
def handle_create_deal(message):
    user_id = message.from_user.id
    
    # Устанавливаем состояние ожидания описания
    user_states[user_id] = {'step': 'waiting_description', 'deal_type': 'nft_gifts'}
    
    text = """
✨ <b>Создание новой сделки</b>

📝 <b>Шаг 1:</b> Опишите, что вы продаете

💡 <b>Пример:</b>
• NFT коллекция "Cool Art"
• Цифровой арт "Sunset"
• Игровой предмет "Legendary Sword"

Напишите описание вашего товара:
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отмена"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    
    # Проверяем, не нажата ли кнопка "Назад" во время создания сделки
    if message.text == get_text(user_id, 'back') or message.text in ['Назад', 'Back']:
        if user_id in user_states:
            del user_states[user_id]
        handle_back(message)
        return
    
    # Проверяем отмену
    if message.text in ['❌ Отмена', 'Назад']:
        handle_back(message)
        return
    
    # Проверяем состояние пользователя
    if user_id in user_states:
        state = user_states[user_id]
        
        if state.get('step') == 'topup_amount':
            try:
                amount = float(message.text.replace(',', '.'))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                text = """
❌ <b>Неверная сумма</b>

Введите число больше нуля.
💡 <b>Пример:</b> 10.5 или 100
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
            
            wallet_id = state.get('wallet_id')
            wallet = db.get_wallet_by_id(wallet_id) if wallet_id else None
            
            if not wallet or wallet[1] != user_id:
                del user_states[user_id]
                bot.send_message(message.chat.id, "❌ Кошелек не найден или вам не принадлежит.", parse_mode='HTML')
                return
            
            wallet_name = state.get('wallet_name') or wallet[2]
            description = f"Пополнение баланса {wallet_name} (#{wallet_id})"
            
            invoice_result = crypto_pay.create_invoice(
                amount=amount,
                currency='USDT',
                description=description
            )
            
            if invoice_result.get('success'):
                invoice_id = str(invoice_result.get('invoice_id'))
                invoice_url = invoice_result.get('invoice_url') or invoice_result.get('pay_url')
                
                topup_id = db.create_topup(
                    user_id=user_id,
                    wallet_id=wallet_id,
                    amount=amount,
                    invoice_id=invoice_id,
                    invoice_url=invoice_url
                )
                
                confirmation_text = f"""
✅ <b>Счет на пополнение создан!</b>

💼 <b>Кошелек:</b> {wallet_name} (#{wallet_id})
🆔 <b>ID пополнения:</b> #{topup_id}
💵 <b>Сумма:</b> {amount:.2f} USDT

🔗 <b>Оплатите счет через кнопку ниже.</b>
После оплаты средства автоматически поступят на ваш баланс.
                """
                
                inline_markup = types.InlineKeyboardMarkup(row_width=1)
                if invoice_url:
                    inline_markup.add(types.InlineKeyboardButton("💳 Оплатить через CryptoBot", url=invoice_url))
                inline_markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
                
                del user_states[user_id]
                
                bot.send_message(message.chat.id, confirmation_text, reply_markup=inline_markup, parse_mode='HTML')
                
                balance = db.get_balance(user_id)
                menu_text = f"""
🏠 <b>Главное меню</b>

💰 <b>Баланс:</b> {balance:.2f} USDT

Выберите действие:
                """
                bot.send_message(message.chat.id, menu_text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
            else:
                error_message = invoice_result.get('error', 'Unknown error')
                text = f"""
❌ <b>Не удалось создать счет.</b>

Причина: {error_message}

Попробуйте ввести сумму снова или нажмите "❌ Отмена".
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
            return
        
        # Обработка админ-панели
        if state.get('step') == 'admin_give_user_id':
            try:
                target_user_id = int(message.text)
                # Проверяем существование пользователя
                target_user = db.get_user(target_user_id)
                if not target_user:
                    text = """
❌ <b>Пользователь не найден</b>

Пользователь с таким ID не существует в системе.
                    """
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                state['target_user_id'] = target_user_id
                state['step'] = 'admin_give_amount'
                text = f"""
💵 <b>Введите сумму</b>

👤 <b>Пользователь:</b> {target_user_id}

💰 <b>Шаг 2:</b> Введите сумму в USDT

💡 <b>Пример:</b> 10.5 или 100
                """
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("❌ Отмена"))
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                return
            except ValueError:
                text = """
❌ <b>Неверный ID пользователя</b>

Введите числовой ID пользователя.
💡 <b>Пример:</b> 123456789
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
        
        elif state.get('step') == 'admin_give_amount':
            try:
                amount = float(message.text.replace(',', '.'))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                
                target_user_id = state['target_user_id']
                new_balance = db.add_balance(target_user_id, amount)
                
                text = f"""
✅ <b>Баланс выдан успешно!</b>

👤 <b>Пользователь:</b> {target_user_id}
💵 <b>Сумма:</b> {amount:.2f} USDT
💰 <b>Новый баланс:</b> {new_balance:.2f} USDT
                """
                
                del user_states[user_id]
                bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
                
                # Уведомляем пользователя
                try:
                    notify_text = f"""
💰 <b>Вам начислено {amount:.2f} USDT</b>

💵 <b>Ваш баланс:</b> {new_balance:.2f} USDT
                    """
                    bot.send_message(target_user_id, notify_text, parse_mode='HTML')
                except:
                    pass
                return
            except ValueError:
                text = """
❌ <b>Неверная сумма</b>

Введите число больше нуля.
💡 <b>Пример:</b> 10.5 или 100
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
        
        elif state.get('step') == 'admin_take_user_id':
            try:
                target_user_id = int(message.text)
                target_user = db.get_user(target_user_id)
                if not target_user:
                    text = """
❌ <b>Пользователь не найден</b>

Пользователь с таким ID не существует в системе.
                    """
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                state['target_user_id'] = target_user_id
                state['step'] = 'admin_take_amount'
                text = f"""
💵 <b>Введите сумму</b>

👤 <b>Пользователь:</b> {target_user_id}

💰 <b>Шаг 2:</b> Введите сумму в USDT

💡 <b>Пример:</b> 10.5 или 100
                """
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("❌ Отмена"))
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                return
            except ValueError:
                text = """
❌ <b>Неверный ID пользователя</b>

Введите числовой ID пользователя.
💡 <b>Пример:</b> 123456789
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
        
        elif state.get('step') == 'admin_take_amount':
            try:
                amount = float(message.text.replace(',', '.'))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                
                target_user_id = state['target_user_id']
                new_balance = db.subtract_balance(target_user_id, amount)
                
                if new_balance is None:
                    text = """
❌ <b>Недостаточно средств</b>

У пользователя недостаточно средств на балансе.
                    """
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                text = f"""
✅ <b>Баланс забран успешно!</b>

👤 <b>Пользователь:</b> {target_user_id}
💵 <b>Сумма:</b> {amount:.2f} USDT
💰 <b>Новый баланс:</b> {new_balance:.2f} USDT
                """
                
                del user_states[user_id]
                bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
                
                # Уведомляем пользователя
                try:
                    notify_text = f"""
💰 <b>С вашего баланса списано {amount:.2f} USDT</b>

💵 <b>Ваш баланс:</b> {new_balance:.2f} USDT
                    """
                    bot.send_message(target_user_id, notify_text, parse_mode='HTML')
                except:
                    pass
                return
            except ValueError:
                text = """
❌ <b>Неверная сумма</b>

Введите число больше нуля.
💡 <b>Пример:</b> 10.5 или 100
                """
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
        
        # Обработка создания сделки
        if state['step'] == 'waiting_description':
            # Сохраняем описание и просим цену
            state['description'] = message.text
            state['step'] = 'waiting_price'
            
            text = """
💵 <b>Установите цену</b>

📝 <b>Описание:</b> {description}

💰 <b>Шаг 2:</b> Введите цену в USDT

💡 <b>Пример:</b> 10.5 или 100
            """.format(description=state['description'])
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Отмена"))
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
            return
        
        elif state['step'] == 'waiting_price':
            # Пытаемся распарсить цену
            try:
                price = float(message.text.replace(',', '.'))
                
                if price <= 0:
                    raise ValueError("Price must be positive")
                
                # Создаем сделку в БД
                deal_id = db.create_deal(
                    creator_id=user_id,
                    deal_type=state['deal_type'],
                    description=state['description'],
                    price_usdt=price
                )
                
                # Создаем счет через CryptoPay
                invoice_result = crypto_pay.create_invoice(
                    amount=price,
                    currency='USDT',
                    description=state['description']
                )
                
                if invoice_result['success']:
                    # Обновляем сделку с информацией о счете
                    db.update_deal_invoice(
                        deal_id=deal_id,
                        invoice_id=str(invoice_result['invoice_id']),
                        invoice_url=invoice_result['invoice_url']
                    )
                    
                    # Генерируем ссылку на сделку
                    deal_link = f"https://t.me/{bot.get_me().username}?start=deal_{deal_id}"
                    
                    text = f"""
✅ <b>Сделка создана успешно!</b>

🆔 <b>ID сделки:</b> #{deal_id}
📝 <b>Описание:</b> {state['description']}
💵 <b>Цена:</b> {price:.2f} USDT

🔗 <b>Ссылка на сделку:</b>
<code>{deal_link}</code>

📤 <b>Отправьте эту ссылку покупателю!</b>
Он сможет перейти по ней и оплатить сделку.

💡 <b>Важно:</b> После оплаты средства автоматически поступят на ваш баланс.
                    """
                    
                    # Очищаем состояние
                    del user_states[user_id]
                    
                    send_video_message(message.chat.id, 'deal.mp4', text, reply_markup=create_main_menu(user_id))
                else:
                    text = f"❌ Ошибка при создании счета: {invoice_result.get('error', 'Unknown error')}"
                    bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id))
                    del user_states[user_id]
                
            except ValueError:
                text = "❌ Неверная цена! Введите число больше нуля.\n\n💡 Пример: 10.5 или 100"
                bot.send_message(message.chat.id, text)
                return
    
def handle_deal_link(message, deal_id):
    """Обработка перехода по ссылке на сделку - второй человек оплачивает"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Создаем пользователя если его нет
    user = db.get_user(user_id)
    if not user:
        db.create_user(user_id, username, language='RU')
    
    deal = db.get_deal(deal_id)
    
    if not deal:
        text = """
❌ <b>Сделка не найдена</b>

Возможные причины:
• Сделка была удалена
• Неверная ссылка
• Сделка не существует
        """
        bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
        return
    
    # Структура: (deal_id, creator_id, buyer_id, deal_type, description, price_usdt, invoice_id, invoice_url, status, created_at)
    creator_id = deal[1] if len(deal) > 1 else None
    buyer_id = deal[2] if len(deal) > 2 else None
    deal_type = deal[3] if len(deal) > 3 else None
    description = deal[4] if len(deal) > 4 else None
    price = deal[5] if len(deal) > 5 else 0
    invoice_id = deal[6] if len(deal) > 6 else None
    invoice_url = deal[7] if len(deal) > 7 else None
    status = deal[8] if len(deal) > 8 else 'pending'
    
    # Проверяем, не является ли пользователь создателем сделки
    if creator_id == user_id:
        text = f"""
⚠️ <b>Это ваша сделка!</b>

🆔 <b>ID сделки:</b> #{deal_id}
📝 <b>Описание:</b> {description}
💵 <b>Цена:</b> {price:.2f} USDT
📊 <b>Статус:</b> {status}

💡 <b>Отправьте эту ссылку покупателю для оплаты!</b>
        """
        bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
        return
    
    # Проверяем статус сделки
    if status == 'paid' or status == 'completed':
        text = """
✅ <b>Сделка уже оплачена</b>

Эта сделка была успешно оплачена ранее.
        """
        bot.send_message(message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')
        return
    
    # Второй человек (покупатель) может оплатить сделку
    balance = db.get_balance(user_id)
    
    text = f"""
💼 <b>Сделка #{deal_id}</b>

📝 <b>Описание:</b>
{description}

💵 <b>Цена:</b> {price:.2f} USDT
💰 <b>Ваш баланс:</b> {balance:.2f} USDT

{"✅ У вас достаточно средств для оплаты с баланса!" if balance >= price else "⚠️ Недостаточно средств на балансе. Используйте CryptoBot для оплаты."}

💡 <b>Выберите способ оплаты:</b>
    """
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка оплаты с баланса (если достаточно средств)
    if balance >= price:
        markup.add(types.InlineKeyboardButton("💳 Оплатить с баланса", callback_data=f"pay_balance_{deal_id}"))
    
    # Кнопка оплаты через CryptoBot
    if invoice_url:
        markup.add(types.InlineKeyboardButton("💵 Оплатить через CryptoBot", url=invoice_url))
    
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('wallet_topup_'))
def handle_wallet_topup(call):
    user_id = call.from_user.id
    try:
        wallet_id = int(call.data.split('_')[2])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "❌ Некорректный кошелек", show_alert=True)
        return
    
    wallet = db.get_wallet_by_id(wallet_id)
    if not wallet or wallet[1] != user_id:
        bot.answer_callback_query(call.id, "❌ Кошелек не найден", show_alert=True)
        return
    
    _, _, display_name, _ = wallet
    bot.answer_callback_query(call.id)
    
    user_states[user_id] = {
        'step': 'topup_amount',
        'wallet_id': wallet_id,
        'wallet_name': display_name
    }
    
    text = f"""
➕ <b>Пополнение баланса</b>

💼 <b>Кошелек:</b> {display_name} (#{wallet_id})

💰 <b>Введите сумму в USDT:</b>
💡 <b>Пример:</b> 10.5 или 100
    """
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отмена"))
    
    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_balance_'))
def handle_pay_balance(call):
    """Обработка оплаты сделки с баланса - второй человек оплачивает"""
    user_id = call.from_user.id
    deal_id = int(call.data.split('_')[2])
    
    deal = db.get_deal(deal_id)
    if not deal:
        bot.answer_callback_query(call.id, "❌ Сделка не найдена", show_alert=True)
        return
    
    # Структура: (deal_id, creator_id, buyer_id, deal_type, description, price_usdt, invoice_id, invoice_url, status, created_at)
    creator_id = deal[1] if len(deal) > 1 else None
    price = deal[5] if len(deal) > 5 else 0
    description = deal[4] if len(deal) > 4 else None
    status = deal[8] if len(deal) > 8 else 'pending'
    
    if status != 'pending':
        bot.answer_callback_query(call.id, "❌ Сделка уже оплачена", show_alert=True)
        return
    
    if creator_id == user_id:
        bot.answer_callback_query(call.id, "❌ Нельзя оплатить свою сделку", show_alert=True)
        return
    
    balance = db.get_balance(user_id)
    if balance < price:
        bot.answer_callback_query(call.id, "❌ Недостаточно средств на балансе", show_alert=True)
        return
    
    # Списываем средства с баланса покупателя (второго человека)
    new_balance = db.subtract_balance(user_id, price)
    
    # Начисляем средства создателю сделки
    db.add_balance(creator_id, price)
    
    # Обновляем статус сделки
    db.update_deal_status(deal_id, 'paid', buyer_id=user_id)
    
    bot.answer_callback_query(call.id, "✅ Сделка успешно оплачена!", show_alert=True)
    
    # Обновляем сообщение
    text = f"""
✅ <b>Сделка #{deal_id} оплачена!</b>

📝 <b>Товар:</b> {description}
💵 <b>Сумма:</b> {price:.2f} USDT

💰 <b>С вашего баланса списано:</b> {price:.2f} USDT
💵 <b>Ваш текущий баланс:</b> {new_balance:.2f} USDT

🎉 <b>Спасибо за покупку!</b>
    """
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    
    # Уведомляем создателя сделки
    try:
        creator_balance = db.get_balance(creator_id)
        notify_text = f"""
💰 <b>Сделка #{deal_id} оплачена!</b>

📝 <b>Товар:</b> {description}
💵 <b>Вам начислено:</b> {price:.2f} USDT

💰 <b>Ваш баланс:</b> {creator_balance:.2f} USDT

🎉 <b>Поздравляем с успешной продажей!</b>
        """
        bot.send_message(creator_id, notify_text, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка уведомления создателя: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def handle_main_menu_callback(call):
    """Обработка возврата в главное меню"""
    user_id = call.from_user.id
    balance = db.get_balance(user_id)
    
    text = f"""
🏠 <b>Главное меню</b>

💰 <b>Баланс:</b> {balance:.2f} USDT

Выберите действие:
    """
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=None, parse_mode='HTML')
    bot.send_message(call.message.chat.id, text, reply_markup=create_main_menu(user_id), parse_mode='HTML')

def check_pending_payments():
    """Периодическая проверка платежей через CryptoBot"""
    while True:
        try:
            time.sleep(30)  # Проверяем каждые 30 секунд
            
            # Получаем все pending сделки с invoice_id
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT deal_id, creator_id, invoice_id, price_usdt, status
                FROM deals
                WHERE status = 'pending' AND invoice_id IS NOT NULL AND invoice_id != ''
            ''')
            pending_deals = cursor.fetchall()
            conn.close()
            
            for deal in pending_deals:
                deal_id, creator_id, invoice_id, price, status = deal
                
                if not invoice_id:
                    continue
                
                # Проверяем статус счета
                invoice_status = crypto_pay.get_invoice_status(invoice_id)
                
                if invoice_status.get('success') and invoice_status.get('paid'):
                    # Платеж выполнен
                    # Обновляем статус сделки
                    db.update_deal_status(deal_id, 'paid')
                    
                    # Начисляем средства создателю
                    db.add_balance(creator_id, price)
                    
                    # Уведомляем создателя
                    try:
                        creator_lang = db.get_user_language(creator_id) or 'RU'
                        if creator_lang == 'RU':
                            notify_text = f"💰 Сделка #{deal_id} оплачена через CryptoBot!\n"
                            notify_text += f"Вам начислено: {price:.2f} USDT"
                        else:
                            notify_text = f"💰 Deal #{deal_id} paid via CryptoBot!\n"
                            notify_text += f"You received: {price:.2f} USDT"
                        bot.send_message(creator_id, notify_text)
                    except Exception as notify_error:
                        print(f"Ошибка уведомления создателя: {notify_error}")
            
            # Проверяем пополнения баланса
            pending_topups = db.get_pending_topups()
            for topup in pending_topups:
                topup_id, topup_user_id, wallet_id, amount, invoice_id = topup
                
                if not invoice_id:
                    continue
                
                invoice_status = crypto_pay.get_invoice_status(invoice_id)
                
                if invoice_status.get('success') and invoice_status.get('paid'):
                    if db.mark_topup_paid(topup_id):
                        new_balance = db.add_balance(topup_user_id, amount)
                        wallet = db.get_wallet_by_id(wallet_id) if wallet_id else None
                        wallet_name = wallet[2] if wallet else "Основной баланс"
                        wallet_suffix = f" (#{wallet_id})" if wallet_id else ""
                        
                        notify_text = f"""
💰 <b>Пополнение успешно!</b>

💼 <b>Кошелек:</b> {wallet_name}{wallet_suffix}
🆔 <b>ID пополнения:</b> #{topup_id}
💵 <b>Сумма:</b> {amount:.2f} USDT

💰 <b>Ваш текущий баланс:</b> {new_balance:.2f} USDT
                        """
                        try:
                            bot.send_message(topup_user_id, notify_text, parse_mode='HTML')
                        except Exception as notify_error:
                            print(f"Ошибка уведомления о пополнении: {notify_error}")
        except Exception as e:
            print(f"Ошибка при проверке платежей: {e}")
            time.sleep(60)  # Увеличиваем интервал при ошибке

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("🚀 Запуск бота...")
        print("=" * 50)
        print(f"Токен бота: {config.BOT_TOKEN[:20]}...")
        print(f"CryptoPay токен: {config.CRYPTOPAY_API_TOKEN[:20]}...")
        print(f"База данных: {config.DATABASE_NAME}")
        print("=" * 50)
        
        # Запускаем проверку платежей в отдельном потоке
        payment_thread = threading.Thread(target=check_pending_payments, daemon=True)
        payment_thread.start()
        print("✅ Проверка платежей запущена")
        print("✅ Бот готов к работе!")
        print("=" * 50)
        print("Ожидание сообщений...")
        print("=" * 50)
        
        bot.infinity_polling(none_stop=True, interval=0, timeout=20)
    except KeyboardInterrupt:
        print("\n⚠️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        print("\nПроверьте:")
        print("1. Правильность токена бота в config.py")
        print("2. Наличие интернет-соединения")
        print("3. Доступность Telegram API")

