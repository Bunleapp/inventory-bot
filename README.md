# 📦 Telegram Inventory Management Bot

A powerful Telegram bot for managing inventory with Google Sheets integration.

## Features

- ✅ Product management (Add, Delete, Search, View)
- 📊 Stock operations (Stock In, Stock Out, Sales)
- 📈 Dashboard with inventory summary
- 📉 Low stock alerts
- 📄 Export to CSV/PDF
- 🔔 Scheduled low-stock notifications
- 🔐 User authentication

## Tech Stack

- Python 3.11
- python-telegram-bot
- Google Sheets API
- APScheduler
- pandas & reportlab for exports

## Deployment on Railway

### 1. Environment Variables

Set these in Railway dashboard:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_USER_IDS=comma_separated_user_ids
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDENTIALS_PATH=credentials.json
LOW_STOCK_THRESHOLD=10
TIMEZONE=Asia/Phnom_Penh
LOW_STOCK_CHECK_INTERVAL=60
```

### 2. Google Credentials

**Important:** You need to add `credentials.json` as a Railway secret:

1. In Railway dashboard, go to your service
2. Click on **Variables** tab
3. Click **Raw Editor**
4. Add a new variable:
   ```
   GOOGLE_APPLICATION_CREDENTIALS_JSON=<paste your entire credentials.json content here>
   ```

Then update `config/settings.py` to handle this (see below).

### 3. Update settings.py for Railway

The bot needs to read credentials from environment variable on Railway.

### 4. Deploy

Railway will automatically:
- Detect Python
- Install dependencies from `requirements.txt`
- Run `python main.py`

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Bunleapp/inventory-bot.git
   cd inventory-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   ALLOWED_USER_IDS=your_user_id
   GOOGLE_SHEET_ID=your_sheet_id
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

4. Add your `credentials.json` file

5. Run the bot:
   ```bash
   python main.py
   ```

## Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download credentials as `credentials.json`
5. Create a Google Sheet with tabs: `Products`, `Transactions`
6. Share the sheet with the service account email

## Bot Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/dashboard` - View inventory summary
- `/lowstock` - Check low stock items
- `/history` - View recent transactions

## Project Structure

```
inventory-bot/
├── config/          # Configuration
├── handlers/        # Telegram handlers
├── services/        # Business logic
├── utils/           # Utilities
├── main.py          # Entry point
└── requirements.txt # Dependencies
```

## License

MIT License
