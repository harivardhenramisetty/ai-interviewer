"""
Centralised CSS styles for the AI Interview Bot frontend.
Import `inject_css()` once at the top of app.py.
"""


def inject_css() -> str:
    """Return the full CSS string to be injected via st.markdown."""
    return """
<style>
/* ===================================================================
   GOOGLE FONTS
   =================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ===================================================================
   ROOT VARIABLES
   =================================================================== */
:root {
    --primary:      #4F46E5;
    --primary-dark: #4338CA;
    --primary-light:#EEF2FF;
    --accent:       #06B6D4;
    --success:      #10B981;
    --warning:      #F59E0B;
    --danger:       #EF4444;
    --bg:           #F8FAFC;
    --surface:      #FFFFFF;
    --text:         #1E293B;
    --text-muted:   #64748B;
    --border:       #E2E8F0;
    --radius:       12px;
    --radius-sm:    8px;
    --shadow-sm:    0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow:       0 4px 6px -1px rgba(0,0,0,.07), 0 2px 4px -2px rgba(0,0,0,.05);
    --shadow-lg:    0 10px 25px -5px rgba(0,0,0,.08), 0 8px 10px -6px rgba(0,0,0,.04);
    --transition:   all .2s ease;
}

/* ===================================================================
   GLOBAL RESETS
   =================================================================== */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: var(--bg) !important;
}

/* Hide default Streamlit header/footer */
header[data-testid="stHeader"] {
    background: transparent !important;
}
#MainMenu, footer, header {visibility: hidden;}

/* ===================================================================
   CARD COMPONENT
   =================================================================== */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
    margin-bottom: 16px;
}
.card:hover {
    box-shadow: var(--shadow);
    border-color: #CBD5E1;
}

/* ===================================================================
   STATUS BADGES
   =================================================================== */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: .02em;
}
.badge-success {
    background: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
}
.badge-warning {
    background: #FFFBEB;
    color: #92400E;
    border: 1px solid #FDE68A;
}
.badge-danger {
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
}
.badge-info {
    background: var(--primary-light);
    color: var(--primary);
    border: 1px solid #C7D2FE;
}

/* ===================================================================
   PROGRESS INDICATOR
   =================================================================== */
.progress-bar-custom {
    height: 8px;
    background: #E2E8F0;
    border-radius: 99px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar-custom .fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 99px;
    transition: width .6s cubic-bezier(.4,0,.2,1);
}

/* ===================================================================
   METRIC CARDS
   =================================================================== */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}
.metric-value {
    font-size: 32px;
    font-weight: 800;
    color: var(--primary);
    line-height: 1.2;
}
.metric-label {
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 500;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: .06em;
}

/* ===================================================================
   HERO / LANDING
   =================================================================== */
.hero-section {
    text-align: center;
    padding: 48px 16px 32px;
}
.hero-section h1 {
    font-size: 44px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
    line-height: 1.15;
}
.hero-section p {
    font-size: 18px;
    color: var(--text-muted);
    max-width: 560px;
    margin: 0 auto 8px;
    line-height: 1.6;
}

/* ===================================================================
   SECTION HEADERS
   =================================================================== */
.section-header {
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ===================================================================
   SYSTEM-CHECK ITEM
   =================================================================== */
.check-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: 10px;
    transition: var(--transition);
}
.check-item:hover { border-color: #CBD5E1; }
.check-label {
    font-weight: 600;
    font-size: 15px;
    color: var(--text);
}
.check-sub {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 2px;
}

/* ===================================================================
   CHAT / INTERVIEW
   =================================================================== */
.interviewer-bubble {
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
    border: 1px solid #C7D2FE;
    border-radius: 16px 16px 16px 4px;
    padding: 20px 24px;
    margin: 12px 0;
    max-width: 85%;
    font-size: 15px;
    line-height: 1.7;
    color: var(--text);
}
.candidate-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px 16px 4px 16px;
    padding: 20px 24px;
    margin: 12px 0 12px auto;
    max-width: 85%;
    font-size: 15px;
    line-height: 1.7;
    color: var(--text);
}

.avatar-interviewer {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 18px;
    flex-shrink: 0;
}
.avatar-candidate {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #F59E0B, #EF4444);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 18px;
    flex-shrink: 0;
}

/* ===================================================================
   INTERVIEW CONTROLS BAR
   =================================================================== */
.controls-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    padding: 16px 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    margin-top: 16px;
}

/* ===================================================================
   TIMER
   =================================================================== */
.timer-display {
    font-size: 20px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--text);
    background: #F1F5F9;
    padding: 8px 18px;
    border-radius: var(--radius-sm);
    letter-spacing: .04em;
}

/* ===================================================================
   REPORT SCORE RING (via plain CSS)
   =================================================================== */
.score-ring {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 10px;
    font-size: 28px;
    font-weight: 800;
    color: var(--primary);
}
.score-ring.strong-hire { border: 6px solid var(--success); color: #065F46; }
.score-ring.hire        { border: 6px solid var(--primary); color: var(--primary); }
.score-ring.no-hire     { border: 6px solid var(--danger);  color: #991B1B; }

/* ===================================================================
   EVIDENCE QUOTE
   =================================================================== */
.evidence-quote {
    background: #F8FAFC;
    border-left: 4px solid var(--primary);
    padding: 14px 18px;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin: 10px 0;
    font-size: 14px;
    color: var(--text-muted);
    font-style: italic;
    line-height: 1.6;
}

/* ===================================================================
   STREAMLIT BUTTON OVERRIDES
   =================================================================== */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 28px !important;
    transition: var(--transition) !important;
    font-size: 15px !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(79,70,229,.25) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 4px 12px rgba(79,70,229,.35) !important;
    transform: translateY(-1px);
}

/* ===================================================================
   STREAMLIT INPUT OVERRIDES
   =================================================================== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    transition: var(--transition) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,.12) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border-radius: var(--radius) !important;
}

/* Chat input */
.stChatInput > div {
    border-radius: var(--radius) !important;
    border: 1.5px solid var(--border) !important;
}
.stChatInput > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,.12) !important;
}
</style>
"""
