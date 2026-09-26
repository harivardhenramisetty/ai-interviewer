import { useState, useRef, useEffect } from 'react';
import { Upload, ChevronRight, Mic, Video, Globe, BrainCircuit, Send, FileText, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

async function apiCall(endpoint, options = {}) {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, options);
  if (!res.ok) {
    let err = 'Unknown Error';
    try {
      const data = await res.json();
      err = data.detail || err;
    } catch {
      err = await res.text();
    }
    if (res.status === 429 || res.status === 503) {
      throw new Error("AI service is currently busy. Please wait a moment and try again.");
    }
    throw new Error(`API Error (${res.status}): ${err}`);
  }
  return await res.json();
}

export default function App() {
  const [step, setStep] = useState('landing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Data State
  const [targetRole, setTargetRole] = useState('');
  const [file, setFile] = useState(null);
  const [candidateId, setCandidateId] = useState(null);
  const [profile, setProfile] = useState(null);
  
  const [interviewId, setInterviewId] = useState(null);
  const [currentQuestionId, setCurrentQuestionId] = useState(null);
  const [questionCount, setQuestionCount] = useState(0);
  const [chatHistory, setChatHistory] = useState([]);
  const [answerInput, setAnswerInput] = useState('');
  const [interviewFinished, setInterviewFinished] = useState(false);
  
  const [report, setReport] = useState(null);
  const [voiceMuted, setVoiceMuted] = useState(false);
  const currentAudioRef = useRef(null);

  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // ── Voice helper ────────────────────────────────────────────────────────
  const speakQuestion = async (text, mode = 'question') => {
    if (voiceMuted || !text) return;
    try {
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      const res = await fetch(`${API_BASE_URL}/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, mode }),
      });
      if (!res.ok) return; // silently skip if TTS fails
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudioRef.current = audio;
      audio.play();
      audio.onended = () => URL.revokeObjectURL(url);
    } catch (_) {
      // TTS errors are non-fatal — interview continues
    }
  };
  // ────────────────────────────────────────────────────────────────────────

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  const handleError = (err) => {
    setError(err.message || 'An unexpected error occurred.');
    setLoading(false);
  };

  const startInterviewSetup = async () => {
    if (!file && !candidateId) return setError("Please upload a resume.");
    if (!targetRole.trim()) return setError("Please enter a target role.");
    
    setError(null);
    setLoading(true);
    
    try {
      let cid = candidateId;
      if (!cid) {
        const formData = new FormData();
        formData.append('file', file);
        const upRes = await apiCall('/upload-resume', { method: 'POST', body: formData });
        cid = upRes.candidate_id;
        setCandidateId(cid);
      }

      const parseRes = await apiCall('/parse-resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: cid, target_role: targetRole })
      });
      
      setProfile(parseRes.profile);
      setStep('system_check');
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const beginInterview = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const startRes = await apiCall('/start-interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: candidateId, target_role: targetRole })
      });
      
      setInterviewId(startRes.interview_id);
      setCurrentQuestionId(startRes.question_id);
      setQuestionCount(1);
      setChatHistory([{ role: 'assistant', content: startRes.question }]);
      setStep('interview');
      speakQuestion(startRes.question, 'question');
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (e) => {
    e?.preventDefault();
    if (!answerInput.trim() || loading) return;
    
    const ans = answerInput;
    setAnswerInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: ans }]);
    setError(null);
    setLoading(true);
    
    try {
      await apiCall('/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          interview_id: interviewId,
          question_id: currentQuestionId,
          answer: ans
        })
      });
      
      const nextRes = await apiCall(`/next-question/${interviewId}`, { method: 'POST' });
      
      if (nextRes.finished) {
        setInterviewFinished(true);
      } else {
        setQuestionCount(nextRes.question_number);
        setCurrentQuestionId(nextRes.question_id);
        const qText = nextRes.question;
        setChatHistory(prev => [...prev, { role: 'assistant', content: qText }]);
        speakQuestion(qText, 'question');
      }
    } catch (err) {
      // Remove the failed user answer from UI to let them retry
      setChatHistory(prev => prev.slice(0, -1));
      setAnswerInput(ans); // put it back
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const rep = await apiCall(`/finish-interview/${interviewId}`, { method: 'POST' });
      setReport(rep);
      setStep('report');
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------------------
  // Sub-components
  // -----------------------------------------------------

  const ErrorBanner = ({ retryFn }) => (
    error ? (
      <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', padding: '16px', borderRadius: '12px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle color="var(--danger)" />
          <span style={{ color: 'var(--text-primary)' }}>{error}</span>
        </div>
        {retryFn && (
          <button onClick={retryFn} className="btn" style={{ background: 'var(--panel-border)', color: 'white' }}>
            <RefreshCw size={16} /> Try Again
          </button>
        )}
      </div>
    ) : null
  );

  const renderLanding = () => (
    <div className="app-container fade-in" style={{ justifyContent: 'center' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '56px', lineHeight: 1.1, marginBottom: '24px' }}>
            Meet your<br /><span className="text-gradient">AI Interviewer.</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '18px', lineHeight: 1.6, marginBottom: '40px' }}>
            Personalised interviews that adapt to your experience, role, and answers — powered by advanced AI evaluation.
          </p>
          
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileText color="var(--primary)" /> Interview Setup
            </h3>
            
            <ErrorBanner retryFn={startInterviewSetup} />

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>Target Role</label>
              <input 
                className="input-field" 
                placeholder="e.g. Senior Frontend Engineer" 
                value={targetRole}
                onChange={e => setTargetRole(e.target.value)}
                disabled={loading}
              />
            </div>
            
            <div 
              className={`upload-area ${file ? 'active' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              style={{ pointerEvents: loading ? 'none' : 'auto', opacity: loading ? 0.6 : 1 }}
            >
              <Upload size={32} color={file ? 'var(--primary)' : 'var(--text-muted)'} style={{ marginBottom: '16px' }} />
              <div style={{ fontWeight: 600 }}>{file ? file.name : 'Upload your Resume (PDF)'}</div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>Extracted locally — securely processed</div>
              <input 
                type="file" 
                ref={fileInputRef} 
                style={{ display: 'none' }} 
                accept=".pdf"
                onChange={e => setFile(e.target.files[0])}
              />
            </div>

            <button 
              className={`btn btn-primary ${loading ? 'btn-disabled' : ''}`}
              style={{ width: '100%', marginTop: '24px', padding: '16px' }}
              onClick={startInterviewSetup}
              disabled={loading}
            >
              {loading ? <div className="spinner"></div> : (
                <>Start Interview <ChevronRight size={18} /></>
              )}
            </button>
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <div className="glass-panel" style={{ padding: '40px', background: 'rgba(17, 24, 39, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BrainCircuit color="white" />
              </div>
              <div>
                <h3 style={{ margin: 0 }}>System Online</h3>
                <div style={{ color: 'var(--success)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)' }}></div>
                  Low Latency Ready
                </div>
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {['Resume Parsing', 'Adaptive Reasoning Engine', 'Real-time Evaluation'].map((t, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <CheckCircle2 size={16} color="var(--primary)" />
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>{t}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSystemCheck = () => (
    <div className="app-container flex-center fade-in">
      <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', padding: '48px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Ready for your interview?</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '40px' }}>Let's quickly verify your setup.</p>
        
        <ErrorBanner retryFn={beginInterview} />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '40px', textAlign: 'left' }}>
          {[
            { icon: <Mic size={20} color="#10b981" />, label: 'Microphone', status: 'Ready' },
            { icon: <Video size={20} color="#3b82f6" />, label: 'Camera', status: 'Ready' },
            { icon: <Globe size={20} color="#f59e0b" />, label: 'Connection', status: 'Excellent' },
            { icon: <BrainCircuit size={20} color="#8b5cf6" />, label: 'AI Engine', status: 'Connected' }
          ].map((item, i) => (
            <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                {item.icon} <span style={{ fontWeight: 600 }}>{item.label}</span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '13px', paddingLeft: '32px' }}>{item.status}</div>
            </div>
          ))}
        </div>

        <button 
          className={`btn btn-primary ${loading ? 'btn-disabled' : ''}`}
          style={{ width: '100%', padding: '16px' }}
          onClick={beginInterview}
          disabled={loading}
        >
          {loading ? <div className="spinner"></div> : "Begin Interview"}
        </button>
      </div>
    </div>
  );

  const renderInterview = () => (
    <div className="app-container fade-in" style={{ padding: '0', display: 'flex', flexDirection: 'row', height: '100vh', maxWidth: 'none' }}>
      
      {/* Sidebar */}
      <div style={{ width: '320px', background: 'var(--panel-bg)', borderRight: '1px solid var(--panel-border)', padding: '32px 24px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
          <BrainCircuit color="var(--primary)" /> AI Interviewer
        </h2>
        
        <div style={{ marginBottom: '40px' }}>
          <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '16px' }}>Candidate</div>
          <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '4px' }}>{profile?.name || 'Candidate'}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>{targetRole}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {(profile?.skills || []).slice(0, 5).map((s, i) => (
              <span key={i} style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary)', padding: '4px 10px', borderRadius: '100px', fontSize: '12px', fontWeight: 500 }}>
                {s}
              </span>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '16px' }}>Progress</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${Math.min((questionCount / 5) * 100, 100)}%`, background: 'var(--primary)', transition: 'width 0.5s ease' }}></div>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', width: '40px' }}>Q{questionCount}</div>
            <button
              onClick={() => {
                setVoiceMuted(m => {
                  if (!m && currentAudioRef.current) {
                    currentAudioRef.current.pause();
                    currentAudioRef.current = null;
                  }
                  return !m;
                });
              }}
              title={voiceMuted ? 'Unmute voice' : 'Mute voice'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: '18px', opacity: voiceMuted ? 0.4 : 1,
                transition: 'opacity 0.2s', padding: '2px 4px'
              }}
            >
              {voiceMuted ? '🔇' : '🔊'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        
        {/* Chat History */}
        <div style={{ flex: 1, padding: '40px 10%', overflowY: 'auto' }}>
          {chatHistory.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className={`chat-avatar ${msg.role === 'assistant' ? 'ai-avatar' : 'user-avatar'}`}>
                {msg.role === 'assistant' ? <BrainCircuit size={20} /> : 'U'}
              </div>
              <div className="chat-bubble">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && !error && (
            <div className="chat-msg assistant">
              <div className="chat-avatar ai-avatar"><BrainCircuit size={20} /></div>
              <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                Thinking...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div style={{ padding: '0 10% 40px' }}>
          
          <ErrorBanner retryFn={() => submitAnswer()} />

          {!interviewFinished ? (
            <form onSubmit={submitAnswer} style={{ position: 'relative' }}>
              <input
                className="input-field"
                style={{ padding: '20px', paddingRight: '64px', fontSize: '16px', borderRadius: '16px', background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', boxShadow: '0 10px 40px rgba(0,0,0,0.5)' }}
                placeholder="Type your answer..."
                value={answerInput}
                onChange={e => setAnswerInput(e.target.value)}
                disabled={loading}
                autoFocus
              />
              <button 
                type="submit"
                disabled={!answerInput.trim() || loading}
                style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'var(--primary)', border: 'none', width: '40px', height: '40px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: (!answerInput.trim() || loading) ? 'not-allowed' : 'pointer', opacity: (!answerInput.trim() || loading) ? 0.5 : 1, transition: '0.2s' }}
              >
                <Send size={18} color="white" />
              </button>
            </form>
          ) : (
            <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
              <CheckCircle2 size={48} color="var(--success)" style={{ marginBottom: '16px' }} />
              <h2 style={{ marginBottom: '24px' }}>Interview Complete</h2>
              <button className={`btn btn-primary ${loading ? 'btn-disabled' : ''}`} onClick={generateReport} disabled={loading}>
                {loading ? <div className="spinner"></div> : "Generate Evaluation Report"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderReport = () => {
    if (!report) return null;

    const scores = [
      { label: 'Technical Accuracy', val: report.technical_score, color: 'var(--primary)' },
      { label: 'Conceptual Depth', val: report.depth_score, color: 'var(--secondary)' },
      { label: 'Clarity', val: report.clarity_score, color: 'var(--success)' },
    ];

    return (
      <div className="app-container fade-in">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '48px' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '13px', marginBottom: '8px' }}>Final Evaluation</div>
            <h1 style={{ fontSize: '40px' }}>{profile?.name || 'Candidate'}</h1>
            <div style={{ color: 'var(--primary)', fontSize: '18px', fontWeight: 500, marginTop: '8px' }}>{targetRole}</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: '100px', height: '100px', borderRadius: '50%', border: `4px solid var(--primary)`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>
              {report.overall_score}
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>Overall / 10</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '48px' }}>
          {scores.map((s, i) => (
            <div key={i} className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ color: 'var(--text-secondary)', marginBottom: '12px' }}>{s.label}</div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: s.color, marginBottom: '16px' }}>{s.val}</div>
              <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                <div style={{ height: '100%', width: `${s.val * 10}%`, background: s.color, borderRadius: '2px' }}></div>
              </div>
            </div>
          ))}
        </div>

        <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={20} color="var(--primary)" /> Executive Summary
          </h3>
          <p style={{ color: 'var(--text-primary)', lineHeight: 1.8, fontSize: '15px' }}>{report.summary}</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px', color: 'var(--success)' }}>Strengths</h3>
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '12px', color: 'var(--text-secondary)' }}>
              {report.strengths.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px', color: 'var(--warning)' }}>Areas for Improvement</h3>
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '12px', color: 'var(--text-secondary)' }}>
              {report.gaps.map((g, i) => <li key={i}>{g}</li>)}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {step === 'landing' && renderLanding()}
      {step === 'system_check' && renderSystemCheck()}
      {step === 'interview' && renderInterview()}
      {step === 'report' && renderReport()}
    </>
  );
}
