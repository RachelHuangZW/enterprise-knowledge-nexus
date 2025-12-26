import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="Knowledge Nexus", page_icon="🤖")
st.title("🤖 Enterprise Knowledge Nexus")
st.markdown("Ask questions about your enterprise data (SQL Database)")

# 2. Initialize Session State (acts as conversation memory)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display previous chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Capture user input
if prompt := st.chat_input("What would you like to know?"):
    # A. Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    # Append user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # B. Call Backend API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Ensure this URL matches the address where server.py is running
            API_URL = "http://127.0.0.1:8000/chat"
            payload = {"query": prompt, "thread_id": "streamlit_user_1"}
            
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["response"]
                message_placeholder.markdown(answer)
                # Append AI response to history
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                message_placeholder.markdown(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            message_placeholder.markdown(f"Connection Error: {str(e)}")
            st.error("Is the backend server running?")