import streamlit as st
import requests
import time
import json
from PIL import Image
from io import BytesIO

API_URL = "http://api_server:8000"

st.set_page_config(page_title="🚦 Traffic Surveillance System", layout="wide")

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
            font-size: 16px;
        }
        .download-button > button {
            background-color: #238636;
            color: white;
            border-radius: 8px;
            padding: 0.75em 2em;
            font-size: 18px;
            font-weight: bold;
        }
        .stats-box {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363d;
            margin: 10px 0;
        }
        .upload-section {
            background: #161b22;
            padding: 30px;
            border-radius: 10px;
            border: 2px dashed #30363d;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='color:#58a6ff;'>🚦 Traffic Surveillance System</h1>
<p style='font-size:18px;'>Upload a traffic surveillance <b>video or image</b> and get a processed output with vehicle detection blocks!</p>
<ul style='font-size:16px;'>
  <li>🚗 <b>Vehicle Detection</b> - Detect and classify vehicles (cars, motorcycles, trucks, buses, bicycles)</li>
  <li>🔤 <b>License Plate Recognition</b> - Extract license plate numbers</li>
  <li>🪖 <b>Helmet Violation Detection</b> - Identify riders without helmets</li>
  <li>📥 <b>Downloadable Output</b> - Get annotated video/image with colored bounding boxes</li>
</ul>
""", unsafe_allow_html=True)

st.markdown("---")

# Upload Section
st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
st.markdown("### 📤 Upload Your Video or Image")
uploaded_file = st.file_uploader(
    "Choose a traffic surveillance file",
    type=["mp4", "avi", "mov", "mkv", "jpg", "jpeg", "png"],
    help="Supported formats: MP4, AVI, MOV, MKV for videos | JPG, JPEG, PNG for images"
)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🚀 Process Video/Image", key="process_btn"):
            st.session_state.processing = True
            st.session_state.task_id = None
            st.session_state.result = None
    
    with col2:
        st.info("Click 'Process Video/Image' to start detection analysis")

# Processing Logic
if st.session_state.get('processing', False):
    st.markdown("---")
    st.markdown("### 🔄 Processing Status")
    
    if not st.session_state.get('task_id'):
        # Upload file
        with st.spinner("⏳ Uploading file to server..."):
            file_ext = uploaded_file.name.split(".")[-1].lower()
            content_type = "video/mp4" if file_ext in ["mp4", "avi", "mov", "mkv"] else "image/jpeg"
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), content_type)}
            headers = {"X-API-Key": "traffic123"}
            
            try:
                response = requests.post(f"{API_URL}/upload/", files=files, headers=headers)
                response.raise_for_status()
                task_id = response.json()["task_id"]
                st.session_state.task_id = task_id
                st.success(f"✅ File uploaded successfully! Task ID: `{task_id}`")
            except Exception as e:
                st.error(f"🚫 Upload Error: {e}")
                st.session_state.processing = False
                st.stop()
    
    # Poll for results
    if st.session_state.get('task_id'):
        task_id = st.session_state.task_id
        progress_bar = st.progress(0, text="Processing video/image...")
        status_text = st.empty()
        
        retries = 0
        max_retries = 180  # 6 minutes max (180 * 2 seconds)
        
        while retries < max_retries:
            try:
                res = requests.get(f"{API_URL}/result/{task_id}")
                res_data = res.json()
                
                if res_data["status"] == "done":
                    result = json.loads(res_data["result"]) if isinstance(res_data["result"], str) else res_data["result"]
                    st.session_state.result = result
                    st.session_state.processing = False
                    progress_bar.progress(100, text="✅ Processing Complete!")
                    break
                elif res_data["status"] == "processing":
                    progress = min((retries / max_retries) * 100, 95)
                    progress_bar.progress(int(progress), text=f"🔄 Processing... ({int(progress)}%)")
                    status_text.info(f"⏳ Analyzing frames and detecting vehicles... (Attempt {retries + 1}/{max_retries})")
                elif res_data["status"] == "queued":
                    status_text.info("📋 Task queued, waiting to start processing...")
                else:
                    status_text.warning(f"Status: {res_data['status']}")
                
            except Exception as e:
                status_text.warning(f"Checking status... ({e})")
            
            time.sleep(2)
            retries += 1
        
        if retries >= max_retries:
            st.error("⏱️ Processing timeout. The video might be too long or the system is busy. Please try again with a shorter video.")
            st.session_state.processing = False

# Display Results
if st.session_state.get('result'):
    result = st.session_state.result
    
    st.markdown("---")
    st.markdown("## 🎉 Processing Complete!")
    
    # Summary Statistics
    st.markdown("### 📊 Detection Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📹 Total Frames", result.get('total_frames_processed', 0))
    with col2:
        st.metric("🚗 Vehicles Detected", sum(result.get("vehicle_types", {}).values()))
    with col3:
        st.metric("🔤 License Plates", len(result.get('license_plates', [])))
    with col4:
        st.metric("⚠️ Helmet Violations", len(result.get('helmet_violations', [])))
    
    # Vehicle Types Breakdown
    st.markdown("### 🚗 Vehicle Types Detected")
    vehicle_types = result.get("vehicle_types", {})
    if vehicle_types:
        cols = st.columns(len(vehicle_types))
        for idx, (vtype, count) in enumerate(vehicle_types.items()):
            with cols[idx]:
                st.markdown(f"""
                <div class='stats-box' style='text-align:center;'>
                    <h3 style='color:#58a6ff;'>{count}</h3>
                    <p style='font-size:16px;'>{vtype.capitalize()}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No vehicles detected in this video/image")
    
    # License Plates
    st.markdown("### 🔤 Detected License Plates")
    plates = result.get('license_plates', [])
    if plates:
        plate_text = " | ".join([f"`{plate}`" for plate in plates])
        st.markdown(f"**Found {len(plates)} unique plate(s):** {plate_text}")
    else:
        st.info("No license plates detected")
    
    # Helmet Violations
    st.markdown("### 🪖 Helmet Violations")
    helmet_violations = result.get("helmet_violations", [])
    if helmet_violations:
        st.warning(f"⚠️ Found {len(helmet_violations)} helmet violation(s):")
        for idx, v in enumerate(helmet_violations, 1):
            st.write(f"{idx}. ❌ No Helmet Detected | License Plate: **{v.get('plate', 'Unknown')}**")
    else:
        st.success("✅ No helmet violations detected")
    
    # Download Section
    st.markdown("---")
    st.markdown("### 📥 Download Processed Output")
    st.markdown("""
    <div style='background:#161b22; padding:20px; border-radius:10px; border:2px solid #238636;'>
        <p style='font-size:18px; margin-bottom:15px;'>
            Your processed video/image is ready with <b>color-coded bounding boxes</b>:
        </p>
        <ul style='font-size:16px;'>
            <li>🟢 <b>Green boxes</b> = Vehicles (with type labels)</li>
            <li>🟡 <b>Yellow boxes</b> = License plates (with text)</li>
            <li>🔴 <b>Red boxes</b> = Helmet violations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        task_id = st.session_state.task_id
        download_url = f"{API_URL}/download/{task_id}"
        
        st.markdown(f"""
        <div style='text-align:center;'>
            <a href='{download_url}' target='_blank'>
                <button style='background-color:#238636; color:white; border:none; border-radius:8px; 
                               padding:15px 40px; font-size:20px; font-weight:bold; cursor:pointer;
                               box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
                    📥 Download Processed Video/Image
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Preview Section
    st.markdown("### 👁️ Preview")
    annotated_url = result.get("annotated_url", "")
    
    if result.get("type") == "image":
        try:
            image_res = requests.get(annotated_url)
            image = Image.open(BytesIO(image_res.content))
            st.image(image, caption="🖼️ Processed Image with Detection Boxes", use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Unable to load image preview: {e}")
    else:
        try:
            st.video(annotated_url)
        except Exception as e:
            st.warning(f"⚠️ Unable to load video preview: {e}")
    
    # Reset button
    st.markdown("---")
    if st.button("🔄 Process Another Video/Image"):
        st.session_state.clear()
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#8b949e; padding:20px;'>
    <p>🚦 <b>Traffic Surveillance System</b> | Powered by YOLO & Computer Vision</p>
    <p style='font-size:14px;'>Upload → Process → Download with Detection Blocks</p>
</div>
""", unsafe_allow_html=True)
