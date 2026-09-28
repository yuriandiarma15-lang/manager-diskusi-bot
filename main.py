import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# ID GRUP TELEGRAM
GROUP_ID = int(os.getenv("GROUP_ID", "-5452358482"))

# Admin Telegram ID
# Bisa satu ID atau beberapa ID dipisahkan koma
# Contoh:
# ADMIN_IDS=123456789,987654321
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
# BOT / DISPATCHER
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler(
    timezone=TIMEZONE
)


# =========================================================
# STATUS
# =========================================================

group_is_open = None


# =========================================================
# CEK ADMIN
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
# BUKA DISKUSI
# =========================================================

async def open_discussion(send_message=True):
    global group_is_open

    try:
        # Semua member boleh mengirim pesan
        await bot.set_chat_permissions(
            chat_id=GROUP_ID,
            permissions={
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_video_notes": True,
                "can_send_voice_notes": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            }
        )

        group_is_open = True

        logger.info("🟢 DISKUSI DIBUKA")

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
        logger.exception(f"Gagal membuka diskusi: {e}")


# =========================================================
# TUTUP DISKUSI
# =========================================================

async def close_discussion(send_message=True):
    global group_is_open

    try:
        # Member tidak boleh mengirim pesan
        await bot.set_chat_permissions(
            chat_id=GROUP_ID,
            permissions={
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_video_notes": False,
                "can_send_voice_notes": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
            }
        )

        group_is_open = False

        logger.info("🔴 DISKUSI DITUTUP")

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
        logger.exception(f"Gagal menutup diskusi: {e}")


# =========================================================
# PENGUMUMAN 5 MENIT SEBELUM BUKA
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

        logger.info("🟡 Pengumuman 5 menit sebelum buka dikirim")

    except Exception as e:
        logger.exception(
            f"Gagal mengirim pengumuman pembukaan: {e}"
        )


# =========================================================
# /BUKA
# =========================================================

@dp.message(Command("buka"))
async def command_buka(message: Message):

    if not await admin_only(message):
        return

    await open_discussion(send_message=False)

    await message.answer(
        "🟢 **DISKUSI BERHASIL DIBUKA**\n\n"
        "Member sekarang dapat mengirim pesan.",
        parse_mode="Markdown"
    )


# =========================================================
# /TUTUP
# =========================================================

@dp.message(Command("tutup"))
async def command_tutup(message: Message):

    if not await admin_only(message):
        return

    await close_discussion(send_message=False)

    await message.answer(
        "🔴 **DISKUSI BERHASIL DITUTUP**\n\n"
        "Member sekarang tidak dapat mengirim pesan.",
        parse_mode="Markdown"
    )


# =========================================================
# /STATUS
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

📅 Hari : {now.strftime("%A")}
📆 Tanggal : {now.strftime("%d-%m-%Y")}
⏰ Waktu : {now.strftime("%H:%M:%S")} WIB

🟢 Buka otomatis : **18:00 WIB**
🔴 Tutup otomatis : **00:00 WIB**
🟡 Reminder : **17:55 WIB**

📅 Jadwal otomatis:
Senin – Jumat

🚫 Sabtu & Minggu:
Tidak ada jadwal otomatis.
""",
        parse_mode="Markdown"
    )


# =========================================================
# /ID
# =========================================================

@dp.message(Command("id"))
async def command_id(message: Message):

    await message.answer(
        f"🆔 **Chat ID:** `{message.chat.id}`\n"
        f"👤 **User ID:** `{message.from_user.id}`",
        parse_mode="Markdown"
    )


# =========================================================
# SCHEDULE
# =========================================================

def setup_scheduler():

    # -----------------------------------------------------
    # 17:55 WIB
    # REMINDER 5 MENIT SEBELUM BUKA
    # SENIN - JUMAT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 18:00 WIB
    # BUKA DISKUSI
    # SENIN - JUMAT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 00:00 WIB
    # TUTUP DISKUSI
    #
    # PENTING:
    # 00:00 hari berikutnya.
    #
    # Contoh:
    # Senin 18:00 buka
    # Selasa 00:00 tutup
    #
    # Jadi sesi Senin malam ditutup tepat tengah malam.
    # -----------------------------------------------------

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

    logger.info("📅 Scheduler berhasil dibuat")
    logger.info("🟡 Reminder : Senin-Jumat 17:55 WIB")
    logger.info("🟢 Open     : Senin-Jumat 18:00 WIB")
    logger.info("🔴 Close    : Selasa-Sabtu 00:00 WIB")


# =========================================================
# STARTUP
# =========================================================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN belum diatur di Environment Variables."
        )

    if not ADMIN_IDS:
        raise RuntimeError(
            "ADMIN_IDS belum diatur di Environment Variables."
        )

    logger.info("==========================================")
    logger.info("🤖 GROUP SCHEDULER BOT STARTING...")
    logger.info("==========================================")

    logger.info(f"GROUP_ID : {GROUP_ID}")
    logger.info(f"TIMEZONE : {TIMEZONE}")
    logger.info(f"ADMIN_IDS: {ADMIN_IDS}")

    # Buat scheduler
    setup_scheduler()

    # Jalankan scheduler
    scheduler.start()

    logger.info("✅ Scheduler aktif")
    logger.info("🚀 Bot polling dimulai...")

    try:
        await dp.start_polling(bot)

    finally:
        scheduler.shutdown()
        await bot.session.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
