const API_BASE = ''

function authHeaders() {
  const key = localStorage.getItem('apiKey') || ''
  const h = {}
  if (key) h['X-API-Key'] = key
  return h
}

export async function getJSON(path) {
  const r = await fetch(API_BASE + path, { headers: authHeaders() })
  if (!r.ok) throw new Error(await r.text())
  return await r.json()
}

export async function postJSON(path, body) {
  const r = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body || {})
  })
  if (!r.ok) throw new Error(await r.text())
  return await r.json()
}
