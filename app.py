import os
import base64
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import io

st.title("ChatGPT-like clone with Vision")

OPENAI_MODEL = "gpt-4o"  # Vision-capable model

# HELPER FUNCTIONS
# -----------------

@st.cache_resource
def get_openai_client():
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except st.errors.StreamlitSecretNotFoundError:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    
    return OpenAI(api_key=api_key)

def encode_image(image):
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

def create_message_content(text, image=None):
    """Create message content that can handle both text and images"""
    content = []
    
    if text:
        content.append({"type": "text", "text": text})
    
    if image is not None:
        image = Image.open(image)
        base64_image = encode_image(image)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        })
    
    return content

# SETUP SESSION STATE
# -------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "toggle_camera" not in st.session_state:
    st.session_state.toggle_camera = False

# LAYOUT
# ------
container_last_response = st.container(border=True)
container_chat_input = st.container(border=True)


with container_chat_input:
    
    st.toggle("Toggle camera", key="toggle_camera")

    with st.form("my_form", border=False, clear_on_submit=False):
        prompt = st.text_area("Enter text:", "tba...", label_visibility="collapsed")
        image = st.camera_input("Take a picture", label_visibility="collapsed") if st.session_state.toggle_camera else None
        
        if st.form_submit_button("Submit", use_container_width=True):
            
            # Create user message content
            user_content = create_message_content(prompt, image)
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_content})
            
            # Ask the model
            response = get_openai_client().chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=False,
            )
            
            # Get the text content from the response
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})


with container_last_response:
    if len(st.session_state.messages) > 0:
        msg = st.session_state.messages[-1]
        st.markdown(msg["content"])