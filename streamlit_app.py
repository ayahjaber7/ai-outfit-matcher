import streamlit as st
from PIL import Image
import requests
from colorthief import ColorThief

# Set up the Streamlit page
st.set_page_config(page_title="AI Outfit Matcher", layout="centered")
st.title("🧕 AI Outfit Matcher")
st.write("Upload a photo of your dress to get hijab, shoes, and bag suggestions.")

# Upload section
uploaded_file = st.file_uploader("Upload your dress image", type=["jpg", "jpeg", "png"])

# Color extraction function
def get_main_color(image_file):
    img = Image.open(image_file).convert("RGB")  # Fix for transparent PNGs
    img.save("temp.jpg")  # Save for ColorThief
    ct = ColorThief("temp.jpg")
    dominant_color = ct.get_color(quality=1)
    return dominant_color

# AI suggestion function
def get_suggestions(color_hex, description):
    OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

    prompt = f"""
    A user uploaded a dress image with the dominant color {color_hex} and described the style as: "{description}".
    Suggest:
    - A hijab color and fabric
    - Matching shoes (type and color)
    - A bag or clutch (style and color)

    Make the suggestions stylish and cohesive.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "ayahjaber7",  # Use your GitHub or personal site here
        "X-Title": "Outfit Recommender"
    }

    data = {
        "model": "openchat/openchat-3.5-0106",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"❌ API Error: {response.status_code} — {response.text}"

# Main app logic
if uploaded_file:
    st.image(uploaded_file, caption="Your Dress", use_container_width=True)

    # Extract main color
    color = get_main_color(uploaded_file)
    hex_color = '#%02x%02x%02x' % color
    st.markdown(f"**Detected Color:** `{hex_color}`")

    # Optional description
    description = st.text_input("Optional: Describe the dress style (e.g. knit lace, wedding guest)")

    # Suggest button
    if st.button("Get Outfit Suggestions"):
        with st.spinner("Thinking..."):
            suggestions = get_suggestions(hex_color, description or "Not specified")
        st.markdown("### 💡 Outfit Suggestions")
        st.markdown(suggestions)
