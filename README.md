## Chatbot vs AI Agent (LangGraph + Local LLM)

This project demonstrates the difference between:
- a chatbot (single prompt → response)
- an AI agent (decide → act → observe → respond)

Both use the SAME local open-source model (llama3).

### Key Insight
Agents are not smarter models.
They are better systems.

### Stack
- LangGraph
- SQLite

### How to Run
1. Initialize database:
   python -c "from db import init_db; init_db()"

2. Run chatbot:
   python chatbot.py

3. Run agent:
   python agent_langgraph.py

