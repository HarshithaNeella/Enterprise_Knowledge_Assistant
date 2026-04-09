import os
import boto3
import streamlit as st
from google import genai
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(page_title="Rag+ Gemini Chat", page_icon="💬")
st.title("Enterprise Knowledge Assistant")

# ------------------ CONFIG ------------------
aws_region = os.getenv("AWS_REGION", "ap-southeast-2")
knowledge_base_id = "BSWC5YVAHC"
os.environ['GEMINI_API_KEY'] = os.getenv("gemini_key")

# ------------------ SESSION MEMORY ------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.write("Chat with your Knowledge Base (with memory + greetings)")

question = st.text_input("Enter your question")

# ------------------ GREETING HANDLING ------------------
greetings = ["hi", "hello", "hey", "good morning", "good evening"]

if st.button("Ask"):

    if not question.strip():
        st.error("Please enter a question.")
        st.stop()

    # Greeting check
    if any(greet in question.lower() for greet in greetings):
        reply = "Hello! 👋 How can I help you today?"
        
        st.subheader("Answer")
        st.write(reply)

        # Save in history
        st.session_state.chat_history.append({
            "question": question,
            "answer": reply
        })

        st.stop()

    # ------------------ BEDROCK RETRIEVAL ------------------
    bedrock = boto3.client("bedrock-agent-runtime", region_name=aws_region)

    kb_response = bedrock.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": 5
            }
        },
    )

    chunks = []
    for item in kb_response.get("retrievalResults", []):
        text = item.get("content", {}).get("text", "")
        if text:
            chunks.append(text)

    context = "\n\n".join(chunks)

    # ------------------ CHAT HISTORY BUILD ------------------
    history_text = ""
    for chat in st.session_state.chat_history:
        history_text += f"User: {chat['question']}\nAssistant: {chat['answer']}\n"

    # ------------------ PROMPT ------------------
    prompt = f"""
You are a helpful assistant.

Use ONLY the provided context and conversation history.

If answer is not in context, say: "Not found in knowledge base."

Conversation History:
{history_text}

Context:
{context}

Question:
{question}
"""

    # ------------------ GEMINI CALL ------------------
    client = genai.Client()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer = response.text

    except Exception:
        answer = "⚠️ Model is busy. Please try again."

    # ------------------ DISPLAY ------------------
    st.subheader("Answer")
    st.write(answer)

    # Save to history
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer
    })

    # ------------------ CONTEXT DISPLAY ------------------
    with st.expander("Retrieved Context"):
        if chunks:
            for i, chunk in enumerate(chunks):
                st.write(f"{i+1}. {chunk}")
        else:
            st.write("No context found")

# ------------------ SHOW CHAT HISTORY ------------------
if st.session_state.chat_history:
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        st.write(f"🧑: {chat['question']}")
        st.write(f"🤖: {chat['answer']}")

























































































