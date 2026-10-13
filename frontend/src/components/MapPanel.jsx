import { useEffect, useState } from "react";
import { API } from "../api.js";

export default function MapPanel({ alertCount }) {
  const [key, setKey] = useState(0);
  // Rebuild the Folium map every 10 new alerts
  useEffect(() => { if (alertCount % 10 === 0) setKey((k) => k + 1); }, [alertCount]);
  return (
    <div className="panel map">
      <div className="panel-head">
        <h2>Forest map</h2>
        <button onClick={() => setKey((k) => k + 1)}>Refresh map</button>
      </div>
      <iframe key={key} title="Folium map" src={`${API}/api/map`} />
    </div>
  );
}
