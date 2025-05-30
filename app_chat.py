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

# LAYOUT
# ------

container_chat_history = st.container()
st.markdown("---")
container_chat_input = st.container()
container_image = st.container()

# MAIN APP
# --------
with container_chat_history:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            
            # Handle multimodal content
            if isinstance(message["content"], list):
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        st.markdown(content_item["text"])
                    elif content_item["type"] == "image_url":
                        # Display image from base64
                        image_data = content_item["image_url"]["url"].split(",")[1]
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, width=300)
            else:
                st.markdown(message["content"])



with container_chat_input:
    prompt = st.chat_input("What is up?")

with container_image:
    image = None
    with st.popover("Take a photo", use_container_width=True):
        image = st.camera_input("Take a picture", label_visibility="collapsed")
        if image:
            image = Image.open(image)


# # Process input when either text or image is provided
if prompt:
        
    # Create user message content
    user_content = create_message_content(prompt, image)
    image = None
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    # Display user message
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if image:
            st.image(image, width=300)

    # Generate assistant response
    with st.chat_message("assistant"):
        stream = get_openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    
    
# with st.expander("Debug"):
    # st.write(st.session_state.messages)