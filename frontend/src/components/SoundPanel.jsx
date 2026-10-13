const NAMES = { chainsaw: "Chainsaw", engine: "Engine / vehicle", gunshot: "Gunshot" };

export default function SoundPanel({ mic }) {
  const running = mic?.status === "running";
  return (
    <div className="panel sound">
      <div className="panel-head">
        <h2>Acoustic sensor</h2>
        <span className="meta">{running ? `hearing: ${mic.top_sound}` : mic?.status || "waiting"}</span>
      </div>
      {Object.entries(NAMES).map(([key, name]) => {
        const v = mic?.levels?.[key] || 0;
        return (
          <div key={key} className="meter">
            <span>{name}</span>
            <div className="bar"><i style={{ width: `${Math.min(100, v * 100)}%` }} className={v >= 0.25 ? "hot" : ""} /></div>
            <b>{(v * 100).toFixed(0)}%</b>
          </div>
        );
      })}
    </div>
  );
}
