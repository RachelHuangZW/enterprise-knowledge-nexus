import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.agent import get_sql_agent_graph

# ---------------------------------------------------------
# 1. Initialize FastAPI Application
# ---------------------------------------------------------
app = FastAPI(
    title="Enterprise Knowledge Nexus API",
    description="HTTP Interface for the SQL-based RAG Agent",
    version="1.0"
)

# ---------------------------------------------------------
# 2. Define Data Models (Pydantic)
# ---------------------------------------------------------

# The structure of the data sent BY the user
class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_thread"  # Used for conversation memory

# The structure of the data sent BACK to the user
class ChatResponse(BaseModel):
    response: str

# ---------------------------------------------------------
# 3. Initialize the Agent
# ---------------------------------------------------------
# Load the agent graph once during server startup to minimize per-request overhead
print("🤖 Loading Agent Graph...")
agent_graph = get_sql_agent_graph()
print("✅ Agent Graph loaded.")

# ---------------------------------------------------------
# 4. Define API Endpoints
# ---------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint: Receives a user query, runs the Agent, and returns the response.
    """
    try:
        # 1. Construct the input for LangGraph
        # Wrap the user's query into the message format expected by LangGraph
        # Format: {"messages": [("user", "User's specific query")]}
        inputs = {"messages": [("user", request.query)]}
        
        # 2. Construct the configuration
        # Pass the request's thread_id to MemorySaver for session persistence
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # 3. Invoke the Agent
        # Pass the prepared inputs and configuration to the agent (the 'brain')
        result = agent_graph.invoke(inputs, config)
        
        # 4. Extract the final AI response
        # result["messages"] is a list; [-1] retrieves the last message (the AI's response)
        # .content retrieves the actual text content of that message
        final_content = result["messages"][-1].content
        
        # Return the result
        return ChatResponse(response=final_content)
        
    except Exception as e:
        # Log the error and return a 500 status code
        print(f"❌ Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 5. Entry Point for Local Testing
# ---------------------------------------------------------
if __name__ == "__main__":
    # This allows you to run the server via: python -m backend.server
    uvicorn.run(app, host="127.0.0.1", port=8000)