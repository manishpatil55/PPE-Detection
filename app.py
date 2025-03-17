import streamlit as st
from ultralytics import YOLO
import cv2
import yaml
from twilio.rest import Client
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import numpy as np
import time
import logging
from logging import ERROR

# Configure logging
logging.basicConfig(level=ERROR)

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="PPE Detection System",
    page_icon="🛡️",
    layout="wide"
)

# Load configurations
with open('sites.yaml') as f:
    SITES = yaml.safe_load(f)

# Initialize YOLO model with suppressed logging
model = YOLO("best.pt", verbose=False)

# Twilio setup
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
TWILIO_PHONE = os.getenv('TWILIO_PHONE')
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

# Constants
ALERT_COOLDOWN = 30  # Reduced to 30s for testing (change to 300 for production)

def initialize_session_state():
    session_defaults = {
        'last_alert': None,
        'alert_history': [],
        'camera_active': True,
        'selected_site': 'regular_site'
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def filter_detections(detections, required_ppe):
    """Filter detections to only include required PPE items"""
    return [item for item in detections if item in required_ppe]

def check_ppe_compliance(detected_ppe, required_ppe):
    return list(set(required_ppe) - set(detected_ppe))

def send_alert(site_config, missing_ppe):
    if not twilio_client:
        return "Twilio not configured"
    
    message_body = f"{st.session_state.selected_site.title()} - 🚨PPE Alert! Missing: {', '.join(missing_ppe)}"
    try:
        # SMS
        twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE,
            to=site_config['admin_contacts']['sms']
        )
        # WhatsApp
        twilio_client.messages.create(
            body=message_body,
            from_='whatsapp:' + TWILIO_PHONE,
            to='whatsapp:' + site_config['admin_contacts']['whatsapp']
        )
        return True
    except Exception as e:
        return str(e)

def main():
    initialize_session_state()
    
    st.title("Real-time PPE Detection System 🦺")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration ⚙️")
        new_site = st.selectbox(
            "Select Work Area 🏗️",
            options=list(SITES.keys()),
            index=list(SITES.keys()).index(st.session_state.selected_site)
        )
        
        # Update site only when changed
        if new_site != st.session_state.selected_site:
            st.session_state.selected_site = new_site
            st.session_state.last_alert = None  # Reset cooldown on site change
            st.rerun()

        site_config = SITES[st.session_state.selected_site]
        
        if st.session_state.selected_site != "regular_site":
            st.markdown("### Required PPE:")
            for item in site_config['required_ppe']:
                st.markdown(f"- {item}")
            
            st.markdown("---")
            st.markdown("### Alert Status:")
            if st.session_state.last_alert:
                time_since = datetime.now() - st.session_state.last_alert
                remaining = max(ALERT_COOLDOWN - time_since.seconds, 0)
                st.progress(remaining/ALERT_COOLDOWN)
                st.caption(f"Next alert available in: {remaining // 60}m {remaining % 60}s")
            else:
                st.caption("Alert system ready")
        else:
            st.markdown("### Regular Monitoring Mode")
            st.info("Showing all detected PPE items without alerts")

    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Live Feed 📸")
        video_placeholder = st.empty()
        
    with col2:
        if st.session_state.selected_site != "regular_site":
            st.subheader("Alerts History 🔔")
            alert_placeholder = st.empty()
        else:
            st.subheader("Detected Items 📋")
            detection_placeholder = st.empty()

    # Video processing
    cap = cv2.VideoCapture(0)
    
    try:
        while st.session_state.camera_active:
            ret, frame = cap.read()
            if not ret:
                st.error("Camera feed lost")
                st.session_state.camera_active = False
                break

            # Perform detection
            results = model(frame)
            all_detections = [results[0].names[int(cls)] for box in results[0].boxes for cls in box.cls]
            annotated_frame = results[0].plot()

            # Site-specific processing
            if st.session_state.selected_site == "regular_site":
                # Show all detections
                unique_detections = list(set(all_detections))
                detection_text = "Detected Items:\n" + "\n".join([f"- {item}" for item in unique_detections])
                detection_placeholder.markdown(detection_text)
            else:
                # Filter detections to required PPE only
                required_ppe = site_config['required_ppe']
                filtered_detections = filter_detections(all_detections, required_ppe)
                missing_ppe = check_ppe_compliance(filtered_detections, required_ppe)

                # Alert logic
                if missing_ppe:
                    now = datetime.now()
                    alert_message = f"Missing: {', '.join(missing_ppe)}"
                    
                    # Check cooldown
                    if (not st.session_state.last_alert or 
                        (now - st.session_state.last_alert).seconds > ALERT_COOLDOWN):
                        
                        # Send alert
                        result = send_alert(site_config, missing_ppe)
                        alert_type = "success" if result is True else "error"
                        alert_text = f"Alert sent! {alert_message}" if result is True else f"Failed: {result}"
                        
                        # Update history
                        st.session_state.alert_history.insert(0, {
                            "timestamp": now.strftime("%H:%M:%S"),
                            "status": alert_type,
                            "message": alert_text
                        })
                        st.session_state.last_alert = now
                        
                        # Keep only last 5 alerts
                        if len(st.session_state.alert_history) > 5:
                            st.session_state.alert_history.pop()

                # Update alerts display
                alert_content = []
                for alert in st.session_state.alert_history[:5]:  # Show latest 5
                    color = "#4CAF50" if alert['status'] == "success" else "#FF5252"
                    alert_content.append(
                        f"<div style='border-left: 3px solid {color}; padding: 5px; margin: 5px 0;'>"
                        f"<small>{alert['timestamp']}</small><br>{alert['message']}</div>"
                    )
                
                if alert_content:
                    alert_placeholder.markdown("\n".join(alert_content), unsafe_allow_html=True)
                else:
                    alert_placeholder.info("No alerts sent yet")

            # Update video feed
            video_placeholder.image(
                cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                channels="RGB",
                use_container_width=True
            )

            time.sleep(0.05)  # Reduce CPU usage

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()