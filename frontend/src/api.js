import { useEffect, useRef, useState } from "react";

export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS = API.replace(/^http/, "ws") + "/ws";

export async function getJSON(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`${path} returned ${r.status}`);
  return r.json();
}

export async function postJSON(path, body) {
  const r = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}

/** Polls an endpoint every `ms` milliseconds. */
export function usePoll(path, ms) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    let alive = true;
    const load = () =>
      getJSON(path)
        .then((d) => alive && (setData(d), setError(null)))
        .catch((e) => alive && setError(e.message));
    load();
    const id = setInterval(load, ms);
    return () => { alive = false; clearInterval(id); };
  }, [path, ms]);
  return { data, error };
}

/** Live alerts: initial load from REST, then pushed over WebSocket. */
export function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    getJSON("/api/alerts?limit=50").then(setAlerts).catch(() => {});
    let retry;
    let stopped = false;
    const connect = () => {
      const ws = new WebSocket(WS);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => { setConnected(false); if (!stopped) retry = setTimeout(connect, 3000); };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "alert") setAlerts((a) => [msg.data, ...a].slice(0, 100));
      };
    };
    connect();
    const ping = setInterval(() => wsRef.current?.readyState === 1 && wsRef.current.send("ping"), 20000);
    return () => { stopped = true; clearTimeout(retry); clearInterval(ping); wsRef.current?.close(); };
  }, []);
  return { alerts, connected };
}
