# 🚀 Deployment Guide: AutoAbsen 24/7

To keep this bot running 24/7 without your laptop, you have 3 main options.

## Option 1: Cheap VPS (Recommended)
Rent a small Linux server ($4-5/mo) like DigitalOcean Droplet, Linode, or Hetzner.

1. **Install Docker**: `curl -fsSL https://get.docker.com | sh`
2. **Clone Repo**: `git clone https://github.com/dhyoprd/AutoAbsen.git`
3. **Setup .env**: Copy your .env content
4. **Run**: `docker-compose up -d`

## Option 2: GitHub Actions (Free, Scheduled Only)
Only works for **scheduled** reports (e.g., every day at 8 AM), NOT for the Telegram Bot (since that needs to listen constantly).

1. Create `.github/workflows/daily_report.yml`
2. Add secrets to GitHub Repository Settings
3. It will spin up a runner, execute the script, and die.

## Option 3: Always-On Cloud Free Tiers
- **Railway / Render**: Might suspend if inactive, but generally good for bots.
- **Oracle Cloud**: Has a generous "Always Free" tier ARM instance.
- **Fly.io**: Good for small apps.

**Since we Dockerized it, Option 1 or 3 is easiest!**
