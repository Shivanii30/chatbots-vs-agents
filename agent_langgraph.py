from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
import json
import re
import sqlite3
from datetime import datetime

# -------------------------
# State Definition
# -------------------------
class AgentState(TypedDict):
    question: str
    needs_db: bool
    result: Optional[Dict[str, Any]]
    answer: Optional[str]
    memory: List[Dict[str, str]]

# -------------------------
# Database Configuration
# -------------------------
DATABASE_PATH = "signups.db"  # Change this to your database path

class DatabaseManager:
    """Manages database connections and queries."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create signups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT,
                signup_date DATE NOT NULL,
                week_number INTEGER,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Check if table is empty and add sample data
        cursor.execute("SELECT COUNT(*) FROM signups")
        if cursor.fetchone()[0] == 0:
            print("📊 Initializing database with sample data...")
            sample_data = [
                ('Alice', 'alice@example.com', '2024-01-02', 1, 'active'),
                ('Bob', 'bob@example.com', '2024-01-05', 1, 'active'),
                ('Charlie', 'charlie@example.com', '2024-01-10', 2, 'active'),
                ('Diana', 'diana@example.com', '2024-01-15', 3, 'active'),
                ('Eve', 'eve@example.com', '2024-01-18', 3, 'active'),
                ('Frank', 'frank@example.com', '2024-01-20', 3, 'inactive'),
            ]
            cursor.executemany(
                "INSERT INTO signups (username, email, signup_date, week_number, status) VALUES (?, ?, ?, ?, ?)",
                sample_data
            )
            conn.commit()
            print("✅ Sample data added!")
        
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SQL query and return results as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            conn.close()
            raise Exception(f"Database error: {e}")
    
    def get_schema(self) -> str:
        """Get database schema description."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = "Database Schema:\n"
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema += f"\nTable: {table_name}\n"
            schema += "Columns:\n"
            for col in columns:
                schema += f"  - {col[1]} ({col[2]})\n"
        
        conn.close()
        return schema
    
    def get_sample_data(self, limit: int = 5) -> str:
        """Get sample data for context."""
        results = self.execute_query(f"SELECT * FROM signups LIMIT {limit}")
        return f"Sample data (first {limit} rows):\n" + json.dumps(results, indent=2, default=str)

# Initialize database manager
db_manager = DatabaseManager()

# -------------------------
# LLM Wrapper (Using Groq)
# -------------------------
from llm import llm as base_llm

def llm(prompt: str) -> str:
    """Wrapper around Groq LLM."""
    return base_llm(prompt)

# -------------------------
# Helper Functions
# -------------------------
def needs_database(question: str, memory: List[Dict]) -> bool:
    """Determine if question requires database access using LLM."""
    mem_context = ""
    if memory:
        recent = memory[-3:]
        mem_context = "Recent conversation:\n" + "\n".join([
            f"Q: {m['question']}\nA: {m['answer']}" for m in recent
        ])
    
    prompt = f"""You are analyzing if a question needs database access.

{mem_context}

Current question: "{question}"

The database contains user signup information with:
- username, email, signup_date, week_number, status

Does this question require querying the database? Consider:
- Questions about users, signups, counts, dates, weeks need DB
- General questions, greetings, clarifications may not need DB
- Follow-up questions may reference previous answers

Answer ONLY with: YES or NO

Answer:"""

    response = llm(prompt).strip().upper()
    return "YES" in response

def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response that might have extra text."""
    # Try to find JSON in the response
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None

def generate_sql_query(question: str, memory: List[Dict], schema: str) -> Dict[str, Any]:
    """Generate SQL query from natural language question."""
    mem_context = ""
    if memory:
        recent = memory[-3:]
        mem_context = "Previous conversation:\n" + "\n".join([
            f"Q: {m['question']}\nA: {m['answer']}" for m in recent
        ])
    
    sample_data = db_manager.get_sample_data(3)
    
    prompt = f"""You are a SQL query generator. Convert natural language questions to SQL queries.

{schema}

{sample_data}

{mem_context}

Current question: "{question}"

Generate a SQL query to answer this question. Consider:
- Use SELECT to retrieve data
- Use COUNT() for counting
- Use WHERE to filter (e.g., week_number, status, date ranges)
- Use GROUP BY for aggregations
- Join tables if needed

Respond with ONLY a valid JSON object:
{{
    "sql_query": "SELECT username, email FROM signups WHERE week_number = 1",
    "intent": "list_users_by_week",
    "description": "Get users who signed up in week 1"
}}

Do not include any text before or after the JSON.

JSON Response:"""

    response = llm(prompt).strip()
    result = extract_json_from_text(response)
    
    if not result:
        result = {
            "sql_query": "SELECT * FROM signups LIMIT 10",
            "intent": "general_query",
            "description": "Default query"
        }
    
    return result

def format_natural_answer(question: str, query_result: Dict, data: List[Dict]) -> str:
    """Format query results into natural language answer."""
    if not data:
        return "I couldn't find any data matching your question."
    
    prompt = f"""Convert database query results into a natural, conversational answer.

Question: "{question}"
Query intent: {query_result.get('intent', 'unknown')}

Data retrieved:
{json.dumps(data[:10], indent=2, default=str)}

Generate a natural language answer that:
- Directly answers the question
- Is conversational and friendly
- Includes relevant details from the data
- Uses appropriate formatting (lists for multiple items)

Answer:"""

    return llm(prompt).strip()

def query_database(question: str, memory: List[Dict]) -> Dict[str, Any]:
    """Query database with natural language and return structured result."""
    try:
        # Get schema
        schema = db_manager.get_schema()
        
        # Generate SQL query
        query_result = generate_sql_query(question, memory, schema)
        sql_query = query_result.get("sql_query", "")
        
        print(f"🔍 Generated SQL: {sql_query}")
        
        # Execute query
        data = db_manager.execute_query(sql_query)
        
        # Generate natural language answer
        answer = format_natural_answer(question, query_result, data)
        
        return {
            "intent": query_result.get("intent"),
            "sql_query": sql_query,
            "data": data,
            "answer": answer
        }
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return {
            "intent": "error",
            "sql_query": None,
            "data": [],
            "answer": f"I encountered an error while querying the database: {str(e)}"
        }

# -------------------------
# Nodes
# -------------------------
def decide_node(state: AgentState) -> Dict[str, Any]:
    """Decide if database access is needed."""
    decision = needs_database(state["question"], state["memory"])
    return {"needs_db": decision}

def query_db_node(state: AgentState) -> Dict[str, Any]:
    """Query the database with natural language."""
    result = query_database(state["question"], state["memory"])
    return {"result": result}

def answer_node(state: AgentState) -> Dict[str, Any]:
    """Generate final answer."""
    result = state.get("result")
    question = state["question"]
    
    if result and result.get("answer"):
        answer_text = result["answer"]
    else:
        # Generate answer using LLM for non-DB questions
        mem_context = ""
        if state["memory"]:
            recent = state["memory"][-2:]
            mem_context = "Previous context:\n" + "\n".join([
                f"Q: {m['question']}\nA: {m['answer']}" for m in recent
            ])
        
        prompt = f"""{mem_context}

Current question: "{question}"

Provide a helpful, natural, and conversational response.

Response:"""
        
        answer_text = llm(prompt).strip()
    
    # Update memory
    memory = state["memory"] + [{
        "question": question,
        "answer": answer_text
    }]
    
    return {"answer": answer_text, "memory": memory}

# -------------------------
# Router
# -------------------------
def route_after_decide(state: AgentState) -> str:
    """Route based on whether DB access is needed."""
    return "query_db" if state["needs_db"] else "answer"

# -------------------------
# Graph Construction
# -------------------------
def create_agent():
    """Create and compile the agent graph."""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("decide", decide_node)
    graph.add_node("query_db", query_db_node)
    graph.add_node("answer", answer_node)
    
    # Set entry point
    graph.set_entry_point("decide")
    
    # Add edges
    graph.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "query_db": "query_db",
            "answer": "answer",
        }
    )
    
    graph.add_edge("query_db", "answer")
    graph.add_edge("answer", END)
    
    return graph.compile()

# -------------------------
# Interactive Run
# -------------------------
def main():
    """Run the agent interactively."""
    agent = create_agent()
    
    state = {
        "question": "",
        "needs_db": False,
        "result": None,
        "answer": None,
        "memory": [],
    }
    
    print("=" * 60)
    print("🤖 Natural Language Database Agent")
    print("=" * 60)
    print("Connected to database:", DATABASE_PATH)
    print("\nAsk questions about user signups!")
    print("\nExample questions:")
    print("  - How many users signed up?")
    print("  - Show me users from week 1")
    print("  - Who signed up in January?")
    print("  - List all active users")
    print("  - What's the email of Alice?")
    print("\nCommands:")
    print("  - Type 'exit' to quit")
    print("  - Type 'reset' to clear conversation memory")
    print("  - Type 'schema' to see database structure")
    print()
    
    while True:
        try:
            question = input("\n🤔 You: ").strip()
            
            if not question:
                continue
            
            if question.lower() == "exit":
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == "reset":
                state["memory"] = []
                print("\n🔄 Conversation memory cleared!")
                continue
            
            if question.lower() == "schema":
                print("\n" + db_manager.get_schema())
                print(db_manager.get_sample_data())
                continue
            
            # Update state with new question
            state["question"] = question
            state["needs_db"] = False
            state["result"] = None
            state["answer"] = None
            
            # Run agent
            state = agent.invoke(state)
            
            # Display answer
            print(f"\n🤖 Agent: {state['answer']}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'schema' to see database structure.")

if __name__ == "__main__":
    main()