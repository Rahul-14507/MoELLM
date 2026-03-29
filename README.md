# MoELLM: Intelligent Mixture-of-LLM Conflict Resolver

MoELLM is a sophisticated routing and conflict resolution engine designed to optimize LLM selection based on real-world constraints such as **latency**, **cost**, **accuracy**, and **privacy**. It dynamically routes user queries to the most appropriate model from the Qwen 2.5 family, ensuring optimal performance for specific tasks like RAG, coding, and reasoning.

## 🚀 Key Features

- **Dynamic Routing**: Automatically selects the best model based on weighted user priorities.
- **Constraint Resolution**: Handles hard constraints (e.g., maximum latency, privacy requirements) and soft constraints (e.g., task fit).
- **Streaming Support**: Real-time streaming of LLM responses from the winning model.
- **Multi-Task Optimization**: Specialized configurations for RAG, Code Generation, Reasoning, Creative Writing, and Summarization.
- **Conflict Feedback**: Detailed explanations of why a specific model was chosen or overridden.

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Validation**: [Pydantic](https://docs.pydantic.dev/)
- **Client**: OpenAI SDK (configured for Featherless.ai)
- **Server**: Uvicorn

### Frontend
- **Framework**: [React](https://reactjs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: Vanilla CSS with modern aesthetics

## 📂 Project Structure

```bash
MoELLM/
├── moellm-resolver/
│   ├── backend/          # FastAPI server and resolution logic
│   │   ├── main.py       # API endpoints
│   │   ├── resolver.py   # Routing & penalty logic
│   │   ├── models_config.py # Model metadata and stats
│   │   └── qwen_client.py   # Featherless/OpenAI API client
│   └── frontend/         # Vite + React user interface
│       ├── src/          # React components and logic
│       └── package.json  # Node dependencies
└── .gitignore            # Git configuration
```

## ⚙️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- [Featherless.ai](https://featherless.ai/) API Key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd moellm-resolver/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in `moellm-resolver/` with your API key:
   ```env
   FEATHERLESS_API_KEY=your_key_here
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd moellm-resolver/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## 🧪 How it Works: The Resolver Engine

The resolver uses a scoring system that combines:
1. **Base Performance**: Accuracy, Speed, and Cost scores of each model.
2. **User Weights**: Priorities set by the user for each dimension.
3. **Hard Constraints**: Penalties applied if a model exceeds latency limits or fails privacy checks.
4. **Task Matching**: Bonuses for models optimized for the specific task type (e.g., Qwen2.5-Coder for `code`).

---

Developed with ❤️ for the Mixture-of-LLM community.
