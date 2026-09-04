const messages = document.getElementById("messages");
const input = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const resetBtn = document.getElementById("resetBtn");
const analyticsBtn = document.getElementById("analyticsBtn");
const analytics = document.getElementById("analytics");

let sessionId = crypto.randomUUID();

function addMessage(text, role) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  input.disabled = loading;
}

async function send() {
  const message = input.value.trim();

  if (!message || sendBtn.disabled) {
    return;
  }

  addMessage(message, "user");
  input.value = "";
  setLoading(true);

  let conversationEnded = false;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id: sessionId,
        message
      })
    });

    const contentType = res.headers.get("content-type") || "";

    const data = contentType.includes("application/json")
      ? await res.json()
      : { detail: await res.text() };

    if (!res.ok) {
      throw new Error(
        data.detail || data.message || "Request failed."
      );
    }

    addMessage(
      data.reply || "No response received.",
      "bot"
    );

    await loadAnalytics();

    if (data.ended) {
      conversationEnded = true;
    }

  } catch (err) {
    console.error("Chat error:", err);

    addMessage(
      `Sorry, something went wrong: ${err.message}`,
      "bot"
    );

  } finally {
    if (conversationEnded) {
      input.disabled = true;
      sendBtn.disabled = true;
    } else {
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }
}

async function loadAnalytics() {
  try {
    const res = await fetch(
      `/api/analytics/${sessionId}`
    );

    if (!res.ok) {
      return;
    }

    const data = await res.json();

    analytics.textContent = JSON.stringify(
      data,
      null,
      2
    );

  } catch (err) {
    console.error("Analytics error:", err);
  }
}

async function resetConversation() {
  try {
    await fetch("/api/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id: sessionId
      })
    });

  } catch (err) {
    console.error("Reset error:", err);
  }

  sessionId = crypto.randomUUID();

  messages.innerHTML = "";

  input.disabled = false;
  sendBtn.disabled = false;

  addMessage(
    "Hi! I can help you with Northstar One, our 2 BHK and 3 BHK homes in Sector 79, Gurugram. What are you looking for?",
    "bot"
  );

  analytics.textContent =
    "Start a conversation to see analytics.";

  input.focus();
}

sendBtn.addEventListener("click", send);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    send();
  }
});

resetBtn.addEventListener(
  "click",
  resetConversation
);

analyticsBtn.addEventListener(
  "click",
  loadAnalytics
);

addMessage(
  "Hi! I can help you with Northstar One, our 2 BHK and 3 BHK homes in Sector 79, Gurugram. What are you looking for?",
  "bot"
);