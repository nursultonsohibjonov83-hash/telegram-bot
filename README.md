# 🎓 Talabalar Test Boti

Telegram orqali talabalarning imtihonga tayyorlanishi uchun bot.

---

## 📦 O'rnatish

### 1. Python o'rnatish
Python 3.10+ kerak: https://python.org

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Bot sozlash

`config.py` faylini oching va quyidagilarni o'zgartiring:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"    # BotFather dan olingan token
ADMIN_IDS = [123456789]         # Sizning Telegram ID ingiz
CLICK_TOKEN = "..."             # Click provider token (ixtiyoriy)
PAYME_TOKEN = "..."             # Payme provider token (ixtiyoriy)
```

### 4. Botni ishga tushirish
```bash
python bot.py
```

---

## 🔑 Token olish

### Bot Token:
1. Telegramda @BotFather ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Token oling → `config.py` ga kiriting

### Telegram ID olish:
1. @userinfobot ga `/start` yuboring
2. ID raqamingizni oling → `ADMIN_IDS` ga kiriting

### Click/Payme Token (mukofot uchun):
- Bu tokenlar to'lov orqali foydalanuvchidan pul olish uchun
- Bizning botda mukofot admin tomonidan qo'lda to'lanadi
- Hozircha bu tokenlar shart emas

---

## 🚀 Imkoniyatlar

| Funksiya | Tavsif |
|----------|--------|
| 📝 Test yechish | 10/20/30 savol, ABCD variantlar |
| 🎲 Random test | Turli fanlardan aralash |
| ☀️ Kunlik mini-test | Har kuni 5 savol |
| 📊 Statistika | Ball, eng yaxshi natija, o'rtacha |
| 🏆 Reyting | Top-10 o'quvchilar |
| 💰 Mukofot | 90%+ ball → Click/Payme orqali pul |
| ⚙️ Admin panel | Savol qo'shish, foydalanuvchilar, broadcast |

---

## 💰 Mukofot tizimi qanday ishlaydi?

1. Talaba 90% yoki undan yuqori ball oladi
2. Bot mukofot tugmasini ko'rsatadi
3. Talaba Click yoki Payme tanlaydi
4. Telefon raqamini kiritadi
5. **Admin Telegram ga xabar keladi**
6. Admin qo'lda to'lovni amalga oshiradi
7. Admin `/admin` → "Mukofot so'rovlar" → "✅ To'landi" bosadi
8. Talabaga avtomatik xabar ketadi

---

## 📱 Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni boshlash |
| `/admin` | Admin panel (faqat adminlar) |
| `/cancel` | Amalni bekor qilish |

---

## 📁 Fayl tuzilishi

```
telegram_bot/
├── bot.py          # Asosiy bot fayli
├── config.py       # Sozlamalar
├── database.py     # Ma'lumotlar bazasi
├── questions.py    # Savollar banki
├── requirements.txt
└── README.md
```

---

## ❓ Savollar qo'shish

**Admin panel orqali:**
1. `/admin` yuboring
2. "➕ Savol qo'shish" bosing
3. Fan, savol, A/B/C/D variantlar, to'g'ri javobni kiriting

**Namuna savollar** botni ishga tushirganda avtomatik yuklanadi (6 fan, 40+ savol).

---

## 🛠 Texnik talablar

- Python 3.10+
- Internet ulanish
- VPS yoki lokal kompyuter (24/7 ishlashi uchun VPS tavsiya etiladi)

---

## 💡 Kengaytirish imkoniyatlari

- [ ] AI yordamida yangi savol generatsiya
- [ ] Grafik statistika (chart)
- [ ] Vaqtli test (timer)
- [ ] Ko'p tilli qo'llab-quvvatlash
- [ ] To'liq avtomatik to'lov (Click API)
