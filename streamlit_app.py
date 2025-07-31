import streamlit as st
from PIL import Image
import requests
from colorthief import ColorThief
import webcolors

# -------------------- Session State --------------------
if "outfit_history" not in st.session_state:
    st.session_state.outfit_history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# -------------------- Streamlit Config --------------------
st.set_page_config(page_title="AI Outfit Matcher", layout="centered")
st.title("🧕 AI Outfit Matcher")
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
    occasion = st.selectbox("Choose the occasion", ["Wedding", "Graduation", "Interview", "Casual", "Party", "Other"])

    if st.button("Get Outfit Suggestions"):
        with st.spinner("Thinking..."):
            suggestions = get_suggestions(hex_color, color_name, description or "Not specified", occasion)

        # Save to history
        outfit_entry = {
            "hex": hex_color,
            "color": color_name,
            "occasion": occasion,
            "description": description,
            "suggestions": suggestions
        }
        st.session_state.outfit_history.append(outfit_entry)

        st.markdown("### 💡 Outfit Suggestions")
        st.markdown(suggestions)

        # Favorite button
        if st.button("❤️ Add to Favorites"):
            st.session_state.favorites.append(outfit_entry)
            st.success("Added to favorites!")

        # Suggest styling upgrades
        st.markdown("### 📝 Suggest Styling Upgrades")
        user_feedback = st.text_area("Have any styling tips to improve this outfit?")
        if user_feedback:
            st.success("Thanks for your input! We'll consider this feedback.")

        # Product recommendations
        show_recommendations = st.checkbox("Show product recommendations (where to buy)")
        if show_recommendations:
            st.markdown("### 🛍️ Where to Buy")
            st.markdown("- Hijab: Ivory chiffon hijab – [Haute Hijab](https://www.hautehijab.com)")
            st.markdown("- Shoes: Black pumps – [DSW](https://www.dsw.com)")
            st.markdown("- Bag: Gold-accent clutch – [Nordstrom](https://www.nordstrom.com)")

        # Copy-to-clipboard
        st.markdown("### 📋 Copy Outfit")
        st.markdown(f"""
            <textarea id='copyTarget' style='width: 100%; height: 100px;'>{suggestions}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('copyTarget').value)">📋 Copy to Clipboard</button>
        """, unsafe_allow_html=True)

        # Email share (placeholder)
        with st.expander("📧 Share via Email"):
            email = st.text_input("Enter recipient email (feature coming soon)")
            st.button("Send (disabled for now)")
            st.caption("💡 Email sharing will use a backend service like SendGrid or Gmail API.")

# -------------------- History and Favorites --------------------
if st.session_state.outfit_history:
    with st.expander("🕘 View Past Looks"):
        for i, look in enumerate(st.session_state.outfit_history):
            st.markdown(f"**{i+1}. {look['occasion']} - {look['color']}**")
            st.markdown(f"- *{look['description']}*")
            st.markdown(f"- {look['suggestions']}")

if st.session_state.favorites:
    with st.expander("⭐ View Favorites"):
        for i, fav in enumerate(st.session_state.favorites):
            st.markdown(f"**{i+1}. {fav['occasion']} - {fav['color']}**")
            st.markdown(f"- *{fav['description']}*")
            st.markdown(f"- {fav['suggestions']}")
