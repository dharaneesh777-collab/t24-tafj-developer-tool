# Temenos T24 / TAFJ / jBASE Master Developer Tool

Enterprise Developer Studio and AI Assistant for **Temenos T24 Core Banking, TAFJ (Temenos Application Framework Java), TAFC / jBASE, and Transact (R08 to R24+)**.

---

## Features

1. **Infobasic Static Linter & Analyzer**:
   - Analyzes source code for 12+ strict Temenos standards.
   - Detects missing `F.RELEASE`, uncalculated `DCOUNT()` in loops, `STOP`/`ABORT` in validation hooks, un-resolved `OPF` calls, and direct file I/O anti-patterns.
2. **Routine Scaffolder & Code Generator**:
   - Parameterized generation of Version Validation Hooks, Multi-threaded Service Batch Routines (`.LOAD`, `.SELECT`, Worker), `EB.ACCOUNTING` Entry Generators, OFS Processors, and `LOCAL.REF` Resolvers.
3. **OFS & Financial Accounting Visualizer**:
   - Interactive OFS message constructor and response parser (`//1` vs `//-1`).
   - Real-time `EB.ACCOUNTING` Net-Zero Debit/Credit ledger calculator.
4. **AI Banking Architect Studio**:
   - Built-in, zero-hallucination expert architecture engine with optional live Gemini / OpenAI integrations.
5. **Knowledge Hub**:
   - Dynamic array delimiters (`@FM`, `@VM`, `@SM`, `@TM`) and standard `I_COMMON` reference directory.

---

## 🚀 How to Deploy on Render (Step-by-Step)

You can deploy this application on **Render** in under 2 minutes using either **Method 1 (Automatic via Blueprint)** or **Method 2 (Manual Web Service)**.

### Method 1: Automatic 1-Click Deployment (Recommended)

1. **Push this directory to a GitHub / GitLab repository**:
   ```bash
   cd C:\Users\dhara\.gemini\antigravity\scratch\t24-tafj-architect-tool
   git init
   git add .
   git commit -m "Initial commit of T24 TAFJ Developer Tool"
   git remote add origin https://github.com/YOUR_USERNAME/t24-tafj-developer-tool.git
   git push -u origin main
   ```
2. Go to the **[Render Dashboard](https://dashboard.render.com/)**.
3. Click **New +** → **Blueprint**.
4. Select your connected repository (`t24-tafj-developer-tool`).
5. Render will automatically read `render.yaml` and configure the Web Service with Python 3.11, build commands, and health checks.
6. Click **Apply**. Your tool will be live at `https://t24-tafj-developer-tool.onrender.com`!

---

### Method 2: Manual Web Service Deployment

1. On the **[Render Dashboard](https://dashboard.render.com/)**, click **New +** → **Web Service**.
2. Select your GitHub repository.
3. Configure the following settings:
   - **Name**: `t24-tafj-developer-tool`
   - **Language / Runtime**: `Python 3`
   - **Region**: Oregon (US West) or Frankfurt (EU Central)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. *(Optional)* Add Environment Variables under **Environment**:
   - `GEMINI_API_KEY`: *(Your Google AI Studio key)*
   - `OPENAI_API_KEY`: *(Your OpenAI API key)*
5. Click **Create Web Service**.

---

## 💻 Running Locally

To run the application locally on your machine:

```bash
# 1. Navigate to directory
cd C:\Users\dhara\.gemini\antigravity\scratch\t24-tafj-architect-tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser at `http://127.0.0.1:8000`.

---

## API Endpoints

- `POST /api/lint`: Analyzes jBC/Infobasic code and returns defect scores and issue cards.
- `GET /api/templates`: Lists all parameterized routine archetypes.
- `POST /api/templates/generate`: Generates customized Infobasic routines.
- `POST /api/chat`: Queries the T24 Banking Architect agent.
- `GET /api/knowledge`: Returns standard dynamic array and common variable metadata.
- `GET /health`: Healthcheck endpoint for Render monitoring.
