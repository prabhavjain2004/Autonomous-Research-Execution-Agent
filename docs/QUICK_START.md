# 🚀 Quick Start Guide

Get the Autonomous Research Agent running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- Git (for cloning)
- Internet connection

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent.git
cd Autonomous-Research-Execution-Agent
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install
```

This will take a few minutes to download all dependencies (~300MB for Playwright browsers).

### 4. Get OpenRouter API Key (FREE)

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Click "Sign Up" (top right)
3. Sign up with Google, GitHub, or email
4. Go to "API Keys" section
5. Click "Create Key"
6. Copy your API key

**Note**: OpenRouter provides free access to many AI models. No credit card required!

### 5. Configure Environment

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Open `.env` in your text editor and paste your API key:

```env
OPENROUTER_API_KEY=your_actual_api_key_here
```

Save and close the file.

### 6. Run the Application

**Option A: Web Interface (Recommended)**

```bash
python main.py server
```

Then open your browser to: `http://localhost:8000`

**Option B: Command Line**

```bash
python main.py cli "Research the latest trends in artificial intelligence"
```

## 🎉 You're Done!

The system will:
1. Initialize the agents
2. Start researching your topic
3. Analyze the findings
4. Generate strategic recommendations
5. Display results with confidence scores

## Example Usage

### Web Interface

1. Open `http://localhost:8000`
2. Enter your research goal: "Research quantum computing applications"
3. Click "Start Research"
4. Watch the agents work in real-time
5. View results when complete

### Command Line

```bash
# Basic research
python main.py cli "Research electric vehicle market trends"

# With custom session ID
python main.py cli "Research renewable energy" --session-id energy-research-001
```

## Common Issues

### "OPENROUTER_API_KEY is required"

**Solution**: Make sure you:
1. Created the `.env` file (copied from `.env.example`)
2. Added your actual API key (not the placeholder text)
3. Saved the file

### "Module not found" errors

**Solution**: Make sure you:
1. Activated the virtual environment
2. Installed all dependencies: `pip install -r requirements.txt`

### Playwright browser errors

**Solution**: Install Playwright browsers:
```bash
playwright install
```

### Port 8000 already in use

**Solution**: Use a different port:
```bash
python main.py server --port 3000
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check out [module READMEs](agents/README.md) for architecture details
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Join discussions on GitHub

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent/discussions)

## What's Happening Behind the Scenes?

When you run a research task:

1. **Boss Agent** receives your goal and creates a plan
2. **Research Agent** searches the web and gathers information
3. **Analyst Agent** analyzes findings and extracts insights
4. **Strategy Agent** generates actionable recommendations
5. **Boss Agent** evaluates quality and aggregates results

Each step includes:
- Confidence scoring (self + boss evaluation)
- Automatic retries if quality is low
- Structured logging for transparency
- Session persistence for audit trails

## Free Tier Limits

OpenRouter's free tier includes:
- Access to multiple AI models
- Reasonable rate limits
- No credit card required
- Perfect for testing and development

For production use, consider upgrading to a paid plan for higher limits.

## Tips for Best Results

1. **Be Specific**: "Research AI trends in healthcare 2024" is better than "AI trends"
2. **Use Context**: Provide background information when relevant
3. **Check Confidence**: Higher confidence scores indicate better results
4. **Review Sources**: Check the sources used for research
5. **Iterate**: Use insights from one research to inform the next

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.10 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 1GB free space (for dependencies and data)
- **Network**: Stable internet connection

## What Gets Created?

The system automatically creates these directories:
- `data/` - SQLite database for sessions
- `logs/` - Structured JSON logs
- `outputs/` - Research results (if configured)

These are excluded from Git (see `.gitignore`).

---

**Ready to start researching? Run `python main.py server` and open http://localhost:8000!**
