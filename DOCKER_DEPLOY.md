# 🐳 Docker Deployment (Recommended)

## Why Docker?

The mise Python installation is failing. Docker bypasses this completely by using an official Python image.

## What Changed

✅ Added `Dockerfile` - Builds the bot in a container
✅ Added `.dockerignore` - Keeps image clean
✅ Updated `railway.toml` - Uses Docker builder

## Deploy to Railway with Docker

### Automatic (Recommended)

Railway will automatically detect the Dockerfile and use it!

1. Push the code (already done)
2. Railway will auto-deploy using Docker
3. Check logs for success

### Manual (If needed)

If Railway doesn't auto-detect:

1. Go to Railway Dashboard
2. Click your service
3. Go to **Settings**
4. Under **Builder**, select **Dockerfile**
5. Click **Deploy**

## Expected Build Output

```
Building Docker image...
✓ Step 1/8 : FROM python:3.11-slim
✓ Step 2/8 : WORKDIR /app
✓ Step 3/8 : RUN apt-get update...
✓ Step 4/8 : COPY requirements.txt .
✓ Step 5/8 : RUN pip install...
✓ Step 6/8 : COPY . .
✓ Step 7/8 : CMD ["python", "main.py"]
Successfully built!
Starting container...
INFO | Connecting to Google Sheets...
INFO | Google Sheets connected ✓
INFO | Bot is running...
```

## Advantages of Docker

✅ **No mise errors** - Uses official Python image
✅ **Consistent builds** - Same environment every time
✅ **Faster deploys** - Docker caching
✅ **Industry standard** - Most production apps use Docker

## Environment Variables

Still need to set in Railway:

```
TELEGRAM_BOT_TOKEN = your_token
ALLOWED_USER_IDS = 1330942600,other_ids
GOOGLE_SHEET_ID = your_sheet_id
GOOGLE_APPLICATION_CREDENTIALS_JSON = {your credentials json}
LOW_STOCK_THRESHOLD = 10
TIMEZONE = Asia/Phnom_Penh
LOW_STOCK_CHECK_INTERVAL = 60
```

## Testing Locally with Docker

If you have Docker installed:

```bash
# Build the image
docker build -t inventory-bot .

# Run the container
docker run --env-file .env inventory-bot
```

## Troubleshooting

### Build fails at pip install

**Solution:** Check `requirements.txt` for typos

### Container starts but crashes

**Solution:** Check environment variables are set

### "Failed to connect to Google Sheets"

**Solution:** Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set correctly

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] Railway detects Dockerfile
- [ ] Build completes successfully
- [ ] Container starts
- [ ] Logs show "Google Sheets connected ✓"
- [ ] Bot responds to /start in Telegram

## This Should Work!

Docker is the most reliable way to deploy Python apps. The mise issue is completely bypassed.

🎉 **Your bot should deploy successfully now!**
