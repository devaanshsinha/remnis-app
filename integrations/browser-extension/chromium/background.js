const SIDECAR_ENDPOINT = "http://127.0.0.1:8765/ingest/browser";
const APP_NAME = "Google Chrome";
const MIN_RESEND_INTERVAL_MS = 3000;

const lastSentByTab = new Map();

function shouldIgnoreUrl(url) {
  if (!url) return true;
  return (
    url.startsWith("chrome://") ||
    url.startsWith("edge://") ||
    url.startsWith("about:") ||
    url.startsWith("chrome-extension://") ||
    url.startsWith("devtools://")
  );
}

function tabSignature(tab) {
  return `${tab.url || ""}|${tab.title || ""}`;
}

function shouldSend(tab) {
  const now = Date.now();
  const signature = tabSignature(tab);
  const previous = lastSentByTab.get(tab.id);

  if (!previous) {
    lastSentByTab.set(tab.id, { signature, at: now, url: tab.url || "" });
    return true;
  }

  if (previous.signature === signature && now - previous.at < MIN_RESEND_INTERVAL_MS) {
    return false;
  }

  lastSentByTab.set(tab.id, { signature, at: now, url: tab.url || "" });
  return true;
}

async function postTabEvent(tab) {
  if (!tab || tab.id === undefined || shouldIgnoreUrl(tab.url)) {
    return;
  }

  const previous = lastSentByTab.get(tab.id);
  if (!shouldSend(tab)) {
    return;
  }

  const pageTitle = tab.title || tab.url || "Untitled Page";
  const payload = {
    event: {
      timestamp_utc: new Date().toISOString(),
      app_name: APP_NAME,
      window_title: pageTitle,
      url: tab.url,
      page_title: pageTitle,
      snippet: null,
      prev_url: previous?.url || null,
      tab_id: tab.id ?? null,
      window_id: tab.windowId ?? null,
      source_version: "event.v1"
    }
  };

  try {
    await fetch(SIDECAR_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (_) {
    // Sidecar may be offline; fail silently to avoid browser noise.
  }
}

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => {
    if (chrome.runtime.lastError) return;
    void postTabEvent(tab);
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;
  if (!tab.active) return;
  void postTabEvent(tab);
});

chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) return;
  chrome.tabs.query({ active: true, windowId }, (tabs) => {
    if (chrome.runtime.lastError) return;
    if (!tabs.length) return;
    void postTabEvent(tabs[0]);
  });
});
