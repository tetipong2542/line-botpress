# 💰 LINE Botpress Income-Expense Tracker

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![LINE](https://img.shields.io/badge/LINE-Messaging%20API-00C300.svg)](https://developers.line.biz/)
[![Botpress](https://img.shields.io/badge/Botpress-AI-purple.svg)](https://botpress.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

แอปพลิเคชันจดรายรับรายจ่ายที่ใช้งานผ่าน **LINE Chatbot** และ **Web Interface** พัฒนาด้วย **Python Flask + SQLite** พร้อม **Botpress AI** สำหรับการวิเคราะห์และสนทนาอัจฉริยะ

![Demo](https://via.placeholder.com/800x400/f9fafb/111827?text=LINE+Botpress+Income-Expense+Tracker)

## ✨ Features

### 🎯 Core Features
- 🔐 **LINE Login** - OAuth2 authentication
- 📊 **Multi-Project** - รองรับหลายโปรเจค/ครอบครัว
- 💸 **Transaction Management** - บันทึกรายรับ-รายจ่าย
- 🏷️ **Category System** - จัดหมวดหมู่ด้วย icon และสี
- 💰 **Budget Envelope** - ตั้งงบประมาณรายหมวด
- 🔁 **Recurring Transactions** - รายการประจำ (รายวัน/สัปดาห์/เดือน)
- 🤖 **LINE Chatbot** - บันทึกผ่านการพิมพ์แชท
- 🧠 **AI Insights** - วิเคราะห์การใช้จ่ายด้วย Botpress

### 🔒 Security Features
- ✅ HMAC signature verification for Botpress API
- ✅ LINE webhook signature verification
- ✅ Idempotency key for preventing duplicate operations
- ✅ Bot nonce for replay attack prevention
- ✅ Session-based authentication
- ✅ Role-Based Access Control (RBAC)

## 🏗️ Architecture

```
┌─────────────┐
│   LINE User │ พิมพ์: "จ่าย 350 เดินทาง ค่ารถ"
└──────┬──────┘
       ↓
┌──────────────────┐
│   LINE Server    │
└──────┬───────────┘
       ↓ Webhook
┌──────────────────────┐
│  Flask /line/webhook │ ← Verify LINE Signature
└──────┬───────────────┘
       ↓ Forward
┌──────────────────┐
│    Botpress      │ ← AI: Extract intent & entities
└──────┬───────────┘
       ↓ Call API with HMAC
┌────────────────────────────┐
│ Flask /api/v1/bot/...      │ ← Verify HMAC + Idempotency
│ - TransactionService       │   Create transaction
│ - SQLite Database          │   Check budget
└──────┬─────────────────────┘
       ↓ Response
┌──────────────────┐
│    Botpress      │ ← Generate Thai response
└──────┬───────────┘
       ↓ Reply
┌──────────────────┐
│   LINE User      │ "บันทึกแล้ว ✅ จ่าย 350 บาท"
└──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- LINE Developer Account
- Botpress Account

### Installation

```bash
# Clone repository
git clone https://github.com/tetipong2542/line-botpress.git
cd line-botpress

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your LINE credentials

# Initialize database
export FLASK_APP=run.py
flask init-db

# Run application
python run.py
```

Application will be available at: `http://localhost:5000`

## 📝 Configuration

Edit `.env` file:

```env
# LINE Login (OAuth2)
LINE_CHANNEL_ID=your-channel-id
LINE_CHANNEL_SECRET=your-channel-secret
LINE_REDIRECT_URI=http://localhost:5000/auth/line/callback

# LINE Messaging API (Chatbot)
LINE_CHANNEL_ACCESS_TOKEN=your-access-token

# Botpress
BOTPRESS_WEBHOOK_URL=your-botpress-webhook-url
BOTPRESS_BOT_SECRET=your-bot-secret

# Security
SECRET_KEY=your-secret-key
BOT_HMAC_SECRET=your-hmac-secret-32-chars-minimum
```

### Get LINE Credentials

1. Visit [LINE Developers Console](https://developers.line.biz/console/)
2. Create Provider & Channel
3. For **LINE Login**: Get Channel ID, Secret, set Callback URL
4. For **Messaging API**: Get Access Token, set Webhook URL

See [SETUP.md](SETUP.md) for detailed instructions.

## 📚 API Documentation

### Authentication
- `GET /auth/line/login` - Start LINE Login
- `GET /auth/line/callback` - LINE Login callback
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project

### Transactions
- `GET /api/v1/projects/{id}/transactions` - List transactions
- `POST /api/v1/projects/{id}/transactions` - Create transaction

### Bot API (Botpress Integration)
- `POST /api/v1/bot/context/resolve` - Resolve user context
- `POST /api/v1/bot/transactions/create` - Create transaction (idempotent)
- `POST /api/v1/bot/insights/export` - Export insights dataset

### LINE Webhook
- `POST /line/webhook` - Receive LINE events

Full API documentation: [SETUP.md](SETUP.md)

## 🤖 LINE Chatbot Commands

Users can send natural language messages:

```
จ่าย 350 เดินทาง ค่ารถ
รับ 1000 เงินเดือน
สรุปเดือนนี้
งบเดินทาง
วิเคราะห์การใช้จ่าย
```

Botpress will understand, extract data, and call Flask API.

## 🗂️ Project Structure

```
line-botpress/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── models/              # Database models (9 models)
│   ├── routes/              # API endpoints (6 blueprints)
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS
├── instance/
│   └── finance.db           # SQLite database
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
├── run.py                   # Entry point
├── start.sh                 # Startup script
├── README.md
└── SETUP.md                 # Detailed setup guide
```

## 📊 Database Schema

15 tables including:
- `user` - LINE authenticated users
- `project` - Projects/households
- `category` - Income/expense categories
- `transaction` - Financial transactions
- `budget` - Budget limits
- `recurring_rule` - Recurring transactions
- `bot_nonce` - Anti-replay tokens
- `idempotency_key` - Idempotency tracking
- `insight` - AI-generated insights

See [PRD-Frontend-Backend.md](PRD-Frontend-Backend.md) for complete schema.

## 🚀 Deployment

### Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set environment variables in Railway dashboard.

### Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
SESSION_COOKIE_SECURE=True
LINE_REDIRECT_URI=https://your-domain.com/auth/line/callback
```

## 🧪 Testing

```bash
# Run tests
pytest

# Test API endpoints
curl http://localhost:5000/auth/me
curl http://localhost:5000/api/v1/projects
```

## 🛠️ Development

```bash
# Format code
black .

# Lint
flake8 .

# Run with debug
FLASK_ENV=development python run.py
```

## 📖 Documentation

- [README.md](README.md) - This file
- [SETUP.md](SETUP.md) - Detailed setup guide
- [PRD-Frontend-Backend.md](PRD-Frontend-Backend.md) - Product requirements

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 💬 Support

- GitHub Issues: [Issues](https://github.com/tetipong2542/line-botpress/issues)
- Documentation: [SETUP.md](SETUP.md)

## 🌟 Features Roadmap

- [ ] Export to CSV/PDF
- [ ] OCR for bill scanning
- [ ] Charts and visualizations
- [ ] Mobile app (React Native)
- [ ] Multi-currency support
- [ ] Bank account integration

## 📊 Statistics

- **26 Python files** (2,532 lines of code)
- **15 Database tables**
- **25+ API endpoints**
- **HMAC security** + **Idempotency** + **Signature verification**

---

Made with ❤️ by [tetipong2542](https://github.com/tetipong2542)

**Star ⭐ this repo if you find it useful!**
