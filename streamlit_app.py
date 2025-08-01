import streamlit as st
from PIL import Image
import requests
import os
from colorthief import ColorThief
from datetime import datetime

# -------------------- Session State --------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "style_tone" not in st.session_state:
    st.session_state.style_tone = "Elegant"

# -------------------- Streamlit Config --------------------
st.set_page_config(page_title="AI Outfit Matcher", page_icon="💅", layout="centered")
st.title("💕 AI Outfit Matcher")
st.caption("Your modest styling assistant. Upload a dress photo to get color-matched outfit suggestions!")
st.markdown("---")

# -------------------- Upload Stage --------------------
st.header("📤 1. Upload Your Dress")
uploaded_file = st.file_uploader("Choose an image file (JPG, PNG)", type=["jpg", "jpeg", "png"])

# -------------------- Color Extraction --------------------
def get_main_color(image_file):
    img = Image.open(image_file).convert("RGB")
    img.save("temp.jpg")
    ct = ColorThief("temp.jpg")
    os.remove("temp.jpg")
    return ct.get_color(quality=1)

# -------------------- Custom Color Naming --------------------
def get_closest_color_name(hex_color):
    named_colors = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "navy": (0, 0, 128),
        "maroon": (128, 0, 0),
        "olive": (128, 128, 0),
        "gray": (128, 128, 128),
        "silver": (192, 192, 192),
        "purple": (128, 0, 128),
        "teal": (0, 128, 128),
        "aqua": (0, 255, 255),
        "fuchsia": (255, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "pink": (255, 192, 203),
        "brown": (165, 42, 42),
        "midnightblue": (25, 25, 112),
        "indigo": (75, 0, 130),
        "skyblue": (135, 206, 235),
        "lightgray": (211, 211, 211),
    }

    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

    min_distance = float("inf")
    closest_color = None
    for name, (r_c, g_c, b_c) in named_colors.items():
        distance = ((r - r_c) ** 2 + (g - g_c) ** 2 + (b - b_c) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_color = name

    return closest_color or "Unknown"

# -------------------- AI Prompt --------------------
def get_suggestions(hex_color, color_name, description, occasion, tone):
    OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
    prompt = f"""
You are a professional modest fashion stylist working for an online wardrobe assistant.

The user uploaded a dress with the dominant color **{color_name}** (hex: {hex_color}).
They described the dress as: "{description}".
The occasion is: **{occasion}**.
Style tone: **{tone}**

Please provide stylish and cohesive recommendations that complement the color and style of the dress for the given occasion.

Your response should include:
1. A hijab recommendation — include a suitable color and fabric (e.g., chiffon, jersey, silk, etc.). Do not mention hijab wrapping or styling techniques.
2. Shoe options — suggest a matching style (e.g., heels, flats, sandals, boots, sneakers, etc.), material, and color that pair well with the dress.
3. A bag, purse, or clutch — include color, texture, shape, and any accents (e.g., gold trim, chain strap) that would elevate the outfit.

Present the output as a styled markdown list with short explanations.
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

# -------------------- Main App Logic --------------------
if uploaded_file:
    st.markdown("---")
    st.header("🎨 2. Review Detected Color")
    st.image(uploaded_file, caption="Your Dress", use_container_width=True)

    color = get_main_color(uploaded_file)
    hex_color = '#%02x%02x%02x' % color
    color_name = get_closest_color_name(hex_color)

    st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
      <div style='width: 50px; height: 30px; background-color: {hex_color}; border-radius: 5px; border: 1px solid #aaa;'></div>
      <span style='font-size: 16px;'>Hex: <code>{hex_color}</code> | Name: <b>{color_name}</b></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("📝 3. Add Dress Details")
    col1, col2 = st.columns(2)
    with col1:
        description = st.text_input("Describe the style (optional)")
    with col2:
        occasion = st.text_input("Occasion (e.g. Eid, Graduation, Picnic)")

    tone = st.selectbox("Style tone preference:", ["Elegant", "Trendy", "Minimalist", "Bold", "Traditional"])

    st.markdown("---")
    st.header("✨ 4. Generate Suggestions")
    if st.button("Get Outfit Suggestions"):
        with st.spinner("Analyzing and styling your outfit..."):
            suggestions = get_suggestions(hex_color, color_name, description or "Not specified", occasion or "General use", tone)

        st.markdown("### 💡 Outfit Suggestions")
        st.markdown(f"""
        <div style='border: 1px solid #444; padding: 15px; border-radius: 10px; background-color: #1e1e1e;'>
        {suggestions}
        </div>
        """, unsafe_allow_html=True)

        if st.button("❤️ Add to Favorites"):
            outfit_entry = {
                "hex": hex_color,
                "color": color_name,
                "occasion": occasion,
                "description": description,
                "suggestions": suggestions,
                "tone": tone,
                "title": f"{occasion or 'Untitled'} – {color_name.title()}",
                "tag": "",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.favorites.append(outfit_entry)
            st.success("Added to favorites!")

# -------------------- Favorites --------------------
if st.session_state.favorites:
    st.markdown("---")
    st.header("⭐ Your Favorite Outfits")
    search_term = st.text_input("Search favorites by tag, title, or occasion")

    for i, fav in enumerate(reversed(st.session_state.favorites)):
        index = len(st.session_state.favorites) - 1 - i
        match = (
            search_term.lower() in fav.get("tag", "").lower()
            or search_term.lower() in fav.get("title", "").lower()
            or search_term.lower() in fav.get("occasion", "").lower()
        )
        if search_term and not match:
            continue

        with st.container():
            if st.session_state.edit_index == index:
                new_title = st.text_input("Rename this favorite:", fav.get("title", ""), key=f"title_{index}")
                new_tag = st.text_input("Add a tag (optional):", fav.get("tag", ""), key=f"tag_{index}")

                col1, col2 = st.columns([1, 1])
                if col1.button("✅ Save", key=f"save_{index}"):
                    st.session_state.favorites[index]["title"] = new_title.strip()
                    st.session_state.favorites[index]["tag"] = new_tag.strip()
                    st.session_state.edit_index = None
                if col2.button("❌ Cancel", key=f"cancel_{index}"):
                    st.session_state.edit_index = None
            else:
                st.markdown(f"""
                <div style='border: 1px solid #444; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: #1e1e1e;'>
                    <h4 style='margin-bottom: 5px;'>✨ {fav.get("title", "")}</h4>
                    <p><strong>Description:</strong> {fav['description'] or "N/A"}</p>
                    <p><strong>Tag:</strong> {fav.get("tag", "None")} | <strong>Tone:</strong> {fav.get("tone", "")} | <strong>Date:</strong> {fav.get("timestamp", "")}</p>
                    <div>{fav['suggestions']}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                if col1.button("✏️ Edit", key=f"edit_{index}"):
                    st.session_state.edit_index = index
                if col2.button("🗑️ Delete", key=f"delete_{index}"):
                    st.session_state.favorites.pop(index)
                    st.success("Favorite deleted.")
                    st.experimental_rerun()
