import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

"""
Core Agent Module
-----------------
This module serves as the Business Logic Layer.
It orchestrates the autonomous SQL Agent workflow using LangGraph, managing:
1. State transitions (User -> Agent -> Tools -> Agent).
2. Tool execution (SQLToolkit for database querying).
3. LLM reasoning to transform natural language into database insights.
"""

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "knowledge_nexus.db")
# Test connection to DB
#table = db.get_usable_table_names()
#if len(table) > 0:
    #print(f"Connection successful! Found {len(table)} tables") 
    #print(table)
#else:
    #print("Connection failed!")

def get_sql_agent_graph():
    # Create and generate SQL Agent
    # 1. Environment and Resource Initialization
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 2. Initialize Toolkit
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    llm_with_tools = llm.bind_tools(tools)

    # 3. Define State Schema
    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]

    # 4. Define Nodes
    def reasoner(state: AgentState):
        messages = state['messages']
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_executor = ToolNode(tools)

    # 5. Build Workflow
    workflow = StateGraph(AgentState)
    # Add node
    workflow.add_node("agent", reasoner)
    workflow.add_node("tools", tool_executor)
    # Set Entry point
    workflow.set_entry_point("agent")
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        tools_condition
    )
    workflow.add_edge("tools", "agent")

    # 6. Add MemorySaver
    memory = MemorySaver()
    
    # 7. Compile App
    app = workflow.compile(
        checkpointer = memory,
        #interrupt_before = ["tools"]
    )

    return app


