import os
import logging
import httpx


# --- AGI Sessions client -----------------------------------------------------

logger = logging.getLogger("vigilancepilot.demo")

AGI_BASE_URL = os.getenv("AGI_BASE_URL", "https://api.agi.tech/v1").rstrip("/")
AGI_API_KEY = os.getenv("AGI_API_KEY")
AGI_AGENT_NAME = os.getenv("AGI_AGENT_NAME", "agi-0")

async def call_agi_session(message: str) -> dict | None:
  """
  Call AGI Sessions API using agent_name (e.g. 'agi-0').

  This is *best-effort* only.
  If anything fails, we return None and let the heuristic engine handle scoring.
  """
  if not AGI_API_KEY:
    logger.warning("AGI_API_KEY not set; skipping AGI call.")
    return None

  url = f"{AGI_BASE_URL}/sessions"

  payload = {
    "agent_name": AGI_AGENT_NAME,
    # Minimal shape – 1 user turn. This is enough to avoid 404s
    # and let the AGI backend run the configured agent.
    "input": [
      {
        "role": "user",
        "content": message,
      }
    ],
    # You can add more fields later (stream, session_id, metadata, etc.)
  }

  headers = {
    "Authorization": f"Bearer {AGI_API_KEY}",
    "Content-Type": "application/json",
  }

  try:
    async with httpx.AsyncClient(timeout=15.0) as client:
      resp = await client.post(url, headers=headers, json=payload)
    logger.info("AGI /sessions status: %s", resp.status_code)

    # If AGI returns a 4xx/5xx we just log and fall back.
    resp.raise_for_status()
    data = resp.json()
    logger.debug("AGI /sessions response: %s", data)

    # For now we just return the raw payload.
    # Your analyze() function can inspect it later if needed.
    return data

  except httpx.HTTPError as e:
    logger.error("AGI session HTTP error: %s", e)
  except Exception as e:
    logger.error("AGI session unexpected error: %s", e)

  # On any failure, return None so the demo still works.
  return None
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import httpx

app = FastAPI(title="VigilancePilot Demo API")

class AnalysisRequest(BaseModel):
  message: str

class AnalysisResponse(BaseModel):
  input: str
  risk_score: float
  risk_label: str
  alert_sent: bool

async def send_parent_sms(text: str) -> bool:
  """
  Fire a real SMS via Telnyx.
  Returns True if sent, False on error or if config missing.
  """
  TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
  TELNYX_MESSAGING_PROFILE_ID = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
  TELNYX_FROM_NUMBER = os.getenv("TELNYX_FROM_NUMBER")
  PARENT_ALERT_PHONE = os.getenv("PARENT_ALERT_PHONE")

  # Config check
  if not (TELNYX_API_KEY and TELNYX_MESSAGING_PROFILE_ID and TELNYX_FROM_NUMBER and PARENT_ALERT_PHONE):
    return False

  headers = {
    "Authorization": f"Bearer {TELNYX_API_KEY}",
    "Content-Type": "application/json",
  }

  payload = {
    "from": TELNYX_FROM_NUMBER,
    "to": PARENT_ALERT_PHONE,
    "text": text,
    "messaging_profile_id": TELNYX_MESSAGING_PROFILE_ID,
  }

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      resp = await client.post("https://api.telnyx.com/v2/messages", headers=headers, json=payload)
      resp.raise_for_status()
      """
      REAL Telnyx SMS sender.
      Returns True if Telnyx responds 2xx, False otherwise.
      """

      api_key = os.getenv("TELNYX_API_KEY")
      profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
      from_number = os.getenv("TELNYX_FROM_NUMBER")
      to_number = os.getenv("TELNYX_TO_NUMBER")  # or PARENT_ALERT_PHONE if you added that

      if not (api_key and profile_id and from_number and to_number):
          print("[Telnyx] Missing config, skipping real SMS.")
          return False

      headers = {
          "Authorization": f"Bearer {api_key}",
          "Content-Type": "application/json",
      }

      payload = {
          "from": from_number,
          "to": to_number,
          "text": text,
          "messaging_profile_id": profile_id,
      }

      try:
          async with httpx.AsyncClient(timeout=10.0) as client:
              resp = await client.post(
                  "https://api.telnyx.com/v2/messages",
                  headers=headers,
                  json=payload,
              )
              resp.raise_for_status()
          print("[Telnyx] SMS sent successfully.")
          return True
      except Exception as e:
          print(f"[Telnyx] SMS send failed: {e}")
          return False
    return True
  except Exception:
    return False

@app.get("/", response_class=HTMLResponse)
def demo_page():
  return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>VigilancePilot – Live Risk Demo</title>
  <style>
  body { background:#020617; color:#e5e7eb; font-family:system-ui, sans-serif; margin:0; padding:40px; }
  h1 { font-size:28px; margin-bottom:4px; }
  h2 { font-size:18px; color:#9ca3af; margin-top:0; margin-bottom:24px; }
  textarea { width:100%; max-width:900px; height:160px; background:#020617; color:#e5e7eb; border:1px solid #374151; border-radius:8px; padding:12px; resize:vertical; }
  button { margin-top:16px; padding:10px 20px; border:none; border-radius:999px; background:#2563eb; color:white; font-weight:600; cursor:pointer; }
  .panel { margin-top:24px; max-width:900px; padding:16px 20px; border-radius:12px; background:#020617; border:1px solid #1f2937; box-shadow:0 0 30px rgba(15,23,42,0.8); }
  .badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
  .badge-low { background:rgba(16,185,129,0.15); color:#6ee7b7; }
  .badge-high { background:rgba(239,68,68,0.2); color:#fecaca; }
  pre { margin-top:16px; padding:12px; background:#020617; border-radius:8px; border:1px solid #374151; overflow-x:auto; font-size:12px; }
  </style>
</head>
<body>
  <h1>VigilancePilot – Live Grooming Risk Demo</h1>
  <h2>Paste a chat conversation and see how the engine flags grooming risk.</h2>

  <textarea id="chat"></textarea>
  <br/>
  <button id="runBtn" onclick="runDemo()">Run Safety Check</button>
</body>
</html>
        // ...existing code...
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        const panel = document.getElementById('result');
        const riskLabel = document.getElementById('riskLabel');
        const explanation = document.getElementById('explanation');
        const sms = document.getElementById('sms');
        const json = document.getElementById('json');

        return (
          """
      <!DOCTYPE html>
      <html lang='en'>
      <head>
        <meta charset='UTF-8'>
        <title>VigilancePilot – Live Risk Demo</title>
        <style>
        body { background:#020617; color:#e5e7eb; font-family:system-ui, sans-serif; margin:0; padding:40px; }
        h1 { font-size:28px; margin-bottom:4px; }
        h2 { font-size:18px; color:#9ca3af; margin-top:0; margin-bottom:24px; }
        textarea { width:100%; max-width:900px; height:160px; background:#020617; color:#e5e7eb; border:1px solid #374151; border-radius:8px; padding:12px; resize:vertical; }
        button { margin-top:16px; padding:10px 20px; border:none; border-radius:999px; background:#2563eb; color:white; font-weight:600; cursor:pointer; }
        .panel { margin-top:24px; max-width:900px; padding:16px 20px; border-radius:12px; background:#020617; border:1px solid #1f2937; box-shadow:0 0 30px rgba(15,23,42,0.8); }
        .badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
        .badge-low { background:rgba(16,185,129,0.15); color:#6ee7b7; }
        .badge-high { background:rgba(239,68,68,0.2); color:#fecaca; }
        pre { margin-top:16px; padding:12px; background:#020617; border-radius:8px; border:1px solid #374151; overflow-x:auto; font-size:12px; }
        </style>
      </head>
      <body>
        <h1>VigilancePilot – Live Grooming Risk Demo</h1>
        <h2>Paste a chat conversation and see how the engine flags grooming risk.</h2>

        <textarea id='chat'></textarea>
        <br/>
        <button id='runBtn' onclick='runDemo()'>Run Safety Check</button>
        <div id='result' class='panel' style='display:none;'>
          <div id='riskLabel'></div>
          <div id='explanation' style='margin-top:8px;'></div>
          <div id='sms' style='margin-top:8px;'></div>
          <pre id='json' style='margin-top:12px;'></pre>
        </div>
        <script>
          async function runDemo() {
            const btn = document.getElementById('runBtn');
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            const text = document.getElementById('chat').value;
            try {
              const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
              });
              const data = await res.json();
              const panel = document.getElementById('result');
              const riskLabel = document.getElementById('riskLabel');
              const explanation = document.getElementById('explanation');
              const sms = document.getElementById('sms');
              const json = document.getElementById('json');
              panel.style.display = 'block';
              const label = (data.risk_label || 'UNKNOWN').toUpperCase();
              const score = typeof data.risk_score === 'number' ? Math.round(data.risk_score * 100) : null;
              let badgeClass = 'badge badge-low';
              if (label === 'HIGH') badgeClass = 'badge badge-high';
              riskLabel.innerHTML = '<span class="' + badgeClass + '">' + label + ' RISK' + (score !== null ? ' • ' + score + '%' : '') + '</span>';
              explanation.textContent = data.explanation || '';
              sms.textContent = data.alert_sent
                ? 'Parent alert SMS: SENT to registered guardian phone.'
                : 'Parent alert SMS: Not sent (below threshold or Telnyx misconfigured).';
              json.textContent = JSON.stringify(data, null, 2);
              if (data.alert_sent) {
                alert('⚠ Parent Alert Triggered\nA high-risk pattern was detected and an SMS was sent to the guardian.');
              }
            } catch (e) {
              alert('Error calling API: ' + e);
            } finally {
              btn.disabled = false;
              btn.textContent = 'Run Safety Check';
            }
          }
        </script>
      </body>
      </html>
          """
        )
        alert_sent=alert_sent,
        explanation=explanation,
        sms_error=sms_error,
      )
        const sms = document.getElementById('sms');
        const json = document.getElementById('json');

        panel.style.display = 'block';

        const label = (data.risk_label || 'UNKNOWN').toUpperCase();
        const score = typeof data.risk_score === 'number' ? Math.round(data.risk_score * 100) : null;

        let badgeClass = 'badge badge-low';
        if (label === 'HIGH') badgeClass = 'badge badge-high';

        riskLabel.innerHTML = '<span class="' + badgeClass + '">' + label + ' RISK' + (score !== null ? ' • ' + score + '%' : '') + '</span>';
        explanation.textContent = data.explanation || '';
        sms.textContent = data.alert_sent ? 'Parent alert SMS: SENT to registered guardian phone.' : 'Parent alert SMS: Not sent (below threshold or Telnyx misconfigured).';

        json.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        alert('Error calling API: ' + e);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Run Safety Check';
      }
    }
  </script>
</body>
</html>
'''

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalysisRequest) -> AnalysisResponse:
    text = req.message.lower()

    high_patterns = [
        "don't tell your parents",
        "dont tell your parents",
        "this is our little secret",
        "send me a picture",
        "send me a pic",
        "nobody has to know",
        "when you are alone",
    ]

    high = any(p in text for p in high_patterns)

    if high:
        risk_score = 0.95
        risk_label = "HIGH"
        alert_sent = True  # simulated SMS trigger
        explanation = (
            "High-risk grooming pattern detected: secrecy, boundary pushing, or requests for images. "
            "In the full system this would trigger a real SMS alert to the guardian."
        )
    else:
        risk_score = 0.10
        risk_label = "LOW"
        alert_sent = False
        explanation = (
            "No strong grooming indicators detected in this short sample. "
            "This demo uses a simplified ruleset for the hackathon."
        )

    return AnalysisResponse(
        input=req.message,
        risk_score=risk_score,
        risk_label=risk_label,
        alert_sent=alert_sent,
        explanation=explanation,
    )
