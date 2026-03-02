# Browser Extension Adapter

This folder contains browser adapters that send page context to the local sidecar endpoint.

## Chromium Adapter

Location:
- `integrations/browser-extension/chromium`

What it sends:
- active tab URL
- tab title
- timestamp

Target endpoint:
- `POST http://127.0.0.1:8765/ingest/browser`

## Local Dev Install (Chrome/Brave/Edge)

1. Open `chrome://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select `integrations/browser-extension/chromium`

## Production Distribution Options

1. Chrome Web Store (recommended)
- Publish extension package for one-click user install.
- Best update and trust experience.

2. Enterprise managed install
- If targeting teams, push extension via managed browser policies.

3. Manual unpacked install
- Useful for alpha/beta testers only.

