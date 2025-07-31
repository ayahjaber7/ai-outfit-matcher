# streamlit_app.py

import streamlit as st
from PIL import Image
import requests
import base64
import io
from colorthief import ColorThief

st.title("🧕 AI Outfit Matcher")
st.write("Upload a photo of your dress to get hijab, shoes, and bag suggestions.")

uploaded_file = st.file_uploader("Upload your dress image", type=["jpg", "jpeg", "png"])

def get_main_color(image_file):
    img = Image.open(image_file)
    img.save("temp.jpg")  # Save temporarily for ColorThief
    ct = ColorThief("temp.jpg")
    dominant_color = ct.get_color(quality=1)
    return dominant_color

def get_suggestions(color_hex, description):
    OPENROUTER_API_KEY = "your-api-key-here"
    prompt = f"""
    A user uploaded a dress image with the dominant color {color_hex} and style: {description}.
    Suggest a hijab color and style, matching shoes, and a bag that fits the look. 
    Mention fabric and accessory types too.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "yourname.com",  # replace with your domain or Replit
        "X-Title": "Outfit Recommender"
    }

    data = {
        "model": "openchat/openchat-3.5-0106",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
    return response.json()['choices'][0]['message']['content']

if uploaded_file:
    st.image(uploaded_file, caption="Your Dress", use_column_width=True)
    
    color = get_main_color(uploaded_file)
    hex_color = '#%02x%02x%02x' % color
    st.markdown(f"**Detected Color:** `{hex_color}`")
    
    description = st.text_input("Optional: Describe the dress (e.g. knit lace, wedding guest)")
    
    if st.button("Get Outfit Suggestions"):
        with st.spinner("Thinking..."):
            suggestions = get_suggestions(hex_color, description)
        st.markdown("### 💡 Suggestions")
        st.markdown(suggestions)
