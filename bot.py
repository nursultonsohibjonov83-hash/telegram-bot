# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes)
from config import BOT_TOKEN, ADMIN_IDS, MIN_SCORE_FOR_REWARD, REWARD_AMOUNT_UZS, TEST_SIZES, DAILY_TEST_SIZE
import database as db
from questions import load_sample_questions

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

(MENU, SELECT_SUBJECT, SELECT_SIZE, ANSWERING, DAILY_ANSWERING,
 ADMIN_MENU, ADMIN_ADD_SUBJECT, ADMIN_ADD_QUESTION,
 ADMIN_ADD_A, ADMIN_ADD_B, ADMIN_ADD_C, ADMIN_ADD_D, ADMIN_ADD_ANSWER,
 ADMIN_DEL_SUBJECT, ADMIN_DEL_QUESTION,
 REWARD_METHOD, REWARD_PHONE, BROADCAST,
 REGISTER_NAME, REGISTER_GROUP,
 ADMIN_ADD_BOOK_NAME, ADMIN_ADD_BOOK_LINK, ADMIN_ADD_BOOK_PDF,
 ADMIN_SET_MIN_SCORE, ADMIN_SET_REWARD) = range(25)

def is_admin(uid): return uid in ADMIN_IDS

def main_kb():
    return ReplyKeyboardMarkup([
        ["📝 Test boshlash",      "☀️ Kunlik mini-test"],
        ["📊 Mening statistikam", "🏆 Reyting"],
        ["🎲 Random test",        "📖 Kitoblar"]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["➕ Savol qo'shish",   "📋 Savollar ro'yxati"],
        ["🗑 Savol o'chirish",   "📚 Fan o'chirish"],
        ["👥 Foydalanuvchilar", "💰 Mukofot so'rovlar"],
        ["📖 Kitob qo'shish",   "📚 Kitoblar ro'yxati"],
        ["⚙️ Yutuq sozlamalari", "📢 Xabar yuborish"],
        ["⬅️ Orqaga"]
    ], resize_keyboard=True)

def back_kb():
    return ReplyKeyboardMarkup([["⬅️ Orqaga"]], resize_keyboard=True)

def subject_kb(subs):
    rows = [[s] for s in subs]
    rows.append(["⬅️ Orqaga"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def size_kb():
    return ReplyKeyboardMarkup(
        [[f"📝 {n} ta savol" for n in TEST_SIZES], ["⬅️ Orqaga"]],
        resize_keyboard=True)

def answer_inline_kb(q_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("A", callback_data=f"ans:{q_id}:A"),
        InlineKeyboardButton("B", callback_data=f"ans:{q_id}:B"),
        InlineKeyboardButton("C", callback_data=f"ans:{q_id}:C"),
        InlineKeyboardButton("D", callback_data=f"ans:{q_id}:D"),
    ], [
        InlineKeyboardButton("⬅️ Oldingi", callback_data=f"ans:{q_id}:BACK"),
        InlineKeyboardButton("❌ To'xtatish", callback_data=f"ans:{q_id}:STOP"),
    ]])

def badge(s):
    if s >= 90: return "👑 A'lo"
    if s >= 70: return "🏅 Yaxshi"
    if s >= 50: return "👍 Qoniqarli"
    return "📌 Ko'proq mashq qiling"

# ============================================================
# RO'YXATDAN O'TISH
# ============================================================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.add_user(u.id, u.username or "", u.full_name)
    ctx.user_data.clear()

    user = db.get_user(u.id)
    if not user or not user["real_name"]:
        await update.message.reply_text(
            f"👋 Salom, *{u.first_name}*!\n\n"
            f"🎓 *Tibbiyot Test Botiga xush kelibsiz!*\n\n"
            f"Boshlash uchun ro'yxatdan o'ting 👇\n\n"
            f"📝 *Ism va familiyangizni* kiriting:\n"
            f"_(Misol: Abdullayev Jasur)_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return REGISTER_NAME

    name = user["real_name"] or u.first_name
    group = user["group_name"] or ""
    grp_txt = f"\n🏫 Guruh: *{group}*" if group else ""
    await update.message.reply_text(
        f"👋 Salom, *{name}*!{grp_txt}\n\n"
        f"🎓 *Tibbiyot Test Botiga xush kelibsiz!*\n\n"
        f"Bu bot orqali siz:\n"
        f"📚 Tibbiyot fanlaridan test yechishingiz\n"
        f"📊 Natijalaringizni kuzatishingiz\n"
        f"🏆 Reyting jadvalida birinchi bo'lishingiz\n"
        f"💰 Yuqori ball uchun *mukofot* olishingiz mumkin!\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi menyudan tanlang 👇",
        parse_mode="Markdown", reply_markup=main_kb()
    )
    if is_admin(u.id):
        await update.message.reply_text("⚙️ Admin panel: /admin")
    return MENU

async def register_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("❗ Ism familiya kamida 3 ta harf bo'lsin!")
        return REGISTER_NAME
    ctx.user_data['reg_name'] = name
    await update.message.reply_text(
        f"✅ Ism: *{name}*\n\n"
        f"🏫 *Guruh raqamingizni* kiriting:\n"
        f"_(Misol: 301-guruh)_",
        parse_mode="Markdown"
    )
    return REGISTER_GROUP

async def register_group(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    group = update.message.text.strip()
    name = ctx.user_data.get('reg_name', '')
    uid = update.effective_user.id
    db.update_user_profile(uid, name, group)
    await update.message.reply_text(
        f"🎉 *Ro'yxatdan o'tdingiz!*\n\n"
        f"👤 Ism: *{name}*\n"
        f"🏫 Guruh: *{group}*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi menyudan tanlang 👇",
        parse_mode="Markdown", reply_markup=main_kb()
    )
    if is_admin(uid):
        await update.message.reply_text("⚙️ Admin panel: /admin")
    ctx.user_data.clear()
    return MENU

# ============================================================
# ASOSIY MENU
# ============================================================

async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    uid = update.effective_user.id

    if "⬅️" in t:
        await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=main_kb())
        return MENU

    if "Test boshlash" in t:
        subs = db.get_subjects()
        if not subs:
            await update.message.reply_text("❗ Savollar bazasi bo'sh!")
            return MENU
        await update.message.reply_text("📚 *Fanni tanlang:*", parse_mode="Markdown", reply_markup=subject_kb(subs))
        ctx.user_data['mode'] = 'normal'
        return SELECT_SUBJECT

    if "Random test" in t:
        ctx.user_data['mode'] = 'random'
        ctx.user_data['subject'] = 'Aralash'
        await update.message.reply_text("🎲 *Random test!* Nechta savol?", parse_mode="Markdown", reply_markup=size_kb())
        return SELECT_SIZE

    if "Kunlik mini-test" in t:
        if db.daily_done(uid):
            await update.message.reply_text("✅ Bugungi testni yechdingiz!\n⏰ Ertaga keling.", reply_markup=main_kb())
            return MENU
        return await daily_start(update, ctx)

    if "Statistikam" in t:
        return await show_stats(update, ctx)

    if "Reyting" in t:
        return await show_leaderboard(update, ctx)

    if "Kitoblar" in t:
        return await show_books(update, ctx)

    return MENU

# ============================================================
# FAN VA SAVOL SONI
# ============================================================

async def select_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "⬅️" in t:
        ctx.user_data.clear()
        await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=main_kb())
        return MENU
    subs = db.get_subjects()
    if t not in subs:
        await update.message.reply_text("❗ Ro'yxatdan tanlang:", reply_markup=subject_kb(subs))
        return SELECT_SUBJECT
    ctx.user_data['subject'] = t
    await update.message.reply_text(f"✅ Fan: *{t}*\n\nNechta savol?", parse_mode="Markdown", reply_markup=size_kb())
    return SELECT_SIZE

async def select_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "⬅️" in t:
        if ctx.user_data.get('mode') == 'random':
            ctx.user_data.clear()
            await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=main_kb())
            return MENU
        subs = db.get_subjects()
        await update.message.reply_text("📚 *Fanni tanlang:*", parse_mode="Markdown", reply_markup=subject_kb(subs))
        return SELECT_SUBJECT

    size = None
    for n in TEST_SIZES:
        if str(n) in t: size = n; break
    if not size:
        await update.message.reply_text("❗ Qaytadan tanlang:", reply_markup=size_kb())
        return SELECT_SIZE

    subj = ctx.user_data.get('subject', 'Aralash')
    qs = db.get_questions(None if ctx.user_data.get('mode') == 'random' else subj, size)

    if not qs:
        await update.message.reply_text(f"❗ *{subj}* fanida yetarli savol yo'q.", parse_mode="Markdown", reply_markup=main_kb())
        return MENU

    ctx.user_data.update({'questions': qs, 'q_index': 0, 'correct': 0, 'answers': []})
    await update.message.reply_text(
        f"🚀 *Test boshlanmoqda!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📚 Fan: *{subj}*  |  ❓ *{len(qs)} savol*\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    await send_question(update, ctx)
    return ANSWERING

async def send_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    idx = ctx.user_data['q_index']
    qs = ctx.user_data['questions']
    q = qs[idx]
    total = len(qs)
    bar = "🟩" * idx + "⬜" * (total - idx)
    await update.message.reply_text(
        f"*Savol {idx+1}/{total}*\n{bar}\n\n"
        f"❓ *{q['question']}*\n\n"
        f"A)  {q['option_a']}\n"
        f"B)  {q['option_b']}\n"
        f"C)  {q['option_c']}\n"
        f"D)  {q['option_d']}",
        parse_mode="Markdown",
        reply_markup=answer_inline_kb(q['id'])
    )

async def inline_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    ans = parts[2]

    if ans == "STOP":
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text("⛔ *Test to'xtatildi.*", parse_mode="Markdown", reply_markup=main_kb())
        ctx.user_data.clear()
        return MENU

    if ans == "BACK":
        idx = ctx.user_data.get('q_index', 0)
        if idx == 0:
            await query.answer("Bu birinchi savol!", show_alert=True)
            return ANSWERING
        ctx.user_data['q_index'] -= 1
        if ctx.user_data['answers']:
            last = ctx.user_data['answers'].pop()
            if last == ctx.user_data['questions'][ctx.user_data['q_index']]['answer'].upper():
                ctx.user_data['correct'] -= 1
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text("⬅️ Oldingi savolga qaytdingiz!")
        class FU:
            def __init__(self, m): self.message = m
        await send_question(FU(query.message), ctx)
        return ANSWERING

    idx = ctx.user_data['q_index']
    q = ctx.user_data['questions'][idx]
    correct = q['answer'].upper()
    total = len(ctx.user_data['questions'])

    ctx.user_data['answers'].append(ans)
    ctx.user_data['q_index'] += 1

    def opt(letter, chosen, right):
        if letter == chosen and letter == right: return "🟩"
        if letter == chosen and letter != right: return "🟥"
        if letter == right: return "🟩"
        return "⬜"

    res = "To'g'ri!" if ans == correct else f"Noto'g'ri! To'g'ri: {correct}"
    result_txt = (
        f"*Savol {idx+1}/{total}*\n\n"
        f"❓ *{q['question']}*\n\n"
        f"{opt('A',ans,correct)} A)  {q['option_a']}\n"
        f"{opt('B',ans,correct)} B)  {q['option_b']}\n"
        f"{opt('C',ans,correct)} C)  {q['option_c']}\n"
        f"{opt('D',ans,correct)} D)  {q['option_d']}\n\n"
        f"{'✅' if ans==correct else '❌'} *{res}*"
    )

    if ans == correct:
        ctx.user_data['correct'] += 1

    await query.message.edit_text(result_txt, parse_mode="Markdown")

    if ctx.user_data['q_index'] >= total:
        return await finish_test(query.message, ctx, update.effective_user.id)

    class FU2:
        def __init__(self, m): self.message = m
    await send_question(FU2(query.message), ctx)
    return ANSWERING

async def finish_test(message, ctx, uid):
    correct = ctx.user_data['correct']
    total = len(ctx.user_data['questions'])
    score = round(correct / total * 100, 1)
    subj = ctx.user_data.get('subject', 'Aralash')

    db.save_result(uid, subj, total, correct, score)

    user = db.get_user(uid)
    name = user['real_name'] if user and user['real_name'] else "Talaba"
    group = user['group_name'] if user and user['group_name'] else ""
    name_line = f"👤 *{name}* | 🏫 {group}" if group else f"👤 *{name}*"

    stars = "⭐" * min(5, int(score / 20))
    result = (
        f"🏁 *Test yakunlandi!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{name_line}\n"
        f"📚 Fan: *{subj}*\n"
        f"✅ To'g'ri: *{correct}/{total}*\n"
        f"📊 Ball: *{score}%*\n"
        f"🏅 Baho: *{badge(score)}*\n"
        f"{stars}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    if score >= db.get_setting('min_score', MIN_SCORE_FOR_REWARD) and not db.already_claimed_reward(uid, subj):
        reward_amt = db.get_setting('reward_amount', REWARD_AMOUNT_UZS)
        result += f"\n\n🎉 *{score}%! Mukofot olasiz!*\n💰 *{reward_amt:,} so'm*"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"💰 {db.get_setting('reward_amount', REWARD_AMOUNT_UZS):,} so'm olish", callback_data=f"reward:{subj}:{score}")
        ]])
        await message.reply_text(result, parse_mode="Markdown", reply_markup=kb)
    else:
        if score < 60:
            result += f"\n\n💪 *{db.get_setting('min_score', MIN_SCORE_FOR_REWARD)}%* ball = mukofot!"
        await message.reply_text(result, parse_mode="Markdown", reply_markup=main_kb())

    ctx.user_data.clear()
    return MENU

# ============================================================
# KUNLIK TEST
# ============================================================

async def daily_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    qs = db.get_questions(None, DAILY_TEST_SIZE)
    if not qs:
        await update.message.reply_text("❗ Savollar yo'q.", reply_markup=main_kb())
        return MENU
    ctx.user_data.update({'dq': qs, 'di': 0, 'dc': 0})
    await update.message.reply_text(
        f"☀️ *Kunlik Mini-Test!*\n━━━━━━━━━━━━━━━━━━\n📝 *{DAILY_TEST_SIZE} ta savol*\n🚀 Boshlaylik!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["A","B"],["C","D"],["❌ To'xtatish"]], resize_keyboard=True)
    )
    await send_daily_q(update, ctx)
    return DAILY_ANSWERING

async def send_daily_q(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    idx = ctx.user_data['di']
    q = ctx.user_data['dq'][idx]
    await update.message.reply_text(
        f"☀️ *Savol {idx+1}/{DAILY_TEST_SIZE}*\n\n❓ *{q['question']}*\n\n"
        f"A)  {q['option_a']}\nB)  {q['option_b']}\nC)  {q['option_c']}\nD)  {q['option_d']}",
        parse_mode="Markdown"
    )

async def daily_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.upper()
    if "TO'XTATISH" in t or "TOXT" in t:
        ctx.user_data.clear()
        await update.message.reply_text("⛔ To'xtatildi.", reply_markup=main_kb())
        return MENU
    ans = None
    for k in ["A","B","C","D"]:
        if k in t: ans = k; break
    if not ans:
        await update.message.reply_text("❗ Faqat A, B, C yoki D!")
        return DAILY_ANSWERING

    q = ctx.user_data['dq'][ctx.user_data['di']]
    if ans == q['answer'].upper():
        ctx.user_data['dc'] += 1
        await update.message.reply_text("✅ *To'g'ri!*", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ *Noto'g'ri!* To'g'ri: *{q['answer']}*", parse_mode="Markdown")

    ctx.user_data['di'] += 1
    if ctx.user_data['di'] >= DAILY_TEST_SIZE:
        c = ctx.user_data['dc']
        s = round(c / DAILY_TEST_SIZE * 100, 1)
        db.mark_daily_done(update.effective_user.id, s)
        await update.message.reply_text(
            f"☀️ *Kunlik test tugadi!*\n━━━━━━━━━━━━━━━━━━\n✅ {c}/{DAILY_TEST_SIZE}  |  📊 {s}%\nErtaga ham keling! 👋",
            parse_mode="Markdown", reply_markup=main_kb()
        )
        ctx.user_data.clear()
        return MENU
    await send_daily_q(update, ctx)
    return DAILY_ANSWERING

# ============================================================
# STATISTIKA
# ============================================================

async def show_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = db.get_user_stats(uid)
    user = db.get_user(uid)

    if not st or not st['total_tests'] or st['total_tests'] == 0:
        await update.message.reply_text(
            "📊 *Mening statistikam*\n\n"
            "Siz hali birorta test yechmagansiz!\n"
            "📝 Test boshlash uchun menyudan tanlang.",
            parse_mode="Markdown", reply_markup=main_kb()
        )
        return MENU

    name = user['real_name'] if user and user['real_name'] else "Talaba"
    group = user['group_name'] if user and user['group_name'] else ""
    name_line = f"👤 *{name}* | 🏫 {group}" if group else f"👤 *{name}*"

    msg = (
        f"📊 *Mening statistikam*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{name_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 Jami testlar: *{st['total_tests']}*\n"
        f"✅ Jami to'g'ri: *{st['total_correct']}/{st['total_questions']}*\n"
        f"🏆 Eng yaxshi: *{st['best_score']}%*\n"
        f"📈 O'rtacha: *{st['avg_score']}%*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📚 *Fanlar bo'yicha:*\n"
    )
    for s in db.get_subjects():
        ss = db.get_subject_stats(uid, s)
        if ss and ss['cnt'] > 0:
            msg += f"  • *{s}*: {ss['cnt']} ta, eng yaxshi {ss['best_s']}%\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_kb())
    return MENU

# ============================================================
# REYTING
# ============================================================

async def show_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.get_leaderboard(10)
    if not rows:
        await update.message.reply_text("🏆 Reyting bo'sh. Birinchi bo'ling!", reply_markup=main_kb())
        return MENU

    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    msg = "🏆 *Top-10 Reyting*\n━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(rows):
        name = r['real_name'] or r['full_name'] or "Foydalanuvchi"
        group = r['group_name'] or ""
        grp = f" ({group})" if group else ""
        msg += (
            f"{medals[i]} *{i+1}. {name}{grp}*\n"
            f"   💯 {r['best']}%  |  📈 {r['avg']}%  |  📝 {r['cnt']} test\n\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_kb())
    return MENU

# ============================================================
# KITOBLAR (FOYDALANUVCHI UCHUN)
# ============================================================

async def show_books(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    books = db.get_books()
    if not books:
        await update.message.reply_text(
            "📚 Hozircha kitoblar yo'q.\nTez orada qo'shiladi!",
            reply_markup=main_kb()
        )
        return MENU

    await update.message.reply_text(
        f"📖 *Kitoblar — {len(books)} ta*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown", reply_markup=main_kb()
    )
    for i, b in enumerate(books):
        name = b['name'] or "Kitob"
        if b.get('file_id'):
            await update.message.reply_document(
                document=b['file_id'],
                caption=f"📗 *{name}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"📗 *{name}*\n🔗 {b['link']}",
                parse_mode="Markdown"
            )
    return MENU

# ============================================================
# MUKOFOT
# ============================================================

async def reward_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data.split(":")
    ctx.user_data['rsubj'] = d[1]
    ctx.user_data['rscore'] = d[2]
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("💳 Click",  callback_data="method:click"),
        InlineKeyboardButton("💳 Payme", callback_data="method:payme")
    ]])
    await q.message.reply_text(
        f"💰 *Mukofot: {REWARD_AMOUNT_UZS:,} so'm*\n\nTo'lov usuli:",
        parse_mode="Markdown", reply_markup=kb
    )
    return REWARD_METHOD

async def method_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data['rmethod'] = q.data.split(":")[1]
    await q.message.reply_text("📱 Telefon raqamingizni kiriting:\nMisol: +998901234567", reply_markup=ReplyKeyboardRemove())
    return REWARD_PHONE

async def reward_phone_h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    uid = update.effective_user.id
    subj = ctx.user_data.get('rsubj','')
    score = ctx.user_data.get('rscore','')
    method = ctx.user_data.get('rmethod','')

    db.add_reward_request(uid, score, subj, phone, method)
    user = db.get_user(uid)
    name = user['real_name'] if user and user['real_name'] else "Talaba"
    group = user['group_name'] if user and user['group_name'] else ""
    name_line = f"👤 *{name}* | 🏫 {group}" if group else f"👤 *{name}*"

    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(aid,
                f"🔔 *Yangi mukofot so'rovi!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{name_line}\n"
                f"📚 Fan: *{subj}*  |  📊 Ball: *{score}%*\n"
                f"💳 {method.upper()}: `{phone}`\n"
                f"💰 *{REWARD_AMOUNT_UZS:,} so'm*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"/admin → 💰 Mukofot so'rovlar",
                parse_mode="Markdown"
            )
        except: pass

    await update.message.reply_text(
        f"✅ *So'rov qabul qilindi!*\n📱 {phone}\n⏳ 24 soat ichida to'lanadi.",
        parse_mode="Markdown", reply_markup=main_kb()
    )
    ctx.user_data.clear()
    return MENU

# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return MENU
    users = db.get_all_users()
    qc = db.get_questions_count()
    rw = db.get_pending_rewards()
    books = db.get_books()
    await update.message.reply_text(
        f"⚙️ *Admin Panel*\n━━━━━━━━━━━━━━━━━━\n"
        f"👥 Foydalanuvchilar: *{len(users)}*\n"
        f"❓ Savollar: *{qc}*\n"
        f"📖 Kitoblar: *{len(books)}*\n"
        f"💰 Kutayotgan mukofotlar: *{len(rw)}*",
        parse_mode="Markdown", reply_markup=admin_kb()
    )
    return ADMIN_MENU

async def admin_menu_h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🏠", reply_markup=main_kb())
        return MENU

    if "⬅️" in t:
        await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=main_kb())
        return MENU

    if "Savol qo'shish" in t:
        subs = db.get_subjects()
        hint = "\n".join(f"• {s}" for s in subs) if subs else "Hali fan yo'q"
        await update.message.reply_text(
            f"📚 Fan nomini kiriting:\n{hint}\n\nYoki yangi fan nomi:",
            reply_markup=back_kb()
        )
        return ADMIN_ADD_SUBJECT

    if "Savollar ro'yxati" in t:
        subs = db.get_subjects()
        qc = db.get_questions_count()
        msg = f"📋 *Savollar: {qc} ta*\n━━━━━━━━━━━━━━━━━━\n"
        for s in subs:
            qs = db.get_questions(s)
            msg += f"📚 *{s}*: {len(qs)} ta\n"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=admin_kb())
        return ADMIN_MENU

    if "Savol o'chirish" in t:
        subs = db.get_subjects()
        if not subs:
            await update.message.reply_text("❗ Savollar yo'q.", reply_markup=admin_kb())
            return ADMIN_MENU
        await update.message.reply_text("🗑 Qaysi fandan?", reply_markup=subject_kb(subs))
        return ADMIN_DEL_SUBJECT

    if "Fan o'chirish" in t:
        subs = db.get_subjects()
        if not subs:
            await update.message.reply_text("❗ Fanlar yo'q.", reply_markup=admin_kb())
            return ADMIN_MENU
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🗑 {s}", callback_data=f"delsub:{s}")] for s in subs])
        await update.message.reply_text("📚 Qaysi fanni o'chirmoqchisiz?", reply_markup=kb)
        return ADMIN_MENU

    if "Foydalanuvchilar" in t:
        users = db.get_all_users()
        if not users:
            await update.message.reply_text("👥 Hali foydalanuvchilar yo'q.", reply_markup=admin_kb())
            return ADMIN_MENU
        msg = f"👥 *{len(users)} ta foydalanuvchi*\n━━━━━━━━━━━━━━━━━━\n"
        kb_rows = []
        for u in users:
            name = u['real_name'] or u['full_name'] or 'Nomsiz'
            group = u['group_name'] or "-"
            msg += f"• *{name}* | {group}\n"
            kb_rows.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"deluser:{u['user_id']}")])
        kb = InlineKeyboardMarkup(kb_rows[:10])
        await update.message.reply_text(msg[:4000], parse_mode="Markdown", reply_markup=admin_kb())
        await update.message.reply_text("Foydalanuvchi o'chirish:", reply_markup=kb)
        return ADMIN_MENU

    if "Mukofot" in t:
        rewards = db.get_pending_rewards()
        if not rewards:
            await update.message.reply_text("✅ Kutayotgan mukofot yo'q.", reply_markup=admin_kb())
            return ADMIN_MENU
        for r in rewards:
            rname = r['real_name'] or r['full_name'] or "Talaba"
            rgroup = r['group_name'] or ""
            rname_line = f"👤 *{rname}* ({rgroup})" if rgroup else f"👤 *{rname}*"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ To'landi", callback_data=f"paid:{r['id']}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{r['id']}")
            ]])
            await update.message.reply_text(
                f"💰 *So'rov #{r['id']}*\n━━━━━━━━━━━━━━━━━━\n"
                f"{rname_line}\n"
                f"📚 {r['subject']}  |  📊 {r['score']}%\n"
                f"💳 {r['method'].upper()}: `{r['phone']}`\n"
                f"💰 *{REWARD_AMOUNT_UZS:,} so'm*",
                parse_mode="Markdown", reply_markup=kb
            )
        return ADMIN_MENU

    if "Kitob qo'shish" in t:
        await update.message.reply_text(
            "📎 *PDF kitobni yuboring!*\n\n"
            "Pastdagi 📎 tugmasini bosib\n"
            "→ *Fayl* tanlang\n"
            "→ PDF ni yuboring!",
            parse_mode="Markdown", reply_markup=back_kb()
        )
        return ADMIN_ADD_BOOK_PDF

    if "Kitoblar ro'yxati" in t:
        books = db.get_books()
        if not books:
            await update.message.reply_text("📚 Hali kitoblar yo'q.", reply_markup=admin_kb())
            return ADMIN_MENU
        msg = f"📚 *Kitoblar: {len(books)} ta*\n━━━━━━━━━━━━━━━━━━\n"
        kb_rows = []
        for b in books:
            msg += f"📖 *{b['name']}*\n🔗 {b['link']}\n\n"
            kb_rows.append([InlineKeyboardButton(f"🗑 {b['name']}", callback_data=f"delbook:{b['id']}")])
        kb = InlineKeyboardMarkup(kb_rows)
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=admin_kb())
        await update.message.reply_text("Kitob o'chirish:", reply_markup=kb)
        return ADMIN_MENU

    if "Yutuq sozlamalari" in t:
        return await admin_settings(update, ctx)

    if "Xabar yuborish" in t:
        await update.message.reply_text("📢 Xabar matnini kiriting:", reply_markup=back_kb())
        return BROADCAST

    return ADMIN_MENU


# ---- Yutuq sozlamalari ----
async def admin_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    min_score = db.get_setting('min_score', 90)
    reward = db.get_setting('reward_amount', 10000)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎯 Minimal ball: {min_score}%", callback_data="set:min_score")],
        [InlineKeyboardButton(f"💰 Mukofot: {reward:,} so'm", callback_data="set:reward")],
    ])
    await update.message.reply_text(
        f"⚙️ *Yutuq sozlamalari*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Minimal ball: *{min_score}%*\n"
        f"💰 Mukofot miqdori: *{reward:,} so'm*\n\n"
        f"O'zgartirish uchun bosing:",
        parse_mode="Markdown", reply_markup=kb
    )
    return ADMIN_MENU

async def settings_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    setting = q.data.split(":")[1]
    ctx.user_data['setting_key'] = setting
    if setting == 'min_score':
        await q.message.reply_text(
            "🎯 Yangi minimal ball foizini kiriting:\nMisol: 85",
            reply_markup=back_kb()
        )
        return ADMIN_SET_MIN_SCORE
    elif setting == 'reward':
        await q.message.reply_text(
            "💰 Yangi mukofot miqdorini kiriting (so'm):\nMisol: 15000",
            reply_markup=back_kb()
        )
        return ADMIN_SET_REWARD

async def admin_set_min_score(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    try:
        val = int(update.message.text.strip())
        if not 1 <= val <= 100:
            await update.message.reply_text("❗ 1 dan 100 gacha son kiriting!")
            return ADMIN_SET_MIN_SCORE
        db.save_setting('min_score', val)
        await update.message.reply_text(
            f"✅ Minimal ball: *{val}%* ga o'zgartirildi!",
            parse_mode="Markdown", reply_markup=admin_kb()
        )
    except:
        await update.message.reply_text("❗ Faqat son kiriting! Misol: 85")
        return ADMIN_SET_MIN_SCORE
    return ADMIN_MENU

async def admin_set_reward(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    try:
        val = int(update.message.text.strip())
        db.save_setting('reward_amount', val)
        await update.message.reply_text(
            f"✅ Mukofot miqdori: *{val:,} so'm* ga o'zgartirildi!",
            parse_mode="Markdown", reply_markup=admin_kb()
        )
    except:
        await update.message.reply_text("❗ Faqat son kiriting! Misol: 15000")
        return ADMIN_SET_REWARD
    return ADMIN_MENU

# ---- Kitob qo'shish ----
async def admin_add_book_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    ctx.user_data['book_name'] = update.message.text.strip()
    await update.message.reply_text(
        f"📎 *PDF faylni yuboring!*\n\n"
        f"Pastdagi 📎 tugmasini bosib\n"
        f"→ *Fayl* tanlang\n"
        f"→ PDF ni yuboring!",
        parse_mode="Markdown", reply_markup=back_kb()
    )
    return ADMIN_ADD_BOOK_PDF

async def admin_add_book_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("📖 Kitob nomi kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_BOOK_NAME
    # Skip link, ask for PDF directly
    await update.message.reply_text(
        "📎 *PDF faylni yuboring:*\n\n"
        "Telegram da 📎 tugmasini bosib → *Fayl* tanlang → PDF ni yuboring!",
        parse_mode="Markdown",
        reply_markup=back_kb()
    )
    return ADMIN_ADD_BOOK_PDF

async def admin_add_book_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text and "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU

    if update.message.document:
        file_id = update.message.document.file_id
        # Fayl nomini kitob nomi sifatida ishlatamiz
        file_name = update.message.document.file_name or "Kitob"
        # .pdf kengaytmasini olib tashlaymiz
        name = file_name.replace('.pdf', '').replace('.PDF', '').strip()
        db.add_book(name, '-', update.effective_user.id, file_id)
        await update.message.reply_text(
            f"✅ *Kitob qo'shildi!*\n📖 *{name}*\n📎 PDF muvaffaqiyatli yuklandi!",
            parse_mode="Markdown", reply_markup=admin_kb()
        )
        return ADMIN_MENU
    else:
        await update.message.reply_text(
            "❗ PDF fayl yuboring!\n\n"
            "📎 tugmasini bosing → *Fayl* tanlang → PDF ni yuboring:",
            parse_mode="Markdown"
        )
        return ADMIN_ADD_BOOK_PDF

# ---- Callbacks ----
async def del_user_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split(":")[1])
    db.block_user(uid)
    await q.message.edit_text(q.message.text + "\n\n✅ Bloklandi!")

async def del_subject_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    subj = q.data.split(":", 1)[1]
    conn = db.get_conn()
    conn.execute('DELETE FROM questions WHERE subject=?', (subj,))
    conn.commit()
    conn.close()
    await q.message.edit_text(f"✅ *{subj}* o'chirildi!", parse_mode="Markdown")

async def del_book_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    book_id = int(q.data.split(":")[1])
    db.delete_book(book_id)
    await q.message.edit_text("✅ Kitob o'chirildi!")

# ---- Savol o'chirish ----
async def admin_del_subject_h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "⬅️" in t:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    subs = db.get_subjects()
    if t not in subs:
        await update.message.reply_text("❗ Ro'yxatdan tanlang:", reply_markup=subject_kb(subs))
        return ADMIN_DEL_SUBJECT
    qs = db.get_questions(t)
    if not qs:
        await update.message.reply_text(f"❗ *{t}* da savol yo'q.", parse_mode="Markdown", reply_markup=admin_kb())
        return ADMIN_MENU
    msg = f"📋 *{t}* savollar:\n━━━━━━━━━━━━━━━━━━\n"
    for i, q in enumerate(qs[:20]):
        msg += f"{i+1}. {q['question'][:50]}...\n   ID: `{q['id']}`\n"
    if len(qs) > 20:
        msg += f"\n...va yana {len(qs)-20} ta"
    msg += "\n\nO'chirmoqchi bo'lgan savol *ID* sini kiriting:"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_kb())
    return ADMIN_DEL_QUESTION

async def admin_del_question_h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    try:
        q_id = int(update.message.text.strip())
        db.delete_question(q_id)
        await update.message.reply_text(f"✅ Savol *#{q_id}* o'chirildi!", parse_mode="Markdown", reply_markup=admin_kb())
    except:
        await update.message.reply_text("❗ Noto'g'ri ID:", reply_markup=back_kb())
        return ADMIN_DEL_QUESTION
    return ADMIN_MENU

# ---- Savol qo'shish ----
async def admin_add_subj(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    ctx.user_data['ns'] = update.message.text.strip()
    await update.message.reply_text("❓ Savol matnini kiriting:", reply_markup=back_kb())
    return ADMIN_ADD_QUESTION

async def admin_add_q(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("📚 Fan nomini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_SUBJECT
    ctx.user_data['nq'] = update.message.text.strip()
    await update.message.reply_text("A) variantini kiriting:", reply_markup=back_kb())
    return ADMIN_ADD_A

async def admin_add_a(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("❓ Savol matnini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_QUESTION
    ctx.user_data['na'] = update.message.text.strip()
    await update.message.reply_text("B) variantini kiriting:", reply_markup=back_kb())
    return ADMIN_ADD_B

async def admin_add_b(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("A) variantini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_A
    ctx.user_data['nb'] = update.message.text.strip()
    await update.message.reply_text("C) variantini kiriting:", reply_markup=back_kb())
    return ADMIN_ADD_C

async def admin_add_c(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("B) variantini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_B
    ctx.user_data['nc'] = update.message.text.strip()
    await update.message.reply_text("D) variantini kiriting:", reply_markup=back_kb())
    return ADMIN_ADD_D

async def admin_add_d(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("C) variantini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_C
    ctx.user_data['nd'] = update.message.text.strip()
    await update.message.reply_text(
        "✅ To'g'ri javob (A, B, C yoki D):",
        reply_markup=ReplyKeyboardMarkup([["A","B","C","D"],["⬅️ Orqaga"]], resize_keyboard=True)
    )
    return ADMIN_ADD_ANSWER

async def admin_add_ans(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("D) variantini kiriting:", reply_markup=back_kb())
        return ADMIN_ADD_D
    ans = update.message.text.strip().upper()
    if ans not in ["A","B","C","D"]:
        await update.message.reply_text("❗ Faqat A, B, C yoki D!")
        return ADMIN_ADD_ANSWER
    db.add_question(ctx.user_data['ns'], ctx.user_data['nq'],
                    ctx.user_data['na'], ctx.user_data['nb'],
                    ctx.user_data['nc'], ctx.user_data['nd'],
                    ans, update.effective_user.id)
    await update.message.reply_text(
        f"✅ *Savol qo'shildi!*\n📚 {ctx.user_data['ns']}\n❓ {ctx.user_data['nq']}\n✅ Javob: *{ans}*",
        parse_mode="Markdown", reply_markup=admin_kb()
    )
    for k in ['ns','nq','na','nb','nc','nd']:
        ctx.user_data.pop(k, None)
    return ADMIN_MENU

async def broadcast_h(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "⬅️" in update.message.text:
        await update.message.reply_text("⚙️ Admin panel:", reply_markup=admin_kb())
        return ADMIN_MENU
    users = db.get_all_users()
    sent = fail = 0
    await update.message.reply_text(f"📤 {len(users)} ta foydalanuvchiga yuborilmoqda...")
    for u in users:
        try:
            await ctx.bot.send_message(u['user_id'], f"📢 {update.message.text}")
            sent += 1
        except: fail += 1
    await update.message.reply_text(
        f"✅ Yuborildi: *{sent}*\n❌ Xato: *{fail}*",
        parse_mode="Markdown", reply_markup=admin_kb()
    )
    return ADMIN_MENU

async def payment_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    d = q.data.split(":")
    action, rid = d[0], int(d[1])
    if action == "paid":
        db.mark_reward_paid(rid)
        await q.message.edit_text(q.message.text + "\n\n✅ TO'LANDI!", parse_mode="Markdown")
        conn = db.get_conn()
        row = conn.execute('SELECT user_id FROM rewards WHERE id=?', (rid,)).fetchone()
        conn.close()
        if row:
            try:
                await ctx.bot.send_message(row['user_id'],
                    f"🎉 *Tabriklaymiz!*\n💰 *{REWARD_AMOUNT_UZS:,} so'm* to'landi!\nDavom eting! 🚀",
                    parse_mode="Markdown")
            except: pass
    elif action == "reject":
        await q.message.edit_text(q.message.text + "\n\n❌ RAD ETILDI", parse_mode="Markdown")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_kb())
    return MENU

async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Menyudan tanlang:", reply_markup=main_kb())

def main():
    db.init_db()
    load_sample_questions()
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("admin", admin_cmd),
        ],
        states={
            REGISTER_NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_GROUP:     [MessageHandler(filters.TEXT & ~filters.COMMAND, register_group)],
            MENU:               [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu),
                CommandHandler("admin", admin_cmd),
            ],
            SELECT_SUBJECT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, select_subject)],
            SELECT_SIZE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, select_size)],
            ANSWERING:          [CallbackQueryHandler(inline_answer, pattern="^ans:")],
            DAILY_ANSWERING:    [MessageHandler(filters.TEXT & ~filters.COMMAND, daily_answer)],
            ADMIN_MENU:         [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_h),
                CommandHandler("admin", admin_cmd),
            ],
            ADMIN_ADD_SUBJECT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_subj)],
            ADMIN_ADD_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_q)],
            ADMIN_ADD_A:        [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_a)],
            ADMIN_ADD_B:        [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_b)],
            ADMIN_ADD_C:        [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_c)],
            ADMIN_ADD_D:        [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_d)],
            ADMIN_ADD_ANSWER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_ans)],
            ADMIN_DEL_SUBJECT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_del_subject_h)],
            ADMIN_DEL_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_del_question_h)],
            ADMIN_ADD_BOOK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_book_name)],
            ADMIN_ADD_BOOK_LINK:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_book_link)],
            ADMIN_SET_MIN_SCORE:[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_min_score)],
            ADMIN_SET_REWARD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_reward)],
            ADMIN_ADD_BOOK_PDF: [
                MessageHandler(filters.Document.PDF, admin_add_book_pdf),
                CommandHandler("skip", lambda u,c: admin_add_book_pdf(u,c)),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_book_pdf),
            ],
            REWARD_METHOD:      [CallbackQueryHandler(method_cb, pattern="^method:")],
            REWARD_PHONE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_phone_h)],
            BROADCAST:          [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_h)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            CommandHandler("admin", admin_cmd),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(settings_cb,    pattern="^set:"))
    app.add_handler(CallbackQueryHandler(reward_cb,      pattern="^reward:"))
    app.add_handler(CallbackQueryHandler(payment_cb,     pattern="^(paid|reject):"))
    app.add_handler(CallbackQueryHandler(del_subject_cb, pattern="^delsub:"))
    app.add_handler(CallbackQueryHandler(del_user_cb,    pattern="^deluser:"))
    app.add_handler(CallbackQueryHandler(del_book_cb,    pattern="^delbook:"))
    app.add_handler(MessageHandler(filters.TEXT, unknown))

    print("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
