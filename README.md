# 💰 จดรายรับรายจ่าย (Income-Expense Tracker)

แอปพลิเคชันจดรายรับรายจ่ายที่ใช้งานผ่าน **LINE Chatbot** และ **Web Interface** พัฒนาด้วย **Python Flask + SQLite** พร้อม **Botpress AI** สำหรับการวิเคราะห์และสนทนาอัจฉริยะ

## 🎯 Features

### ✅ Core Features (MVP)
- 🔐 **LINE Login** - เข้าสู่ระบบด้วย LINE OAuth2
- 📊 **Multi-Project** - รองรับหลายโปรเจค/ครอบครัว
- 💸 **Transaction Management** - บันทึกรายรับ-รายจ่าย
- 🏷️ **Category System** - จัดหมวดหมู่รายรับ-รายจ่าย
- 💰 **Budget Envelope** - ตั้งงบประมาณรายหมวด
- 🔁 **Recurring Transactions** - รายการประจำ (รายวัน/รายสัปดาห์/รายเดือน)
- 🤖 **LINE Chatbot** - บันทึกผ่านการพิมพ์แชท
- 🧠 **AI Insights** - วิเคราะห์การใช้จ่ายด้วย Botpress

### 🔒 Security Features
- ✅ HMAC signature verification for Botpress API
- ✅ LINE webhook signature verification
- ✅ Idempotency key for preventing duplicate operations
- ✅ Bot nonce for replay attack prevention
- ✅ Session-based authentication

## 🏗️ Architecture

```
User (LINE)
  ↓
Botpress (Intent Recognition + NLU)
  ↓ REST API with HMAC
Flask Backend (/api/v1/bot/*)
  ↓ Business Logic
SQLite Database
  ↓ Response
Botpress (Natural Language Response)
  ↓
LINE (User-friendly message)
```

## 📁 Project Structure

```
python-line-Income-expenses/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── models/               # Database models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── category.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   ├── recurring.py
│   │   ├── security.py
│   │   └── insight.py
│   ├── routes/               # API endpoints
│   │   ├── web.py           # HTML pages
│   │   ├── auth.py          # LINE Login OAuth2
│   │   ├── api.py           # REST API
│   │   ├── bot.py           # Botpress integration
│   │   └── line.py          # LINE webhook
│   ├── services/            # Business logic
│   │   ├── transaction_service.py
│   │   ├── botpress_service.py
│   │   └── init_service.py
│   ├── utils/               # Utilities
│   │   ├── helpers.py
│   │   ├── security.py
│   │   └── validators.py
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS files
├── instance/                # SQLite database
├── migrations/              # Database migrations
├── tests/                   # Unit tests
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
└── README.md
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- LINE Developer Account
- Botpress Account

### 2. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd python-line-Income-expenses

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Flask
SECRET_KEY=your-secret-key-change-this

# LINE Login (OAuth2)
LINE_CHANNEL_ID=your-line-channel-id
LINE_CHANNEL_SECRET=your-line-channel-secret
LINE_REDIRECT_URI=http://localhost:5000/auth/line/callback

# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=your-line-channel-access-token

# Botpress
BOTPRESS_WEBHOOK_URL=https://webhook.botpress.cloud/68043144-896b-4278-b4d3-66693df66942
BOTPRESS_BOT_SECRET=your-bot-secret

# Security
BOT_HMAC_SECRET=your-hmac-secret-minimum-32-characters
```

### 4. Initialize Database

```bash
# Create database tables
flask init-db
```

### 5. Run Application

```bash
# Development mode
python run.py

# Or using Flask CLI
flask run
```

Application will be available at: `http://localhost:5000`

## 📝 API Documentation

### Authentication

#### LINE Login
```
GET /auth/line/login
GET /auth/line/callback
POST /auth/logout
GET /auth/me
```

### Projects API

```
GET    /api/v1/projects                    # List projects
POST   /api/v1/projects                    # Create project
GET    /api/v1/projects/{id}               # Get project
PUT    /api/v1/projects/{id}               # Update project
DELETE /api/v1/projects/{id}               # Delete project
```

### Transactions API

```
GET    /api/v1/projects/{id}/transactions  # List transactions
POST   /api/v1/projects/{id}/transactions  # Create transaction
GET    /api/v1/transactions/{id}           # Get transaction
PUT    /api/v1/transactions/{id}           # Update transaction
DELETE /api/v1/transactions/{id}           # Delete transaction
```

### Categories API

```
GET    /api/v1/projects/{id}/categories    # List categories
POST   /api/v1/projects/{id}/categories    # Create category
```

### Budgets API

```
GET    /api/v1/projects/{id}/budgets       # List budgets
PUT    /api/v1/projects/{id}/budgets/{category_id}  # Upsert budget
```

### Bot API (Botpress Integration)

**Authentication:** Requires `X-BOT-ID`, `X-BOT-TS`, `X-BOT-HMAC` headers

```
POST /api/v1/bot/context/resolve          # Get user context
POST /api/v1/bot/transactions/create      # Create transaction (idempotent)
POST /api/v1/bot/insights/export          # Export dataset for insights
```

### LINE Webhook

```
POST /line/webhook                         # Receive LINE events
```

## 🤖 LINE Chatbot Commands

Users can send natural language messages to the LINE bot:

### Examples:

```
จ่าย 350 เดินทาง ค่ารถ
รับ 1000 เงินเดือน
สรุปเดือนนี้
งบเดินทาง
วิเคราะห์การใช้จ่าย
```

Botpress will:
1. Understand the intent
2. Extract entities (amount, category, note)
3. Call Flask API to create transaction
4. Reply with confirmation and budget status

## 🔧 Development

### Run Tests

```bash
pytest
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "description"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

### Code Style

```bash
# Format code
black .

# Lint
flake8 .
```

## 🚀 Deployment

### Deploy to Railway

1. Create account at [Railway.app](https://railway.app)

2. Install Railway CLI:
```bash
npm install -g @railway/cli
```

3. Deploy:
```bash
railway login
railway init
railway up
```

4. Set environment variables in Railway dashboard

### Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=<postgresql-url>  # Or use SQLite
SESSION_COOKIE_SECURE=True
```

## 🔐 Security Considerations

### HMAC Verification

Botpress calls to Flask API are verified using HMAC:

```python
# Botpress sends:
X-BOT-ID: botpress-prod
X-BOT-TS: 1234567890
X-BOT-HMAC: sha256_signature

# Flask verifies:
message = f"{bot_id}:{timestamp}:{body}"
expected = hmac.new(secret, message, sha256).hexdigest()
```

### Idempotency

Bot operations use `event_id` for idempotency:

```json
{
  "event_id": "line_msg_123456",
  "line_user_id": "U1234...",
  "type": "expense",
  "amount": 35000
}
```

Same `event_id` will return cached response.

## 📊 Database Schema

See `PRD-Frontend-Backend.md` for complete schema documentation.

Key tables:
- `user` - LINE authenticated users
- `project` - Projects/households
- `project_member` - Project memberships
- `category` - Income/expense categories
- `transaction` - Financial transactions
- `budget` - Budget limits per category
- `recurring_rule` - Recurring transactions
- `bot_nonce` - Anti-replay tokens
- `idempotency_key` - Idempotency tracking
- `insight` - AI-generated insights

## 🎨 Customization

### Add Custom Categories

Edit default categories in `app/routes/api.py`:

```python
default_categories = [
    ('expense', 'อาหาร', 'food', '🍜', '#FF6B6B'),
    # Add your categories here
]
```

### Modify Insight Policy

Edit project settings:

```python
settings.insight_max_records = 100  # Max records to send
settings.insight_max_days = 30      # Max days to look back
settings.insight_fields_level = 'minimal'  # minimal/standard/full
```

## 🐛 Troubleshooting

### Database Locked Error

```bash
# Close all connections and restart
rm instance/finance.db
flask init-db
```

### LINE Webhook Not Working

1. Check ngrok/cloudflare tunnel is running
2. Verify webhook URL in LINE Developers Console
3. Check signature verification

### Botpress Not Responding

1. Verify webhook URL in `.env`
2. Check Botpress bot is published
3. View Botpress logs for errors

## 📚 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
- [Botpress Documentation](https://botpress.com/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 📄 License

MIT License - See LICENSE file for details

## 👥 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Email: your-email@example.com

---

Made with ❤️ by Pond Dev
