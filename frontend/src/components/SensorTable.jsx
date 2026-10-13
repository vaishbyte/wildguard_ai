import { usePoll } from "../api.js";

export default function SensorTable() {
  const { data } = usePoll("/api/sensors", 3000);
  const nodes = (data || []).sort((a, b) => a.node_id.localeCompare(b.node_id));
  return (
    <div className="panel sensors">
      <div className="panel-head">
        <h2>Field sensor nodes</h2>
        <span className="meta">{nodes.length} reporting</span>
      </div>
      {nodes.length === 0 ? (
        <div className="empty">No nodes yet. Run <code>python sensor_sim.py</code> or start the Wokwi ESP32.</div>
      ) : (
        <div className="scroll">
          <table>
            <thead><tr><th>Node</th><th>Motion</th><th>Sound (dB)</th><th>Vibration</th><th>Battery</th><th>Last seen</th></tr></thead>
            <tbody>
              {nodes.map((n) => (
                <tr key={n.node_id} className={n.vibration >= 0.6 && n.sound_db >= 80 ? "hot" : ""}>
                  <td>{n.node_id}</td>
                  <td>{n.motion ? "Yes" : "–"}</td>
                  <td>{n.sound_db}</td>
                  <td>{n.vibration}</td>
                  <td>{n.battery}%</td>
                  <td>{new Date(n.ts).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
