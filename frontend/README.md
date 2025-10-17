# Fantasy Football Frontend

This is the Next.js React frontend for the Fantasy Football Dashboard, migrated from Streamlit.

## Features

- 🏈 **Team Matchup Display** - ESPN-style matchup headers with projected scores
- 📊 **Roster Tables** - Interactive player tables with position advantages
- 🤖 **AI Chat Interface** - Chat with the AI assistant for fantasy advice
- 💰 **Usage Monitor** - Real-time API cost tracking
- 📱 **Responsive Design** - Works on desktop and mobile

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - API calls

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   The `.env.local` file is already configured for local development.

3. **Start both backend and frontend:**
   ```bash
   npm start
   # or
   npm run dev
   ```

4. **Open** [http://localhost:3000](http://localhost:3000) in your browser

## 📜 Available Scripts

- **`npm start`** - Starts both backend (Python FastAPI) and frontend (Next.js) simultaneously
- **`npm run dev`** - Same as `npm start` - full development environment
- **`npm run frontend`** - Start only the Next.js frontend (port 3000)
- **`npm run backend`** - Start only the Python FastAPI backend (port 8000)
- **`npm run backend:uvicorn`** - Alternative way to start backend using uvicorn directly
- **`npm run build`** - Build the Next.js app for production
- **`npm run prod`** - Start the production build of Next.js only
- **`npm run lint`** - Run ESLint to check for code issues

## 🚀 Quick Start (One Command)

```bash
cd frontend
npm install
npm start
```

This will automatically:
- Start the Python FastAPI backend on http://localhost:8000
- Start the Next.js frontend on http://localhost:3000
- Display color-coded logs for both services

## API Integration

The frontend connects to the existing FastAPI backend running on port 8000. Make sure your backend is running:

```bash
# In the parent directory
python api/main.py
# or
uvicorn api.main:app --reload --port 8000
```

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000)

## Components

- **Dashboard** (`src/app/page.tsx`) - Main dashboard page
- **MatchupHeader** - ESPN-style team matchup display
- **RosterTable** - Player roster with position advantages
- **ChatInterface** - AI assistant chat
- **UsageMonitor** - API usage tracking

## API Client

The `src/lib/api.ts` file contains all API calls with proper error handling and TypeScript types.

## Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start
```

The app can be deployed to Vercel, Netlify, or any platform that supports Next.js.
