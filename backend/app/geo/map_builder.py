"""Folium map: monitoring area, loss heatmap, alerts and sensor nodes."""
import folium
from folium.plugins import HeatMap

from .. import config

COLORS = {"critical": "red", "high": "orange", "medium": "beige", "info": "green"}
ICONS = {"chainsaw": "tree", "engine": "truck", "gunshot": "crosshairs",
         "human": "user", "animal": "paw", "intrusion": "eye",
         "loud_noise": "volume-up"}


def build_map(forest, alerts, nodes):
    lat, lon = forest["center"]
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles=None)
    folium.TileLayer("OpenStreetMap", name="Street").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="Satellite").add_to(m)

    folium.Circle([lat, lon], radius=forest["radius_km"] * 1000, color="#2f7d5b",
                  fill=True, fill_opacity=0.05,
                  tooltip=f"Monitoring area ({forest['radius_km']} km)").add_to(m)

    heat = folium.FeatureGroup(name=f"Tree cover loss hotspots ({forest['hotspots_source']})")
    HeatMap(forest["hotspots"], radius=18, blur=22, min_opacity=0.3).add_to(heat)
    heat.add_to(m)

    folium.Marker([config.STATION_LAT, config.STATION_LON], tooltip="Field station (camera + mic)",
                  icon=folium.Icon(color="blue", icon="video-camera", prefix="fa")).add_to(m)

    alert_fg = folium.FeatureGroup(name="Alerts")
    for a in alerts:
        popup = (f"<b>{a['category']}</b>: {a['label']}<br>conf {a['confidence']}<br>"
                 f"{a['source']}<br>{a['ts'][:19].replace('T', ' ')} UTC")
        folium.Marker([a["lat"], a["lon"]], popup=popup,
                      icon=folium.Icon(color=COLORS.get(a["severity"], "gray"),
                                       icon=ICONS.get(a["category"], "info"),
                                       prefix="fa")).add_to(alert_fg)
    alert_fg.add_to(m)

    node_fg = folium.FeatureGroup(name="Sensor nodes")
    for n in nodes:
        folium.CircleMarker([n["lat"], n["lon"]], radius=6, color="#1d4ed8", fill=True,
                            tooltip=f"{n['node_id']} | sound {n.get('sound_db')} dB | "
                                    f"vib {n.get('vibration')} | motion {n.get('motion')}"
                            ).add_to(node_fg)
    node_fg.add_to(m)

    folium.LayerControl().add_to(m)
    return m.get_root().render()
