import React, { useEffect, useState } from 'react'
import { getJSON, postJSON } from '../api'

function Pill({label, value}){
  return <div className="pill">{label}: <b style={{marginLeft:6}}>{value}</b></div>
}

function GPU({g}){
  const used = Math.round((g.mem_used||0)/1024/1024/1024)
  const total = Math.round((g.mem_total||0)/1024/1024/1024)
  return (
    <div className="card">
      <div style={{fontWeight:600}}>{g.name} (GPU {g.index})</div>
      <div className="kpi" style={{marginTop:8}}>
        <Pill label="Utilisation" value={(g.utilization||0)+'%'} />
        <Pill label="Mémoire" value={used+' / '+total+' Go'} />
      </div>
    </div>
  )
}

export default function Dashboard(){
  const [stats, setStats] = useState({pending:0,processing:0,done:0,failed:0})
  const [gpus, setGpus] = useState([])
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(false)

  async function refresh(){
    const [s, g, j] = await Promise.all([
      getJSON('/api/stats'), getJSON('/api/gpus'), getJSON('/api/jobs')
    ])
    setStats(s); setGpus(g.gpus || []); setRecent(j.recent || [])
  }

  useEffect(()=>{
    refresh()
    const t = setInterval(refresh, 2500)
    return ()=>clearInterval(t)
  }, [])

  async function scan(){
    setLoading(true)
    try{ await postJSON('/api/scan', {}) } finally { setLoading(false); refresh() }
  }

  return (
    <>
      <div className="card">
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <div style={{fontSize:18, fontWeight:700}}>Etat des jobs</div>
          <button className="button" onClick={scan} disabled={loading}>{loading ? 'Scan en cours...' : 'Scanner la bibliothèque'}</button>
        </div>
        <div className="kpi" style={{marginTop:10}}>
          <Pill label="En attente" value={stats.pending} />
          <Pill label="En cours" value={stats.processing} />
          <Pill label="Terminés" value={stats.done} />
          <Pill label="Échecs" value={stats.failed} />
        </div>
      </div>

      {gpus.map(g => <GPU key={g.index} g={g} />)}

      <div className="card">
        <div style={{fontWeight:600}}>Historique récent</div>
        <table className="table">
          <thead><tr><th>Source</th><th>Destination</th><th>Statut</th><th>Dernière maj</th><th>Erreur</th></tr></thead>
          <tbody>
            {recent.map((r,i)=>(
              <tr key={i}>
                <td title={r.src}>{r.src.split('/').pop()}</td>
                <td title={r.dst}>{r.dst?.split('/').pop()}</td>
                <td>{r.status}</td>
                <td>{r.updated_at}</td>
                <td style={{color:'#f88'}}>{r.error||''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
