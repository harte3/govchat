# 🏛️ SAM.gov AI Chatbot

An AI-powered chatbot that lets you query SAM.gov federal contract data using plain English.

## Features
- 🔍 **Opportunity Search** – Find RFPs, solicitations, presolicitations, award notices
- 🏆 **Contract Awards** – Search awarded contracts by agency, NAICS, state
- 🤖 **Agentic AI** – Claude automatically selects the right API call based on your question
- 📊 **Live Data** – Queries SAM.gov's production API in real time
- 💬 **Chat Interface** – Natural conversation with full history

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your API keys

**SAM.gov API Key** (free):
1. Register at [sam.gov](https://sam.gov)
2. Go to Account Details → request a Public API Key
3. Public access: 10 req/day | Registered entity: 1,000 req/day

**Anthropic API Key**:
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Create an API key

### 3. Run the app
```bash
streamlit run app.py
```

## Usage

Enter your API keys in the sidebar, then ask questions like:
- *"Find cybersecurity solicitations posted this week"*
- *"Show me small business set-aside contracts in Virginia"*
- *"What DoD opportunities are closing soon?"*
- *"Find NAICS 541512 opportunities from NASA"*
- *"Show recent contract award notices"*

## SAM.gov API Reference

| API | Endpoint | Use Case |
|-----|----------|----------|
| Opportunities | `api.sam.gov/prod/opportunities/v2/search` | Open solicitations & awards |
| Contract Awards | `api.sam.gov/contract-awards/v1/search` | Awarded contract records |

### Notice Types (`ptype`)
| Code | Type |
|------|------|
| `o` | Solicitation (RFP/RFQ/IFB) |
| `p` | Presolicitation |
| `a` | Award Notice |
| `r` | Sources Sought |
| `k` | Special Notice |
| `s` | Sale of Surplus Property |
# sam.gov-chatbot
# govchat
