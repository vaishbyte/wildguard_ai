function Dot({ ok, label }) {
  return <span className={`dot ${ok ? "ok" : "off"}`}>{label}</span>;
}

export default function Header({ status, error, wsConnected, alerts }) {
  const lastHour = alerts.filter((a) => Date.now() - new Date(a.ts) < 3600e3);
  const critical = lastHour.filter((a) => a.severity === "critical").length;
  return (
    <header className="top">
      <div>
        <h1>WildGuard</h1>
        <p className="sub">
          Sundarbans National Park
          {status && ` · ${status.area.radius_km} km around ${status.area.lat}, ${status.area.lon}`}
        </p>
      </div>
      <div className={`threat ${critical ? "hot" : ""}`}>
        <strong>{critical}</strong>
        <span>critical alerts in the last hour</span>
      </div>
      <div className="dots">
        <Dot ok={!error} label="Backend" />
        <Dot ok={wsConnected} label="Live feed" />
        <Dot ok={status?.camera.status === "running"} label="Camera" />
        <Dot ok={status?.mic.status === "running"} label="Microphone" />
        <Dot ok={status?.store === "firestore-emulator"} label={status?.store === "memory" ? "Memory store" : "Firestore"} />
      </div>
    </header>
  );
}
