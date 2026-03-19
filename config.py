# =============================================
#  BOT SOZLAMALARI - config.py
#  Bu faylda barcha sozlamalar joylashgan
# =============================================

# BotFather dan olingan token
BOT_TOKEN = "8658574224:AAHicI9RzMWqRIsszw9iCRYgwKUfizNkCxs"

# Admin Telegram ID lari (bir nechta bo'lishi mumkin)
ADMIN_IDS = [7988379865 , 8399862833]  # O'z Telegram ID ingizni kiriting

# To'lov provider tokenlari (BotFather -> Payments dan olinadi)
CLICK_TOKEN = "YOUR_CLICK_PROVIDER_TOKEN"
PAYME_TOKEN = "YOUR_PAYME_PROVIDER_TOKEN"

# Mukofot sozlamalari
MIN_SCORE_FOR_REWARD = 90      # % - mukofot uchun minimal ball
REWARD_AMOUNT_UZS = 10000      # so'm - mukofot miqdori

# Database fayl nomi
DB_NAME = "students_bot.db"

# Kunlik test vaqti (soat:minut)
DAILY_TEST_TIME = "09:00"

# Test sozlamalari
TEST_SIZES = [10, 20, 30]      # Savol soni variantlari
DAILY_TEST_SIZE = 5            # Kunlik mini-test savollari

# Emoji lari
EMOJI = {
    "book": "📚",
    "test": "📝",
    "stats": "📊",
    "daily": "☀️",
    "admin": "⚙️",
    "correct": "✅",
    "wrong": "❌",
    "money": "💰",
    "fire": "🔥",
    "medal": "🏅",
    "crown": "👑",
    "chart": "📈",
}
