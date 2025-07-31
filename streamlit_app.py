import streamlit as st
from PIL import Image
import requests
from colorthief import ColorThief
from webcolors import hex_to_name, CSS3_HEX_TO_NAMES

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

# Get closest color name
def get_closest_color_name(hex_color):
    try:
        return hex_to_name(hex_color)
    except ValueError:
        # If exact name not found, return closest CSS3 color
        min_distance = float("inf")
        closest_color = None
        r1, g1, b1 = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:], 16)
        for hex_val, name in CSS3_HEX_TO_NAMES.items():
            r2, g2, b2 = int(hex_val[1:3], 16), int(hex_val[3:5], 16), int(hex_val[5:], 16)
            distance = (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
            if distance < min_distance:
                min_distance = distance
                closest_color = name
        return closest_color

# AI suggestion function
def get_suggestions(hex_color, color_name, description, occasion):
    OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

    prompt = f"""
    A user uploaded a dress with the dominant color {color_name} ({hex_color}).
    The dress style is described as: "{description}".
    The occasion is: {occasion}.

    Suggest:
    - A hijab color and fabric
    - Matching shoes (type and color)
    - A bag or clutch (style and color)

    Make the suggestions modest, stylish, and cohesive.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "ayahjaber7",
        "X-Title": "Outfit Recommender"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
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
    color_name = get_closest_color_name(hex_color)

    # Show color swatch + name
    st.markdown("**Detected Color:**")
    st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
      <div style='width: 50px; height: 30px; background-color: {hex_color}; border-radius: 5px; border: 1px solid #aaa;'></div>
      <span style='font-size: 16px;'>Hex: <code>{hex_color}</code> | Name: <b>{color_name}</b></span>
    </div>
    """, unsafe_allow_html=True)

    # User input
    description = st.text_input("Optional: Describe the dress style (e.g. knit lace, wedding guest)")
    occasion = st.selectbox("Choose the occasion", ["Wedding", "Graduation", "Interview", "Casual", "Party", "Other"])

    if st.button("Get Outfit Suggestions"):
        with st.spinner("Thinking..."):
            suggestions = get_suggestions(hex_color, color_name, description or "Not specified", occasion)
        st.markdown("### 💡 Outfit Suggestions")
        st.markdown(suggestions)
