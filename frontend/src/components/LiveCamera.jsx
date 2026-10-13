import { API } from "../api.js";

export default function LiveCamera({ camera }) {
  const running = camera?.status === "running";
  const counts = Object.entries(camera?.counts || {});
  return (
    <div className="panel camera">
      <div className="panel-head">
        <h2>Camera trap</h2>
        <span className="meta">{running ? `${camera.fps} fps · YOLOv8` : camera?.status || "waiting"}</span>
      </div>
      {running ? (
        <img src={`${API}/api/video_feed`} alt="Live camera with detections" />
      ) : (
        <div className="empty">Camera is {camera?.status || "starting"}. Check ENABLE_CAMERA and CAMERA_INDEX in backend .env.</div>
      )}
      <div className="chips">
        {counts.length === 0 && <span className="chip quiet">Nothing in frame</span>}
        {counts.map(([label, n]) => (
          <span key={label} className={`chip ${label === "human" ? "warn" : ""}`}>{n} × {label}</span>
        ))}
      </div>
    </div>
  );
}
