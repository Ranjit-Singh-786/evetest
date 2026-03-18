import os
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from openai import OpenAI

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------ PDF TEXT ------------------
def extract_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


# ------------------ SPLIT ------------------
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=80
    )
    return splitter.split_text(text)


# ------------------ VECTOR STORE ------------------
def create_vector_store(chunks):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.from_texts(chunks, embeddings)


# ------------------ SIMPLE RAG ------------------
def ask_question(vector_store, query):
    docs = vector_store.similarity_search(query, k=3)

    context = "\n\n".join([doc.page_content for doc in docs])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Answer only from the provided context. If not found, say 'Not found in document'."
            },
            {
                "role": "user",
                "content": f"""
Context:
{context}

Question:
{query}
"""
            }
        ]
    )

    answer = response.choices[0].message.content
    return answer, context


# ------------------ STREAMLIT ------------------
def app():
    st.title("Simple PDF RAG (OpenAI API)")

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

    pdf_docs = st.file_uploader("Upload PDFs", accept_multiple_files=True)

    if st.button("Process"):
        text = extract_text(pdf_docs)
        chunks = split_text(text)
        vector_store = create_vector_store(chunks)

        st.session_state.vector_store = vector_store
        st.success("PDF processed!")

    query = st.text_input("Ask question")

    if query and st.session_state.vector_store:
        answer, context = ask_question(st.session_state.vector_store, query)

        st.write("### Answer")
        st.write(answer)

        with st.expander("Context used"):
            st.write(context)


if __name__ == "__main__":
    app()