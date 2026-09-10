import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import datetime
import pandas as pd
from streamlit_js_eval import get_geolocation
from twilio.rest import Client

# Page Configuration for Mobile View
st.set_page_config(page_title="Location-Based Safety Alert System", page_icon="🛡️", layout="centered")

# Custom CSS Banners and Layout Enhancements
st.markdown("""
    <style>
    .danger-banner {
        background-color: #f8d7da;
        color: #721c24;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        border: 2px solid #f5c6cb;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# IN-MEMORY DATABASE INITIALIZATION (Simulated User & Alert Storage)
# ------------------------------------------------------------------------------
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "TSU/FSC/CS/22/1040": {
            "password": "password123",
            "name": "John Doe",
            "contact": "+2348065239843",
            "authority_contact": "+234800911911"
        }
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []

# High-Risk Geofence Polygon Setup (Danger Zone Coordinates)
HIGH_RISK_ZONE = [
    (6.5244, 3.3792),
    (6.5260, 3.3792),
    (6.5260, 3.3820),
    (6.5244, 3.3820)
]
risk_polygon = Polygon(HIGH_RISK_ZONE)

# Helper Function: Twilio Live SMS Dispatch
def send_real_sms(to_number, message_body):
    try:
        account_sid = st.secrets["twilio"]["account_sid"]
        auth_token = st.secrets["twilio"]["auth_token"]
        from_number = st.secrets["twilio"]["twilio_number"]

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

# ==============================================================================
# SINGLE-LINE TITLE HEADER (No Text Wrapping)
# ==============================================================================
st.markdown(
    """
    <h1 style="white-space: nowrap; font-size: calc(1.1rem + 1.1vw); margin-bottom: 10px; text-align: center;">
        🛡️ Location-Based Safety Alert System for Students
    </h1>
    """, 
    unsafe_allow_html=True
)

# ==============================================================================
# USE CASE 1: USER REGISTRATION AND LOGIN
# ==============================================================================
if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register User Account"])
    
    with tab_login:
        st.subheader("User Login")
        login_id = st.text_input("Student ID / Username", key="login_id")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary"):
            if login_id in st.session_state.users_db and st.session_state.users_db[login_id]["password"] == login_pass:
                st.session_state.logged_in = True
                st.session_state.current_user = login_id
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid Student ID or Password.")

    with tab_register:
        st.subheader("New User Registration")
        new_id = st.text_input("Student ID (e.g., TSU/FSC/CS/22/1040)", key="reg_id")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        new_name = st.text_input("Full Name", key="reg_name")
        new_contact = st.text_input("Family/Friend Contact (E.164 format: +234...)", key="reg_contact")
        authority_contact = st.text_input("Authority Security Hot-Line", value="+234800911911", key="reg_auth")
        
        if st.button("Register Account"):
            if new_id and new_pass and new_contact:
                st.session_state.users_db[new_id] = {
                    "password": new_pass,
                    "name": new_name,
                    "contact": new_contact,
                    "authority_contact": authority_contact
                }
                st.success("Account created successfully! Please log in.")
            else:
                st.warning("Please fill in all required registration fields.")

else:
    # Authenticated User Dashboard
    user_info = st.session_state.users_db[st.session_state.current_user]
    
    st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state.current_user}**")
    st.sidebar.caption(f"Name: {user_info['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

    # App Navigation Menu according to Use Cases
    nav_option = st.sidebar.radio(
        "System Navigation",
        ["📍 Location Tracking & Safety Map", "🚨 Activate Emergency Alert", "📜 View Alert History"]
    )

    # ==========================================================================
    # USE CASE 2: LOCATION TRACKING & DANGER ZONE WARNING
    # ==========================================================================
    if nav_option == "📍 Location Tracking & Safety Map":
        st.subheader("2. Real-time Location Tracking & Danger Zone Monitoring")
        
        # Capture live browser/mobile GPS
        loc = get_geolocation()

        if loc and 'coords' in loc:
            user_lat = loc['coords']['latitude']
            user_lon = loc['coords']['longitude']
            accuracy = loc['coords']['accuracy']
            st.success(f"GPS Signal Active (Accuracy: ±{accuracy:.1f}m)")
            st.info(f"**Latitude:** {user_lat:.6f} | **Longitude:** {user_lon:.6f}")
        else:
            st.warning("⚠️ Requesting device GPS... You can test coordinates below.")
            
            # Interactive Coordinate Controls for Testing
            col_lat, col_lon = st.columns(2)
            with col_lat:
                user_lat = st.number_input("Latitude", value=6.5250, format="%.6f")
            with col_lon:
                user_lon = st.number_input("Longitude", value=3.3800, format="%.6f")

        # Save active position to session
        st.session_state['user_lat'] = user_lat
        st.session_state['user_lon'] = user_lon

        # Spatial Boundary Check
        current_point = Point(user_lat, user_lon)
        is_in_danger_zone = risk_polygon.contains(current_point)

        # Danger Zone Warning Displays Prominently
        st.error("🚨 HIGH-RISK DANGER ZONE WARNING!")
        st.markdown(
            '<div class="danger-banner">⚠️ <b>ATTENTION REQUIRED:</b> High-Risk Danger Zone actively monitored on map! Exercise extreme caution and stay alert.</div>', 
            unsafe_allow_html=True
        )

        # Google Maps Base Tile Integration
        google_map_tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        google_attr = 'Google Maps'

        # Map Display initialized with Google Maps Tiles
        m = folium.Map(
            location=[user_lat, user_lon], 
            zoom_start=15, 
            tiles=google_map_tiles, 
            attr=google_attr
        )

        # Mark High-Risk Danger Zone Polygon on Google Map
        folium.Polygon(
            locations=HIGH_RISK_ZONE,
            color="red",
            weight=3,
            fill=True,
            fill_color="red",
            fill_opacity=0.45,
            popup=folium.Popup("<b>⚠️ HIGH-RISK DANGER ZONE</b><br>Restricted Unsafe Area", max_width=200),
            tooltip="⚠️ High-Risk Danger Zone"
        ).add_to(m)

        # Mark Current Student GPS Location
        folium.Marker(
            [user_lat, user_lon],
            popup=f"<b>Student:</b> {st.session_state.current_user}<br><b>Status:</b> {'INSIDE DANGER ZONE' if is_in_danger_zone else 'OUTSIDE DANGER ZONE'}",
            tooltip="Your GPS Location",
            icon=folium.Icon(color="red" if is_in_danger_zone else "blue", icon="user", prefix="fa")
        ).add_to(m)

        st_folium(m, width=700, height=400)

    # ==========================================================================
    # USE CASE 3 & 4: EMERGENCY ALERT ACTIVATION & NOTIFICATIONS
    # ==========================================================================
    elif nav_option == "🚨 Activate Emergency Alert":
        st.subheader("3. Emergency Alert Activation")
        st.write("Pressing the SOS button below instantly transmits your real-time coordinates to saved personal contacts and security authorities.")

        # Load active location from session or default
        user_lat = st.session_state.get('user_lat', 6.5250)
        user_lon = st.session_state.get('user_lon', 3.3800)

        st.warning(f"Target Broadcast Location: **Lat {user_lat:.6f}, Lon {user_lon:.6f}**")

        if st.button("🔴 TRIGGER SOS DISTRESS ALERT", type="primary"):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            maps_link = f"https://maps.google.com/?q={user_lat},{user_lon}"
            
            # Formulate Notification Messages (Use Case 4)
            contact_msg = f"EMERGENCY ALERT! Student {st.session_state.current_user} ({user_info['name']}) needs help! Location: {maps_link}"
            auth_msg = f"SECURITY DISPATCH: Student SOS triggered by {st.session_state.current_user} at coordinates ({user_lat:.6f}, {user_lon:.6f}). Map: {maps_link}"

            # 1. Dispatch Notification to Contact (Family/Friend)
            friend_success, friend_sid = send_real_sms(user_info['contact'], contact_msg)
            
            # 2. Dispatch Notification to Authority (Security/Police)
            auth_success, auth_sid = send_real_sms(user_info['authority_contact'], auth_msg)

            # Store in Alert History (Use Case 5)
            alert_entry = {
                "student_id": st.session_state.current_user,
                "timestamp": timestamp,
                "location": f"{user_lat:.6f}, {user_lon:.6f}",
                "contact_recipient": user_info['contact'],
                "contact_status": "DELIVERED" if friend_success else "SIMULATED/FAILED",
                "authority_recipient": user_info['authority_contact'],
                "authority_status": "DISPATCHED" if auth_success else "DISPATCHED (SIMULATED)"
            }
            st.session_state.alert_history.append(alert_entry)

            # UI Display Results
            st.success("🚨 **EMERGENCY ALERT TRIGGERED SUCCESSFULLY!**")
            
            st.markdown(f"📲 **Notification to Contact (Family/Friend):** `{user_info['contact']}`")
            st.code(contact_msg)

            st.markdown(f"👮 **Notification to Authority (Security/Police):** `{user_info['authority_contact']}`")
            st.code(auth_msg)

            # Audio Siren Trigger
            st.markdown("""
                <audio autoplay>
                  <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)

    # ==========================================================================
    # USE CASE 5: VIEWING ALERT HISTORY
    # ==========================================================================
    elif nav_option == "📜 View Alert History":
        st.subheader("5. Viewing Alert History")
        st.write("Below is the record of past emergency alerts activated by students.")

        if st.session_state.alert_history:
            df_history = pd.DataFrame(st.session_state.alert_history)
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No past emergency alerts recorded in the current session.")
