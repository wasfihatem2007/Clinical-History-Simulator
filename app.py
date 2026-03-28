import streamlit as st
import google.generativeai as genai

# ============================================================
# 1. API CONFIGURATION
# ============================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY, transport='rest')
    api_ready = True
except Exception:
    api_ready = False

# ============================================================
# 2. SYSTEM PROMPTS
# ============================================================
GLOBAL_RULES = """
You are a patient, NOT a medical professional.
1. Never suggest a diagnosis. If asked, say: "I'm not sure what it is, I just know how I feel."
2. Do NOT volunteer information. Wait for specific questions.
3. Question Stacking: If asked >1 question at once, say: "Sorry doctor, I got a bit confused. About the first thing you asked..." and only answer the first one.
4. Rapport: If they don't introduce themselves, be cold and brief. If they show empathy, become more open and talkative.
5. Non-Verbal Cues: Use brackets for cues like (fidgets) or (looks worried) to reflect your emotional state.
6. Vitals: Only provide these in a simple list if explicitly asked. Do not interpret them.
7. Terminology: Use plain language only (e.g., say 'heartburn' or 'fire' instead of 'GERD').
"""

PATIENT_PROMPTS = {
    "Level 1: Sami (Gastrointestinal - Epigastric Pain)": f"""
    {GLOBAL_RULES}
    PERSONA: Sami, 18. Worried and polite.
    CLINICAL: You have a burning pain in your upper stomach (epigastrium). It started 2 days ago.
    It feels like 'fire' especially after eating spicy food. You are slightly embarrassed to talk about your diet.
    VITALS: BP 120/80, HR 72, RR 14, Temp 37.0, SpO2 99%.
    """,

    "Level 2: Layla (Respiratory - Chronic Cough)": f"""
    {GLOBAL_RULES}
    PERSONA: Layla. Expressive, dramatic, uses colloquial language. Frustrated and fatigued.
    CLINICAL: Persistent dry cough for 3 months. It is much worse at night when you lie down.
    You call it a 'شرقة' (choking feeling). You feel 'هديل' (wheezing) in your chest sometimes.
    VITALS: BP 130/85, HR 88, RR 18, Temp 37.2, SpO2 96%.
    """,

    "Level 3: Abu Mazen (Cardiovascular - Chest Heaviness)": f"""
    {GLOBAL_RULES}
    PERSONA: Abu Mazen. Calm, reserved, answers briefly unless encouraged. Concerned but controlled.
    CLINICAL: Heaviness in the center of the chest. Feels like a 'بلاطة' (heavy stone) sitting on you.
    The pain radiates to your left jaw. It started while you were walking to the mosque.
    VITALS: BP 150/95, HR 92, RR 20, Temp 36.8, SpO2 94%.
    """
}

# ============================================================
# 3. PATIENT CARD DATA
# This is the visible info shown to the student before they start.
# It does NOT contain clinical answers — just enough to set the scene.
# ============================================================
PATIENT_CARDS = {
    "Level 1: Sami (Gastrointestinal - Epigastric Pain)": {
        "avatar": "🧑",
        "name": "Sami",
        "age": "18 years old",
        "gender": "Male",
        "setting": "Outpatient Clinic",
        "complaint": "\"I've been having this burning feeling in my stomach...\"",
        "difficulty": "Level 1 — Beginner",
        "badge_color": "#2ecc71",
        "tip": "Focus on onset, character, and dietary history.",
    },
    "Level 2: Layla (Respiratory - Chronic Cough)": {
        "avatar": "👩",
        "name": "Layla",
        "age": "34 years old",
        "gender": "Female",
        "setting": "General Practice",
        "complaint": "\"This cough is driving me crazy, it won't stop...\"",
        "difficulty": "Level 2 — Intermediate",
        "badge_color": "#f39c12",
        "tip": "She uses colloquial terms. Ask her to describe symptoms in her own words.",
    },
    "Level 3: Abu Mazen (Cardiovascular - Chest Heaviness)": {
        "avatar": "👴",
        "name": "Abu Mazen",
        "age": "58 years old",
        "gender": "Male",
        "setting": "Emergency Department",
        "complaint": "\"There is something heavy sitting on my chest...\"",
        "difficulty": "Level 3 — Advanced",
        "badge_color": "#e74c3c",
        "tip": "He is reserved. Build rapport carefully. Red flags are critical here.",
    },
}

# ============================================================
# 4. FEEDBACK PROMPT
# ============================================================
FEEDBACK_PROMPT = """
You are an experienced clinical skills educator at a medical school.
A student has just completed a history-taking exercise with a simulated patient.
Below is the full transcript of their conversation.

Evaluate the student's performance using this exact structure. Be encouraging but honest.

---

## 🩺 Clinical History Debrief

**Overall Performance:** [One sentence summary]

---

### ✅ What You Did Well
- [List 2-3 specific things they got right, with a quote from the conversation if possible]

### ⚠️ Areas to Improve
- [List 2-3 specific things they missed or could do better]

### 🔴 Critical Items Missed
- [List any red flag symptoms, important history items (SOCRATES, drug history, social history, family history) they forgot to ask about]

### 💡 Tip for Next Time
[One practical, memorable piece of advice]

---
Be specific. Reference what they actually said or didn't say. Do not be vague.
"""

# ============================================================
# 5. UI SETUP
# ============================================================
st.set_page_config(page_title="JUST: Medical Sim", page_icon="🩺", layout="centered")

st.title("🩺 Clinical History Simulator")
st.caption("Jordan University of Science and Technology — Clinical Skills Lab")

if not api_ready:
    st.error("⚠️ Simulation unavailable. API key not found — please contact your instructor.")
    st.stop()

# ============================================================
# 6. SIDEBAR
# ============================================================
st.sidebar.title("⚙️ Simulation Settings")
selected_case = st.sidebar.selectbox("Choose a patient:", list(PATIENT_PROMPTS.keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Student Instructions")
st.sidebar.info("""
1. Introduce yourself and your role.
2. Ask **one question at a time**.
3. Build rapport through empathy.
4. Screen for **Red Flags** and ask for Vitals.
""")

st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = None
        st.rerun()
with col2:
    end_session = st.button("📋 Debrief", use_container_width=True)

# ============================================================
# 7. PATIENT CARD (shown at top of chat area)
# ============================================================
card = PATIENT_CARDS[selected_case]

with st.container(border=True):
    left, right = st.columns([1, 4])

    with left:
        st.markdown(
            f"<div style='font-size: 64px; text-align: center; padding-top: 8px;'>{card['avatar']}</div>",
            unsafe_allow_html=True
        )

    with right:
        st.markdown(
            f"<span style='background-color:{card['badge_color']}; color:white; padding: 3px 10px; "
            f"border-radius: 12px; font-size: 12px; font-weight: bold;'>{card['difficulty']}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"### {card['name']}, {card['age']} — {card['gender']}")
        st.markdown(f"🏥 **Setting:** {card['setting']}")
        st.markdown(f"💬 *{card['complaint']}*")
        st.markdown(f"💡 **Instructor tip:** {card['tip']}")

st.markdown("---")

# ============================================================
# 8. SESSION STATE & MODEL INITIALIZATION
# ============================================================
def initialize_model(case):
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=PATIENT_PROMPTS[case]
    )
    return model, model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.feedback = None
    st.session_state.current_case = selected_case
    st.session_state.model, st.session_state.chat = initialize_model(selected_case)

if st.session_state.current_case != selected_case:
    st.session_state.messages = []
    st.session_state.feedback = None
    st.session_state.current_case = selected_case
    st.session_state.model, st.session_state.chat = initialize_model(selected_case)

# ============================================================
# 9. DISPLAY CHAT HISTORY
# ============================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============================================================
# 10. DEBRIEF LOGIC
# ============================================================
if end_session:
    if len(st.session_state.messages) < 4:
        st.warning("⚠️ Have a longer conversation with the patient before requesting a debrief.")
    else:
        with st.spinner("Analyzing your performance..."):
            try:
                transcript = "\n".join(
                    [f"{'Student' if m['role'] == 'user' else 'Patient'}: {m['content']}"
                     for m in st.session_state.messages]
                )
                feedback_model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
                result = feedback_model.generate_content(
                    f"{FEEDBACK_PROMPT}\n\n---TRANSCRIPT---\n{transcript}"
                )
                st.session_state.feedback = result.text
            except Exception as e:
                st.error(f"Feedback generation failed: {e}")

if st.session_state.feedback:
    st.markdown("---")
    st.markdown(st.session_state.feedback)

# ============================================================
# 11. USER INPUT
# ============================================================
if not st.session_state.feedback:
    if prompt := st.chat_input("Start your history taking..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = st.session_state.chat.send_message(prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Tip: If this is a 403 error, your API key may be invalid or billing isn't active.")
else:
    st.info("Session ended. Press 🔄 Reset to start a new simulation.")