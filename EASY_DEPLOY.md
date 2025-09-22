# 🚀 Easy 3-Step Deployment

## Step 1: Push to GitHub
1. **Double-click** `push_to_github.bat`
2. **Go to GitHub.com** and create new repository called `mcp-host`
3. **Copy the repo URL** and run the commands shown in the script

## Step 2: Deploy to Coolify
1. **Open Coolify** → New Resource → Application
2. **Paste your GitHub URL:** `https://github.com/yourusername/mcp-host`
3. **Set Build Pack:** Docker Compose

## Step 3: Environment Variables
Add these in Coolify:

```
SECRET_KEY=yRXnz9HGEjmZlJQGJ8K1vF2sB7N3P4T6uM8Y2wX5qA=
NODE_ENV=production
ENVIRONMENT=production
```

## 🎉 Done!
Your MCP Host will be running at your Coolify URL!

### Test it:
- Health: `https://yourdomain.com/health`
- Dashboard: `https://yourdomain.com`

### Connect to ChatGPT:
- Authorization URL: `https://yourdomain.com/auth/authorize`
- Token URL: `https://yourdomain.com/auth/token`