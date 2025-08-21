const API_BASE = ''

export async function getJSON(path) {
  const r = await fetch(API_BASE + path, { credentials: 'include' })
  if (!r.ok) throw new Error(await r.text())
  return await r.json()
}

export async function postJSON(path, body) {
  const r = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body || {})
  })
  if (!r.ok) throw new Error(await r.text())
  return await r.json()
}

export async function login(username, password){
  return postJSON('/api/login', { username, password })
}

export async function logout(){
  return postJSON('/api/logout', {})
}
