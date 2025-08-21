import React, { useEffect, useState } from 'react'
import { getJSON, postJSON } from '../api'

export default function Settings(){
  const [app, setApp] = useState(null)
  const [bit, setBit] = useState(null)
  const [saving, setSaving] = useState(false)

  async function load(){
    const data = await getJSON('/api/settings')
    setApp(data.app); setBit(data.bitrates)
  }
  useEffect(()=>{ load() }, [])

  async function saveApp(){
    setSaving(true)
    try { await postJSON('/api/settings/app', app) } finally { setSaving(false) }
  }
  const [newUser, setNewUser] = useState('')
  const [newPass, setNewPass] = useState('')
  async function changeAccount(){
    if(!newUser && !newPass) return
    await postJSON('/api/auth/change', { username: newUser || undefined, password: newPass || undefined })
    setNewPass(''); setNewUser(''); load()
  }
  async function saveBit(){
    setSaving(true)
    try { await postJSON('/api/settings/bitrates', bit) } finally { setSaving(false) }
  }

  function addOverride(){
    setBit({...bit, overrides: [...(bit.overrides||[]), {directory_pattern:'', width:1920, hdr:false, bitrate_kbps:6000}]})
  }

  if (!app || !bit) return <div className="card">Chargement…</div>

  return (
    <>
      <div className="card">
        <div style={{fontWeight:700, marginBottom:10}}>Configuration</div>
        <div className="row">
          <div>
            <label>Chemin bibliothèque (input)</label>
            <input className="input" value={app.library_path} onChange={e=>setApp({...app, library_path: e.target.value})}/>
          </div>
          <div>
            <label>Chemin sortie (output)</label>
            <input className="input" value={app.output_path} onChange={e=>setApp({...app, output_path: e.target.value})}/>
          </div>
        </div>
        <div className="row" style={{marginTop:10}}>
          <div>
            <label>Cache temporaire</label>
            <input className="input" value={app.cache_path} onChange={e=>setApp({...app, cache_path: e.target.value})}/>
          </div>
          <div>
            <label>Codec vidéo</label>
            <select value={app.video_codec} onChange={e=>setApp({...app, video_codec: e.target.value})}>
              <option value="hevc">HEVC</option>
              <option value="h264">H264</option>
              <option value="av1">AV1</option>
            </select>
          </div>
        </div>
        <div className="row" style={{marginTop:10}}>
          <div>
            <label>GPU indices (ex: 0,1)</label>
            <input className="input" value={(app.gpu_indices||[]).join(',')} onChange={e=>setApp({...app, gpu_indices: e.target.value.split(',').map(x=>x.trim()).filter(Boolean).map(x=>parseInt(x))})} />
          </div>
          <div>
            <label>Workers / GPU</label>
            <input type="number" className="input" value={app.workers_per_gpu} onChange={e=>setApp({...app, workers_per_gpu: parseInt(e.target.value||'1')})} />
          </div>
          <div>
            <label>Re-scan (heures)</label>
            <input type="number" className="input" value={app.scan_interval_hours} onChange={e=>setApp({...app, scan_interval_hours: parseInt(e.target.value||'6')})} />
          </div>
        </div>
        <div className="row" style={{marginTop:10}}>
          <div>
            <label>API key (optionnel)</label>
            <input className="input" value={app.api_key||''} onChange={e=>setApp({...app, api_key: e.target.value})} disabled />
          </div>
          <div>
            <label>Identifiant admin</label>
            <input className="input" value={app.admin?.username||''} onChange={e=>setApp({...app, admin:{...(app.admin||{}), username:e.target.value}})} />
          </div>
          <div>
            <label>Mot de passe admin</label>
            <input className="input" value={'●●●●●●'} disabled />
          </div>
        </div>
        <div style={{marginTop:10}}>
          <button className="button" onClick={saveApp} disabled={saving}>{saving ? 'Sauvegarde…' : 'Sauvegarder la configuration'}</button>
        </div>
      </div>

      <div className="card">
        <div style={{fontWeight:700}}>Règles de bitrate</div>
        <div style={{marginTop:10}}>
          <div style={{fontWeight:600}}>Défauts</div>
          <table className="table">
            <thead><tr><th>Width ≤</th><th>HDR</th><th>Bitrate (kbps)</th></tr></thead>
            <tbody>
              {bit.defaults.map((r,i)=>(
                <tr key={i}>
                  <td><input className="input" value={r.width} onChange={e=>{const d=[...bit.defaults]; d[i]={...d[i], width: parseInt(e.target.value||'0')}; setBit({...bit, defaults:d})}}/></td>
                  <td><input type="checkbox" checked={r.hdr} onChange={e=>{const d=[...bit.defaults]; d[i]={...d[i], hdr: e.target.checked}; setBit({...bit, defaults:d})}}/></td>
                  <td><input className="input" value={r.bitrate_kbps} onChange={e=>{const d=[...bit.defaults]; d[i]={...d[i], bitrate_kbps: parseInt(e.target.value||'0')}; setBit({...bit, defaults:d})}}/></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{marginTop:10}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div style={{fontWeight:600}}>Overrides par répertoire</div>
            <button className="button" onClick={addOverride}>Ajouter une règle</button>
          </div>
          <table className="table">
            <thead><tr><th>Pattern dossier</th><th>Width ≤</th><th>HDR</th><th>Bitrate (kbps)</th></tr></thead>
            <tbody>
              {(bit.overrides||[]).map((r,i)=>(
                <tr key={i}>
                  <td><input className="input" value={r.directory_pattern} onChange={e=>{const d=[...bit.overrides]; d[i]={...d[i], directory_pattern: e.target.value}; setBit({...bit, overrides:d})}}/></td>
                  <td><input className="input" value={r.width} onChange={e=>{const d=[...bit.overrides]; d[i]={...d[i], width: parseInt(e.target.value||'0')}; setBit({...bit, overrides:d})}}/></td>
                  <td><input type="checkbox" checked={r.hdr} onChange={e=>{const d=[...bit.overrides]; d[i]={...d[i], hdr: e.target.checked}; setBit({...bit, overrides:d})}}/></td>
                  <td><input className="input" value={r.bitrate_kbps} onChange={e=>{const d=[...bit.overrides]; d[i]={...d[i], bitrate_kbps: parseInt(e.target.value||'0')}; setBit({...bit, overrides:d})}}/></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{marginTop:10}}>
          <button className="button" onClick={saveBit} disabled={saving}>{saving ? 'Sauvegarde…' : 'Sauvegarder les bitrates'}</button>
        </div>
      </div>

      <div className="card">
        <div style={{fontWeight:700}}>Compte administrateur</div>
        <div className="row" style={{marginTop:10}}>
          <div>
            <label>Nouveau login (laisser vide pour ne pas changer)</label>
            <input className="input" value={newUser} onChange={e=>setNewUser(e.target.value)} />
          </div>
          <div>
            <label>Nouveau mot de passe (laisser vide pour ne pas changer)</label>
            <input type="password" className="input" value={newPass} onChange={e=>setNewPass(e.target.value)} />
          </div>
        </div>
        <div style={{marginTop:10}}>
          <button className="button" onClick={changeAccount} disabled={saving}>Mettre à jour le compte</button>
        </div>
      </div>
    </>
  )
}
