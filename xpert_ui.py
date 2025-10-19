import streamlit as st
import random
import time
import requests

# ---------------------
# Page config & styling
# ---------------------
st.set_page_config(page_title="Xpert — AI X-Ray Assistant", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    :root {
        --primary: #1a73e8;
        --bg: #f7fbff;
        --card: #ffffff;
    }
    body { background: var(--bg); }
    /* Navbar */
    .nav { display:flex; gap:24px; align-items:center; padding:14px 24px; background: linear-gradient(90deg, white, #f0f6ff); border-bottom:1px solid #e6eefc; position:sticky; top:0; z-index:999;}
    .nav .brand { font-weight:800; color:var(--primary); font-size:20px; margin-right:16px; }
    .nav .link { color:#333; font-weight:600; cursor:pointer; padding:8px 12px; border-radius:8px; }
    .nav .link:hover { background: rgba(26,115,232,0.08); color:var(--primary); }
    .nav .active { color:var(--primary); background: rgba(26,115,232,0.08); }

    /* Splash */
    .splash { text-align:center; padding:80px 20px; }
    .splash h1 { font-size:44px; color:var(--primary); margin-bottom:6px; opacity:0; animation:fadeIn 0.9s forwards 0.2s; }
    .splash p { font-size:18px; color:#444; margin-bottom:24px; opacity:0; animation:fadeIn 0.9s forwards 0.5s; }
    .cta { display:inline-block; padding:12px 22px; background:var(--primary); color:white; border-radius:12px; font-weight:700; cursor:pointer; text-decoration:none; }

    @keyframes fadeIn { to { opacity:1; transform: translateY(0);} from { opacity:0; transform: translateY(10px);} }

    /* Role selection */
    .roles { display:flex; gap:20px; justify-content:center; margin-top:18px; }
    .role-btn { background:white; border:2px solid var(--primary); color:var(--primary); padding:16px 28px; border-radius:12px; font-weight:700; cursor:pointer; }
    .role-btn:hover { background: #eaf3ff; transform: translateY(-3px); }

    /* Layout */
    .container { max-width:1100px; margin:0 auto; padding:22px; }

    /* Chat & Upload */
    .uploader { border:2px dashed var(--primary); padding:20px; border-radius:12px; background:linear-gradient(180deg,#ffffff,#fbfdff); margin-bottom:12px;}
    .chat-box { background:var(--card); border-radius:12px; padding:14px; box-shadow:0 4px 18px rgba(26,115,232,0.06); margin-bottom:12px; }
    .user { color:var(--primary); font-weight:700; margin-bottom:6px; }
    .ai { color:#1f2937; margin-bottom:6px; }
    .send-row { display:flex; gap:12px; align-items:center; }

    /* Footer */
    .footer { text-align:center; color:#6b7280; padding:30px 0; margin-top:24px; font-size:14px; }

    /* Small screens */
    @media (max-width:720px) {
        .roles { flex-direction:column; align-items:center; }
        .nav { padding:12px; gap:10px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------
# Helper: AI integration stub
# ---------------------
FASTAPI_HOST = "http://localhost:8000"
def get_ai_response(user_text: str, image=None, role="student"):
    
    # simulate processing delay for nicer UX
    CHAT_URL = f"{FASTAPI_HOST}/v1/chat/completions"
    payload = {
        # 'model' is a required field for the OpenAI API format
        "model": "your-llm-model-id", 
        "messages": [
            # The system message is crucial for Adaptive Prompting
            {"role": "system", "content": f"You are Xpert, operating in {role} mode. Analyze context and respond to the user."},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        # 2. Make the POST request to your running Uvicorn server
        response = requests.post(CHAT_URL, json=payload, timeout=20)
        response.raise_for_status() # Check for 4xx or 5xx errors
        
        # 3. Parse the response
        ai_data = response.json()

        # 4. Extract the content from the API's response structure
        # (This structure assumes your FastAPI returns an OpenAI-like response)
        return ai_data['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        # This handles network errors, timeouts, and HTTP errors (4xx/5xx)
        return f"ERROR: API Connection Failed. Ensure FastAPI server is running. Details: {e}"
    except KeyError:
        # This handles errors if the JSON structure from the backend is unexpected
        return "ERROR: Invalid JSON format returned by the backend. Check FastAPI logs."

# ---------------------
# Session state init
# ---------------------
if "page" not in st.session_state:
    st.session_state.page = "home"  # home | about | team
if "role" not in st.session_state:
    st.session_state.role = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of tuples: (speaker, text)

# ---------------------
# Navbar
# ---------------------
def set_page(p):
    st.session_state.page = p

nav_col1, nav_col2, nav_col3 = st.columns([1, 6, 1])
with nav_col1:
    st.markdown(f'<div class="nav"><span class="brand">Xpert</span></div>', unsafe_allow_html=True)
with nav_col2:
    # navbar links inline
    links_html = (
        f'<div class="nav" style="gap:14px;">'
        f'<span class="link {"active" if st.session_state.page=="home" else ""}" onclick="window.dispatchEvent(new CustomEvent(\'nav\', {{detail: \"home\"}}))">Home</span>'
        f'<span class="link {"active" if st.session_state.page=="about" else ""}" onclick="window.dispatchEvent(new CustomEvent(\'nav\', {{detail: \"about\"}}))">About</span>'
        f'<span class="link {"active" if st.session_state.page=="team" else ""}" onclick="window.dispatchEvent(new CustomEvent(\'nav\', {{detail: \"team\"}}))">Team Xpert</span>'
        f'</div>'
    )
    st.markdown(links_html, unsafe_allow_html=True)
with nav_col3:
    # placeholder to keep nav centered
    st.write("")

# Note: Streamlit can't capture onclick from raw html easily; use st.button alternatives below:
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("Home"):
        set_page("home")
with nav2:
    if st.button("About"):
        set_page("about")
with nav3:
    if st.button("Team Xpert"):
        set_page("team")

# ---------------------
# Home Page (splash + role selection)
# ---------------------
if st.session_state.page == "home" and st.session_state.role is None:
    st.markdown(
        """
        <div class="container">
            <div class="splash">
                <h1>Welcome to Xpert</h1>
                <p>AI-powered medical insights for doctors and learners.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="roles">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Doctor", key="role_doctor"):
            st.session_state.role = "doctor"
            st.session_state.chat_history = []
    with c2:
        if st.button("Student", key="role_student"):
            st.session_state.role = "student"
            st.session_state.chat_history = []
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------
# About Page
# ---------------------
if st.session_state.page == "about":
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:var(--primary);'>About Xpert</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style="font-size:16px; color:#333;">
        Xpert is an AI-powered medical assistant created to help doctors analyze X-rays and support students in learning diagnostic reasoning.
        The system blends real medical insight with interactive learning to make radiology smarter, faster, and more accessible.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------
# Team Page
# ---------------------
if st.session_state.page == "team":
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:var(--primary);'>Team Xpert</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display:flex; gap:18px; flex-wrap:wrap;">
            <div style="min-width:200px; padding:12px; border-radius:10px; background:#fff; border:1px solid #e6f0ff;">
                <strong>Islam Al-Mamoori</strong><br><small>Frontend & Design</small>
            </div>
            <div style="min-width:200px; padding:12px; border-radius:10px; background:#fff; border:1px solid #e6f0ff;">
                <strong>Yahya Kanjo</strong><br><small>Model Training</small>
            </div>
            <div style="min-width:200px; padding:12px; border-radius:10px; background:#fff; border:1px solid #e6f0ff;">
                <strong>Ibraheem</strong><br><small>AI Development</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------
# Role-specific UI (Doctor / Student)
# ---------------------
if st.session_state.role in ("doctor", "student"):
    # header for role
    role_title = "Doctor Interface" if st.session_state.role == "doctor" else "Student Interface"
    greeting = "How can I help you today, Doctor?" if st.session_state.role == "doctor" else "Hello Learner — let's explore this X-ray."
    st.markdown(f"<div class='container'><h2 style='color:var(--primary);'>{role_title}</h2></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='container'><p style='color:#333;'>{greeting}</p></div>", unsafe_allow_html=True)

    # Upload area
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Drag and drop an X-ray image here (optional)", type=["png", "jpg", "jpeg"])
    if uploaded:
        st.image(uploaded, use_container_width=True)
        st.markdown('<div class="uploader">Image uploaded. You can now ask questions about this image.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="uploader">No image uploaded. You can still ask text questions.</div>', unsafe_allow_html=True)

    # Chat input & send 

# 1. Use st.form to wrap the input and button
with st.form("chat_form", clear_on_submit=True):
    # This input must have a unique key for the form to manage its state
    user_text = st.text_area("", placeholder="Type your question here...", key="input_area_form") 
    
    # Use st.form_submit_button instead of st.button
    # Use a column layout for better design integration
    col_send, col_empty = st.columns([1, 4])
    with col_send:
        submitted = st.form_submit_button("Send") 

    # 2. Logic runs only when the form is submitted and there is text
    if submitted and user_text and user_text.strip():
        # Append user message
        st.session_state.chat_history.append(("user", user_text.strip()))
        
        # Call the AI/model integration point
        with st.spinner("Xpert is analyzing..."):
            # IMPORTANT: Get the user_text value *before* it gets cleared by the form reset
            ai_reply = get_ai_response(user_text.strip(), image=uploaded, role=st.session_state.role)
        
        st.session_state.chat_history.append(("ai", ai_reply))
        
        # 3. NO MANUAL CLEARING: The 'clear_on_submit=True' handles the reset
        
        # Force a rerun to show the chat history immediately
        st.rerun()

    # Display chat history
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    for speaker, text in st.session_state.chat_history:
        if speaker == "user":
            st.markdown(f'<div class="chat-box"><div class="user">You:</div><div class="ai">{st.markdown(text, unsafe_allow_html=False) or ""}</div></div>', unsafe_allow_html=True)
        else:
            # AI message
            st.markdown(f'<div class="chat-box"><div class="ai"><strong>Xpert:</strong> {text}</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Small controls
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Back to Home", key="back_home"):
            st.session_state.role = None
            st.session_state.chat_history = []
    with c2:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
    with c3:
        st.markdown("<div style='padding-top:8px;color:#6b7280'>Team Xpert</div>", unsafe_allow_html=True)

# ---------------------
# Footer
# ---------------------
st.markdown("<div class='footer'>Built by Team Xpert — Hackathon 2025 · ©️ 2025</div>", unsafe_allow_html=True)