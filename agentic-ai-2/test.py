from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings 
from dotenv import load_dotenv
import os 
load_dotenv()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" 
# ------------------ STATE ------------------
class AgentState(TypedDict):
    topic: str
    plan: str
    research: str
    blog: str


llm = ChatOpenAI(model="gpt-4o-mini")

# ------------------ TOOL (RAG as tool) ------------------
def create_vector_store(): # politics
    docs = [
        "AI in healthcare improves diagnosis and treatment.",
        "Machine learning helps in detecting diseases early.",
        "DSA is a very important for software development,",
        "Mathmatics Geometric formula",
     
      
    ]
    embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(docs, embeddings)

vector_store = create_vector_store()


# ------------------ NODES ------------------

# 1. Planner Agent
def planner(state: AgentState):
    response = llm.invoke(f"Create a step-by-step research plan for: {state['topic']}")
    return {"plan": response.content}


# 2. Research Agent (USES TOOL 🔥)
def researcher(state: AgentState):
    docs = vector_store.similarity_search(state["topic"], k=2) # ai 
    context = "\n".join([d.page_content for d in docs])  # mke

    response = llm.invoke(f"""
Use this context to research:

{context}

Follow this plan:
{state['plan']}
""")
    return {"research": response.content}


# 3. Writer Agent
def writer(state: AgentState):
    response = llm.invoke(f"""
Write a structured blog using this research:

{state['research']}
""")
    return {"blog": response.content}


# ------------------ GRAPH ------------------

builder = StateGraph(AgentState)

builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

builder.set_entry_point("planner")

builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

graph = builder.compile()

# ------------------ RUN ------------------

result = graph.invoke({"topic": "AI in healthcare"})

print("\n--- FINAL BLOG ---\n")
print(result["blog"])