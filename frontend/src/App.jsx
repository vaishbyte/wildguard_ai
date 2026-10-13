import { useAlerts, usePoll } from "./api.js";
import Header from "./components/Header.jsx";
import LiveCamera from "./components/LiveCamera.jsx";
import SoundPanel from "./components/SoundPanel.jsx";
import AlertFeed from "./components/AlertFeed.jsx";
import MapPanel from "./components/MapPanel.jsx";
import ForestPanel from "./components/ForestPanel.jsx";
import SensorTable from "./components/SensorTable.jsx";

export default function App() {
  const { data: status, error } = usePoll("/api/status", 1500);
  const { alerts, connected } = useAlerts();

  return (
    <div className="shell">
      <Header status={status} error={error} wsConnected={connected} alerts={alerts} />
      {error && (
        <p className="banner">
          Backend not reachable at the configured URL. Start it with
          <code>uvicorn app.main:app --reload</code> in the backend folder.
        </p>
      )}
      <main className="grid">
        <section className="watch">
          <LiveCamera camera={status?.camera} />
          <SoundPanel mic={status?.mic} />
        </section>
        <AlertFeed alerts={alerts} />
        <MapPanel alertCount={alerts.length} />
        <ForestPanel />
        <SensorTable />
      </main>
    </div>
  );
}
