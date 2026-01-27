## Chatbot vs AI Agent: Understanding the Architectural Difference

### Overview

This project provides a practical demonstration of the fundamental difference between traditional **chatbots** and modern **AI agents**. Using the same underlying language model (LLM), it showcases how architectural patterns—not just model intelligence—determine system capabilities.

**Chatbot Approach:**
- Single-step: prompt → response
- No planning or tool usage
- Limited to knowledge in the model

**Agent Approach:**
- Multi-step: decide → act → observe → respond
- Uses tools (database queries) to augment capabilities
- Can reason about when and how to use external resources

### Key Insight

🎯 **Agents are not smarter models. They are better systems.**

The same LLM can appear much more capable when wrapped in an agentic architecture that allows it to:
- Make decisions about what actions to take
- Use tools to fetch real-time data
- Break down complex queries into steps
- Learn from observations and adapt responses

### Features

This implementation demonstrates:

- **Natural Language to SQL**: Convert user questions into SQL queries dynamically
- **Intelligent Routing**: LLM-powered decision-making to determine when database access is needed
- **Conversational Memory**: Context-aware responses across multiple turns
- **Safe Query Execution**: Validation and safety checks for database operations
- **LangGraph State Machine**: Visual, debuggable agent workflow using graph-based architecture

### Architecture

The agent uses **LangGraph** to implement a state machine with three key nodes:

1. **Decide Node**: Analyzes the question and determines if database access is required
2. **Query DB Node**: Generates and executes SQL queries based on natural language input
3. **Answer Node**: Formats results into natural, conversational responses

The state flows through these nodes conditionally, creating an intelligent system that only queries the database when necessary.

### Tech Stack

- **LangGraph**: Graph-based agent orchestration framework
- **SQLite**: Lightweight database for user signup data
- **Local LLM**: Open-source model (llama3) via Groq API
- **Python**: Core implementation language

### How to Run

1. **Initialize database:**
   ```bash
   python -c "from db import init_db; init_db()"
   ```

2. **Run chatbot (simple approach):**
   ```bash
   python chatbot.py
   ```

3. **Run agent (agentic approach):**
   ```bash
   python agent_langgraph.py
   ```

### Example Questions

Try asking the agent:
- "How many users signed up?"
- "Show me users from week 1"
- "Who signed up in January?"
- "List all active users"
- "What's the email of Alice?"

### Learning Outcomes

This project helps you understand:
- The architectural difference between chatbots and agents
- How to build agentic workflows with LangGraph
- Natural language to SQL query generation
- Tool usage patterns in LLM applications
- State management in multi-step AI systems

