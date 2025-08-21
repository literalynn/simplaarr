import React, { useEffect, useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import Logs from './components/Logs.jsx'
import Settings from './components/Settings.jsx'
import { login, logout, getJSON, postJSON } from './api'

export default function App(){
  const [tab, setTab] = useState('dashboard')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [user, setUser] = useState(null)
  const [authError, setAuthError] = useState('')
  const [setupNeeded, setSetupNeeded] = useState(false)
  const [setupUser, setSetupUser] = useState('')
  const [setupPass, setSetupPass] = useState('')

  async function doLogin(){
    setAuthError('')
    try{
      const r = await login(username, password)
      setUser(r.user)
      setPassword('')
    }catch(e){ setAuthError('Identifiants invalides') }
  }
  async function doLogout(){ await logout(); setUser(null) }

  useEffect(()=>{
    getJSON('/api/auth/status').then(r=>{ setSetupNeeded(!!r.setup_needed); if(r.authenticated){ setUser(r.user) } }).catch(()=>{})
  },[])

  async function doSetup(){
    if(!setupUser || !setupPass) return
    await postJSON('/api/auth/setup', { username: setupUser, password: setupPass })
    // connexion automatique avec les identifiants créés
    const r = await login(setupUser, setupPass)
    setUser(r.user)
    setSetupNeeded(false)
    setSetupPass('')
  }

  // Ecran de connexion / setup si nécessaire
  if (setupNeeded || !user) {
    return (
      <div className="auth-wrapper">
        <div className="card auth-card">
          <div style={{fontWeight:700, marginBottom:10}}>{setupNeeded ? 'Initialiser le compte admin' : 'Connexion'}</div>
          {setupNeeded ? (
            <div className="row">
              <div>
                <label>Identifiant</label>
                <input className="input" value={setupUser} onChange={e=>setSetupUser(e.target.value)} />
              </div>
              <div>
                <label>Mot de passe</label>
                <input type="password" className="input" value={setupPass} onChange={e=>setSetupPass(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter') doSetup() }} />
              </div>
            </div>
          ) : (
            <div className="row">
              <div>
                <label>Identifiant</label>
                <input className="input" value={username} onChange={e=>setUsername(e.target.value)} />
              </div>
              <div>
                <label>Mot de passe</label>
                <input type="password" className="input" value={password} onChange={e=>setPassword(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter') doLogin() }} />
              </div>
            </div>
          )}
          <div style={{marginTop:12, display:'flex', gap:8, justifyContent:'flex-end'}}>
            {setupNeeded ? (
              <button className="button" onClick={doSetup}>Initialiser et se connecter</button>
            ) : (
              <button className="button" onClick={doLogin}>Connexion</button>
            )}
            {authError && <div style={{color:'#f88', fontSize:12}}>{authError}</div>}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <div className="brand">SimplAarr</div>
        <div style={{display:'flex', gap:12, alignItems:'center'}}>
          {
            <div style={{display:'flex', gap:8, alignItems:'center'}}>
              <div>Connecté: <b>{user.username}</b></div>
              <button className="button" onClick={doLogout}>Déconnexion</button>
            </div>
          }
          <nav className="nav">
            <a className={tab==='dashboard' ? 'active':''} onClick={()=>setTab('dashboard')}>Dashboard</a>
            <a className={tab==='logs' ? 'active':''} onClick={()=>setTab('logs')}>Logs</a>
            <a className={tab==='settings' ? 'active':''} onClick={()=>setTab('settings')}>Settings</a>
          </nav>
        </div>
      </div>
      {tab==='dashboard' && <Dashboard />}
      {tab==='logs' && <Logs />}
      {tab==='settings' && <Settings />}
      <div className="footer">© {new Date().getFullYear()} SimplAarr — Ultra simple, rapide, optimal.</div>
    </div>
  )
}
