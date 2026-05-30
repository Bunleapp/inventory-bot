# 🔧 Railway Build Fix

## The Problem

Railway is using `mise` to install Python, but it's failing with attestation errors.

## The Solution

We've added multiple fixes:

### 1. Files Added/Updated

- ✅ `.mise.toml` - Disables attestation checks
- ✅ `nixpacks.toml` - Sets environment variables
- ✅ `railway.toml` - Configures Railway deployment
- ✅ `runtime.txt` - Specifies Python 3.11

### 2. Environment Variables to Add in Railway

Go to Railway Dashboard → Your Service → Variables → Add these:

```
MISE_PYTHON_GITHUB_ATTESTATIONS = false
PYTHONUNBUFFERED = 1
```

### 3. Redeploy

After pushing these changes:

1. Railway will auto-detect the new config
2. Or manually click **Deploy** in Railway dashboard
3. Watch the logs

### 4. Expected Build Output

You should see:
```
✓ Installing Python 3.11
✓ Installing dependencies
✓ Starting application
INFO | Connecting to Google Sheets...
INFO | Google Sheets connected ✓
INFO | Bot is running...
```

## If Build Still Fails

### Option A: Try Different Python Version

Edit `runtime.txt`:
```
python-3.10
```

### Option B: Use Docker Instead

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Then in Railway:
1. Settings → Builder → Select **Dockerfile**
2. Redeploy

### Option C: Contact Railway Support

If nothing works, Railway support is very responsive:
- Discord: https://discord.gg/railway
- Email: team@railway.app

## Current Configuration Summary

| File | Purpose |
|------|---------|
| `.mise.toml` | Disables attestation for mise |
| `nixpacks.toml` | Build configuration |
| `railway.toml` | Railway-specific settings |
| `runtime.txt` | Python version |
| `Procfile` | Start command |
| `requirements.txt` | Dependencies |

## Verification Checklist

Before deploying, verify:

- [ ] All environment variables set in Railway
- [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON` is valid JSON
- [ ] Google Sheet is shared with service account
- [ ] Bot token is correct
- [ ] User IDs are in `ALLOWED_USER_IDS`

## Still Getting "Failed to connect to Google Sheets"?

This is a **different issue** from the build error. It means:

1. ❌ `GOOGLE_APPLICATION_CREDENTIALS_JSON` not set
2. ❌ JSON is invalid (use jsonlint.com to validate)
3. ❌ Google Sheet not shared with service account email

**Fix:**
1. Copy your entire `credentials.json` content
2. Validate at https://jsonlint.com
3. Copy the minified version
4. Paste in Railway as `GOOGLE_APPLICATION_CREDENTIALS_JSON`
5. Make sure Google Sheet is shared with the email from credentials

## Success Indicators

✅ Build completes without errors
✅ Logs show "Google Sheets connected ✓"
✅ Logs show "Bot is running..."
✅ Bot responds to /start command in Telegram

## Need More Help?

Check the logs in Railway:
```
Dashboard → Your Service → Deployments → Latest → View Logs
```

Look for specific error messages and search them.
