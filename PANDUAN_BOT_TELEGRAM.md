# PANDUAN PENGGUNAAN & PELANCARAN BOT TELEGRAM AL-MASAR (المسار)

Bot Telegram ini dibina khas untuk memudahkan capaian kepada seluruh perbincangan kitab **Al-Masar (المسار)** karya **As-Syeikh Muhammad Ahmad Ar-Rasyid (رحمه الله)** secara interaktif di telefon bimbit dan komputer.

---

## 🌟 Ciri-Ciri Utama Bot

1. **Navigasi Penuh 20 Bab + Mukadimah:**
   - Menyokong kesemua **210 topik lengkap** dalam kitab.
   - Paginasi pintar untuk membaca teks panjang tanpa membebankan skrin sembang.
2. **Sokongan Dwi-Lapisan (Dual Layer):**
   - **Layer 1:** Versi Penuh Terjemahan Lengkap kitab.
   - **Layer 2:** Ringkasan Eksklusif Berstruktur (boleh ditukar bila-bila masa melalui butang interaktif).
3. **Carian Topik & Dalil Pintar (`/cari`):**
   - Taip `/cari syaitan`, `/cari tanzim`, `/cari wanita`, `/cari banna` untuk mendapatkan topik berkaitan secara serta-merta.
4. **Mutiara Hikmah Dakwah (`/hikmah`):**
   - Memaparkan petikan-petikan tajam kata-kata pengarang, salafussoleh, dan tokoh harakah secara rawak.

---

## 🚀 Langkah 1: Dapatkan Token Bot Percuma dari Telegram

1. Buka aplikasi Telegram anda dan cari akaun rasmi: **`@BotFather`**
2. Tekan **`/start`** kemudian taip arahan: **`/newbot`**
3. Masukkan **Nama Bot** (Contoh: `Al-Masar Fiqh Dakwah`).
4. Masukkan **Username Bot** yang diakhiri dengan perkataan `bot` (Contoh: `AlMasarDakwah_bot` atau `MasarHarakiBot`).
5. **@BotFather** akan memberikan **HTTP API Token** (Contoh: `7123456789:AAFlkjhsdf876sdf...`).
6. Salin token tersebut!

---

## ⚙️ Langkah 2: Masukkan Token ke Dalam Sistem

Buka fail [`telegram_bot_al-Masar/config.json`](file:///c:/Users/pc/OneDrive/Documents/Bahan_Ilmiah_Dakwah/telegram_bot_al-Masar/config.json) dan gantikan nilai `"ISI_TOKEN_BOT_ANDA_DI_SINI"` dengan token anda:

```json
{
  "bot_token": "7123456789:AAFlkjhsdf876sdf...",
  "bot_name": "AlMasarDakwahBot"
}
```

---

## ▶️ Langkah 3: Jalankan Bot

Ada 2 cara mudah untuk menjalankan bot:

### Cara A: Klik Dua Kali Fail Pelancar (Paling Mudah di Windows)
- Buka folder `telegram_bot_al-Masar` dan klik dua kali fail: **`start_bot.bat`**

### Cara B: Guna Arahan Terminal / PowerShell
```bash
cd c:\Users\pc\OneDrive\Documents\Bahan_Ilmiah_Dakwah\telegram_bot_al-Masar
python bot.py
```

Setelah bot berjalan, buka Telegram, cari bot anda, dan tekan **`/start`**!
