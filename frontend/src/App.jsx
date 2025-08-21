import React, { useEffect, useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import Logs from './components/Logs.jsx'
import Settings from './components/Settings.jsx'

export default function App(){
  const [tab, setTab] = useState('dashboard')
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '')

  useEffect(() => {
    localStorage.setItem('apiKey', apiKey || '')
  }, [apiKey])

  return (
    <div className="container">
      <div className="header">
        <div className="brand">SimplAarr</div>
        <div style={{display:'flex', gap:12, alignItems:'center'}}>
          <input placeholder="API key (optionnel)" className="input" style={{width:220}} value={apiKey} onChange={e=>setApiKey(e.target.value)} />
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
