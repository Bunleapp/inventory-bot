# 🚂 Railway Deployment Guide

## Step-by-Step Deployment

### 1. Prepare Your credentials.json

Open your `credentials.json` file and copy **ALL** the content. It should look like:

```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  ...
}
```

### 2. Set Up Railway Project

1. Go to [Railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose `Bunleapp/inventory-bot`

### 3. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

#### Required Variables:

```bash
TELEGRAM_BOT_TOKEN=8954170864:AAGc7riqOxpsyvSTlr1qHXHZi8oeAZNtC7c
ALLOWED_USER_IDS=1330942600
GOOGLE_SHEET_ID=1AIJ_TIRcvKFAQpNi0O8DTobJ9Naes3cRO4Zbos4RU68
LOW_STOCK_THRESHOLD=10
TIMEZONE=Asia/Phnom_Penh
LOW_STOCK_CHECK_INTERVAL=60
```

#### Google Credentials (IMPORTANT):

Click **"RAW Editor"** and add:

```
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}
```

**⚠️ Paste the ENTIRE credentials.json content as a single line!**

### 4. Deploy

Railway will automatically:
1. ✅ Detect Python 3.11
2. ✅ Install dependencies
3. ✅ Run `python main.py`
4. ✅ Keep the bot running 24/7

### 5. Check Logs

In Railway dashboard:
- Click on **"Deployments"**
- Click on the latest deployment
- View logs to confirm bot started:

```
INFO │ Connecting to Google Sheets…
INFO │ Google Sheets connected ✓
INFO │ Bot is running…
```

## Troubleshooting

### Build Failed: pip install error

**Solution:** The updated `requirements.txt` and `nixpacks.toml` should fix this.

### Google Sheets Authentication Error

**Problem:** credentials.json not found

**Solution:** 
1. Make sure you added `GOOGLE_APPLICATION_CREDENTIALS_JSON` variable
2. The value must be the ENTIRE JSON content (no line breaks in the middle of strings)
3. Copy from `{` to `}` including all content

### Bot Not Responding

**Check:**
1. Bot token is correct
2. User ID is in ALLOWED_USER_IDS
3. Google Sheet is shared with service account email
4. Logs show "Bot is running"

## Files Added for Railway

- ✅ `Procfile` - Tells Railway how to run the bot
- ✅ `runtime.txt` - Specifies Python version
- ✅ `nixpacks.toml` - Build configuration
- ✅ Updated `config/settings.py` - Handles Railway credentials

## Cost

Railway offers:
- **$5 free credit** per month
- This bot uses minimal resources
- Should run free or very cheap (~$1-2/month)

## Monitoring

Railway provides:
- 📊 CPU/Memory usage graphs
- 📝 Real-time logs
- 🔔 Deployment notifications
- ⚡ Auto-restart on crashes

## Need Help?

Check Railway logs first:
```
Railway Dashboard → Your Service → Deployments → View Logs
```

Common issues are usually:
1. Missing environment variables
2. Incorrect credentials format
3. Google Sheet permissions
