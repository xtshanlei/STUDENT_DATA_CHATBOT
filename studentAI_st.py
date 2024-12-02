import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from typing_extensions import TypedDict, Annotated

st.title("💬 SQL Database Chatbot")

# Define State and QueryOutput classes
class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]

# Sidebar for API key and information
openai_api_key = "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"

# Initialize the LLM and database connection
if openai_api_key:
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    db_path = 'student_database.db'
    db_uri = f"sqlite:///{db_path}"
    db = SQLDatabase.from_uri(db_uri)
else:
    st.warning("Please provide an OpenAI API key to proceed.")
    st.stop()

# Sidebar: List table columns
st.sidebar.header("📋 Database Schema")
st.sidebar.subheader('Basic Info')
st.sidebar.write(['Student ID', 'First Name', 'Last Name', 'Age', 'Gender', 'Email', 'Phone Number', 'Major'])
st.sidebar.subheader('Student Marks')
st.sidebar.write(['Student ID', 'Mathematics', 'Computer Science', 'Biology', 'Engineering', 'Psychology'])
st.sidebar.subheader('Student Attendance')
st.sidebar.write(['Student ID', 'Module', 'Week', 'Attendance'])


# Load query prompt template
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")
assert len(query_prompt_template.messages) == 1

# Streamlit's session state to manage conversation
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I assist you with the student database?"}]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Function definitions
def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDataBaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

# Input box for user prompt
if prompt := st.chat_input("Ask a question about the student database"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Process the user question
    state = {"question": prompt}
    state.update(write_query(state))
    state.update(execute_query(state))
    state.update(generate_answer(state))

    # Append assistant's response
    response = state["answer"]
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
