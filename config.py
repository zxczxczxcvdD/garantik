import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = "8371254653:AAGn68VSqjTSvsDNkh4JSeeLar1gjphmkvg"

# CryptoPay API credentials
CRYPTOPAY_API_TOKEN = "487121:AAWizwT4RhpHC0JH5cXgy4Q8hLrUbfDSTaz"
CRYPTOPAY_API_URL = 'https://pay.crypt.bot/api'

# Admin user IDs (можно добавить через переменную окружения или вручную в БД)
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '7768260052').split(',') if x.strip()]

# Database
DATABASE_NAME = 'bot_database.db'

# Supported languages
LANGUAGES = {
    'RU': {
        'select_language': '🇷🇺 → Выберите язык бота прежде чем начать пользоваться.',
        'wallet_menu': '💰 Мой кошелёк\n\nВыберите ваш кошелёк из списка или добавьте новый:',
        'add_wallet': 'Добавить кошелек',
        'main_menu': 'Главное меню',
        'my_wallet': 'Мой кошелек',
        'create_deal': 'Создать сделку',
        'select_deal_type': 'Выберите тип сделки:',
        'nft_gifts': 'NFT Подарки',
        'enter_description': 'Напишите, что вы продаете:',
        'enter_price': 'Введите цену в USDT:',
        'deal_created': 'Сделка создана! Ссылка на сделку:',
        'payment_link': 'Счет для оплаты:',
        'payment_info': 'После оплаты средства поступят на ваш кошелек.',
        'invalid_price': 'Неверная цена. Введите число.',
        'back': 'Назад',
        'no_wallets': 'У вас пока нет кошельков.',
        'wallet_added': 'Кошелек успешно добавлен!',
        'admin_menu': '🔐 Админ-панель\n\nВыберите действие:',
        'admin_balance': '💰 Управление балансом',
        'admin_give_balance': '➕ Выдать баланс',
        'admin_take_balance': '➖ Забрать баланс',
        'admin_enter_user_id': 'Введите ID пользователя:',
        'admin_enter_amount': 'Введите сумму:',
        'admin_balance_given': 'Баланс выдан успешно!',
        'admin_balance_taken': 'Баланс забран успешно!',
        'admin_invalid_user': 'Пользователь не найден!',
        'admin_invalid_amount': 'Неверная сумма!',
        'admin_insufficient_balance': 'Недостаточно средств у пользователя!',
        'admin_access_denied': 'У вас нет доступа к админ-панели!',
        'deal_pay': '💳 Оплатить сделку',
        'deal_paid': 'Сделка оплачена!',
        'deal_payment_failed': 'Ошибка при оплате сделки.',
        'balance': 'Баланс',
        'your_balance': 'Ваш баланс:',
        'insufficient_funds': 'Недостаточно средств на балансе!',
    },
    'EN': {
        'select_language': '🇺🇸 → Choose the bot\'s language before you start using it.',
        'wallet_menu': '💰 My Wallet\n\nSelect your wallet from the list or add a new one:',
        'add_wallet': 'Add wallet',
        'main_menu': 'Main menu',
        'my_wallet': 'My Wallet',
        'create_deal': 'Create Deal',
        'select_deal_type': 'Select deal type:',
        'nft_gifts': 'NFT Gifts',
        'enter_description': 'Write what you are selling:',
        'enter_price': 'Enter price in USDT:',
        'deal_created': 'Deal created! Deal link:',
        'payment_link': 'Payment invoice:',
        'payment_info': 'After payment, funds will be credited to your wallet.',
        'invalid_price': 'Invalid price. Enter a number.',
        'back': 'Back',
        'no_wallets': 'You don\'t have any wallets yet.',
        'wallet_added': 'Wallet added successfully!',
        'admin_menu': '🔐 Admin Panel\n\nSelect an action:',
        'admin_balance': '💰 Balance Management',
        'admin_give_balance': '➕ Give Balance',
        'admin_take_balance': '➖ Take Balance',
        'admin_enter_user_id': 'Enter user ID:',
        'admin_enter_amount': 'Enter amount:',
        'admin_balance_given': 'Balance given successfully!',
        'admin_balance_taken': 'Balance taken successfully!',
        'admin_invalid_user': 'User not found!',
        'admin_invalid_amount': 'Invalid amount!',
        'admin_insufficient_balance': 'Insufficient user balance!',
        'admin_access_denied': 'You don\'t have access to admin panel!',
        'deal_pay': '💳 Pay Deal',
        'deal_paid': 'Deal paid!',
        'deal_payment_failed': 'Error paying for deal.',
        'balance': 'Balance',
        'your_balance': 'Your balance:',
        'insufficient_funds': 'Insufficient funds!',
    }
}

