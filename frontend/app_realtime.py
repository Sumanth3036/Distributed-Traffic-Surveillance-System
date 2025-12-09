import streamlit as st
import requests
import time
import json
from PIL import Image
from io import BytesIO
import base64
import cv2
import numpy as np

API_URL = "http://api_server:8000"

st.set_page_config(page_title="🚦 Real-Time Traffic System", layout="wide")

# Custom CSS for better UI
st.markdown("""
    <style>
        .main {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Segoe UI', sans-serif;
        }
        .stButton > button {
            background-color: #1f6feb;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1.5em;
        }
        .frame-container {
            border: 2px solid #30363d;
            border-radius: 10px;
            padding: 10px;
            background: #161b22;
        }
        .stats-box {
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #30363d;
            margin: 10px 0;
        }
        .progress-text {
            font-size: 18px;
            font-weight: bold;
            color: #58a6ff;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='color:#58a6ff;'>🚦 Real-Time Traffic Processing System</h1>
<p>Upload a traffic surveillance <b>video or image</b> and watch the AI process it <b>frame by frame in real-time!</b></p>
<ul>
  <li>🎥 <b>Live Processing View</b> - See each frame being analyzed</li>
  <li>🔍 Detect vehicles and their types</li>
  <li>🔤 Extract license plates</li>
  <li>🪖 Detect helmet violations</li>
  <li>📊 Real-time statistics updates</li>
</ul>
""", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("📤 Upload a Traffic Video/Image", type=["mp4", "avi", "mov", "mkv", "jpg", "jpeg", "png"])

if uploaded_file and st.button("🚀 Start Real-Time Processing"):
    st.info("⏳ Uploading file... Please wait.")
    file_ext = uploaded_file.name.split(".")[-1].lower()
    content_type = "video/mp4" if file_ext in ["mp4", "avi", "mov", "mkv"] else "image/jpeg"
    files = {"file": (uploaded_file.name, uploaded_file, content_type)}
    headers = {"X-API-Key": "traffic123"}

    try:
        # Upload file
        response = requests.post(f"{API_URL}/upload/", files=files, headers=headers)
        response.raise_for_status()
        task_id = response.json()["task_id"]
        st.success(f"✅ Task ID `{task_id}` submitted. Starting real-time processing...")

        # Create layout for real-time display
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎥 Live Processing View")
            frame_placeholder = st.empty()
        
        with col2:
            st.markdown("### 📊 Live Statistics")
            stats_placeholder = st.empty()
            progress_placeholder = st.empty()
        
        # Initialize counters
        total_vehicles = 0
        total_plates = 0
        total_violations = 0
        vehicle_types = {}
        all_plates = []
        all_violations = []
        
        retries = 0
        max_retries = 120
        last_frame_count = 0
        
        # Poll for progress and frames
        while retries < max_retries:
            try:
                # Get current status
                res = requests.get(f"{API_URL}/result/{task_id}")
                res_data = res.json()
                
                # Check if processing is done
                if res_data["status"] == "done":
                    result = json.loads(res_data["result"]) if isinstance(res_data["result"], str) else res_data["result"]
                    st.session_state.result = result
                    st.success("✅ Processing Complete!")
                    break
                
                # Try to get progress info from Redis
                progress_res = requests.get(f"{API_URL}/progress/{task_id}")
                if progress_res.status_code == 200:
                    progress_data = progress_res.json()
                    
                    # Update frame display if new frame is available
                    if "current_frame" in progress_data:
                        frame_data = progress_data["current_frame"]
                        if frame_data:
                            # Decode base64 frame
                            img_bytes = base64.b64decode(frame_data)
                            img = Image.open(BytesIO(img_bytes))
                            frame_placeholder.image(img, caption=f"Frame {progress_data.get('frame_number', 0)}", use_container_width=True)
                    
                    # Update statistics
                    frame_num = progress_data.get('frame_number', 0)
                    total_frames = progress_data.get('total_frames', 0)
                    
                    # Update counters from progress
                    if 'vehicles' in progress_data:
                        for v in progress_data['vehicles']:
                            vtype = v.get('type', 'unknown')
                            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
                    
                    if 'plates' in progress_data:
                        all_plates.extend(progress_data['plates'])
                    
                    if 'violations' in progress_data:
                        all_violations.extend(progress_data['violations'])
                    
                    # Display live stats
                    with stats_placeholder.container():
                        st.markdown(f"""
                        <div class='stats-box'>
                            <p class='progress-text'>Frame: {frame_num} / {total_frames}</p>
                            <p>🚗 Vehicles: {sum(vehicle_types.values())}</p>
                            <p>🔤 Plates: {len(set(all_plates))}</p>
                            <p>⚠️ Violations: {len(all_violations)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if vehicle_types:
                            st.markdown("**Vehicle Breakdown:**")
                            for vtype, count in vehicle_types.items():
                                st.write(f"• {vtype}: {count}")
                    
                    # Progress bar
                    if total_frames > 0:
                        progress = frame_num / total_frames
                        progress_placeholder.progress(progress, text=f"Processing: {int(progress*100)}%")
                
            except Exception as e:
                st.warning(f"Waiting for processing to start... ({e})")
            
            time.sleep(2)
            retries += 1
        
        if retries >= max_retries:
            st.error("⏱️ Timeout: Task took too long. Please try again.")

    except Exception as e:
        st.error(f"🚫 Error: {e}")

# Display final results if available
if "result" in st.session_state:
    result = st.session_state.result
    
    st.markdown("---")
    st.markdown("""<h2 style='color:#8b949e;'>📊 Final Summary:</h2>""", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Frames", result.get('total_frames_processed', 0))
    with col2:
        st.metric("Vehicles", sum(result.get("vehicle_types", {}).values()))
    with col3:
        st.metric("License Plates", len(result.get('license_plates', [])))
    with col4:
        st.metric("Violations", len(result.get('helmet_violations', [])))
    
    # Vehicle types breakdown
    st.markdown("""<h3 style='color:#d2a8ff;'>🚗 Vehicle Types:</h3>""", unsafe_allow_html=True)
    vehicle_types = result.get("vehicle_types", {})
    if vehicle_types:
        cols = st.columns(len(vehicle_types))
        for idx, (vtype, count) in enumerate(vehicle_types.items()):
            with cols[idx]:
                st.metric(vtype.capitalize(), count)
    
    # Helmet violations
    st.markdown("""<h3 style='color:#ff7b72;'>🔴 Helmet Violations:</h3>""", unsafe_allow_html=True)
    helmet_violations = result.get("helmet_violations", [])
    
    if helmet_violations:
        for idx, v in enumerate(helmet_violations, 1):
            st.write(f"{idx}. ❌ No Helmet | Plate: **{v.get('plate', 'Unknown')}**")
    else:
        st.success("✅ No Helmet Violations Detected")
    
    # License plates
    st.markdown("""<h3 style='color:#79c0ff;'>🔤 Detected License Plates:</h3>""", unsafe_allow_html=True)
    plates = result.get('license_plates', [])
    if plates:
        st.write(", ".join([f"`{plate}`" for plate in plates]))
    else:
        st.info("No license plates detected")
    
    # Final annotated output
    st.markdown("""<h3 style='color:#79c0ff;'>📎 Final Annotated Output:</h3>""", unsafe_allow_html=True)
    annotated_url = result.get("annotated_url", "")
    
    if result["type"] == "image":
        try:
            image_res = requests.get(annotated_url)
            image = Image.open(BytesIO(image_res.content))
            st.image(image, caption="🖼️ Final Annotated Image", use_container_width=True)
        except Exception:
            st.warning("⚠️ Unable to load image preview.")
    else:
        st.video(annotated_url)
