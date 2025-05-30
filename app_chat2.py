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


# LAYOUT
# ------
container_last_response = st.container(border=True)
container_chat_input = st.container(border=True)

with container_chat_input:
    
    # add image from camera
    with st.popover("Take a picture"):
        image = st.camera_input("Take a picture", label_visibility="collapsed")
        if image:
            st.session_state.messages.append({"role": "user", "content": create_message_content(None, image)})
        
        
    with st.form("my_form", border=False, clear_on_submit=False):
        
        prompt = st.text_area("Enter text:", "tba...", label_visibility="collapsed")
        image = None
        
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
            
            
            
            
# with container_last_response:

    
#     images = []
#     for message in st.session_state.messages:
#         if isinstance(message["content"], list):
#             for content_item in message["content"]:
#                 if content_item["type"] == "image_url":
#                     # Decode base64 image
#                     image_data = content_item["image_url"]["url"].split(",")[1]
#                     image_bytes = base64.b64decode(image_data)
#                     image = Image.open(io.BytesIO(image_bytes))
#                     images.append(image)
    
#     if len(images) > 0:
#         cols = st.columns(len(images))
#         for i, image in enumerate(images):
#             cols[i].image(image)
    
    
#     if len(st.session_state.messages) > 0:
#         msg = st.session_state.messages[-1]
#         st.markdown(msg["content"])


with st.expander("all images"):
    for message in st.session_state.messages:
        if isinstance(message["content"], list):
            for content_item in message["content"]:
                if content_item["type"] == "image_url":
                    image_data = content_item["image_url"]["url"].split(",")[1]
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image) 
        
        
with st.expander("Debug"):
    for message in st.session_state.messages:
        
        st.write(message)