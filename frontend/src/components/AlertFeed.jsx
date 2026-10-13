import { postJSON } from "../api.js";

const time = (ts) => new Date(ts).toLocaleTimeString();

export default function AlertFeed({ alerts }) {
  return (
    <aside className="panel feed">
      <div className="panel-head">
        <h2>Alerts</h2>
        <button onClick={() => postJSON("/api/alerts/test", { category: "chainsaw" })}>
          Send test alert
        </button>
      </div>
      {alerts.length === 0 && <div className="empty">No alerts yet. Stand in front of the camera or run the sensor simulator.</div>}
      <ol>
        {alerts.map((a) => (
          <li key={a.id} className={`sev-${a.severity}`}>
            <div className="row">
              <strong>{a.category.replace("_", " ")}</strong>
              <time>{time(a.ts)}</time>
            </div>
            <div className="row small">
              <span>{a.label}</span>
              <span>{Math.round(a.confidence * 100)}% · {a.source}</span>
            </div>
          </li>
        ))}
      </ol>
    </aside>
  );
}
