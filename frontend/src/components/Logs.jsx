import React, { useEffect, useState } from 'react'

export default function Logs(){
  const [text, setText] = useState('')
  async function refresh(){
    const t = await fetch('/api/logs').then(r=>r.text())
    setText(t)
  }
  useEffect(()=>{
    refresh()
    const t = setInterval(refresh, 2000)
    return ()=>clearInterval(t)
  }, [])
  return (
    <div className="card">
      <div style={{fontWeight:600}}>Logs (live)</div>
      <pre style={{whiteSpace:'pre-wrap', background:'rgba(0,0,0,0.35)', padding:12, borderRadius:12, marginTop:8, maxHeight: '60vh', overflow:'auto'}}>{text}</pre>
    </div>
  )
}
