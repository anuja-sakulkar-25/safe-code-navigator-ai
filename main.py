import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from schemas import AnalyzeRequest, AnalyzeResponse
from agent import run_safecode_navigator_agent
from scanner import classify_question

load_dotenv()

app = FastAPI(
    title="SafeCode Navigator AI",
    description="AI agent that helps new developers navigate legacy codebases safely.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SafeCode Navigator AI",
        "model": "gemini-1.5-flash",
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Main analysis endpoint — full pipeline."""
    return await run_safecode_navigator_agent(request)


@app.post("/preflight")
async def preflight(payload: dict):
    """Returns safety checklist BEFORE user pastes code."""
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="'question' field required")
    result = classify_question(question)
    return {
        "question_type": result["question_type"],
        "risk_level":    result["risk_level"],
        "warning_checklist": result["warning_checklist"],
    }


@app.get("/demo")
async def demo():
    """Pre-run example — shows full output without needing your own input."""
    req = AnalyzeRequest(
        question="Why does this function sometimes return None instead of raising?",
        code="""def sync_payments(client_id, threshold=0.01):
    url = 'https://API_ENDPOINT_PLACEHOLDER/v2/sync'
    try:
        response = requests.get(url, params={'client': client_id})
        records = response.json().get('records', [])
        results = []
        for record in records:
            if abs(record['amount'] - record['expected']) > threshold:
                record['flagged'] = True
            results.append(record)
        return results
    except Exception:
        return None""",
        context="Nightly billing reconciliation module"
    )
    return await run_safecode_navigator_agent(req)


# ══════════════════════════════════════════════
# CHAT UI
# ══════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def chat_ui():
    return HTMLResponse(content=CHAT_HTML)


# ══════════════════════════════════════════════
# EMBEDDED CHAT HTML — fully corrected
# ══════════════════════════════════════════════

CHAT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>SafeCode Navigator AI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0f172a;color:#e2e8f0;height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* ── Header ── */
header{background:#1e293b;border-bottom:2px solid #0d9488;padding:12px 20px;display:flex;align-items:center;gap:10px;flex-shrink:0}
.logo{width:34px;height:34px;background:#0d9488;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px}
header h1{font-size:17px;font-weight:700;color:#f8fafc}
header p{font-size:11px;color:#94a3b8;margin-top:1px}
.online{margin-left:auto;display:flex;align-items:center;gap:5px;font-size:11px;color:#94a3b8}
.dot{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}

/* ── Layout ── */
.layout{display:flex;flex:1;overflow:hidden}

/* ── Sidebar ── */
.sidebar{width:240px;background:#1e293b;border-right:1px solid #1e3a5f;padding:14px;display:flex;flex-direction:column;gap:10px;overflow-y:auto;flex-shrink:0}
.sidebar h3{font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:1px;margin-bottom:2px}
.tip{background:#0f172a;border:1px solid #1e3a5f;border-left:3px solid #0d9488;border-radius:6px;padding:8px 10px;font-size:11px;color:#94a3b8;line-height:1.5}
.tip b{color:#e2e8f0;display:block;margin-bottom:2px}
.ex{background:#0f172a;border:1px solid #1e3a5f;border-radius:6px;padding:8px 10px;font-size:11px;color:#94a3b8;cursor:pointer;text-align:left;transition:all .15s;line-height:1.4;width:100%;margin-top:4px}
.ex:hover{border-color:#0d9488;color:#e2e8f0}
.ex .lbl{font-size:9px;color:#0d9488;font-weight:700;margin-bottom:2px;text-transform:uppercase}

/* ── Chat ── */
.chat{flex:1;display:flex;flex-direction:column;overflow:hidden}
.msgs{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px}

/* ── Messages ── */
.msg{display:flex;gap:8px;max-width:88%;animation:fi .2s ease}
@keyframes fi{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.msg.user{align-self:flex-end;flex-direction:row-reverse}
.msg.agent{align-self:flex-start}
.av{width:30px;height:30px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700}
.av.u{background:#3b82f6;color:#fff}
.av.a{background:#0d9488;color:#fff}
.bub{border-radius:12px;padding:10px 14px;font-size:13px;line-height:1.65;max-width:100%;word-break:break-word}
.msg.user .bub{background:#1d4ed8;color:#eff6ff;border-bottom-right-radius:3px}
.msg.agent .bub{background:#1e293b;color:#e2e8f0;border:1px solid #1e3a5f;border-bottom-left-radius:3px}
.bub pre{background:#0f172a;border:1px solid #1e3a5f;border-radius:5px;padding:8px 10px;margin-top:7px;overflow-x:auto;font-size:11px;font-family:Consolas,monospace;color:#a5f3fc}

/* ── Security alert ── */
.sec-alert{background:#1c0a0a;border:1px solid #ef4444;border-radius:10px;padding:12px 14px}
.sec-hd{display:flex;align-items:center;gap:7px;color:#ef4444;font-weight:700;font-size:13px;margin-bottom:8px}
.flag{background:#0f172a;border-left:3px solid #ef4444;border-radius:4px;padding:7px 9px;margin-top:5px;font-size:11px;color:#fca5a5}
.flag b{color:#ef4444}
.safe-msg{margin-top:8px;font-size:11px;color:#94a3b8;font-style:italic}
.replace-hint{color:#6ee7b7;display:block;margin-top:3px}

/* ── Warning checklist ── */
.warn-box{background:#1c1400;border:1px solid #f59e0b;border-radius:8px;padding:10px 12px;margin-bottom:8px}
.warn-hd{color:#f59e0b;font-weight:700;font-size:12px;margin-bottom:6px}
.warn-item{font-size:11px;color:#fde68a;padding:2px 0}

/* ── Explanation sections ── */
.exp{display:flex;flex-direction:column;gap:8px}
.esec{background:#0f172a;border:1px solid #1e3a5f;border-radius:7px;overflow:hidden}
.esec-hd{background:#1e293b;padding:7px 11px;font-size:10px;font-weight:700;color:#0d9488;text-transform:uppercase;letter-spacing:1px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none}
.esec-hd:hover{background:#263548}
.esec-bd{padding:10px 12px;font-size:12px;color:#cbd5e1;line-height:1.7;display:none}
.esec-bd.open{display:block}
.esec.always .esec-bd{display:block}
.risk-item{background:#1c0f0f;border-left:3px solid #ef4444;border-radius:4px;padding:7px 9px;margin-top:5px;font-size:11px;color:#fca5a5}
.risk-item.high{border-color:#f59e0b;color:#fde68a;background:#1c160a}
.risk-item.medium{border-color:#3b82f6;color:#bfdbfe;background:#0a0f1c}
.tag{display:inline-block;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:600;margin-right:3px}
.tag.low{background:#14532d;color:#86efac}
.tag.medium{background:#1e3a5f;color:#93c5fd}
.tag.high{background:#431407;color:#fdba74}
.tag.critical{background:#450a0a;color:#fca5a5}
.doc-box{background:#0a0f1a;border:1px solid #1e3a5f;border-radius:5px;padding:9px 11px;font-family:Consolas,monospace;font-size:11px;color:#67e8f9;white-space:pre-wrap;overflow-x:auto}
.q-item{display:flex;gap:7px;padding:5px 0;font-size:12px;color:#cbd5e1;border-bottom:1px solid #1e293b}
.q-item:last-child{border:none}
.qn{color:#0d9488;font-weight:700;min-width:18px}

/* ── Typing indicator ── */
.typing-wrap{display:flex;align-items:center;gap:3px;padding:10px 14px}
.typing-wrap span{width:6px;height:6px;background:#0d9488;border-radius:50%;animation:bounce 1.2s infinite}
.typing-wrap span:nth-child(2){animation-delay:.2s}
.typing-wrap span:nth-child(3){animation-delay:.4s}
@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}

/* ── Input area ── */
.inp-area{background:#1e293b;border-top:1px solid #1e3a5f;padding:12px 16px;flex-shrink:0}
.inp-actions{display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;align-items:center}

/* Action buttons */
.ibtn{height:32px;padding:0 12px;border:1px solid #334155;border-radius:7px;background:#0f172a;color:#94a3b8;font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
.ibtn:hover{border-color:#0d9488;color:#e2e8f0}
.ibtn.active{border-color:#0d9488;color:#0d9488;background:rgba(13,148,136,0.1)}

/* File upload */
.file-lbl{height:32px;padding:0 12px;border:1px solid #334155;border-radius:7px;background:#0f172a;color:#94a3b8;font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
.file-lbl:hover{border-color:#0d9488;color:#e2e8f0}
#fileInput{display:none}
.fname{font-size:10px;color:#0d9488;margin-left:2px}

/* Code textarea panel */
.code-panel{display:none;margin-bottom:8px}
.code-panel.open{display:block}
.code-panel label{font-size:10px;color:#475569;font-weight:700;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:4px}
.code-ta{width:100%;background:#0f172a;border:1px solid #1e3a5f;border-radius:7px;padding:8px 10px;font-family:Consolas,monospace;font-size:12px;color:#a5f3fc;resize:vertical;min-height:100px;max-height:240px;outline:none;transition:border-color .15s}
.code-ta:focus{border-color:#0d9488}

/* Context input panel */
.ctx-panel{display:none;margin-bottom:8px}
.ctx-panel.open{display:block}
.ctx-panel label{font-size:10px;color:#475569;font-weight:700;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:4px}
.ctx-ta{width:100%;background:#0f172a;border:1px solid #1e3a5f;border-radius:7px;padding:8px 10px;font-size:12px;color:#e2e8f0;outline:none;transition:border-color .15s;resize:none;height:44px;font-family:inherit}
.ctx-ta:focus{border-color:#0d9488}
.ctx-ta::placeholder{color:#334155}

/* Main question row */
.inp-row{display:flex;gap:7px;align-items:flex-end}
.q-inp{flex:1;background:#0f172a;border:1px solid #1e3a5f;border-radius:9px;padding:10px 13px;font-size:13px;color:#e2e8f0;outline:none;resize:none;min-height:42px;max-height:110px;font-family:inherit;line-height:1.5;transition:border-color .15s}
.q-inp:focus{border-color:#0d9488}
.q-inp::placeholder{color:#334155}
.send-btn{height:42px;min-width:72px;padding:0 16px;border:none;border-radius:9px;background:#0d9488;color:#fff;font-size:13px;font-weight:700;cursor:pointer;transition:background .15s;flex-shrink:0}
.send-btn:hover{background:#0f766e}
.send-btn:disabled{background:#134e4a;color:#64748b;cursor:not-allowed}

/* ── Welcome screen ── */
.welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;gap:14px;padding:30px;text-align:center}
.welcome h2{font-size:22px;font-weight:700;color:#f8fafc}
.welcome p{font-size:13px;color:#64748b;max-width:400px;line-height:1.65}
.wcards{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:6px}
.wcard{background:#1e293b;border:1px solid #1e3a5f;border-radius:8px;padding:12px 14px;font-size:12px;color:#94a3b8;max-width:170px;line-height:1.5}
.wcard .wi{font-size:20px;display:block;margin-bottom:6px}
</style>
</head>
<body>

<!-- ── Header ── -->
<header>
  <div class="logo">&#128737;</div>
  <div>
    <h1>SafeCode Navigator AI</h1>
    <p>Navigate legacy codebases safely</p>
  </div>
  <div class="online"><span class="dot"></span>Agent Online</div>
</header>

<div class="layout">

  <!-- ── Sidebar ── -->
  <div class="sidebar">
    <div>
      <h3>How to use</h3>
      <div class="tip"><b>1. Type your question</b>Ask anything about a function, workflow, or dependency.</div>
      <div class="tip" style="margin-top:6px;border-color:#f59e0b"><b>2. Add code (optional)</b>Click "Add Code". Replace real API keys and passwords first.</div>
      <div class="tip" style="margin-top:6px;border-color:#3b82f6"><b>3. Get the answer</b>The agent explains purpose, behavior, and what's risky to change.</div>
    </div>
    <div>
      <h3>Try an example</h3>
      <button class="ex" onclick="loadEx('fn')">
        <div class="lbl">Function logic</div>
        Why does this return None sometimes?
      </button>
      <button class="ex" onclick="loadEx('sec')">
        <div class="lbl">Security demo</div>
        Test the scanner with a fake API key
      </button>
      <button class="ex" onclick="loadEx('q')">
        <div class="lbl">No code question</div>
        How does payment reconciliation work?
      </button>
    </div>
    <div>
      <h3>Safety rules</h3>
      <div class="tip" style="border-color:#ef4444">The agent <b style="color:#ef4444">blocks</b> real API keys, DB URLs, JWT tokens and internal IPs before they reach the AI.</div>
    </div>
  </div>

  <!-- ── Chat ── -->
  <div class="chat">
    <div class="msgs" id="msgs">
      <!-- Welcome shown until first message -->
      <div class="welcome" id="welcome">
        <div style="font-size:44px">&#128737;</div>
        <h2>Welcome to SafeCode Navigator AI</h2>
        <p>Ask me anything about the codebase. I explain what code does, why it was written that way, and what's safe to change — without leaking company data.</p>
        <div class="wcards">
          <div class="wcard"><span class="wi">&#128269;</span>Understand functions you've never seen before</div>
          <div class="wcard"><span class="wi">&#9888;</span>Know what's risky to change before touching it</div>
          <div class="wcard"><span class="wi">&#128274;</span>Your sensitive data never reaches the AI</div>
        </div>
      </div>
    </div>

    <!-- ── Input area ── -->
    <div class="inp-area">

      <!-- Toggle buttons row -->
      <div class="inp-actions">
        <button class="ibtn" id="codeBtn" onclick="toggleCode()">
          &#128196; Add Code
        </button>
        <button class="ibtn" id="ctxBtn" onclick="toggleCtx()">
          &#128193; Add Context
        </button>
        <label class="file-lbl" for="fileInput">
          &#128206; Upload File
        </label>
        <input type="file" id="fileInput"
               accept=".py,.js,.ts,.java,.go,.cs,.rb,.cpp,.c,.sql,.txt"
               onchange="handleFile(event)"/>
        <span class="fname" id="fname"></span>
      </div>

      <!-- Code panel (hidden until Add Code clicked) -->
      <div class="code-panel" id="codePanel">
        <label>Code snippet — replace real secrets first (API keys, passwords, DB URLs)</label>
        <textarea class="code-ta" id="codeInput"
          placeholder="Paste your code here...&#10;&#10;Replace before pasting:&#10;  API keys    → API_KEY_PLACEHOLDER&#10;  DB URLs     → DATABASE_URL_PLACEHOLDER&#10;  Passwords   → PASSWORD_PLACEHOLDER&#10;  JWT tokens  → JWT_TOKEN_PLACEHOLDER"></textarea>
      </div>

      <!-- Context panel (hidden until Add Context clicked) -->
      <div class="ctx-panel" id="ctxPanel">
        <label>Context (optional) — which module, system, or team owns this code?</label>
        <textarea class="ctx-ta" id="ctxInput"
          placeholder="e.g. 'This is part of the billing module, called by the nightly cron job'"></textarea>
      </div>

      <!-- Question row -->
      <div class="inp-row">
        <textarea class="q-inp" id="questionInput" rows="1"
          placeholder="Ask anything about the code... e.g. 'What does this function do?'"
          onkeydown="handleKey(event)"
          oninput="autoResize(this)"></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendMessage()">
          Send &#9654;
        </button>
      </div>

    </div>
  </div>
</div>

<script>
// ── State ─────────────────────────────────────────────────────────
var codeOpen = false;
var ctxOpen  = false;
var loading  = false;

// ── Toggle: Add Code panel ────────────────────────────────────────
function toggleCode() {
  codeOpen = !codeOpen;
  document.getElementById('codePanel').classList.toggle('open', codeOpen);
  document.getElementById('codeBtn').classList.toggle('active', codeOpen);
  if (codeOpen) {
    document.getElementById('codeInput').focus();
  }
}

// ── Toggle: Add Context panel ─────────────────────────────────────
function toggleCtx() {
  ctxOpen = !ctxOpen;
  document.getElementById('ctxPanel').classList.toggle('open', ctxOpen);
  document.getElementById('ctxBtn').classList.toggle('active', ctxOpen);
  if (ctxOpen) {
    document.getElementById('ctxInput').focus();
  }
}

// ── File upload → auto-fills code panel ───────────────────────────
function handleFile(event) {
  var file = event.target.files[0];
  if (!file) return;

  document.getElementById('fname').textContent = file.name;

  var reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById('codeInput').value = e.target.result;
    // Open code panel automatically
    if (!codeOpen) toggleCode();
    // Pre-fill context with filename if empty
    var ctxEl = document.getElementById('ctxInput');
    if (!ctxEl.value) {
      ctxEl.value = 'File: ' + file.name;
      if (!ctxOpen) toggleCtx();
    }
  };
  reader.readAsText(file);
}

// ── Auto-resize question textarea ─────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 110) + 'px';
}

// ── Enter = send, Shift+Enter = newline ───────────────────────────
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Load sidebar examples ─────────────────────────────────────────
function loadEx(type) {
  var examples = {
    fn: {
      q: 'Why does this function return None sometimes instead of raising an error?',
      c: 'def process_records(items, threshold=0.01):\n    try:\n        results = []\n        for item in items:\n            if item[\'value\'] > threshold:\n                results.append(item)\n        return results\n    except Exception:\n        return None',
      ctx: 'Part of the nightly data processing pipeline'
    },
    sec: {
      q: 'Why is my Stripe API call failing?',
      c: 'api_key = \'<API_KEY_REMOVED_BY_SAFECODE>\'\nresponse = requests.post(\'https://api.stripe.com/v1/charges\',\n    headers={\'Authorization\': \'Bearer \' + api_key},\n    data={\'amount\': 1000})',
      ctx: 'Payment processing module'
    },
    q: {
      q: 'How does the payment reconciliation workflow connect to the billing system?',
      c: '',
      ctx: 'I am new to the billing team and trying to understand the overall flow'
    }
  };

  var ex = examples[type];
  if (!ex) return;

  document.getElementById('questionInput').value = ex.q;
  autoResize(document.getElementById('questionInput'));

  if (ex.c) {
    document.getElementById('codeInput').value = ex.c;
    if (!codeOpen) toggleCode();
  }
  if (ex.ctx) {
    document.getElementById('ctxInput').value = ex.ctx;
    if (!ctxOpen) toggleCtx();
  }
  document.getElementById('questionInput').focus();
}

// ── Main send function ────────────────────────────────────────────
async function sendMessage() {
  if (loading) return;

  var question = document.getElementById('questionInput').value.trim();
  if (!question) {
    document.getElementById('questionInput').focus();
    return;
  }

  var code    = document.getElementById('codeInput').value.trim();
  var context = document.getElementById('ctxInput').value.trim();

  // Remove welcome screen on first message
  var welcome = document.getElementById('welcome');
  if (welcome) welcome.remove();

  // Step 1: if code is attached, call /preflight first for warning
  if (code) {
    try {
      var pfRes = await fetch('/preflight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      });
      var pfData = await pfRes.json();
      if (pfData.warning_checklist && pfData.warning_checklist.length > 0 && pfData.risk_level !== 'low') {
        showWarning(pfData);
      }
    } catch (e) {
      // preflight is optional — continue if it fails
    }
  }

  // Step 2: show user's message bubble
  addUserBubble(question, code, context);

  // Step 3: clear question input
  document.getElementById('questionInput').value = '';
  document.getElementById('questionInput').style.height = 'auto';

  // Step 4: show typing indicator
  var typingId = showTyping();

  // Step 5: disable send button while waiting
  loading = true;
  document.getElementById('sendBtn').disabled = true;

  // Step 6: call /analyze
  try {
    var body = { question: question };
    if (code)    body.code    = code;
    if (context) body.context = context;

    var res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      throw new Error('Server returned ' + res.status + ': ' + res.statusText);
    }

    var data = await res.json();
    removeTyping(typingId);
    renderAgentResponse(data);

  } catch (err) {
    removeTyping(typingId);
    addMsgBubble('agent',
      '<div style="color:#fca5a5">&#10060; Could not reach the agent.<br>' +
      '<span style="font-size:11px;color:#64748b">Error: ' + esc(err.message) + '</span></div>'
    );
  } finally {
    loading = false;
    document.getElementById('sendBtn').disabled = false;
  }
}

// ── Render preflight warning ──────────────────────────────────────
function showWarning(pd) {
  var items = (pd.warning_checklist || [])
    .map(function(w) { return '<div class="warn-item">&#8226; ' + esc(w) + '</div>'; })
    .join('');
  addMsgBubble('agent',
    '<div class="warn-box">' +
    '<div class="warn-hd">&#9888; Before you paste — replace these first (risk level: ' + esc(pd.risk_level) + ')</div>' +
    items + '</div>'
  );
}

// ── Render user bubble ────────────────────────────────────────────
function addUserBubble(question, code, context) {
  var html = '<div>' + esc(question) + '</div>';
  if (code) {
    var preview = code.length > 200 ? code.slice(0, 200) + '\n...' : code;
    html += '<pre>' + esc(preview) + '</pre>';
  }
  if (context) {
    html += '<div style="margin-top:5px;font-size:11px;color:#93c5fd">&#128193; ' + esc(context) + '</div>';
  }
  addMsgBubble('user', html);
}

// ── Render agent response ─────────────────────────────────────────
function renderAgentResponse(data) {

  // Case 1: security blocked
  if (data.security_check && !data.security_check.passed) {
    var flags = (data.security_check.flags || []).map(function(f) {
      return '<div class="flag">' +
        '<b>&#9940; ' + esc(f.type.replace(/_/g, ' ').toUpperCase()) + '</b><br/>' +
        esc(f.description) +
        '<span class="replace-hint">&#10003; ' + esc(f.replacement_suggestion) + '</span>' +
        '</div>';
    }).join('');
    addMsgBubble('agent',
      '<div class="sec-alert">' +
      '<div class="sec-hd">&#128680; Input Blocked — Sensitive Data Detected</div>' +
      flags +
      '<div class="safe-msg">Your code was NOT sent to the AI. Replace the values above and try again.</div>' +
      '</div>'
    );
    return;
  }

  // Case 2: error with no explanation
  if (data.error && !data.explanation) {
    addMsgBubble('agent', '<div style="color:#fca5a5">&#9888; ' + esc(data.error) + '</div>');
    return;
  }

  // Case 3: successful explanation
  var exp = data.explanation;
  if (!exp) {
    addMsgBubble('agent', 'Could not generate an explanation. Please try again.');
    return;
  }

  var rl = data.risk_level || 'low';
  var qt = (data.question_type || '').replace(/_/g, ' ');
  var conf = data.coverage_confidence
    ? '<span style="font-size:10px;color:#64748b">Confidence: ' + Math.round(data.coverage_confidence * 100) + '%</span>'
    : '';

  var html =
    '<div style="display:flex;gap:6px;align-items:center;margin-bottom:10px;flex-wrap:wrap">' +
    (qt ? '<span style="background:#1e293b;border:1px solid #334155;border-radius:5px;padding:2px 8px;font-size:10px;color:#94a3b8">' + esc(qt) + '</span>' : '') +
    '<span class="tag ' + esc(rl) + '">Risk: ' + esc(rl) + '</span>' +
    conf +
    '</div>' +
    '<div class="exp">';

  // Always-open sections
  html += makeSection('&#127919; Purpose',   exp.purpose,   true,  false);
  html += makeSection('&#9881; Behavior',    exp.behavior,  true,  false);

  // Risk surface — always open, red header
  if (exp.risk_surface && exp.risk_surface.length > 0) {
    var risksHtml = exp.risk_surface.map(function(r) {
      var sv = (r.severity || 'high').toLowerCase();
      return '<div class="risk-item ' + sv + '">' +
        '<b>&#9888; ' + esc(r.description) + '</b><br/>' +
        '<span style="font-size:11px">' + esc(r.reason) + '</span>' +
        '</div>';
    }).join('');
    html +=
      '<div class="esec always">' +
      '<div class="esec-hd" style="color:#ef4444">&#128680; What\'s risky to change</div>' +
      '<div class="esec-bd open">' + risksHtml + '</div>' +
      '</div>';
  }

  // Collapsible sections
  if (exp.intent_reconstruction) {
    html += makeSection('&#129504; Why it was written this way', exp.intent_reconstruction, false, false);
  }
  if (exp.edge_cases && exp.edge_cases.length > 0) {
    var edgeHtml = exp.edge_cases
      .map(function(e) { return '<div style="padding:3px 0;border-bottom:1px solid #1e293b;font-size:12px">&#8226; ' + esc(e) + '</div>'; })
      .join('');
    html += makeSection('&#128270; Edge cases', edgeHtml, false, true);
  }
  if (exp.inputs_outputs) {
    html += makeSection('&#8644; Inputs &amp; outputs', exp.inputs_outputs, false, false);
  }
  if (exp.dependencies && exp.dependencies.length > 0) {
    var depsHtml = exp.dependencies
      .map(function(d) { return '<div style="padding:3px 0;font-size:12px;color:#94a3b8">&#8594; ' + esc(d) + '</div>'; })
      .join('');
    html += makeSection('&#128279; Dependencies', depsHtml, false, true);
  }
  if (exp.suggested_documentation) {
    var docHtml = '<div class="doc-box">' + esc(exp.suggested_documentation) + '</div>';
    html += makeSection('&#128221; Suggested documentation', docHtml, false, true);
  }
  if (exp.questions_for_manager && exp.questions_for_manager.length > 0) {
    var qHtml = exp.questions_for_manager.map(function(q, i) {
      return '<div class="q-item"><span class="qn">Q' + (i + 1) + '</span><span>' + esc(q) + '</span></div>';
    }).join('');
    html += makeSection('&#128172; Ask your manager', qHtml, false, true);
  }

  html += '</div>';
  addMsgBubble('agent', html);
}

// ── Build a collapsible explanation section ───────────────────────
function makeSection(title, content, alwaysOpen, isRawHtml) {
  var id = 'sec_' + Math.random().toString(36).slice(2);
  var bodyClass = alwaysOpen ? 'esec-bd open' : 'esec-bd';
  var sectionClass = alwaysOpen ? 'esec always' : 'esec';
  var arrow = alwaysOpen ? '' : '<span id="' + id + '_a">&#9654;</span>';
  var bodyContent = isRawHtml ? content : '<p>' + esc(content) + '</p>';

  return '<div class="' + sectionClass + '">' +
    '<div class="esec-hd" onclick="toggleSection(\'' + id + '\')">' +
    title + ' ' + arrow +
    '</div>' +
    '<div class="' + bodyClass + '" id="' + id + '">' + bodyContent + '</div>' +
    '</div>';
}

// ── Toggle a collapsible section ──────────────────────────────────
function toggleSection(id) {
  var body  = document.getElementById(id);
  var arrow = document.getElementById(id + '_a');
  if (!body) return;
  var isOpen = body.classList.toggle('open');
  if (arrow) arrow.innerHTML = isOpen ? '&#9660;' : '&#9654;';
}

// ── Typing indicator ──────────────────────────────────────────────
function showTyping() {
  var id = 'typing_' + Date.now();
  var div = document.createElement('div');
  div.id = id;
  div.className = 'msg agent';
  div.innerHTML =
    '<div class="av a">S</div>' +
    '<div class="bub">' +
    '<div class="typing-wrap"><span></span><span></span><span></span></div>' +
    '<div style="font-size:10px;color:#475569;margin-top:3px;padding:0 4px">Analyzing safely...</div>' +
    '</div>';
  document.getElementById('msgs').appendChild(div);
  scrollBottom();
  return id;
}

function removeTyping(id) {
  var el = document.getElementById(id);
  if (el) el.remove();
}

// ── Append a message bubble ───────────────────────────────────────
function addMsgBubble(role, contentHtml) {
  var isUser = role === 'user';
  var div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML =
    '<div class="av ' + (isUser ? 'u' : 'a') + '">' + (isUser ? 'Y' : 'S') + '</div>' +
    '<div class="bub">' + contentHtml + '</div>';
  document.getElementById('msgs').appendChild(div);
  scrollBottom();
}

// ── Scroll chat to bottom ─────────────────────────────────────────
function scrollBottom() {
  var msgs = document.getElementById('msgs');
  msgs.scrollTop = msgs.scrollHeight;
}

// ── HTML escape helper ────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
</script>
</body>
</html>"""