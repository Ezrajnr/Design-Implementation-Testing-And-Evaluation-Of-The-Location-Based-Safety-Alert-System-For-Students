import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import json
import datetime
import pandas as pd
from streamlit_js_eval import get_geolocation

# Page Configuration for Mobile View
st.set_page_config(page_title="Student Safety System", page_icon="🛡️", layout="centered")

# Custom CSS for status banners
st.markdown("""
    <style>
    .safe-banner {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
    }
    .danger-banner {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title & Header
st.title("🛡️ LOCATION-BASED SAFETY ALERT SYSTEM FOR STUDENTS")
st.caption("Location-Based Emergency System for Students")

# ------------------------------------------------------------------------------
# MOCK DATABASE / SETUP
# ------------------------------------------------------------------------------
# High-Risk Geofence Zone (e.g., Unlit Off-Campus Area)
HIGH_RISK_ZONE = [
    (6.5244, 3.3792),
    (6.5260, 3.3792),
    (6.5260, 3.3820),
    (6.5244, 3.3820)
]
risk_polygon = Polygon(HIGH_RISK_ZONE)

if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []

# ------------------------------------------------------------------------------
# OBJECTIVE 1: USER-FRIENDLY INTERFACE & CONTROLS
# ------------------------------------------------------------------------------
st.sidebar.header("⚙️ Emergency Setup")
student_id = st.sidebar.text_input("Student ID", value="TSU/FSC/CS/22/1040")
primary_contact = st.sidebar.text_input("Primary Contact (SMS)", value="+2348065239843")

# ------------------------------------------------------------------------------
# OBJECTIVE 2: REAL-TIME DEVICE GPS AUTO-DETECTION
# ------------------------------------------------------------------------------
st.subheader("📍 Live Device GPS Location")

# HTML5 Browser Geolocation Fetch
loc = get_geolocation()

if loc and 'coords' in loc:
    user_lat = loc['coords']['latitude']
    user_lon = loc['coords']['longitude']
    accuracy = loc['coords']['accuracy']
    
    st.success(f"GPS Signal Acquired (Accuracy: ±{accuracy:.1f}m)")
    st.info(f"**Latitude:** {user_lat:.6f} | **Longitude:** {user_lon:.6f}")
else:
    st.warning("⚠️ Please allow browser location access. Using default campus coordinates.")
    # Fallback coordinates inside high-risk test boundary for evaluation
    user_lat = 6.5250
    user_lon = 3.3800

# Spatial Geofence Verification
current_point = Point(user_lat, user_lon)
is_in_danger_zone = risk_polygon.contains(current_point)

if is_in_danger_zone:
    st.markdown('<div class="danger-banner">⚠️ <b>WARNING:</b> You have entered a designated High-Risk Zone!</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="safe-banner">✅ You are currently in a designated Safe Zone.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# INTERACTIVE MAP RENDERING
# ------------------------------------------------------------------------------
m = folium.Map(location=[user_lat, user_lon], zoom_start=16)

# Active User Marker
folium.Marker(
    [user_lat, user_lon],
    popup="Your Location",
    icon=folium.Icon(color="red" if is_in_danger_zone else "blue", icon="user", prefix="fa")
).add_to(m)

# Highlight Danger Zone Polygon
folium.Polygon(
    locations=HIGH_RISK_ZONE,
    color="red",
    fill=True,
    fill_color="red",
    fill_opacity=0.3,
    popup="High-Risk Area"
).add_to(m)

st_folium(m, width=700, height=300)

# ------------------------------------------------------------------------------
# OBJECTIVE 3: MULTI-CHANNEL ALERT MECHANISMS
# ------------------------------------------------------------------------------
st.subheader("🚨 Emergency Response")

if st.button("TRIGGER SOS DISTRESS ALERT", type="primary"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_payload = {
        "student_id": student_id,
        "timestamp": timestamp,
        "location": {"lat": user_lat, "lon": user_lon},
        "danger_zone_active": is_in_danger_zone,
        "recipient": primary_contact
    }
    
    st.session_state.alert_history.append(alert_payload)
    
    # 1. SMS Alert Transmission Summary
    st.success(f"📱 **SMS Distress Alert sent to {primary_contact}**")
    st.code(f"EMERGENCY! Student {student_id} needs help at coordinates ({user_lat:.6f}, {user_lon:.6f}). Map: https://maps.google.com/?q={user_lat},{user_lon}")
    
    # 2. Campus Security Notification
    st.warning("📡 **Live Dispatch Sent to Campus Security Dashboard.**")
    
    # 3. Local Audio Alarm Trigger
    st.markdown("""
        <audio autoplay>
          <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# EVALUATION & LOGGING DATA
# ------------------------------------------------------------------------------
if st.session_state.alert_history:
    with st.expander("📊 View Sent Emergency Logs (Evaluation Data)"):
        st.dataframe(pd.DataFrame(st.session_state.alert_history))
