"""
Design system for InterviewAI.
Single source of truth for all visual styling.
"""


def inject_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --primary: #635BFF;
    --primary-dark: #5046E4;
    --secondary: #8B5CF6;
    --blue: #3B82F6;
    --pink: #EC4899;
    --green: #10B981;
    --orange: #F59E0B;
    --red: #EF4444;
    --bg: #F7F8FC;
    --surface: #FFFFFF;
    --text: #172033;
    --text-muted: #667085;
    --text-light: #98A2B3;
    --border: #E4E7EC;
    --border-light: #F2F4F7;
    --r: 16px;
    --r-sm: 12px;
    --r-xs: 8px;
    --shadow: 0 2px 8px rgba(0,0,0,.06);
    --shadow-md: 0 4px 16px rgba(0,0,0,.08);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.10);
    --gradient: linear-gradient(135deg, #635BFF, #8B5CF6);
    --gradient-blue: linear-gradient(135deg, #3B82F6, #8B5CF6);
    --gradient-warm: linear-gradient(135deg, #F59E0B, #EC4899);
    --gradient-green: linear-gradient(135deg, #10B981, #3B82F6);
}

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
.stApp { background: var(--bg) !important; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ── Layout wrappers ──────────────────────────────────────────────── */
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
.container-sm { max-width: 800px; margin: 0 auto; padding: 0 24px; }

/* ── Cards ────────────────────────────────────────────────────────── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 24px;
    box-shadow: var(--shadow);
    transition: all .2s ease;
}
.card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
.card-flat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 24px;
}
.card-accent {
    border-top: 3px solid var(--primary);
}
.card-glass {
    background: rgba(255,255,255,.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,.5);
    border-radius: var(--r);
    padding: 24px;
    box-shadow: var(--shadow);
}

/* ── Hero ─────────────────────────────────────────────────────────── */
.hero-wrap {
    background: linear-gradient(135deg, #635BFF 0%, #8B5CF6 50%, #3B82F6 100%);
    border-radius: 24px;
    padding: 56px 48px;
    position: relative;
    overflow: hidden;
    margin-bottom: 32px;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(255,255,255,.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-wrap::after {
    content: '';
    position: absolute;
    bottom: -30%; left: 10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: white;
    line-height: 1.15;
    margin: 0 0 12px;
    letter-spacing: -0.02em;
    position: relative;
    z-index: 1;
}
.hero-sub {
    font-size: 17px;
    color: rgba(255,255,255,.8);
    line-height: 1.6;
    max-width: 460px;
    margin: 0 0 28px;
    position: relative;
    z-index: 1;
}

/* ── AI Visual Card (landing) ─────────────────────────────────────── */
.ai-visual {
    position: relative;
    z-index: 1;
    background: rgba(255,255,255,.12);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 20px;
    padding: 32px;
    color: white;
}
.ai-orb {
    width: 64px; height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(255,255,255,.3), rgba(255,255,255,.1));
    border: 2px solid rgba(255,255,255,.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    margin-bottom: 16px;
    animation: pulse-orb 3s ease-in-out infinite;
}
@keyframes pulse-orb {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,255,255,.2); }
    50% { box-shadow: 0 0 0 16px rgba(255,255,255,0); }
}
.ai-visual-line {
    height: 4px;
    border-radius: 2px;
    margin: 8px 0;
    opacity: .5;
}

/* ── Feature cards ────────────────────────────────────────────────── */
.feat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 28px 24px;
    box-shadow: var(--shadow);
    transition: all .2s ease;
    height: 100%;
}
.feat-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-3px);
}
.feat-icon {
    width: 44px; height: 44px;
    border-radius: var(--r-sm);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    margin-bottom: 16px;
}
.feat-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
}
.feat-desc {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.55;
}

/* ── Status cards (system check) ──────────────────────────────────── */
.status-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 20px;
    box-shadow: var(--shadow);
    text-align: center;
    transition: all .2s ease;
}
.status-card:hover { box-shadow: var(--shadow-md); }
.status-icon {
    font-size: 28px;
    margin-bottom: 8px;
}
.status-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
}
.status-val {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 8px;
}
.status-dot {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
}
.dot-green { background: #ECFDF5; color: #059669; }
.dot-blue  { background: #EFF6FF; color: #2563EB; }

/* ── Tips card ────────────────────────────────────────────────────── */
.tips-card {
    background: linear-gradient(135deg, #FFFBEB, #FEF3C7);
    border: 1px solid #FDE68A;
    border-radius: var(--r);
    padding: 20px 24px;
    margin: 20px 0;
}
.tips-card strong { color: var(--text); font-size: 14px; }
.tips-card ul {
    margin: 8px 0 0; padding-left: 18px;
    font-size: 13px; color: var(--text-muted); line-height: 1.8;
}

/* ── Badges / pills ───────────────────────────────────────────────── */
.pill {
    display: inline-block;
    font-size: 12px; font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin: 0 4px 6px 0;
    background: #EEF2FF; color: var(--primary);
}
.badge-live {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600;
    padding: 4px 12px; border-radius: 20px;
    background: #ECFDF5; color: #059669;
}
.badge-live::before {
    content: '';
    width: 7px; height: 7px; border-radius: 50%;
    background: #10B981;
    animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: .3; }
}

/* ── Progress bar ─────────────────────────────────────────────────── */
.prog-track {
    height: 6px; background: #E4E7EC;
    border-radius: 3px; overflow: hidden;
}
.prog-fill {
    height: 100%;
    background: var(--gradient);
    border-radius: 3px;
    transition: width .6s ease;
}
.prog-mini-track {
    height: 4px; background: #E4E7EC;
    border-radius: 2px; overflow: hidden;
    margin-top: 8px;
}
.prog-mini-fill {
    height: 100%; border-radius: 2px;
    transition: width .4s ease;
}

/* ── Timer ────────────────────────────────────────────────────────── */
.timer {
    font-size: 14px; font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--text);
    background: #F2F4F7;
    padding: 6px 14px;
    border-radius: var(--r-xs);
}

/* ── Top bar ──────────────────────────────────────────────────────── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
.topbar-brand {
    display: flex; align-items: center; gap: 12px;
}
.topbar-logo {
    width: 36px; height: 36px; border-radius: 10px;
    background: var(--gradient);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 800; font-size: 16px;
}
.topbar-info { display: flex; flex-direction: column; }
.topbar-name { font-weight: 700; font-size: 15px; color: var(--text); }
.topbar-role { font-size: 12px; color: var(--text-muted); }
.topbar-right {
    display: flex; align-items: center; gap: 16px;
}
.topbar-qcount {
    font-size: 13px; font-weight: 600; color: var(--text-muted);
}

/* ── Chat ─────────────────────────────────────────────────────────── */
.ai-msg {
    display: flex; gap: 12px; align-items: flex-start;
    margin-bottom: 20px;
}
.ai-avatar {
    width: 38px; height: 38px; border-radius: 12px;
    background: var(--gradient);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 14px;
    flex-shrink: 0;
}
.ai-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px 16px 16px 16px;
    padding: 18px 22px;
    font-size: 15px; line-height: 1.7;
    color: var(--text);
    box-shadow: var(--shadow);
    max-width: 90%;
}
.ai-bubble-label {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em;
    color: var(--primary); margin-bottom: 8px;
}
.user-msg {
    display: flex; gap: 12px; align-items: flex-start;
    justify-content: flex-end;
    margin-bottom: 20px;
}
.user-avatar {
    width: 38px; height: 38px; border-radius: 12px;
    background: linear-gradient(135deg, #F59E0B, #EC4899);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 14px;
    flex-shrink: 0;
}
.user-bubble {
    background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
    border: 1px solid #DDD6FE;
    border-radius: 16px 4px 16px 16px;
    padding: 18px 22px;
    font-size: 15px; line-height: 1.7;
    color: var(--text);
    max-width: 90%;
}

/* ── Sidebar section ──────────────────────────────────────────────── */
.side-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 20px;
    margin-bottom: 12px;
    box-shadow: var(--shadow);
}
.side-label {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em;
    color: var(--text-light); margin-bottom: 12px;
}
.side-name {
    font-size: 16px; font-weight: 700; color: var(--text);
}
.side-role {
    font-size: 13px; color: var(--text-muted); margin-top: 2px;
}
.topic-item {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 0; font-size: 13px;
}
.topic-done { color: var(--green); font-weight: 600; }
.topic-pending { color: var(--text-light); }
.topic-dot {
    width: 8px; height: 8px; border-radius: 50%;
    flex-shrink: 0;
}
.topic-dot.done { background: var(--green); }
.topic-dot.active { background: var(--primary); animation: blink 1.5s ease-in-out infinite; }
.topic-dot.pending { background: var(--border); }

/* ── Control placeholder ──────────────────────────────────────────── */
.ctrl-placeholder {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    background: #F9FAFB; border: 1px solid var(--border);
    border-radius: var(--r-xs);
    margin-bottom: 8px;
    font-size: 13px; color: var(--text-muted);
}
.ctrl-icon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}

/* ── Interview complete ───────────────────────────────────────────── */
.complete-card {
    background: linear-gradient(135deg, #ECFDF5, #F0FDF4);
    border: 1px solid #A7F3D0;
    border-radius: var(--r);
    text-align: center;
    padding: 32px 24px;
    margin: 20px 0;
}
.complete-card h3 {
    font-size: 18px; font-weight: 700;
    color: #065F46; margin: 8px 0 4px;
}
.complete-card p {
    font-size: 14px; color: var(--text-muted); margin: 0;
}

/* ── Report ───────────────────────────────────────────────────────── */
.report-hero {
    background: var(--gradient);
    border-radius: 20px;
    padding: 40px;
    color: white;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.report-hero::before {
    content: '';
    position: absolute; top: -40%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,.1) 0%, transparent 70%);
    border-radius: 50%;
}
.report-candidate {
    font-size: 14px; color: rgba(255,255,255,.7);
    margin-bottom: 4px; position: relative; z-index: 1;
}
.report-title {
    font-size: 28px; font-weight: 800;
    color: white; margin: 0 0 4px;
    position: relative; z-index: 1;
}
.report-role {
    font-size: 14px; color: rgba(255,255,255,.7);
    position: relative; z-index: 1;
}

/* Score ring */
.score-ring-wrap {
    text-align: center;
    position: relative; z-index: 1;
}
.score-ring {
    width: 100px; height: 100px;
    border-radius: 50%;
    border: 5px solid rgba(255,255,255,.3);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    margin: 0 auto 8px;
    background: rgba(255,255,255,.1);
    backdrop-filter: blur(8px);
}
.score-num {
    font-size: 32px; font-weight: 800;
    color: white; line-height: 1;
}
.score-of {
    font-size: 12px; color: rgba(255,255,255,.6);
}
.score-label {
    font-size: 15px; font-weight: 700;
    color: white;
}

/* Dimension cards */
.dim-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 24px;
    box-shadow: var(--shadow);
    height: 100%;
}
.dim-top {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px;
}
.dim-title {
    font-size: 14px; font-weight: 700; color: var(--text);
}
.dim-score {
    font-size: 22px; font-weight: 800;
}
.dim-text {
    font-size: 13px; color: var(--text-muted); line-height: 1.65;
    margin-top: 12px;
}

/* Strengths / Weaknesses */
.sw-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xs);
    margin-bottom: 8px;
    font-size: 14px; color: var(--text);
    line-height: 1.5;
    transition: all .15s ease;
}
.sw-item:hover { border-color: var(--border-light); box-shadow: var(--shadow); }
.sw-icon {
    width: 24px; height: 24px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; flex-shrink: 0; font-weight: 700;
}
.sw-icon.green { background: #ECFDF5; color: #059669; }
.sw-icon.orange { background: #FFF7ED; color: #D97706; }

/* Evidence */
.ev-card {
    border-left: 3px solid var(--primary);
    background: var(--surface);
    border-radius: 0 var(--r-xs) var(--r-xs) 0;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
}
.ev-q {
    font-size: 14px; font-weight: 600; color: var(--primary);
    margin-bottom: 6px;
}
.ev-a {
    font-size: 13px; color: var(--text-muted);
    font-style: italic; line-height: 1.6;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-light);
    margin-bottom: 8px;
}
.ev-assess {
    font-size: 12px; color: var(--text-light);
}

/* Integrity */
.int-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-light);
    font-size: 13px;
}
.int-row:last-child { border-bottom: none; }
.sev-badge {
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    text-transform: uppercase; letter-spacing: .03em;
}
.sev-warn { background: #FFF7ED; color: #D97706; }
.sev-info { background: #EFF6FF; color: #2563EB; }
.sev-clear { background: #ECFDF5; color: #059669; }

/* Section header with icon */
.sec-header {
    display: flex; align-items: center; gap: 10px;
    font-size: 18px; font-weight: 700;
    color: var(--text);
    margin: 28px 0 16px;
}
.sec-icon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}

/* ── Mic pulse (placeholder) ──────────────────────────────────────── */
.mic-pulse {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: var(--gradient);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; color: white;
    animation: mic-ring 2s ease-in-out infinite;
    margin: 0 auto;
}
@keyframes mic-ring {
    0%, 100% { box-shadow: 0 0 0 0 rgba(99,91,255,.3); }
    50% { box-shadow: 0 0 0 12px rgba(99,91,255,0); }
}

/* ── Buttons ──────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: var(--r-xs) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 24px !important;
    font-size: 14px !important;
    transition: all .15s ease !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: var(--gradient) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(99,91,255,.3) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(99,91,255,.4) !important;
    transform: translateY(-1px);
}

/* ── Inputs ───────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: var(--r-xs) !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    transition: all .15s ease !important;
    background: var(--surface) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99,91,255,.1) !important;
}
[data-testid="stFileUploader"] {
    border-radius: var(--r) !important;
}
.stChatInput > div {
    border-radius: var(--r) !important;
    border: 1.5px solid var(--border) !important;
}
.stChatInput > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99,91,255,.1) !important;
}
</style>
"""
