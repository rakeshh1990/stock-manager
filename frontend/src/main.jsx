import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  const [health, setHealth] = useState('?')
  const [email, setEmail] = useState('test@example.com')
  const [password, setPassword] = useState('password123')
  const [token, setToken] = useState(null)
  const [portfolio, setPortfolio] = useState([])
  const [symbol, setSymbol] = useState('RELIANCE.NS')
  const [analysis, setAnalysis] = useState(null)

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(d => setHealth(d.status)).catch(()=>setHealth('down'))
  }, [])

  const register = async () => {
    await fetch('/api/auth/register', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, password}) })
  }
  const login = async () => {
    const r = await fetch('/api/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, password}) })
    const d = await r.json()
    setToken(d.access_token)
  }
  const loadPortfolio = async () => {
    const r = await fetch('/api/portfolio?user_id=1')
    const d = await r.json()
    setPortfolio(d.symbols || [])
  }
  const savePortfolio = async () => {
    await fetch('/api/portfolio', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:1, symbols: portfolio}) })
    loadPortfolio()
  }
  const analyze = async () => {
    const r = await fetch('/api/analyze?symbol=' + encodeURIComponent(symbol))
    const d = await r.json()
    setAnalysis(d)
  }

  return (
    <div style={{fontFamily:'system-ui', padding:24}}>
      <h1>Stock Alert</h1>
      <p>Gateway health: <b>{health}</b></p>

      <h2>Auth</h2>
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
      <button onClick={register}>Register</button>
      <button onClick={login}>Login</button>
      <p>Token: {token ? token.slice(0,16)+'...' : 'none'}</p>

      <h2>Portfolio</h2>
      <div>
        <input placeholder="Add symbol" onKeyDown={(e)=>{
          if(e.key==='Enter' && e.target.value){
            setPortfolio([...portfolio, e.target.value]); e.target.value=''
          }
        }}/>
        <button onClick={savePortfolio}>Save</button>
        <button onClick={loadPortfolio}>Load</button>
      </div>
      <ul>{portfolio.map((s,i)=>(<li key={i}>{s}</li>))}</ul>

      <h2>Analyze</h2>
      <input value={symbol} onChange={e=>setSymbol(e.target.value)} />
      <button onClick={analyze}>Analyze</button>
      <pre>{analysis ? JSON.stringify(analysis, null, 2) : 'No analysis yet'}</pre>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App/>)
