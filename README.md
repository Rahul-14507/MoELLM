# MOELLM — Multi-Context Conflict Resolver

> **Real preferences. Real market data. Real conflicts. Resolved.**

MOELLM is an AI-powered decision engine that resolves the gap between what you *want* and what the *market actually offers*. You describe your ideal product or service in plain English, set hard constraints, and MOELLM searches the live web, detects every conflict, and uses a large language model to recommend the single best option — with a clear, concise rationale.

---

## How It Works

MOELLM runs a three-stage pipeline on every request:

```
User Input → Live Web Search → Conflict Detection → LLM Resolution → Verdict
```

### Stage 1 — Live Market Search
The Tavily Search API performs a context-aware, domain-scoped search based on your preference. The system automatically classifies your query (laptop, flight, hotel, or generic) and selects the most relevant search domains (e.g., `amazon.com`, `kayak.com`, `booking.com`).

### Stage 2 — Structured Conflict Detection
Each result is evaluated against your constraints by the rule-based Conflict Engine:

| Constraint Type | Severity | Examples |
|---|---|---|
| Budget ceiling | **Hard** | Price exceeds `max $1200` |
| Availability today | **Hard** | No same-day pickup available |
| Brand preference | Soft | Different brand than requested |
| Display type (OLED/IPS) | Soft | Non-OLED screen |

Products are scored (0–100) and ranked: hard-constraint violators are filtered to the bottom, soft-conflict products are sorted by match score.

### Stage 3 — LLM-Powered Resolution
The evaluated product context is sent to **Qwen 2.5-7B-Instruct** (via Featherless AI) with a precisely crafted prompt. The model returns a clean, opinionated verdict:

```
BEST CHOICE: [Product Title]

WHY IT WON: [Primary reason — typically the constraint that mattered most]

THE TRADEOFF: [What was sacrificed to make this work]
```

The response streams token-by-token to the frontend in real time via **Server-Sent Events (SSE)**.

---

## Tech Stack

### Backend
| Technology | Role |
|---|---|
| **FastAPI** | Async REST API with SSE streaming |
| **Tavily Python SDK** | Context-aware live web search |
| **OpenAI-compatible SDK** | Interface to Featherless AI/Qwen 2.5 |
| **Pydantic** | Request validation and schema enforcement |
| **python-dotenv** | Environment variable management |

### Frontend
| Technology | Role |
|---|---|
| **React 18** | Component-based UI |
| **Vite 5** | Fast development server and build tool |
| **Vanilla CSS** | Custom design system with dark theme |

### AI Services
| Service | Purpose |
|---|---|
| **Tavily API** | Real-time web search (products, flights, hotels) |
| **Featherless AI** | OpenAI-compatible inference endpoint |
| **Qwen 2.5-7B-Instruct** | Conflict resolution and recommendation model |

---

## Project Structure

```
MoELLM/
├── backend/
│   ├── main.py               # FastAPI app — /resolve SSE endpoint
│   ├── scraper.py            # Tavily integration + multi-context query routing
│   ├── conflict_engine.py    # Rule-based constraint parsing and product scoring
│   ├── llm_client.py         # Prompt construction and Qwen streaming
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Root component — SSE consumer and state manager
│   │   ├── components/
│   │   │   ├── InputPanel.jsx    # Preference and constraint inputs
│   │   │   ├── StepsPanel.jsx    # Live pipeline progress tracker
│   │   │   └── OutputPanel.jsx   # Conflict cards + streaming resolution box
│   │   └── styles/
│   │       └── main.css          # Full design system — dark theme, tokens, components
│   ├── index.html
│   └── package.json
│
├── .env                      # API keys (not committed)
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Tavily API key](https://tavily.com)
- A [Featherless AI API key](https://featherless.ai)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/MoELLM.git
cd MoELLM
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=tvly-your-key-here
FEATHERLESS_API_KEY=rc_your-key-here
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## Usage Examples

### Laptop Shopping
| Field | Input |
|---|---|
| **Preference** | `I want a high-end ASUS gaming laptop with an OLED screen` |
| **Constraints** | `budget under $1800, must have store pickup today` |

### Flight Search
| Field | Input |
|---|---|
| **Preference** | `I want to fly from Hyderabad to London, non-stop, window seat` |
| **Constraints** | `budget under $1000, economy class` |

### Hotel Booking
| Field | Input |
|---|---|
| **Preference** | `I want a budget hotel near central London with free breakfast` |
| **Constraints** | `under $100 per night, free cancellation` |

---

## API Reference

### `POST /resolve`

Initiates a conflict resolution pipeline. Returns a stream of **Server-Sent Events**.

**Request Body**
```json
{
  "preference": "string (min 5 chars)",
  "constraints": "string (min 5 chars)"
}
```

**Event Stream**

| Event Type | Payload | Description |
|---|---|---|
| `step` | `{ step, message }` | Pipeline progress update |
| `products` | `{ data: [...] }` | Raw search results |
| `conflicts` | `{ data: [...] }` | Evaluated conflict data per product |
| `token` | `{ content }` | LLM response chunk (streaming) |
| `done` | — | Pipeline complete |
| `error` | `{ message }` | Error details |

### `GET /health`

Returns `{ "status": "ok" }`. Used for liveness checks.

---

## Conflict Engine — Constraint Schema

The backend parses natural language constraints into structured fields:

| Parsed Field | Extracted From | Example |
|---|---|---|
| `max_budget` | `$X`, `under $X`, `max $X` | `"budget $1200"` → `1200.0` |
| `requires_today` | `today`, `pickup`, `same day` | `"need it today"` → `true` |
| `max_shipping_days` | `X days` | `"within 3 days"` → `3` |

Preferences are separately parsed for brand, display type (OLED/IPS), and tier (budget/mid-range/high-end) to generate soft-constraint scores.

---

## Supported Search Contexts

MOELLM automatically detects the type of your query and routes it to the correct search strategy:

| Context | Trigger Keywords | Search Domains |
|---|---|---|
| `laptop` | laptop, notebook, MacBook, gaming laptop | Amazon, Best Buy, Newegg, Walmart |
| `flight` | fly, flight, airline, Hyderabad, London | Kayak, Skyscanner, Expedia, MakeMyTrip |
| `hotel` | hotel, stay, resort, hostel, Airbnb | Booking.com, Hotels.com, Airbnb, Expedia |
| `generic` | *(fallback for all other queries)* | Amazon, Best Buy, Walmart |

---

## License

MIT License. See `LICENSE` for details.
