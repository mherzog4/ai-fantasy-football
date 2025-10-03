# 🏈 AI Fantasy Football Assistant

**Reverse Engineering ESPN's Fantasy Football API + AI-Powered Analysis**

Transform your fantasy football experience with an intelligent AI assistant that provides data-driven insights for lineup optimization, trade analysis, waiver wire recommendations, and player comparisons.

## 🚀 Features

### 🤖 AI Chat Interface (NEW!)
- **Natural Language Interaction**: Ask questions like "Who should I start this week?" or "Find me good trade targets"
- **Intelligent Tool Calling**: AI automatically uses the right analysis tools based on your questions
- **Streaming Responses**: Real-time responses with tool execution indicators
- **Conversation Context**: Maintains conversation history for better recommendations

### 📊 Advanced Analysis Tools
- **🎯 Lineup Optimization**: AI-powered starting lineup recommendations with current NFL data
- **⚡ Start/Sit Decisions**: Compare players with matchup analysis and injury reports
- **🔍 Waiver Wire Analysis**: Identify the best available pickups for your team
- **🤝 Trade Opportunities**: Discover realistic trade targets based on team needs

### 📈 Data-Driven Insights
- **Real-time ESPN Data**: Live roster, matchup, and projection data
- **Current NFL Information**: Weather, injuries, and defensive matchups
- **Rate-Limited AI Calls**: Cost-effective usage tracking
- **Multi-format Support**: Both chat interface and classic dashboard

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- ESPN Fantasy Football account with valid cookies
- OpenAI API key

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/mherzog4/ai-fantasy-football.git
   cd ai-fantasy-football
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

   Required variables:
   ```env
   # ESPN Authentication (from browser cookies)
   ESPN_S2=your_espn_s2_cookie
   ESPN_S2_ENCODED=url_encoded_version
   ESPN_AUTH=your_espn_auth_json
   SWID=your_swid_cookie
   
   # League Configuration
   LEAGUE_ID=your_league_id
   TEAM_ID=your_team_id
   SEASON=2025
   
   # OpenAI for AI features
   OPENAI_API_KEY=your_openai_key
   ```

## 🚀 Running the Application

### Option 1: AI Chat Interface (Recommended)

```bash
python start_chat.py
```

**Access at**: http://localhost:8501

**Features:**
- 🤖 Natural language interaction with your fantasy team
- 🎯 Automatic lineup optimization via chat
- ⚡ Smart start/sit recommendations  
- 🔍 Waiver wire analysis through conversation
- 🤝 Trade opportunity discovery

### Option 2: Classic Dashboard

```bash
python start_dashboard.py
```

**Access at**: http://localhost:8501

**Features:**
- 📊 Detailed roster and matchup views
- 🎯 Individual AI analysis tools
- 📈 Player projections and statistics

### Option 3: API Only

```bash
# FastAPI server only
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation**: http://localhost:8000/docs

## 💬 Chat Interface Examples

The AI assistant can handle natural language questions like:

- **"Who should I start this week?"** → Triggers lineup optimization
- **"Compare Travis Kelce vs Mark Andrews"** → Player comparison analysis  
- **"Find me some waiver wire pickups"** → Waiver wire recommendations
- **"What trades should I make?"** → Trade opportunity analysis
- **"Is my RB depth good enough?"** → Roster analysis and suggestions

## 🔧 API Endpoints

### ESPN Data Endpoints
- `GET /get_roster` - Your team's roster and projections
- `GET /get_matchup` - Current week matchup data

### AI Analysis Endpoints  
- `POST /ai/optimize_lineup` - Lineup optimization
- `POST /ai/compare_players` - Player comparisons
- `POST /ai/waiver_wire` - Waiver wire analysis
- `POST /ai/trade_analysis` - Trade recommendations

### Chat Endpoints (NEW!)
- `POST /chat` - Complete chat interaction
- `POST /chat/stream` - Streaming chat responses
- `POST /chat/enhanced` - Chat with real data integration

## 📋 Getting ESPN Credentials

1. **Log into ESPN Fantasy Football** in your browser
2. **Open Developer Tools** (F12)
3. **Go to Application/Storage tab** → Cookies
4. **Find cookies for fantasy.espn.com**:
   - `ESPN_S2` (long string)
   - `SWID` (format: `{ABC123-DEF456-...}`)
5. **Find League and Team IDs** in your fantasy URL:
   - URL: `fantasy.espn.com/football/team?leagueId=123456&teamId=7`
   - `LEAGUE_ID=123456`, `TEAM_ID=7`

## 💰 Cost Management

The application includes intelligent rate limiting to control OpenAI API costs:

- **Hourly spending limit**: $10/hour (configurable)
- **Token estimation**: Pre-calculates costs before API calls
- **Usage tracking**: Real-time cost monitoring in the UI
- **Smart caching**: Reduces redundant API calls

## 🧪 Testing

```bash
# Test individual components
python test_rate_limiting.py
python test_trade_analyzer.py
python test_waiver_filter.py
python test_improved_trades.py

# Test ESPN API connection
python espn_api.py
```

## 📁 Project Structure

```
├── api/                      # FastAPI backend
│   ├── main.py              # API endpoints
│   ├── ai_services.py       # OpenAI integration  
│   ├── chat_agent.py        # Chat agent with tool calling
│   ├── get_roster.py        # Roster data fetching
│   └── get_matchup.py       # Matchup data fetching
├── main_client.py           # AI Chat interface (NEW!)
├── chat_client.py           # Standalone chat app
├── client.py                # Classic Streamlit dashboard
├── espn_api.py              # Core ESPN API wrapper
├── rate_limiter.py          # OpenAI cost control
├── start_chat.py            # Chat interface launcher
├── start_dashboard.py       # Classic dashboard launcher
└── test_*.py                # Test scripts
```

## 🐳 Docker Support

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t fantasy-ai .
docker run -p 8000:8000 -p 8501:8501 fantasy-ai
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## ⚠️ Disclaimer

This project uses ESPN's undocumented API through reverse engineering. Use responsibly and be aware that:

- ESPN's API may change without notice
- Rate limiting is important to avoid being blocked
- This is for educational and personal use only

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- ESPN for providing fantasy football data
- OpenAI for powering the AI analysis
- Streamlit for the excellent UI framework
- FastAPI for the robust API backend

---

**Ready to dominate your fantasy league with AI? Start chatting with your new assistant!** 🏆
