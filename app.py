import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, date
import pandas as pd
import numpy as np

DB_PATH = "agriculture.db"

st.set_page_config(
    page_title="Smart Agriculture Management System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Styling --------------------
st.markdown("""
<style>
:root { --green:#087fba; --dark:#075985; --sky:#87ceeb; --blue:#1687d9; }
.stApp { background: linear-gradient(135deg, #87ceeb 0%, #d8f3ff 100%); color:#ffffff; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#075985,#063b63); }
[data-testid="stSidebar"] * { color: #ffffff !important; }
h1,h2,h3,h4,p,label,span { color: inherit; }
.stApp [data-testid="stAppViewContainer"] { color: #ffffff; }
div.stButton > button, div.stFormSubmitButton > button {
    background: #0b84bd; color: white; border: 1px solid #ffffff55; border-radius: 10px;
    padding: .55rem 1rem; font-weight: 650;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    background:#075985; color:white; border:1px solid white;
}
div[data-testid="stMetric"], .panel, div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    background: #111827; color: #ffffff; border: 1px solid #334155; border-radius: 16px;
    padding: 18px; box-shadow: 0 4px 14px rgba(0,0,0,.12);
}
.panel { margin-bottom: 12px; }
.hero {
    padding: 30px; border-radius: 18px; color: #ffffff;
    background: linear-gradient(100deg, #075985, #0b84bd);
    border: 1px solid #ffffff55; margin-bottom: 20px;
}
.hero h1, .hero p { color:#ffffff !important; margin-bottom: 8px; }
.small-muted, [data-testid="stCaptionContainer"], .stMarkdown, .stText, .stAlert p { color: #ffffff; }
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #ffffff !important; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, [data-baseweb="select"] > div {
    background-color: #111827 !important; color: #ffffff !important; border-color: #64748b !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #cbd5e1 !important; }
.stProgress > div > div { background-color: #0b84bd; }
div[data-testid="stDataFrame"] { overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# -------------------- Database --------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soil_moisture REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.commit()

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return digest, salt

def register_user(name, email, password):
    password_hash, salt = hash_password(password)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users(name,email,password_hash,salt,created_at) VALUES(?,?,?,?,?)",
                (name.strip(), email.strip().lower(), password_hash, salt, datetime.now().isoformat(timespec="seconds"))
            )
            conn.commit()
        return True, "Registration successful. You can now log in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

def verify_user(email, password):
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not user:
        return None
    expected, _ = hash_password(password, user["salt"])
    if secrets.compare_digest(expected, user["password_hash"]):
        return {"id": user["id"], "name": user["name"], "email": user["email"]}
    return None

def add_blog(title, category, content, author):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO blogs(title,category,content,author,created_at) VALUES(?,?,?,?,?)",
            (title.strip(), category, content.strip(), author, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()

def get_blogs():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT title,category,content,author,created_at FROM blogs ORDER BY id DESC", conn)

def save_sensor_log(soil, temp, humidity):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sensor_logs(soil_moisture,temperature,humidity,created_at) VALUES(?,?,?,?)",
            (float(soil), float(temp), float(humidity), datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()

def get_sensor_logs():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT soil_moisture,temperature,humidity,created_at FROM sensor_logs ORDER BY id DESC LIMIT 100", conn)

init_db()

# -------------------- Session state --------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "irrigation_on" not in st.session_state:
    st.session_state.irrigation_on = True
if "soil" not in st.session_state:
    st.session_state.soil = 68
if "temp" not in st.session_state:
    st.session_state.temp = 28
if "humidity" not in st.session_state:
    st.session_state.humidity = 72

# -------------------- Auth screen --------------------
def auth_screen():
    st.markdown('<div class="hero"><h1>🌱 Smart Agriculture Management System</h1><p>Monitor • Manage • Grow</p><p>Better farm data. Healthier crops. A more sustainable future.</p></div>', unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email address", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                user = verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Incorrect email or password.")
        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Full name")
                email_new = st.text_input("Email address", key="reg_email", placeholder="you@example.com")
                pass_new = st.text_input("Password (minimum 8 characters)", type="password", key="reg_pass")
                pass_confirm = st.text_input("Confirm password", type="password")
                submitted_reg = st.form_submit_button("Create account", use_container_width=True)
            if submitted_reg:
                if not name.strip() or not email_new.strip() or not pass_new:
                    st.error("Please complete all fields.")
                elif "@" not in email_new or "." not in email_new.split("@")[-1]:
                    st.error("Enter a valid email address.")
                elif len(pass_new) < 8:
                    st.error("Use a password with at least 8 characters.")
                elif pass_new != pass_confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, message = register_user(name, email_new, pass_new)
                    (st.success if ok else st.error)(message)
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Demo note: sensor values are sample/manual values until real farm sensors are connected.")

if not st.session_state.user:
    auth_screen()
    st.stop()

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("# 🌿 AgriTech")
    st.caption("SMART FARMING PLATFORM")
    st.divider()
    page = st.radio(
        "Navigation",
        ["Dashboard", "Farm Monitoring", "Irrigation Control", "My Blogs", "Data & Analytics", "Alerts", "Settings"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown(f"**Signed in as**  \n{st.session_state.user['name']}")
    if st.button("↪ Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# -------------------- Header --------------------
st.markdown(f"""
<div class="hero">
  <h1>🌱 Smart Agriculture Management System</h1>
  <p><b>Monitor · Manage · Grow</b></p>
  <p>Welcome, {st.session_state.user['name']} — make informed decisions for a healthier farm.</p>
</div>
""", unsafe_allow_html=True)

# Sample trend data; replace with sensor/API data when hardware is connected.
rng = np.random.default_rng(17)
trend_dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=7)
trend_df = pd.DataFrame({
    "Date": trend_dates,
    "Soil Moisture (%)": np.clip(st.session_state.soil + rng.normal(0, 7, 7), 10, 95),
    "Temperature (°C)": np.clip(st.session_state.temp + rng.normal(0, 2, 7), 10, 45),
    "Humidity (%)": np.clip(st.session_state.humidity + rng.normal(0, 6, 7), 20, 100),
})

if page == "Dashboard":
    st.subheader("Farm Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💧 Soil Moisture", f"{st.session_state.soil}%", "Healthy range: 40–75%")
    c2.metric("🌡️ Temperature", f"{st.session_state.temp} °C", "Sample reading")
    c3.metric("☁️ Humidity", f"{st.session_state.humidity}%", "Relative humidity")
    c4.metric("🌿 Crop Health", "Healthy" if st.session_state.soil >= 35 and st.session_state.temp < 38 else "Needs attention")
    a, b = st.columns([1.3, 1])
    with a:
        st.markdown('<div class="panel"><h3>📈 Soil Moisture Trend</h3>', unsafe_allow_html=True)
        st.line_chart(trend_df.set_index("Date")[["Soil Moisture (%)"]])
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel"><h3>🚿 Irrigation Status</h3>', unsafe_allow_html=True)
        if st.session_state.irrigation_on:
            st.success("Automatic irrigation is enabled.")
        else:
            st.warning("Automatic irrigation is disabled.")
        if st.session_state.soil < 35 and st.session_state.irrigation_on:
            st.info("Soil moisture is low. Irrigation may be needed.")
        elif st.session_state.soil >= 35:
            st.info("Soil moisture is currently above the low-moisture threshold.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.subheader("Latest Agriculture Blogs")
    blogs = get_blogs()
    if blogs.empty:
        st.info("No blog posts yet. Open **My Blogs** to publish your first agriculture article.")
    else:
        for _, row in blogs.head(3).iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['title']}**  ·  `{row['category']}`")
                st.write(row["content"][:260] + ("..." if len(row["content"]) > 260 else ""))
                st.caption(f"By {row['author']} · {row['created_at']}")

elif page == "Farm Monitoring":
    st.subheader("🌾 Farm Monitoring")
    st.write("Adjust these sample readings to explore the dashboard. They are not live hardware readings.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.soil = st.slider("Soil moisture (%)", 0, 100, int(st.session_state.soil))
    with c2:
        st.session_state.temp = st.slider("Temperature (°C)", 0, 50, int(st.session_state.temp))
    with c3:
        st.session_state.humidity = st.slider("Humidity (%)", 0, 100, int(st.session_state.humidity))
    if st.button("💾 Save current sensor readings"):
        save_sensor_log(st.session_state.soil, st.session_state.temp, st.session_state.humidity)
        st.success("Readings saved to the local database.")
    st.markdown('<div class="panel"><h3>Current Farm Conditions</h3>', unsafe_allow_html=True)
    st.progress(st.session_state.soil / 100, text=f"Soil moisture: {st.session_state.soil}%")
    st.progress(st.session_state.humidity / 100, text=f"Humidity: {st.session_state.humidity}%")
    if st.session_state.temp >= 38:
        st.error(f"High temperature warning: {st.session_state.temp}°C")
    elif st.session_state.temp <= 10:
        st.warning(f"Low temperature warning: {st.session_state.temp}°C")
    else:
        st.success(f"Temperature is within the demo comfort range: {st.session_state.temp}°C")
    st.markdown('</div>', unsafe_allow_html=True)
    logs = get_sensor_logs()
    if not logs.empty:
        st.subheader("Saved Sensor Readings")
        st.dataframe(logs, use_container_width=True, hide_index=True)

elif page == "Irrigation Control":
    st.subheader("🚿 Irrigation Control")
    st.markdown('<div class="panel"><h3>Automatic Irrigation</h3><p class="small-muted">This demo changes the displayed system status only. Connect a relay/controller before operating real pumps.</p></div>', unsafe_allow_html=True)
    st.session_state.irrigation_on = st.toggle("Enable automatic irrigation", value=st.session_state.irrigation_on)
    if st.session_state.irrigation_on:
        st.success("Automatic irrigation is enabled in the demo.")
    else:
        st.warning("Automatic irrigation is disabled in the demo.")
    if st.session_state.soil < 35 and st.session_state.irrigation_on:
        st.info("Low soil moisture detected. The demo recommends irrigation.")
    elif st.session_state.soil >= 35:
        st.success("Soil moisture is sufficient according to the demo threshold.")
    else:
        st.info("Enable irrigation if watering is required.")

elif page == "My Blogs":
    st.subheader("📰 Agriculture Blogs")
    create_tab, browse_tab = st.tabs(["✍️ Create Blog", "📚 Browse Blogs"])
    with create_tab:
        with st.form("blog_form", clear_on_submit=True):
            title = st.text_input("Blog title", placeholder="e.g. Five ways to improve soil health")
            category = st.selectbox("Category", ["Soil Health", "Irrigation", "Crop Care", "Technology", "Sustainability", "Other"])
            content = st.text_area("Blog content", height=180, placeholder="Share practical farming knowledge...")
            submitted_blog = st.form_submit_button("Publish blog")
        if submitted_blog:
            if not title.strip() or not content.strip():
                st.error("Please enter both a title and blog content.")
            else:
                add_blog(title, category, content, st.session_state.user["name"])
                st.success("Blog published.")
                st.rerun()
    with browse_tab:
        blogs = get_blogs()
        if blogs.empty:
            st.info("No blog posts have been published yet.")
        else:
            search_text = st.text_input("Search blogs by title, category, or content")
            if search_text.strip():
                mask = blogs.apply(lambda col: col.astype(str).str.contains(search_text, case=False, na=False)).any(axis=1)
                blogs = blogs[mask]
            for _, row in blogs.iterrows():
                with st.expander(f"{row['title']}  ·  {row['category']}"):
                    st.write(row["content"])
                    st.caption(f"By {row['author']} · {row['created_at']}")

elif page == "Data & Analytics":
    st.subheader("📊 Data & Analytics")
    logs = get_sensor_logs()
    if logs.empty:
        st.info("Save readings from Farm Monitoring to start building your local analytics history.")
        st.line_chart(trend_df.set_index("Date"))
    else:
        logs["created_at"] = pd.to_datetime(logs["created_at"], errors="coerce")
        logs = logs.sort_values("created_at")
        st.line_chart(logs.set_index("created_at")[["soil_moisture", "temperature", "humidity"]])
        st.dataframe(logs.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        csv = logs.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download sensor data as CSV", csv, "farm_sensor_data.csv", "text/csv")
    st.caption("Charts use saved local readings when available; the initial dashboard trend is sample data.")

elif page == "Alerts":
    st.subheader("🔔 Farm Alerts")
    alerts = []
    if st.session_state.soil < 30:
        alerts.append(("🚨 Critical", f"Soil moisture is very low at {st.session_state.soil}%. Check irrigation."))
    elif st.session_state.soil < 40:
        alerts.append(("⚠️ Warning", f"Soil moisture is low at {st.session_state.soil}%. Monitor crop water needs."))
    else:
        alerts.append(("✅ Normal", f"Soil moisture is {st.session_state.soil}%, above the demo warning threshold."))
    if st.session_state.temp >= 38:
        alerts.append(("🚨 Critical", f"Temperature is high at {st.session_state.temp}°C. Check crop heat stress."))
    elif st.session_state.temp >= 34:
        alerts.append(("⚠️ Warning", f"Temperature is elevated at {st.session_state.temp}°C."))
    else:
        alerts.append(("✅ Normal", f"Temperature is {st.session_state.temp}°C."))
    if st.session_state.humidity < 30:
        alerts.append(("⚠️ Warning", f"Humidity is low at {st.session_state.humidity}%."))
    for status, message in alerts:
        with st.container(border=True):
            st.markdown(f"**{status}**")
            st.write(message)
    st.caption("Alerts are generated from demo thresholds, not agronomic advice or a connected sensor feed.")

elif page == "Settings":
    st.subheader("⚙️ Settings")
    st.markdown('<div class="panel"><h3>Account</h3>', unsafe_allow_html=True)
    st.write(f"**Name:** {st.session_state.user['name']}")
    st.write(f"**Email:** {st.session_state.user['email']}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><h3>Application Information</h3><p>Smart Agriculture Management System · Local Streamlit edition</p><p>Database: SQLite (agriculture.db)</p></div>', unsafe_allow_html=True)

st.divider()
st.caption("Smart Agriculture Management System · Local demo · Connect compatible sensors and irrigation hardware for real-time operation.")
