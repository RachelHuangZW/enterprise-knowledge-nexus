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
    thread_id: str = "default_thread" # Used for conversation memory

# The structure of the data sent BACK to the user
class ChatResponse(BaseModel):
    response: str

# ---------------------------------------------------------
# 3. Initialize the Agent
# ---------------------------------------------------------
# We load the agent graph once when the server starts to avoid overhead per request
print("🤖 Loading Agent Graph...")
agent_graph = get_sql_agent_graph()
print("✅ Agent Graph loaded.")

# ---------------------------------------------------------
# 4. Define API Endpoints
# ---------------------------------------------------------
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint: Receives a user query, runs the Agent, and returns the response.
    """
    try:
        # 1. Construct the input for LangGraph
        # 我们把用户发来的 request.query 包装成 LangGraph 需要的消息格式
        # 格式: {"messages": [("user", "用户的具体问题")]}
        inputs = {"messages": [("user", request.query)]}
        
        # 2. Construct the configuration
        # 我们把用户发来的 request.thread_id 传给 MemorySaver
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # 3. Invoke the Agent
        # 把刚才打包好的 inputs 和 config 扔给大脑
        result = agent_graph.invoke(inputs, config)
        
        # 4. Extract the final AI response
        # result["messages"] 是一个列表，[-1] 表示取最后一条（也就是 AI 的回复）
        # .content 表示取里面的文字内容
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

