# 📦 Pyrogram Forwarder Bot

A Telegram bot built using **Pyrogram** that can forward **messages and media albums** from multiple source chats to target chats — intelligently, reliably, and with Docker support 🚀

---

### ✨ Features

- 🔄 Forward messages from **multiple source ➝ target chat pairs**
- 🖼️ Auto-forward **media groups (albums)** as proper Telegram albums
- 📝 **Captions preserved** for media or text messages
- 🧠 Smart buffering to ensure complete albums are captured
- 💬 Also supports **text-only** messages
- 🐳 Runs inside **Docker** or with **docker-compose**
- 🔐 Clean logging and graceful shutdowns

---

### 📁 Folder Structure

```
.
├── main.py                # Bot logic
├── config.py              # Bot configs
├── map_utils.py           # Map logic
├── mappings.json          # Json with source ➝ target mappings
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose setup
└── README.md              # You're here 😎
```

---

### ⚙️ Configuration

Edit `config.py` to define your Telegram API credentials and forward rules:

```python
API_ID = 123456
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"
OWNER_ID = [123456789, 987654321] # Replace with your actual Telegram user IDs

```

> 🔁 Use **channel/group IDs** (must be numeric). You can get IDs using bots like [@getidsbot](https://t.me/getidsbot)

---

### 🐍 Local Run (Without Docker)

Install dependencies and run:

```bash
pip install -r requirements.txt
python main.py
```

---

### 🐳 Docker Setup

#### 1. Build the image:
```bash
docker-compose build
```

#### 2. Run the bot:
```bash
docker-compose up -d
```

#### 3. View logs:
```bash
docker-compose logs -f
```

#### 4. Stop the bot:
```bash
docker-compose down
```

---

### 📝 Example Log Output

```
2025-07-08 16:03:12 - INFO - __main__ - Bot Started!
2025-07-08 16:04:28 - INFO - __main__ - Forwarded album to -1009876543210
2025-07-08 16:05:47 - INFO - __main__ - Forwarded text message
2025-07-08 16:06:14 - INFO - __main__ - Bot Stopped
```

---

### ❤️ Credits

- Built with [PyroFork](https://pyrofork.wulan17.dev/main/)
- Uses `copy_media_group()` and `message.copy()` for best forwarding behavior
- Inspired by real-world automation needs!

---

### 📜 License

This project is released under the [MIT License](LICENSE).
