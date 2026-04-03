# 🪝 Webhook Debugger — Flask API

A simple yet powerful **Webhook Debugger UI** built with Flask.

It captures requests sent to **any URL path**, logs them, and provides a clean UI to inspect everything — headers, body, params, files, and more.

---

## ✨ Features

- ✅ Catch **ALL paths** (`/anything/you/want`)
- 📡 Supports all HTTP methods:
  - GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
- 📜 Live request list (auto-refresh)
- 🔍 Detailed request inspector:
  - Headers
  - Query params
  - JSON body
  - Raw body
  - Form data & files
  - Cookies
- 🧠 Smart JSON highlighting
- 🧾 Copy-to-clipboard buttons
- ♻️ Clear all logs instantly
- ⚡ Always returns **200 OK** (perfect for webhook testing)

---
## Screenshot 

<img width="1916" height="861" alt="image" src="https://github.com/user-attachments/assets/567c6b2d-c768-43ec-b8ae-cc73fd04ebcc" />

---

## 🚀 Installation

```bash
pip install flask
```

---

## ▶️ Run the App

```bash
python webhook_debugger.py
```

---

## 🌐 Open Dashboard

```
http://localhost:5000/
```

---

## 📡 Send Test Webhooks

Send requests to **any path**:

```bash
curl -X POST http://localhost:5000/anything/you/want \
     -H "Content-Type: application/json" \
     -d '{"hi":1}'
```

Example endpoints:

```
/stripe/events
/github/push
/test
/abc/xyz
```

---

## 🖥️ UI Overview

### Left Panel
- Live list of incoming requests
- Auto-refreshes every 2.5 seconds
- Filter by method, path, or IP

### Right Panel
- Full request details (does NOT auto-refresh)
- Tabs include:
  - Overview
  - Headers
  - Query Params
  - Body
  - Form / Files
  - Cookies
  - Raw JSON

---

## 📦 API Endpoints

| Endpoint            | Method | Description                  |
|--------------------|--------|------------------------------|
| `/`                | GET    | Web UI dashboard             |
| `/api/requests`    | GET    | Get all captured requests    |
| `/api/clear`       | POST   | Clear request logs           |
| `/<any_path>`      | ALL    | Capture incoming webhook     |

---

## ⚙️ Configuration

```python
MAX_REQUESTS = 200
```

- Limits stored requests in memory (FIFO queue)

---

## 🧪 Use Cases

- Debug webhook integrations (Stripe, GitHub, etc.)
- Inspect incoming HTTP requests
- Test APIs locally
- Validate payload structure

---

## 📸 Example Output

When a request is received:

```json
{
  "status": "captured",
  "request_id": "a1b2c3d4",
  "message": "Received. Open http://localhost:5000 to inspect."
}
```

---

## ⚠️ Notes

- Data is stored **in memory only** (not persistent)
- Not recommended for production use
- Designed for **local debugging & development**

---

## 🧠 Future Ideas

- Save logs to file / database
- Export requests
- Webhook replay feature
- Auth protection
- Dark/light theme toggle

---

## 🪝 Author

Built for developers who want a **fast, no-BS webhook inspector**.

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
