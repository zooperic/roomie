# Roomy Web Dashboard

Next.js 14 web interface for Project Roomy smart home inventory system.

## Tech Stack

- **Next.js 14** - App Router, Server Components
- **TypeScript** - Type safety
- **React Query** - Server state management
- **Axios** - HTTP client for Alfred API

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Alfred API running on port 8000

### Installation

```bash
cd roomie-web
npm install
```

### Development

```bash
# Start development server on port 3001
npm run dev
```

Dashboard: http://localhost:3001

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
roomie-web/
├── app/
│   ├── layout.tsx       # Root layout with providers
│   ├── page.tsx         # Main dashboard page
│   ├── globals.css      # Global styles
│   └── providers.tsx    # React Query provider
├── lib/
│   └── alfred-client.ts # API client for Alfred backend
├── components/          # Reusable components (future)
└── public/             # Static assets
```

## Features (Phase 3.1)

- ✅ Dashboard overview with system status
- ✅ Quick stats (inventory count, agents, events)
- ✅ Low stock warnings
- ✅ Recent activity feed
- ✅ Inventory grid view
- ✅ Real-time Alfred API connection
- ⏳ Recipe parser interface (Phase 3.3)
- ⏳ Shopping cart builder (Phase 3.4)
- ⏳ Analytics dashboard (Phase 3.2)

## API Integration

The dashboard connects to Alfred API at `http://localhost:8000`:

- `GET /health` - System status
- `POST /message` - Send messages to agents
- Force-agent routing with `force_agent` parameter

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_ALFRED_API=http://localhost:8000
```

## Current Status

**Phase 3.1 COMPLETE** - Dashboard foundation working with:
- Real Alfred API connection
- System health monitoring
- Mock inventory data (real API integration in 3.2)

**Next:** Phase 3.2 - Inventory managers with CRUD operations
