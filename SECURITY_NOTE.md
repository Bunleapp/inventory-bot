# 🔒 Security Note

## ⚠️ IMPORTANT: Regenerate Your Google Credentials

Your Google service account credentials were briefly exposed in git history. While we've removed them, you should:

### 1. Delete the Old Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: `telegram-bot-496917`
3. Go to **IAM & Admin** → **Service Accounts**
4. Find: `inventory-bot@telegram-bot-496917.iam.gserviceaccount.com`
5. Click the 3 dots → **Delete**

### 2. Create a New Service Account

1. Click **+ CREATE SERVICE ACCOUNT**
2. Name: `inventory-bot-v2`
3. Click **Create and Continue**
4. Role: **Editor**
5. Click **Done**

### 3. Generate New Credentials

1. Click on the new service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON**
5. Download the file
6. Save as `credentials.json` (locally only!)

### 4. Update Google Sheet Permissions

1. Open your Google Sheet
2. Click **Share**
3. Remove the old email: `inventory-bot@telegram-bot-496917.iam.gserviceaccount.com`
4. Add the new email from your new credentials.json
5. Give **Editor** access

### 5. Update Railway

1. Go to Railway dashboard
2. Variables tab
3. Update `GOOGLE_APPLICATION_CREDENTIALS_JSON` with the NEW credentials
4. Redeploy

## Files That Should NEVER Be Pushed

- ✅ `.env` - Protected by .gitignore
- ✅ `credentials.json` - Protected by .gitignore
- ✅ `railway_credentials.txt` - Protected by .gitignore
- ✅ `bot.log` - Protected by .gitignore

## Safe to Push

- ✅ `README.md` - Documentation
- ✅ `RAILWAY_DEPLOYMENT.md` - Instructions
- ✅ `.env.example` - Template (no real values)
- ✅ All `.py` files - Source code
- ✅ `requirements.txt` - Dependencies

## Current Status

✅ Credentials removed from GitHub
✅ .gitignore updated
✅ Clean code pushed

⚠️ **Next step: Regenerate credentials as described above**
