# Perfume Watcher

Dekant Parfüm Depo ve Splitcim (Az Kalan Şişeler) sitelerinde **yeni ürün** çıktığında Telegram grubuna mesaj gönderir.

Çalışma yeri: **GitHub Actions** (yaklaşık her 5 dakikada bir).

## Telegram

1. [@BotFather](https://t.me/BotFather) → `/newbot` → token
2. Botu gruba ekle, mesaj yaz
3. Chat id: `python -m watcher.get_chat_id`

## GitHub Secrets

Repo → **Settings → Secrets and variables → Actions**:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Workflow: **Actions → Perfume Watcher** (schedule otomatik; manuel: Run workflow)

İlk başarılı taramada mevcut ürünler sessizce kaydedilir; sonra sadece yeniler bildirilir.

## Yerel test

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
set TELEGRAM_BOT_TOKEN=...
set TELEGRAM_CHAT_ID=...
python -m watcher.main --force
```

## Notlar

- GitHub Actions cron en sık ~5 dk çalışır
- State Actions cache’te tutulur; cache silinirse kaynak bazlı bootstrap tekrarlanır (toplu spam yok)
- `python -m watcher.main --loop` VPS için sürekli mod (opsiyonel)
- Sitelerin HTML’i değişirse scraper güncellenmeli
