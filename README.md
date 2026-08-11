# Perfume Watcher

Dekant Parfüm Depo ve Splitcim (Az Kalan Şişeler) sitelerinde **yeni ürün** çıktığında Telegram grubuna mesaj gönderir.

GitHub Actions üzerinde 7–13 dakika arası rastgele aralıklarla çalışır.

## 1) Telegram bot oluştur

1. Telegram’da [@BotFather](https://t.me/BotFather) aç
2. `/newbot` yaz
3. Bot adı ve kullanıcı adı ver (ör. `perfume_watch_bot`)
4. BotFather’ın verdiği **token**’ı kopyala  
   Örnek: `7123456789:AAH...`

## 2) Gruba ekle ve chat id al

1. Telegram’da bir grup oluştur (veya mevcut grubu kullan)
2. Botu gruba ekle
3. Gruba herhangi bir mesaj yaz (ör. `ping`)
4. Tarayıcıda şunu aç (TOKEN yerine bot token’ını koy):

```text
https://api.telegram.org/botTOKEN/getUpdates
```

5. JSON içinde `"chat":{"id":-100xxxxxxxxxx}` değerini bul  
   Grup id’leri genelde **-100** ile başlar.

> Bot mesaj göremiyorsa: gruptan bir mesaj daha atıp `getUpdates`’i yenile.  
> Gerekirse bota grupta mesaj gönderme izni ver.

## 3) GitHub’a kur

1. Bu repoyu GitHub’a push et (**public** repo önerilir — Actions dakikası sınırsız)
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**
   - `TELEGRAM_BOT_TOKEN` → bot token
   - `TELEGRAM_CHAT_ID` → grup chat id (ör. `-1001234567890`)
3. **Actions** sekmesinden `Perfume Watcher` workflow’unu aç
4. **Run workflow** ile ilk kez manuel çalıştır

İlk çalıştırmada mevcut ürünler sessizce kaydedilir (spam olmaz). Sonrakilerde sadece **yeni** ürünler bildirilir.

## Yerel test

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

set TELEGRAM_BOT_TOKEN=...
set TELEGRAM_CHAT_ID=...
python -m watcher.main --force
```

## Nasıl çalışır?

- Actions her 5 dakikada bir tetiklenir
- Script `data/state.json` içindeki `next_check_at` değerine bakar
- Erken ise çıkar; zamanı geldiyse siteleri tarar
- Yeni ürün varsa Telegram grubuna mesaj atar
- Sonraki kontrolü 7–13 dk arası rastgele ayarlar

## Notlar

- GitHub cron bazen birkaç dakika gecikebilir (normal)
- State, Actions cache ile saklanır; cache silinirse bir kez daha bootstrap olur (toplu spam yok)
- Sitelerin HTML’i değişirse scraper güncellenmeli
