# 🚀 Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `.env` file and fill in your LINE credentials:

```env
# LINE Login (OAuth2) - Get from LINE Developers Console
LINE_CHANNEL_ID=your-channel-id-here
LINE_CHANNEL_SECRET=your-channel-secret-here
LINE_REDIRECT_URI=http://localhost:5000/auth/line/callback

# LINE Messaging API - For chatbot
LINE_CHANNEL_ACCESS_TOKEN=your-access-token-here

# Botpress - Already configured
BOTPRESS_WEBHOOK_URL=https://webhook.botpress.cloud/68043144-896b-4278-b4d3-66693df66942

# Security - Change these in production!
SECRET_KEY=your-secret-key-change-this
BOT_HMAC_SECRET=your-hmac-secret-minimum-32-characters
```

### 3. Get LINE Credentials

#### For LINE Login:

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Create a new provider (or use existing)
3. Create a new channel → **LINE Login**
4. In channel settings:
   - Copy **Channel ID** → paste to `LINE_CHANNEL_ID`
   - Copy **Channel Secret** → paste to `LINE_CHANNEL_SECRET`
   - Add Callback URL: `http://localhost:5000/auth/line/callback`

#### For LINE Messaging API (Chatbot):

1. In LINE Developers Console
2. Create a new channel → **Messaging API**
3. In channel settings:
   - Copy **Channel Access Token** → paste to `LINE_CHANNEL_ACCESS_TOKEN`
   - Copy **Channel Secret** → paste to `LINE_CHANNEL_SECRET`
   - Set Webhook URL: `https://your-server.com/line/webhook` (use ngrok for local)

### 4. Initialize Database

```bash
export FLASK_APP=run.py
flask init-db
```

### 5. Run Application

**Option A: Using startup script**
```bash
./start.sh
```

**Option B: Manual**
```bash
export FLASK_APP=run.py
python run.py
```

Application will start at: **http://localhost:5000**

---

## 📝 Testing the Application

### 1. Test Web Interface

Open browser: http://localhost:5000

You should see the login page with "Login with LINE" button.

### 2. Test API Endpoints

```bash
# Test auth endpoint (should return 401 - not logged in)
curl http://localhost:5000/auth/me

# Test projects endpoint (should return 401)
curl http://localhost:5000/api/v1/projects
```

### 3. Test LINE Login Flow

1. Click "Login with LINE" button
2. You'll be redirected to LINE authorization page
3. Approve the app
4. You'll be redirected back and logged in

---

## 🔧 For Local Development with LINE Webhook

Since LINE webhooks require HTTPS, use **ngrok**:

### Install ngrok
```bash
# macOS
brew install ngrok

# or download from https://ngrok.com/download
```

### Start ngrok tunnel
```bash
ngrok http 5000
```

This will give you a public HTTPS URL like:
```
https://abc123.ngrok.io -> http://localhost:5000
```

### Update LINE Webhook URL

1. Go to LINE Developers Console
2. Your Messaging API channel → Webhook settings
3. Set Webhook URL: `https://abc123.ngrok.io/line/webhook`
4. Enable "Use webhook"

---

## 🤖 Setting up Botpress

### 1. Botpress Configuration

Your webhook URL is already set:
```
https://webhook.botpress.cloud/68043144-896b-4278-b4d3-66693df66942
```

### 2. Create Actions in Botpress

In your Botpress bot, create actions to call Flask API:

#### Action: `create_transaction`

```javascript
const axios = require('axios');
const crypto = require('crypto');

// Configuration
const botId = 'botpress-prod';
const botSecret = process.env.BOT_HMAC_SECRET || 'your-secret';
const flaskUrl = process.env.FLASK_URL || 'https://your-server.com';

// Generate HMAC
const timestamp = Math.floor(Date.now() / 1000).toString();
const payload = {
  event_id: event.id,
  line_user_id: event.payload.userId,
  type: workflow.type,
  category_id: workflow.category_id,
  amount: workflow.amount,
  note: workflow.note
};

const body = JSON.stringify(payload);
const message = `${botId}:${timestamp}:${body}`;
const signature = crypto.createHmac('sha256', botSecret).update(message).digest('hex');

// Call Flask API
try {
  const response = await axios.post(
    `${flaskUrl}/api/v1/bot/transactions/create`,
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
        'X-BOT-ID': botId,
        'X-BOT-TS': timestamp,
        'X-BOT-HMAC': signature
      }
    }
  );

  workflow.transaction = response.data.transaction;
  workflow.budget_status = response.data.budget_status;

} catch (error) {
  console.error('Failed to create transaction:', error.message);
  workflow.error = error.message;
}
```

### 3. Create Intents

**Intent: `create_expense`**
```
Utterances:
- จ่าย {amount} {category} {note}
- ใช้ {amount} {category}
- expense {amount} {category}

Entities:
- @amount (number)
- @category (text)
- @note (any - optional)
```

**Intent: `create_income`**
```
Utterances:
- รับ {amount} {category} {note}
- ได้ {amount} {category}
- income {amount} {category}
```

---

## 🐛 Troubleshooting

### Database Error
```bash
# Remove old database and reinitialize
rm instance/finance.db
flask init-db
```

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
python run.py --port 8000
```

### LINE Webhook 401 Error
- Check `LINE_CHANNEL_SECRET` in `.env` is correct
- Verify webhook signature verification logic

### Botpress HMAC Error
- Check `BOT_HMAC_SECRET` matches between Flask and Botpress
- Verify timestamp is within 5-minute window

---

## 📚 Next Steps

1. **Setup LINE Channels** (see above)
2. **Configure Botpress** (create intents and actions)
3. **Test End-to-End** (send message in LINE → Botpress → Flask → Reply)
4. **Deploy to Production** (Railway, Heroku, or your server)

---

## 🎯 Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Login page |
| `/app` | GET | App home (requires login) |
| `/auth/line/login` | GET | Start LINE Login |
| `/auth/line/callback` | GET | LINE Login callback |
| `/auth/logout` | POST | Logout |
| `/auth/me` | GET | Get current user |
| `/api/v1/projects` | GET/POST | Projects CRUD |
| `/api/v1/projects/{id}/transactions` | GET/POST | Transactions CRUD |
| `/api/v1/projects/{id}/categories` | GET | Categories list |
| `/api/v1/projects/{id}/budgets` | GET | Budgets list |
| `/api/v1/bot/context/resolve` | POST | Bot: Resolve user context |
| `/api/v1/bot/transactions/create` | POST | Bot: Create transaction |
| `/api/v1/bot/insights/export` | POST | Bot: Export insights |
| `/line/webhook` | POST | LINE webhook receiver |

---

## 💡 Tips

- Use **Postman** or **curl** to test API endpoints
- Check `instance/finance.db` with **DB Browser for SQLite** to see data
- View logs in terminal where Flask is running
- Use **ngrok** for local LINE webhook testing
- Keep `.env` file secure - never commit to git

---

Good luck! 🚀
