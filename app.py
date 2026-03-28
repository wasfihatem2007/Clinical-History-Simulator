import streamlit as st
import google.generativeai as genai

# 1. API Configuration
# This pulls the key from your Streamlit Secrets (Cloud) or .streamlit/secrets.toml (Local)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY, transport='rest')
except Exception as e:
    st.error("API Key not found. Please check your Streamlit Secrets.")

# 2. Hidden System Prompts (The Behavioral & Clinical Layer)
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

# 3. UI Setup
st.set_page_config(page_title="JUST: Medical Sim", page_icon="🩺", layout="centered")
st.title("🩺 Clinical History Simulator")

# Sidebar Configuration
st.sidebar.title("Simulation Settings")
selected_case = st.sidebar.selectbox("Choose a patient level:", list(PATIENT_PROMPTS.keys()))

st.sidebar.markdown("---")
st.sidebar.info("""
**Student Instructions:**
1. Introduce yourself and your role.
2. Ask one question at a time.
3. Build rapport through empathy.
4. Screen for 'Red Flags' and Vitals.
""")

if st.sidebar.button("Reset Simulation"):
    st.session_state.messages = []
    st.rerun()

# 4. Initialize Chat Session with "Change Detection"
# This ensures that if you switch from Sami to Layla, the AI actually changes persona
if "current_case" not in st.session_state:
    st.session_state.current_case = selected_case

# If the user picks a different case in the sidebar, reset the chat automatically
if st.session_state.current_case != selected_case:
    st.session_state.messages = []
    st.session_state.current_case = selected_case
    # This force-restarts the model with the new hidden instructions
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=PATIENT_PROMPTS[selected_case]
    )
    st.session_state.chat = st.session_state.model.start_chat(history=[])

# Regular initialization for the very first load
if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        st.session_state.model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=PATIENT_PROMPTS[selected_case]
        )
        st.session_state.chat = st.session_state.model.start_chat(history=[])
    except Exception as e:
        st.error(f"Model initialization failed: {e}")

# 5. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. User Input & AI Response
if prompt := st.chat_input("Start your history taking..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display AI response
    try:
        response = st.session_state.chat.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Tip: If this is a 403 error, your API key might be leaked or billing isn't active yet.")
