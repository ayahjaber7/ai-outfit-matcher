import streamlit as st
from PIL import Image
import requests
from colorthief import ColorThief
import webcolors

# -------------------- Session State --------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# -------------------- Streamlit Config --------------------
st.set_page_config(page_title="AI Outfit Matcher", layout="centered")
st.title("💕 AI Outfit Matcher")
st.write("Upload a photo of your dress to get hijab, shoes, and bag suggestions.")

# -------------------- File Upload --------------------
uploaded_file = st.file_uploader("Upload your dress image", type=["jpg", "jpeg", "png"])

# -------------------- Color Extraction --------------------
def get_main_color(image_file):
    img = Image.open(image_file).convert("RGB")
    img.save("temp.jpg")
    ct = ColorThief("temp.jpg")
    return ct.get_color(quality=1)

# -------------------- Color Naming --------------------
def get_closest_color_name(hex_color):
    css3_color_names = [
        "black", "silver", "gray", "white", "maroon", "red", "purple", "fuchsia",
        "green", "lime", "olive", "yellow", "navy", "blue", "teal", "aqua",
        "orange", "aliceblue", "gold", "beige", "brown", "chocolate", "coral",
        "crimson", "darkblue", "darkgreen", "darkred", "deeppink", "dodgerblue",
        "firebrick", "gainsboro", "indigo", "ivory", "khaki", "lavender",
        "lightblue", "lightgray", "lightpink", "lightyellow", "mediumblue",
        "mediumorchid", "mediumseagreen", "midnightblue", "mintcream",
        "mistyrose", "moccasin", "navajowhite", "oldlace", "orchid", "peachpuff",
        "peru", "pink", "plum", "rosybrown", "royalblue", "saddlebrown", "salmon",
        "sandybrown", "seagreen", "seashell", "sienna", "skyblue", "slateblue",
        "slategray", "snow", "springgreen", "steelblue", "tan", "thistle", "tomato",
        "turquoise", "violet", "wheat", "whitesmoke"
    ]

    def closest_color(requested_rgb):
        min_distance = float("inf")
        closest_name = None
        for name in css3_color_names:
            try:
                r_c, g_c, b_c = webcolors.name_to_rgb(name)
                distance = ((r_c - requested_rgb[0]) ** 2 +
                            (g_c - requested_rgb[1]) ** 2 +
                            (b_c - requested_rgb[2]) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_name = name
            except:
                continue
        return closest_name

    try:
        return webcolors.hex_to_name(hex_color)
    except ValueError:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        return closest_color((r, g, b))

# -------------------- AI Prompt --------------------
def get_suggestions(hex_color, color_name, description, occasion):
    OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]
    prompt = f"""
You are a professional modest fashion stylist working for an online wardrobe assistant.

The user uploaded a dress with the dominant color **{color_name}** (hex: {hex_color}).
They described the dress as: "{description}".
The occasion is: **{occasion}**.

Please provide stylish and cohesive recommendations that complement the color and style of the dress for the given occasion.

Your response should include:
1. A hijab recommendation — include a suitable color and fabric (e.g., chiffon, jersey, silk, etc.). Do not mention hijab wrapping or styling techniques.
2. Shoe options — suggest a matching style (e.g., heels, flats, sandals, boots, sneakers, etc.), material, and color that pair well with the dress.
3. A bag, purse, or clutch — include color, texture, shape, and any accents (e.g., gold trim, chain strap) that would elevate the outfit.

Feel free to suggest any colors, fabrics, materials, or styles that best fit the outfit — do not limit suggestions to predefined lists.

Make sure all recommendations are modest, elegant, and appropriate for the selected occasion. Include short explanations for why each piece complements the overall look.

Present the output as a styled markdown list with clear sections.
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
    st.image(uploaded_file, caption="Your Dress", use_container_width=True)

    color = get_main_color(uploaded_file)
    hex_color = '#%02x%02x%02x' % color
    color_name = get_closest_color_name(hex_color)

    st.markdown("**Detected Color:**")
    st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
      <div style='width: 50px; height: 30px; background-color: {hex_color}; border-radius: 5px; border: 1px solid #aaa;'></div>
      <span style='font-size: 16px;'>Hex: <code>{hex_color}</code> | Name: <b>{color_name}</b></span>
    </div>
    """, unsafe_allow_html=True)

    description = st.text_input("Optional: Describe the dress style (e.g. knit lace, wedding guest)")
    occasion = st.text_input("Enter the occasion (e.g. wedding, graduation, party)")

    if st.button("Get Outfit Suggestions"):
        with st.spinner("Thinking..."):
            suggestions = get_suggestions(hex_color, color_name, description or "Not specified", occasion)

        st.markdown("### 💡 Outfit Suggestions")
        st.markdown(suggestions)

        if st.button("❤️ Add to Favorites"):
            outfit_entry = {
                "hex": hex_color,
                "color": color_name,
                "occasion": occasion,
                "description": description,
                "suggestions": suggestions,
                "title": f"{occasion} – {color_name.title()}",
                "tag": ""
            }
            st.session_state.favorites.append(outfit_entry)
            st.success("Added to favorites!")

# -------------------- Favorites --------------------
if st.session_state.favorites:
    st.markdown("## ⭐ Your Favorite Outfits")
    for i, fav in enumerate(st.session_state.favorites[::-1]):
        index = len(st.session_state.favorites) - 1 - i

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
                    <p><strong>Tag:</strong> {fav.get("tag", "None")}</p>
                    <p><strong>Suggestions:</strong><br>{fav['suggestions']}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                if col1.button("✏️ Edit", key=f"edit_{index}"):
                    st.session_state.edit_index = index
                if col2.button("🗑️ Delete", key=f"delete_{index}"):
                    st.session_state.favorites.pop(index)
                    st.success("Favorite deleted.")
                    st.experimental_rerun()
