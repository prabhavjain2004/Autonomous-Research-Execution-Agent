# Tavily API Setup Guide

Tavily is a search API specifically designed for AI agents. It provides reliable, high-quality search results without rate limiting issues.

## Why Tavily?

- ✅ **No Rate Limiting**: Designed for AI agents with generous limits
- ✅ **High Quality Results**: Optimized for AI consumption
- ✅ **Fast & Reliable**: Better than scraping DuckDuckGo/Google
- ✅ **Free Tier Available**: 1000 searches/month free

## How to Get Your API Key

### Step 1: Sign Up
1. Go to https://tavily.com
2. Click "Get Started" or "Sign Up"
3. Create an account (free)

### Step 2: Get API Key
1. After signing in, go to your dashboard
2. Find your API key in the "API Keys" section
3. Copy the API key

### Step 3: Add to .env File
1. Open your `.env` file
2. Find the line: `TAVILY_API_KEY=your_tavily_api_key_here`
3. Replace `your_tavily_api_key_here` with your actual API key
4. Save the file

Example:
```
TAVILY_API_KEY=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
```

### Step 4: Restart the Server
```bash
# Stop the current server (Ctrl+C)
# Then restart:
python main.py server
```

## Testing

Once configured, the system will automatically:
1. Try Tavily first (most reliable)
2. Fall back to DuckDuckGo if Tavily fails
3. Fall back to Google if both fail

You should see in the logs:
```
"Tavily search completed: 5 results"
```

## Free Tier Limits

- **1000 searches per month** (free)
- **5 results per search** (default)
- **Advanced search depth** included

For most testing and development, the free tier is sufficient!

## Troubleshooting

### "Tavily API key not configured"
- Make sure you added the key to `.env`
- Make sure there are no extra spaces
- Restart the server after adding the key

### "Tavily API returned status 401"
- Your API key is invalid
- Double-check you copied it correctly
- Generate a new key from the Tavily dashboard

### "Tavily API returned status 429"
- You've exceeded your monthly limit
- Upgrade your plan or wait for next month
- System will automatically fall back to DuckDuckGo/Google

## Alternative: Continue Without Tavily

If you don't want to use Tavily, the system will still work with DuckDuckGo and Google, but you may experience rate limiting. To avoid rate limiting:

1. Wait longer between searches (15-30 minutes)
2. Use a VPN to change your IP
3. Try simpler, less specific queries
4. Use the demo mode (coming soon)
