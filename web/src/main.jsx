import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// NOTE: no <React.StrictMode>. StrictMode double-invokes effects in development, which
// creates and immediately destroys a MapLibre instance on every mount. That leaves the
// map canvas in a broken state and makes local verification unreliable. The map component
// itself is written to be idempotent; this simply avoids the dev-only churn.
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
