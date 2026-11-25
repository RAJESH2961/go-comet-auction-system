import { useEffect, useRef, useState } from 'react'

export function useAuctionSocket(rfqId, onEvent) {
  const [connected, setConnected] = useState(false)
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    if (!rfqId) return
    const token = localStorage.getItem('access_token')
    if (!token) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${proto}://${window.location.host}/ws/auctions/${rfqId}?token=${token}`
    let ws, closed = false, retry

    const connect = () => {
      ws = new WebSocket(wsUrl)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (!closed) retry = setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          cbRef.current?.(msg.event, msg.data)
        } catch {}
      }
    }
    connect()
    return () => {
      closed = true
      clearTimeout(retry)
      ws?.close()
    }
  }, [rfqId])

  return connected
}
