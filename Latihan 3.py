import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import folium
from streamlit_folium import st_folium
import json

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO Survey Lot System", layout="wide")

# --- DATABASE USER ---
if 'user_db' not in st.session_state:
    st.session_state['user_db'] = {
        "admin": {"pass": "puo123", "full_name": "ADMINISTRATOR"},
        "1": {"pass": "puo123", "full_name": "DHIA ARWIENA"},
        "2": {"pass": "puo123", "full_name": "QURRATU AIN"},
        "3": {"pass": "puo123", "full_name": "AIN NURLYDIA"}
    }

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = ""

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .header-box {
        background-color: white; padding: 25px; border-radius: 10px;
        border-left: 10px solid #007bff; color: black;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.3); margin-bottom: 20px;
    }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; color: white; }
    .sidebar-header { font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIN ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div style="background: #262730; padding: 30px; border-radius: 15px; border: 1px solid #444;">', unsafe_allow_html=True)
        st.image("https://www.puo.edu.my/webportal/wp-content/uploads/2023/12/Poli_Logo1-1024x599.png", width=250)
        st.subheader("🔑 Log Masuk Sistem")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if u in st.session_state['user_db'] and st.session_state['user_db'][u]['pass'] == p:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else:
                st.error("Username atau Password salah!")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['logged_in']:
    login_page()
else:
    user_id = st.session_state['current_user']
    nama_surveyor = st.session_state['user_db'][user_id]['full_name']

    # --- HEADER ---
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image("https://www.puo.edu.my/webportal/wp-content/uploads/2023/12/Poli_Logo1-1024x599.png", width=180)
    with col_title:
        st.markdown(f"""<div class="header-box">
            <h1 style='margin:0; font-size: 28pt;'>SISTEM SURVEY LOT</h1>
            <p style='margin:0; font-size: 14pt; color: #555;'>Politeknik Ungku Omar | Surveyor: {nama_surveyor}</p>
        </div>""", unsafe_allow_html=True)

    # --- SIDEBAR ---
    st.sidebar.markdown(f"### 👤 {nama_surveyor}")
    if st.sidebar.button("Keluar (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="sidebar-header">👁️ Kawalan Paparan</p>', unsafe_allow_html=True)
    show_satelit = st.sidebar.toggle("Imej Satelit (Google)", value=True)
    show_stn_dot = st.sidebar.checkbox("Paparkan Titik Stesen", value=True)
    show_stn_no = st.sidebar.checkbox("Paparkan No Stesen", value=True)
    show_brg_dist = st.sidebar.checkbox("Paparkan Bearing/Jarak", value=True)
    show_poly = st.sidebar.checkbox("Paparkan Poligon", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="sidebar-header">⚙️ Tetapan Visual</p>', unsafe_allow_html=True)
    sz_marker = st.sidebar.slider("Saiz Marker", 5, 40, 22)
    sz_font = st.sidebar.slider("Saiz Tulisan", 8, 25, 12)
    poly_color = st.sidebar.color_picker("Warna Poligon", "#FFFF00")

    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("Muat naik fail CSV", type=["csv"])
    no_lot_input = st.sidebar.text_input("No Lot", "LOT 12345")

    # --- PROSES DATA ---
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            try:
                # 1. Transformasi Koordinat
                gdf_rso = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.E, df.N), crs="EPSG:4390")
                gdf_wgs = gdf_rso.to_crs("EPSG:4326")
                df['lat'], df['lon'] = gdf_wgs.geometry.y, gdf_wgs.geometry.x
                
                coords_meter = df[['E', 'N']].values.tolist()
                poly_obj = Polygon(coords_meter)
                area_val = poly_obj.area
                perimeter_val = poly_obj.length

                # Bina Peta Folium
                m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, max_zoom=25)
                if show_satelit:
                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                        attr='Google', name='Google Hybrid', max_zoom=25, overlay=False
                    ).add_to(m)

                # --- 2. POPUP MAKLUMAT LOT ---
                if show_poly:
                    popup_lot_html = f"""
                    <div style="font-family: Arial; width: 220px; padding: 5px;">
                        <b style="color:#007bff; font-size: 14px;">MAKLUMAT LOT</b><br>
                        <hr style="margin:5px 0;">
                        <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                            <tr><td style="padding:2px;"><b>Surveyor:</b></td><td>{nama_surveyor}</td></tr>
                            <tr><td style="padding:2px;"><b>Luas:</b></td><td>{area_val:.3f} m²</td></tr>
                            <tr><td style="padding:2px;"><b>Perimeter:</b></td><td>{perimeter_val:.3f} m</td></tr>
                        </table>
                    </div>
                    """
                    folium.Polygon(
                        locations=list(zip(df.lat, df.lon)),
                        color=poly_color, weight=3, fill=True, fill_opacity=0.3,
                        popup=folium.Popup(popup_lot_html, max_width=300)
                    ).add_to(m)

                # --- 3. MARKER STESEN & POPUP ---
                for i, row in df.iterrows():
                    stn_popup_html = f"""
                    <div style="font-family: Arial; width: 160px; padding: 5px;">
                        <b style="color:red; font-size: 14px;">STESEN {int(row['STN'])}</b><br><br>
                        <table style="width: 100%; font-size: 12px;">
                            <tr><td><b>E:</b></td><td>{row['E']:.3f}</td></tr>
                            <tr><td><b>N:</b></td><td>{row['N']:.3f}</td></tr>
                        </table>
                    </div>
                    """
                    if show_stn_dot:
                        folium.CircleMarker(
                            [row['lat'], row['lon']], 
                            radius=sz_marker/2.5, color='white', weight=2, 
                            fill=True, fill_color='red', fill_opacity=1,
                            popup=folium.Popup(stn_popup_html, max_width=250),
                            tooltip=f"Klik untuk Maklumat STN {int(row['STN'])}"
                        ).add_to(m)
                    if show_stn_no:
                        folium.Marker(
                            [row['lat'], row['lon']], 
                            icon=folium.DivIcon(html=f'<b style="color:white; font-size:{sz_font}pt; text-shadow:2px 2px #000; transform:translate(-50%,-50%); display:block; text-align:center; width:30px;">{int(row["STN"])}</b>'),
                            popup=folium.Popup(stn_popup_html, max_width=250)
                        ).add_to(m)

                # --- 4. BEARING & JARAK (PADA PETA & UNTUK EKSPORT) ---
                line_features_data = [] # Untuk simpan data garisan sempadan
                if True: # Sentiasa kira untuk kegunaan eksport
                    for i in range(len(coords_meter)):
                        p1, p2 = coords_meter[i], coords_meter[(i+1)%len(coords_meter)]
                        w1, w2 = (df.lat.iloc[i], df.lon.iloc[i]), (df.lat.iloc[(i+1)%len(df)], df.lon.iloc[(i+1)%len(df)])
                        
                        # Pengiraan Bearing & Jarak
                        de, dn = p2[0]-p1[0], p2[1]-p1[1]
                        dist = np.sqrt(de**2 + dn**2)
                        brg = np.degrees(np.arctan2(de, dn)) % 360
                        
                        deg = int(brg); mnt = int((brg-deg)*60); sec = round(((brg-deg)*60-mnt)*60)
                        brg_text = f"{deg}°{mnt:02d}'{sec:02d}\""
                        
                        # Simpan data untuk GeoJSON
                        line_features_data.append({
                            "type": "Feature",
                            "properties": {
                                "Layer": "Sempadan",
                                "Dari_STN": int(df.STN.iloc[i]),
                                "Ke_STN": int(df.STN.iloc[(i+1)%len(df)]),
                                "Bearing": brg_text,
                                "Jarak_m": round(dist, 3)
                            },
                            "geometry": {"type": "LineString", "coordinates": [[w1[1], w1[0]], [w2[1], w2[0]]]}
                        })

                        # Papar pada peta jika checkbox ditanda
                        if show_brg_dist:
                            angle = np.degrees(np.arctan2(w2[0]-w1[0], w2[1]-w1[1]))
                            if angle > 90: angle -= 180
                            if angle < -90: angle += 180
                            folium.Marker(location=[(w1[0]+w2[0])/2, (w1[1]+w2[1])/2],
                                icon=folium.DivIcon(html=f'<div style="font-size:{sz_font-2}pt; color:#FFFF00; font-weight:bold; text-shadow:2px 2px #000; transform:translate(-50%,-50%) rotate({-angle}deg); text-align:center;">{brg_text}<br>{dist:.2f}m</div>')
                            ).add_to(m)

                # --- 5. EKSPORT QGIS (3 LAYER TERMASUK DATA BEARING/JARAK) ---
                all_features = []
                
                # A. Layer Titik (Stesen)
                for i, row in df.iterrows():
                    all_features.append({
                        "type": "Feature",
                        "properties": {"Layer": "Stesen", "STN": int(row['STN']), "E": row['E'], "N": row['N']},
                        "geometry": {"type": "Point", "coordinates": [row['lon'], row['lat']]}
                    })

                # B. Layer Garisan (Sempadan) - Menggunakan data line_features_data yang sudah ada bearing/jarak
                all_features.extend(line_features_data)

                # C. Layer Poligon (Lot)
                wgs_coords = [[df.lon.iloc[i], df.lat.iloc[i]] for i in range(len(df))]
                wgs_coords.append(wgs_coords[0])
                all_features.append({
                    "type": "Feature",
                    "properties": {"Layer": "Lot", "No_Lot": no_lot_input, "Luas_m2": round(area_val, 3)},
                    "geometry": {"type": "Polygon", "coordinates": [wgs_coords]}
                })

                final_data = json.dumps({"type": "FeatureCollection", "features": all_features}, indent=2)
                st.sidebar.download_button(label="🚀 Export to QGIS (.geojson)", data=final_data, file_name=f"survey_{no_lot_input}.geojson", use_container_width=True)

                # PAPARAN UTAMA
                c1, c2 = st.columns([3, 1])
                with c1:
                    st_folium(m, width=950, height=600, key="survey_map", returned_objects=[])
                with c2:
                    st.metric("Luas (m²)", f"{area_val:.3f}")
                    st.metric("Perimeter (m)", f"{perimeter_val:.3f}")
                    st.write("---")
                    st.dataframe(df[['STN', 'E', 'N']], hide_index=True, use_container_width=True)

            except Exception as e:
                st.error(f"Terjadi ralat: {e}")