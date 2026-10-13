# -*- coding: utf-8 -*-
"""
BOT TELEGRAM AL-MASAR (المسار)
Fiqh Perancangan & Strategi Harakah Islamiyah
Karya: Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)
"""

import os
import sys
import json
import time
import re
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Bot Al-Masar Telegram (@MasarKu_bot) beroperasi 24/7.".encode("utf-8"))

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 0))
    if port:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"Health-check HTTP Server aktif pada port {port} (Sedia untuk Render).")

# Pastikan konsol Windows menyokong emoji dan teks Arab (UTF-8)
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Konfigurasi Token
# Pengguna boleh letak token dalam environment variable atau terus dalam fail ini/config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DATA_PATH = os.path.join(os.path.dirname(__file__), "almasar_data.json")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if not BOT_TOKEN and cfg.get("bot_token"):
                BOT_TOKEN = cfg.get("bot_token")
    except Exception as e:
        print(f"Ralat membaca config.json: {e}")

# Muat Pangkalan Data Al-Masar
if not os.path.exists(DATA_PATH):
    print(f"Ralat: Fail pangkalan data {DATA_PATH} tidak dijumpai!")
    sys.exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    ALMASAR_DATA = json.load(f)

CHAPTERS = ALMASAR_DATA.get("chapters", [])
print(f"Berjaya memuatkan {len(CHAPTERS)} bab Al-Masar.")

# Sesi HTTP
session = requests.Session()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Penyimpanan Sesi Pengguna Sementara
USER_STATE = {} # { chat_id: { 'layer': 'layer1' } }

def get_user_layer(chat_id):
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = {'layer': 'layer1'}
    return USER_STATE[chat_id].get('layer', 'layer1')

def set_user_layer(chat_id, layer):
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = {}
    USER_STATE[chat_id]['layer'] = layer

def send_api(method, payload):
    url = f"{API_BASE}/{method}"
    try:
        res = session.post(url, json=payload, timeout=30)
        data = res.json()
        if not data.get("ok"):
            print(f"Ralat Telegram ({method}): {data.get('description')}")
        return data
    except Exception as e:
        print(f"Ralat API Telegram ({method}): {e}")
        return None

def md_to_telegram_html(text):
    if not text:
        return ""
    # 1. Escape aksara khas HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 2. Format Bold **teks** -> <b>teks</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    # 3. Format Italic *teks* atau _teks_ -> <i>teks</i>
    text = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_\n]+?)_(?!_)', r'<i>\1</i>', text)
    # 4. Senarai bullet (* atau - di awal baris) -> • 
    text = re.sub(r'^[ \t]*[\*\-][ \t]+', '• ', text, flags=re.MULTILINE)
    return text

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = send_api("sendMessage", payload)
    # Fallback ke plain text jika ada isu entiti HTML
    if (not res or not res.get("ok")) and parse_mode:
        payload["parse_mode"] = None
        res = send_api("sendMessage", payload)
    return res

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = send_api("editMessageText", payload)
    # Fallback ke plain text jika ada isu entiti HTML
    if res and not res.get("ok"):
        desc = res.get("description", "")
        if "message is not modified" in desc:
            return res
        if parse_mode and "can't parse entities" in desc:
            payload["parse_mode"] = None
            res = send_api("editMessageText", payload)
    return res

def answer_callback_query(callback_query_id, text=""):
    payload = {
        "callback_query_id": callback_query_id,
        "text": text
    }
    return send_api("answerCallbackQuery", payload)

# ================= MENU GENERATORS =================

def get_main_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📖 Baca Ikut Bab (11 Bab)", "callback_data": "menu_chapters"},
                {"text": "🔍 Carian Topik", "callback_data": "menu_search_info"}
            ],
            [
                {"text": "💎 Mutiara Hikmah Dakwah", "callback_data": "hikmah_random"},
                {"text": "🔄 Pilihan Mod Bacaan", "callback_data": "menu_mode"}
            ],
            [
                {"text": "🌐 Buka Web PWA Al-Masar", "url": "https://al-masar-dakwah.netlify.app/"}
            ],
            [
                {"text": "ℹ️ Info Kitab & Syeikh", "callback_data": "menu_about"}
            ]
        ]
    }

def get_chapters_keyboard():
    buttons = []
    # Mukadimah
    buttons.append([{"text": "📌 Mukadimah: Fiqh Perancangan", "callback_data": "ch_0"}])
    
    # Bab 1 hingga 11 (2 butang per baris)
    row = []
    for idx in range(1, len(CHAPTERS)):
        ch = CHAPTERS[idx]
        title_short = f"Bab {idx}: {ch['title'].split(':')[1].strip() if ':' in ch['title'] else ch['title']}"
        if len(title_short) > 24:
            title_short = title_short[:22] + "..."
        row.append({"text": title_short, "callback_data": f"ch_{idx}"})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([{"text": "⬅️ Kembali ke Menu Utama", "callback_data": "menu_main"}])
    return {"inline_keyboard": buttons}

def get_subtopics_keyboard(ch_idx):
    ch = CHAPTERS[ch_idx]
    buttons = []
    
    for s_idx, sub in enumerate(ch["subtopics"]):
        title_btn = f"{s_idx+1}. {sub['title']}"
        if len(title_btn) > 34:
            title_btn = title_btn[:32] + ".."
        buttons.append([{"text": title_btn, "callback_data": f"sub_{ch_idx}_{s_idx}_0"}])
        
    buttons.append([
        {"text": "⬅️ Senarai Bab", "callback_data": "menu_chapters"},
        {"text": "🏠 Utama", "callback_data": "menu_main"}
    ])
    return {"inline_keyboard": buttons}

def format_subtopic_text(ch_idx, s_idx, layer, page=0):
    ch = CHAPTERS[ch_idx]
    sub = ch["subtopics"][s_idx]
    
    mode_label = "📖 <b>Versi Lengkap (Terjemahan Penuh)</b>" if layer == "layer1" else "⚡ <b>Ringkasan Eksklusif (Layer 2)</b>"
    
    header = (
        f"🏛 <b>AL-MASAR (المسار)</b>\n"
        f"📚 <b>{ch['number']}: {ch['title']}</b>\n"
        f"📑 <b>Tajuk: {sub['title']}</b>\n"
        f"🏷 <i>{mode_label}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if layer == "layer1":
        paras = sub.get("paragraphs", [])
        if not paras:
            return header + "<i>Tiada teks dalam bahagian ini.</i>", 1
            
        # Paginasi perenggan (setiap muka surat memaparkan sekitar 3-4 perenggan / ~1800 aksara)
        pages_content = []
        cur_page = []
        cur_len = 0
        
        for p in paras:
            cur_page.append(p)
            cur_len += len(p)
            if cur_len > 1400:
                pages_content.append("\n\n".join(cur_page))
                cur_page = []
                cur_len = 0
        if cur_page:
            pages_content.append("\n\n".join(cur_page))
            
        total_pages = len(pages_content)
        page = min(page, total_pages - 1)
        body = pages_content[page] if pages_content else "<i>Tiada kandungan.</i>"
        
        footer = f"\n\n━━━━━━━━━━━━━━━━━━━\n📄 <i>Halaman {page+1} daripada {total_pages}</i>"
        return header + body + footer, total_pages
    else:
        # Layer 2: Ringkasan Eksklusif
        summary_raw = sub.get("summary", "Ringkasan sedang dimantapkan...")
        summary_clean = md_to_telegram_html(summary_raw)
        return header + summary_clean, 1

def get_subtopic_reading_keyboard(ch_idx, s_idx, layer, page, total_pages):
    ch = CHAPTERS[ch_idx]
    buttons = []
    
    # 1. Butang Paginasi (jika teks panjang)
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append({"text": "◀️ Sebelum", "callback_data": f"sub_{ch_idx}_{s_idx}_{page-1}"})
        nav_row.append({"text": f"{page+1}/{total_pages}", "callback_data": "noop"})
        if page < total_pages - 1:
            nav_row.append({"text": "Seterusnya ▶️", "callback_data": f"sub_{ch_idx}_{s_idx}_{page+1}"})
        buttons.append(nav_row)
        
    # 2. Butang Tukar Layer (Lengkap vs Ringkasan)
    toggle_text = "⚡ Tukar ke Ringkasan" if layer == "layer1" else "📖 Tukar ke Versi Lengkap"
    buttons.append([{"text": toggle_text, "callback_data": f"toglayer_{ch_idx}_{s_idx}"}])
    
    # 3. Butang Subtajuk Sebelumnya / Seterusnya
    sub_nav = []
    if s_idx > 0:
        sub_nav.append({"text": "⏮ Subtajuk Lepas", "callback_data": f"sub_{ch_idx}_{s_idx-1}_0"})
    if s_idx < len(ch["subtopics"]) - 1:
        sub_nav.append({"text": "Subtajuk Depan ⏭", "callback_data": f"sub_{ch_idx}_{s_idx+1}_0"})
    if sub_nav:
        buttons.append(sub_nav)
        
    # 4. Navigasi Pulang
    buttons.append([
        {"text": "📋 Senarai Subtajuk", "callback_data": f"ch_{ch_idx}"},
        {"text": "🏠 Menu Utama", "callback_data": "menu_main"}
    ])
    return {"inline_keyboard": buttons}

# ================= MUTIARA HIKMAH =================
HIKMAH_LIST = [
    "“Manusia akan mempedulikan urusan anda, sekadar mana anda peduli dengan urusan Allah. Sesiapa yang datang kepada Allah dengan hatinya, nescaya Allah akan mendatangkan hati-hati manusia kepadanya.”\n— <b>Yahya bin Mu'az (Kitab Al-Masar, Mukadimah)</b>",
    "“Tiada seorang pun yang membuat dakwaan, melainkan kerana dia kosong daripada memiliki sebarang hakikat. Jika dia telah memiliki hakikat itu, nescaya hakikat dirinya akan memperkatakan tentangnya tanpa perlu berpropaganda.”\n— <b>Kalam Salafussoleh (Al-Masar, Mukadimah)</b>",
    "“Wahai manusia! Beramal salihlah sebelum berperang, sesungguhnya kamu sebenarnya berperang berbekalkan amalan-amalan kamu!”\n— <b>Abu ad-Darda' RA (Al-Masar, Mukadimah)</b>",
    "“Jika anda tidak menambah sesuatu kebaikan atau impak kepada dunia ini, maka anda sebenarnya adalah barang lebihan kepada dunia ini.”\n— <b>Mustafa Sadiq ar-Rafi'ie (Al-Masar, Bab 1)</b>",
    "“Hanya seseorang yang boleh melakukan pemilihan yang baik untuk dirinya sahaja, yang dapat membuat pilihan yang baik untuk orang lain.”\n— <b>Abdullah bin Wahab (Al-Masar, Mukadimah)</b>",
    "“Kekuatan dalam segala sesuatu. Kita adalah musuh terhadap setiap pemimpin atau parti yang tidak bekerja untuk membantu Islam dan mengembalikan kemegahan Islam.”\n— <b>Imam Hasan Al-Banna (Al-Masar, Bab 3)</b>",
    "“Sesiapa yang tidak memuji niat anda yang baik, dia tidak akan mensyukuri perbuatan anda yang terpuji.”\n— <b>Khalifah Al-Ma'mun (Al-Masar, Bab 2)</b>",
    "“Fahamilah Kitab Allah daripada Al-Razi... tetapi fahamilah pandanganku: Adakah kita boleh hidup dengan hati yang tidak bernyala?”\n— <b>Dr. Muhammad Iqbal (Al-Masar, Bab 3)</b>",
    "“Himpunkanlah mereka yang jauh kepadamu, kerana sesungguhnya lembah tidak akan melimpah dengan air melainkan dengan aliran anak-anak sungai.”\n— <b>Abu Tammam (Al-Masar, Bab 7)</b>",
    "“Markas jamaah dan pusat perancangan mestilah berfungsi seperti makmal penyelidikan saintifik yang mengkaji data dan realiti, bukannya seperti istana raja yang dipenuhi protokol feudal.”\n— <b>Syeikh Muhammad Ahmad Ar-Rasyid (Al-Masar, Bab 11)</b>"
]

# ================= HANDLERS =================

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    
    if text.startswith("/start") or text.startswith("/menu"):
        welcome_txt = (
            "✨ <b>SELAMAT DATANG KE BOT AL-MASAR (المسار)</b> ✨\n\n"
            "<b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n\n"
            "Al-Masar adalah buku siri kelima daripada siri-siri fiqh dakwah dan harakah Islamiyah dimulai dengan <i>al-Muntalaq</i> (untuk mengenali tabiatnya), <i>al-‘Awa’iq</i> (yang dipenuhi dengan segala macam jenis halangan), <i>al-Raqa’iq</i> (yang boleh melembutkan hati anda dengan kelembutan makna-maknanya) dan <i>al-Bawariq</i> (yang mengandungi lintasan-lintasan yang boleh dijadikan panduan).\n\n"
            "Bot ini memuatkan <b>11 Bab Utama + Mukadimah</b> dengan <b>116 Sub-Tajuk Lengkap</b>:\n"
            "• 📖 <b>Layer 1:</b> Versi Penuh Terjemahan Lengkap\n"
            "• ⚡ <b>Layer 2:</b> Ringkasan Eksklusif Berstruktur\n\n"
            "🌐 Aplikasi Web PWA: https://al-masar-dakwah.netlify.app/\n\n"
            "<i>Sila pilih menu di bawah untuk memulakan bacaan:</i>"
        )
        send_message(chat_id, welcome_txt, get_main_menu_keyboard())
        return

    if text.startswith("/cari"):
        query = text.replace("/cari", "").strip()
        if not query:
            send_message(chat_id, "ℹ️ Sila taip kata kunci carian selepas arahan.\nContoh: <code>/cari syaitan</code> atau <code>/cari tanzim</code>")
            return
        handle_search(chat_id, query)
        return

    if text.startswith("/hikmah"):
        send_message(chat_id, f"💎 <b>MUTIARA DAKWAH AL-MASAR:</b>\n\n{random.choice(HIKMAH_LIST)}")
        return

    # Mesej biasa -> Lakukan carian pantas
    handle_search(chat_id, text)

def handle_search(chat_id, query):
    query_lower = query.lower()
    matches = []
    
    for ch_idx, ch in enumerate(CHAPTERS):
        for s_idx, sub in enumerate(ch["subtopics"]):
            # Cari dalam tajuk
            if query_lower in sub["title"].lower():
                matches.append((ch_idx, s_idx, f"📌 {ch['number']}: {sub['title']}"))
                continue
            # Cari dalam perenggan
            for p in sub.get("paragraphs", []):
                if query_lower in p.lower():
                    matches.append((ch_idx, s_idx, f"📄 {ch['number']}: {sub['title']}"))
                    break
            if len(matches) >= 8:
                break
        if len(matches) >= 8:
            break
            
    if not matches:
        send_message(chat_id, f"🔍 Maaf, tiada perbincangan dijumpai bagi kata kunci: <b>\"{query}\"</b>.\nCuba kata kunci lain seperti <i>tarbiah, politik, tanzim, banna, iktibar</i>.")
        return

    keyboard = []
    for ch_idx, s_idx, label in matches:
        keyboard.append([{"text": label[:38], "callback_data": f"sub_{ch_idx}_{s_idx}_0"}])
    keyboard.append([{"text": "🏠 Menu Utama", "callback_data": "menu_main"}])
    
    send_message(
        chat_id, 
        f"🔍 <b>Hasil Carian untuk: \"{query}\"</b>\nDijumpai {len(matches)} topik berkaitan. Sila pilih:",
        {"inline_keyboard": keyboard}
    )

def handle_callback(cb):
    cb_id = cb["id"]
    data = cb.get("data", "")
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    
    answer_callback_query(cb_id)
    
    if data == "menu_main":
        welcome_txt = (
            "✨ <b>MENU UTAMA AL-MASAR (المسار)</b> ✨\n\n"
            "<b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n\n"
            "Al-Masar adalah buku siri kelima daripada siri-siri fiqh dakwah dan harakah Islamiyah dimulai dengan <i>al-Muntalaq</i> (untuk mengenali tabiatnya), <i>al-‘Awa’iq</i> (yang dipenuhi dengan segala macam jenis halangan), <i>al-Raqa’iq</i> (yang boleh melembutkan hati anda dengan kelembutan makna-maknanya) dan <i>al-Bawariq</i> (yang mengandungi lintasan-lintasan yang boleh dijadikan panduan).\n\n"
            "🌐 Aplikasi Web PWA: https://al-masar-dakwah.netlify.app/\n\n"
            "Sila pilih seksyen yang anda ingin terokai:"
        )
        edit_message(chat_id, msg_id, welcome_txt, get_main_menu_keyboard())
        return

    if data == "menu_chapters":
        txt = "📚 <b>PILIH BAB KANDUNGAN AL-MASAR:</b>\n\nKitab ini mengandungi Mukadimah dan 11 Bab utama. Pilih bab untuk melihat sub-tajuk:"
        edit_message(chat_id, msg_id, txt, get_chapters_keyboard())
        return

    if data.startswith("ch_"):
        ch_idx = int(data.split("_")[1])
        ch = CHAPTERS[ch_idx]
        txt = (
            f"🏛 <b>{ch['number']}: {ch['title']}</b>\n"
            f"🏷 <i>{ch['title_ar']}</i>\n\n"
            f"Terdapat <b>{len(ch['subtopics'])} sub-tajuk</b> dalam bab ini. Sila pilih tajuk yang ingin dibaca:"
        )
        edit_message(chat_id, msg_id, txt, get_subtopics_keyboard(ch_idx))
        return

    if data.startswith("sub_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        s_idx = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
        layer = get_user_layer(chat_id)
        
        content_txt, total_pages = format_subtopic_text(ch_idx, s_idx, layer, page)
        kb = get_subtopic_reading_keyboard(ch_idx, s_idx, layer, page, total_pages)
        edit_message(chat_id, msg_id, content_txt, kb)
        return

    if data.startswith("toglayer_"):
        parts = data.split("_")
        ch_idx = int(parts[1])
        s_idx = int(parts[2])
        cur_layer = get_user_layer(chat_id)
        new_layer = "layer2" if cur_layer == "layer1" else "layer1"
        set_user_layer(chat_id, new_layer)
        
        content_txt, total_pages = format_subtopic_text(ch_idx, s_idx, new_layer, 0)
        kb = get_subtopic_reading_keyboard(ch_idx, s_idx, new_layer, 0, total_pages)
        edit_message(chat_id, msg_id, content_txt, kb)
        return

    if data == "hikmah_random":
        quote = random.choice(HIKMAH_LIST)
        txt = f"💎 <b>MUTIARA DAKWAH AL-MASAR:</b>\n\n{quote}"
        kb = {
            "inline_keyboard": [
                [{"text": "🎲 Mutiara Lain", "callback_data": "hikmah_random"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        edit_message(chat_id, msg_id, txt, kb)
        return

    if data == "menu_mode":
        cur = get_user_layer(chat_id)
        cur_name = "Versi Penuh (Terjemahan Lengkap)" if cur == "layer1" else "Ringkasan Eksklusif"
        txt = (
            f"🔄 <b>TETAPAN MOD BACAAN</b>\n\n"
            f"Mod semasa anda: <b>{cur_name}</b>\n\n"
            f"• <b>Versi Penuh (Layer 1):</b> Memaparkan teks terjemahan penuh kitab tanpa tapisan.\n"
            f"• <b>Ringkasan Eksklusif (Layer 2):</b> Memaparkan intisari padat, poin-poin utama, serta nukilan tokoh penting bagi semakan pantas."
        )
        kb = {
            "inline_keyboard": [
                [{"text": "📖 Tetapkan: Versi Penuh", "callback_data": "setmode_layer1"}],
                [{"text": "⚡ Tetapkan: Ringkasan Eksklusif", "callback_data": "setmode_layer2"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        edit_message(chat_id, msg_id, txt, kb)
        return

    if data.startswith("setmode_"):
        new_mode = data.split("_")[1]
        set_user_layer(chat_id, new_mode)
        mode_str = "Versi Penuh" if new_mode == "layer1" else "Ringkasan Eksklusif"
        answer_callback_query(cb_id, f"Mod berjaya ditukar kepada: {mode_str}")
        # Kembali ke menu utama
        handle_callback({"id": cb_id, "data": "menu_main", "message": cb["message"]})
        return

    if data == "menu_search_info":
        txt = (
            "🔍 <b>PANDUAN CARIAN PANTAS</b>\n\n"
            "Anda boleh mencari sebarang topik, nama tokoh, atau istilah fiqh dakwah dengan menaip terus:\n\n"
            "👉 <code>/cari [kata kunci]</code>\n\n"
            "<b>Contoh:</b>\n"
            "• <code>/cari syaitan</code> (6 medan perang syaitan)\n"
            "• <code>/cari tanzim</code> (Fiqh organisasi & rahsia)\n"
            "• <code>/cari wanita</code> (Peranan dakwah muslimat)\n"
            "• <code>/cari banna</code> (Nukilan Imam Hasan al-Banna)\n"
            "• <code>/cari qutb</code> (Kritikan Sayyid Qutb terhadap tanzim khas)\n"
            "• <code>/cari tajmi</code> (10 Seni pengumpulan mad'u)"
        )
        kb = {"inline_keyboard": [[{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]]}
        edit_message(chat_id, msg_id, txt, kb)
        return

    if data == "menu_about":
        txt = (
            "🏛 <b>TENTANG KITAB AL-MASAR (المسار)</b>\n\n"
            "<b>Pengarang:</b> As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)\n"
            "<b>Genre:</b> Strategi, Polisi & Fiqh Perancangan Harakah Islamiyah\n"
            "<b>Cakupan:</b> Polisi Luaran, Polisi Dalaman & Polisi Tarbawi Harakah Islamiyah\n\n"
            "Al-Masar adalah buku siri kelima daripada siri-siri fiqh dakwah dan harakah Islamiyah dimulai dengan <i>al-Muntalaq</i> (untuk mengenali tabiatnya), <i>al-‘Awa’iq</i> (yang dipenuhi dengan segala macam jenis halangan), <i>al-Raqa’iq</i> (yang boleh melembutkan hati anda dengan kelembutan makna-maknanya) dan <i>al-Bawariq</i> (yang mengandungi lintasan-lintasan yang boleh dijadikan panduan).\n\n"
            "🌐 Aplikasi Web PWA: https://al-masar-dakwah.netlify.app/"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🌐 Layari Web PWA", "url": "https://al-masar-dakwah.netlify.app/"}],
                [{"text": "⬅️ Menu Utama", "callback_data": "menu_main"}]
            ]
        }
        edit_message(chat_id, msg_id, txt, kb)
        return

# ================= POLLING ENGINE =================

def run_bot():
    if not BOT_TOKEN or BOT_TOKEN == "ISI_TOKEN_BOT_ANDA_DI_SINI":
        print("\n" + "="*60)
        print("PERHATIAN: Token Bot Telegram Belum Ditetapkan!")
        print("Sila masukkan token bot anda ke dalam fail config.json atau set environment variable TELEGRAM_BOT_TOKEN.")
        print("="*60 + "\n")
        return

    print("="*60)
    print("Bot Telegram Al-Masar sedang dijalankan (Polling Mode)...")
    print("Tekan Ctrl + C untuk menghentikan bot.")
    print("="*60)

    # Aktifkan server HTTP jika berjalan di Render / cloud (PORT dikesan)
    start_health_server()
    
    # Uji sambungan ke Telegram
    me = send_api("getMe", {})
    if not me or not me.get("ok"):
        print(f"Ralat menyambung ke Telegram: {me}")
        return
        
    bot_info = me["result"]
    print(f"Berjaya log masuk sebagai @{bot_info.get('username')} ({bot_info.get('first_name')})")

    last_update_id = 0
    while True:
        try:
            url = f"{API_BASE}/getUpdates?offset={last_update_id + 1}&timeout=20"
            resp = session.get(url, timeout=25)
            data = resp.json()
            
            if data.get("ok"):
                for upd in data.get("result", []):
                    last_update_id = upd["update_id"]
                    if "message" in upd:
                        handle_message(upd["message"])
                    elif "callback_query" in upd:
                        handle_callback(upd["callback_query"])
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nBot dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"Ralat polling: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
