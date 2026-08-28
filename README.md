# Perfume Watcher

Dekant Parfüm Depo ve Splitcim (Az Kalan Şişeler) sitelerinde **yeni ürün** çıktığında Telegram grubuna mesaj gönderir.

Asıl çalışma yeri: **Oracle Cloud Always Free** VPS (30 sn–2 dk aralık).  
GitHub Actions sadece manuel yedek olarak durur.

## 1) Telegram (zaten kuruluysa atla)

1. [@BotFather](https://t.me/BotFather) → `/newbot` → token al
2. Botu gruba ekle, gruba mesaj yaz
3. Chat id al: `python -m watcher.get_chat_id`

## 2) Oracle Cloud Always Free kurulum

### A) Hesap + VM

1. https://cloud.oracle.com adresinden Always Free hesap aç
2. **Compute → Instances → Create instance**
3. Image: **Canonical Ubuntu 22.04** (veya 24.04)
4. Shape: **VM.Standard.A1.Flex** (Ampere, Always Free) — 1 OCPU / 6 GB yeterli
5. SSH key ekle, instance oluştur
6. Public IP’yi not et

> Kapasite yoksa başka region dene (ör. Frankfurt, Amsterdam).

### B) SSH ile bağlan

```bash
ssh -i your-key.pem ubuntu@PUBLIC_IP
```

### C) Projeyi kur

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip

git clone https://github.com/LeventDonmez/perfume.git
cd perfume

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp deploy/env.example .env
nano .env   # TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID doldur
```

### D) systemd servisi (reboot sonrası da çalışsın)

```bash
sudo cp deploy/perfume-watcher.service /etc/systemd/system/
# User/yol farklıysa service dosyasını düzenle:
# sudo nano /etc/systemd/system/perfume-watcher.service

sudo systemctl daemon-reload
sudo systemctl enable --now perfume-watcher
sudo systemctl status perfume-watcher
```

Log:

```bash
journalctl -u perfume-watcher -f
```

İlk çalışmada mevcut ürünler sessizce kaydedilir; sonra sadece yeni ürünler Telegram’a gider.

## Yerel / tek seferlik test

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
python -m watcher.main --force          # bir kez
python -m watcher.main --loop           # sürekli (VPS)
```

## GitHub Actions

Schedule kapalı. Sadece **Actions → Perfume Watcher → Run workflow** ile manuel yedek çalıştırabilirsin.  
Oracle açıkken Actions’ı sürekli çalıştırma (çift bildirim olur).

## Notlar

- Aralık: rastgele **30 sn – 2 dk**
- State: `data/state.json` (VPS diskinde kalır)
- Sitelerin HTML’i değişirse scraper güncellenmeli
