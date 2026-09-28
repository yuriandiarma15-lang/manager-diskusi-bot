import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

GROUP_ID = int(
    os.getenv("GROUP_ID", "-1003949834371").strip()
)

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}

TIMEZONE = ZoneInfo("Asia/Jakarta")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("group_scheduler")


# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler(
    timezone=TIMEZONE
)


# =========================================================
# STATUS INTERNAL
# =========================================================

group_is_open = None


# =========================================================
# PERMISSION
# =========================================================

OPEN_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)

CLOSED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def admin_only(message: Message) -> bool:

    if message.from_user is None:
        return False

    if not is_admin(message.from_user.id):

        await message.answer(
            "⛔ Kamu tidak memiliki izin untuk menggunakan command ini."
        )

        return False

    return True


# =========================================================
# OPEN DISCUSSION
# =========================================================

async def open_discussion(send_message=True):

    global group_is_open

    try:

        await bot.set_chat_permissions(
            chat_id=GROUP_ID,
            permissions=OPEN_PERMISSIONS
        )

        group_is_open = True

        logger.info(
            "🟢 DISKUSI DIBUKA | GROUP_ID=%s",
            GROUP_ID
        )

        if send_message:

            await bot.send_message(
                GROUP_ID,
                """🟢 **DISKUSI TELAH DIBUKA**

Selamat malam teman-teman! 👋

Ruang diskusi resmi **AI Assistant Gold** telah dibuka.

Silakan berdiskusi, sharing analisa, pengalaman, dan insight seputar market bersama member lainnya.

Tetap jaga komunikasi yang baik, hindari spam, dan yang paling penting:

**Disiplin dalam setiap keputusan trading.** 📊

🔥 **LET'S DISCUSS & SHARE**""",
                parse_mode="Markdown"
            )

    except Exception as e:

        logger.exception(
            "❌ Gagal membuka diskusi: %s",
            e
        )


# =========================================================
# CLOSE DISCUSSION
# =========================================================

async def close_discussion(send_message=True):

    global group_is_open

    try:

        await bot.set_chat_permissions(
            chat_id=GROUP_ID,
            permissions=CLOSED_PERMISSIONS
        )

        group_is_open = False

        logger.info(
            "🔴 DISKUSI DITUTUP | GROUP_ID=%s",
            GROUP_ID
        )

        if send_message:

            await bot.send_message(
                GROUP_ID,
                """🔴 **DISKUSI KITA TUTUP DULU SEMENTARA**

Terima kasih teman-teman untuk diskusinya hari ini. 🙏

Kita tutup sementara dan tunggu sesi berikutnya **besok pukul 18.00 WIB**.

Tetap jaga **Money Management**, disiplin, dan jangan memaksakan entry.

**See you tomorrow! 👋**

🏆 **AI ASSISTANT GOLD**""",
                parse_mode="Markdown"
            )

    except Exception as e:

        logger.exception(
            "❌ Gagal menutup diskusi: %s",
            e
        )


# =========================================================
# REMINDER 5 MENIT SEBELUM BUKA
# =========================================================

async def opening_reminder():

    try:

        await bot.send_message(
            GROUP_ID,
            """🟡 **5 MENIT LAGI DISKUSI DIBUKA**

Halo teman-teman 👋

5 menit lagi, tepat pukul **18.00 WIB**, ruang diskusi akan kita buka kembali.

Siapkan pertanyaan, analisa, dan insight kalian.

Mari gunakan sesi diskusi dengan bijak, saling berbagi informasi, dan tetap fokus pada trading yang disiplin.

⏰ **Diskusi dibuka pukul 18.00 WIB**

See you inside, teman-teman! 🚀""",
            parse_mode="Markdown"
        )

        logger.info(
            "🟡 Reminder 5 menit sebelum buka dikirim"
        )

    except Exception as e:

        logger.exception(
            "❌ Gagal mengirim reminder: %s",
            e
        )


# =========================================================
# SYNC STATUS SAAT BOT STARTUP
# =========================================================

async def sync_group_status():

    now = datetime.now(TIMEZONE)

    weekday = now.weekday()

    hour = now.hour
    minute = now.minute

    current_minutes = (
        hour * 60
    ) + minute

    logger.info(
        "🕐 Startup time: %s WIB",
        now.strftime("%d-%m-%Y %H:%M:%S")
    )

    # =====================================================
    # SENIN - JUMAT
    # =====================================================

    if weekday <= 4:

        # -----------------------------------------------
        # 18:00 - 23:59
        # DISKUSI TERBUKA
        # -----------------------------------------------

        if current_minutes >= (18 * 60):

            logger.info(
                "🟢 Startup berada di jam diskusi."
            )

            await open_discussion(
                send_message=False
            )

        # -----------------------------------------------
        # 00:00 - 17:59
        # DISKUSI TERTUTUP
        # -----------------------------------------------

        else:

            logger.info(
                "🔴 Startup berada di luar jam diskusi."
            )

            await close_discussion(
                send_message=False
            )

    # =====================================================
    # SABTU
    # =====================================================

    elif weekday == 5:

        logger.info(
            "🔴 Hari Sabtu - diskusi otomatis ditutup."
        )

        await close_discussion(
            send_message=False
        )

    # =====================================================
    # MINGGU
    # =====================================================

    else:

        logger.info(
            "🔴 Hari Minggu - diskusi otomatis ditutup."
        )

        await close_discussion(
            send_message=False
        )


# =========================================================
# COMMAND /BUKA
# =========================================================

@dp.message(Command("buka"))
async def command_buka(message: Message):

    if not await admin_only(message):
        return

    await open_discussion(
        send_message=False
    )

    await message.answer(
        """🟢 **DISKUSI BERHASIL DIBUKA**

Member sekarang dapat mengirim pesan.""",
        parse_mode="Markdown"
    )


# =========================================================
# COMMAND /TUTUP
# =========================================================

@dp.message(Command("tutup"))
async def command_tutup(message: Message):

    if not await admin_only(message):
        return

    await close_discussion(
        send_message=False
    )

    await message.answer(
        """🔴 **DISKUSI BERHASIL DITUTUP**

Member sekarang tidak dapat mengirim pesan.""",
        parse_mode="Markdown"
    )


# =========================================================
# COMMAND /STATUS
# =========================================================

@dp.message(Command("status"))
async def command_status(message: Message):

    if not await admin_only(message):
        return

    now = datetime.now(TIMEZONE)

    if group_is_open is True:

        status = "🟢 DISKUSI TERBUKA"

    elif group_is_open is False:

        status = "🔴 DISKUSI TERTUTUP"

    else:

        status = "⚪ STATUS BELUM DIKETAHUI"

    await message.answer(
        f"""🤖 **GROUP SCHEDULER**

{status}

📅 Hari     : {now.strftime("%A")}
📆 Tanggal  : {now.strftime("%d-%m-%Y")}
⏰ Waktu    : {now.strftime("%H:%M:%S")} WIB

🟡 Reminder : **17:55 WIB**
🟢 Buka     : **18:00 WIB**
🔴 Tutup    : **00:00 WIB**

📅 Jadwal otomatis:
**Senin – Jumat**

🚫 Sabtu & Minggu:
**Tidak ada jadwal buka otomatis.**
""",
        parse_mode="Markdown"
    )


# =========================================================
# COMMAND /ID
# =========================================================

@dp.message(Command("id"))
async def command_id(message: Message):

    user_id = (
        message.from_user.id
        if message.from_user
        else "Unknown"
    )

    await message.answer(
        f"""🆔 **INFORMASI**

💬 Chat ID:
`{message.chat.id}`

👤 User ID:
`{user_id}`
""",
        parse_mode="Markdown"
    )


# =========================================================
# SCHEDULER
# =========================================================

def setup_scheduler():

    # =====================================================
    # 17:55 WIB
    # REMINDER
    # SENIN - JUMAT
    # =====================================================

    scheduler.add_job(
        opening_reminder,
        CronTrigger(
            day_of_week="mon-fri",
            hour=17,
            minute=55,
            timezone=TIMEZONE
        ),
        id="opening_reminder",
        replace_existing=True
    )

    # =====================================================
    # 18:00 WIB
    # OPEN
    # SENIN - JUMAT
    # =====================================================

    scheduler.add_job(
        open_discussion,
        CronTrigger(
            day_of_week="mon-fri",
            hour=18,
            minute=0,
            timezone=TIMEZONE
        ),
        id="open_discussion",
        replace_existing=True
    )

    # =====================================================
    # 00:00 WIB
    # CLOSE
    #
    # Selasa - Sabtu
    #
    # Karena sesi malam:
    #
    # Senin 18:00
    # ↓
    # Selasa 00:00 tutup
    #
    # Jumat 18:00
    # ↓
    # Sabtu 00:00 tutup
    # =====================================================

    scheduler.add_job(
        close_discussion,
        CronTrigger(
            day_of_week="tue-sat",
            hour=0,
            minute=0,
            timezone=TIMEZONE
        ),
        id="close_discussion",
        replace_existing=True
    )

    logger.info(
        "📅 Scheduler berhasil dibuat"
    )

    logger.info(
        "🟡 Reminder : Senin-Jumat 17:55 WIB"
    )

    logger.info(
        "🟢 Open     : Senin-Jumat 18:00 WIB"
    )

    logger.info(
        "🔴 Close    : Selasa-Sabtu 00:00 WIB"
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    # =====================================================
    # VALIDASI TOKEN
    # =====================================================

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN belum diatur di Railway Variables."
        )

    # =====================================================
    # VALIDASI ADMIN
    # =====================================================

    if not ADMIN_IDS:

        raise RuntimeError(
            "ADMIN_IDS belum diatur di Railway Variables."
        )

    logger.info(
        "=========================================="
    )

    logger.info(
        "🤖 GROUP SCHEDULER BOT STARTING..."
    )

    logger.info(
        "=========================================="
    )

    logger.info(
        "GROUP_ID : %s",
        GROUP_ID
    )

    logger.info(
        "TIMEZONE : Asia/Jakarta"
    )

    logger.info(
        "ADMIN_IDS: %s",
        ADMIN_IDS
    )

    # =====================================================
    # SETUP SCHEDULER
    # =====================================================

    setup_scheduler()

    # =====================================================
    # START SCHEDULER
    # =====================================================

    scheduler.start()

    logger.info(
        "✅ Scheduler aktif"
    )

    # =====================================================
    # SINKRONISASI STATUS GRUP
    #
    # INI YANG DIPERBAIKI.
    #
    # Kalau bot restart jam 17:31:
    # → otomatis CLOSE
    #
    # Kalau bot restart jam 19:00:
    # → otomatis OPEN
    #
    # Kalau bot restart hari Minggu:
    # → otomatis CLOSE
    # =====================================================

    await sync_group_status()

    logger.info(
        "✅ Status grup berhasil disinkronkan"
    )

    # =====================================================
    # START POLLING
    # =====================================================

    logger.info(
        "🚀 Bot polling dimulai..."
    )

    try:

        await dp.start_polling(bot)

    finally:

        logger.info(
            "🛑 Bot shutting down..."
        )

        scheduler.shutdown()

        await bot.session.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    asyncio.run(main())
