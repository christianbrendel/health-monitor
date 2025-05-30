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

if "show_camera" not in st.session_state:
    st.session_state.show_camera = False

if "submitted_with_image" not in st.session_state:
    st.session_state.submitted_with_image = False

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
    # Handle camera toggle
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.chat_input("What is up?")
    
    with col2:
        if st.button("📷 Camera", help="Toggle camera on/off"):
            st.session_state.show_camera = not st.session_state.show_camera
            st.rerun()

with container_image:
    image = None
    if st.session_state.show_camera:
        with st.container():
            st.write("📸 Camera is active")
            image = st.camera_input("Take a picture", label_visibility="collapsed")
            if image:
                image = Image.open(image)
                st.image(image, caption="Preview", width=200)
    
    # Auto-turn off camera if we just submitted with an image
    if st.session_state.submitted_with_image:
        st.session_state.show_camera = False
        st.session_state.submitted_with_image = False
        st.rerun()

# # Process input when either text or image is provided
if prompt:
    # Check if we're submitting with an image
    has_image = image is not None
    
    # Create user message content
    user_content = create_message_content(prompt, image)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    # Set flag to turn off camera after this submission if we had an image
    if has_image:
        st.session_state.submitted_with_image = True

    # Display user message
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if image:
            st.image(image, width=300)

    # Generate assistant response
    with st.chat_message("assistant"):
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
        st.markdown(assistant_message)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    
    
    
# with st.expander("Debug"):
    # st.write(st.session_state.messages)