# import streamlit as st
# import rasterio
# import numpy as np
# import tempfile
# import matplotlib.pyplot as plt
# import matplotlib.cm as cm
# import os
# import cv2
# from compute_suitability import compute_final_suitability
# from compute_suitability import align_raster_to_base


# # Modern custom CSS
# st.markdown(
#     """
#     <style>
#     .main {
#         background-color: #f7fbff;
#     }
#     h1, h2, h3 {
#         color: #2471A3;
#         font-family: 'Helvetica Neue', Arial, sans-serif;
#     }
#     .stButton button, .stDownloadButton button {
#         background-color: #2471A3;
#         color: white;
#         font-weight: bold;
#         border-radius: 5px;
#         transition: background 0.2s;
#     }
#     .stButton button:hover, .stDownloadButton button:hover {
#         background-color: #145A8A;
#     }
#     .stRadio label {
#         font-size: 16px;
#     }
#     .stAlert {
#         font-size: 16px;
#     }
#     </style>
#     """, unsafe_allow_html=True
# )

# st.set_page_config(layout="wide", page_title="Horticultural Suitability Mapper", page_icon="🌾")
# st.title("🌾:rainbow[ Horticultural Suitability Mapper]")


# # Session state initialization
# if "raster_data" not in st.session_state:
#     st.session_state.raster_data = {}
# if "uploaded_layers" not in st.session_state:
#     st.session_state.uploaded_layers = []
# if "meta" not in st.session_state:
#     st.session_state.meta = None
# if "reclass_rules" not in st.session_state:
#     st.session_state.reclass_rules = {}
# if "weights" not in st.session_state:
#     st.session_state.weights = {}

# # ---------- Sidebar Navigation ----------
# st.sidebar.markdown(
#     "<h2 style='font-size:2em; background: linear-gradient(90deg, #ff0000, #ff9900, #ffff00, #33cc33, #3399ff, #9900cc); \
#     -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:bold;'>Layer Management</h2>",
#     unsafe_allow_html=True
# )
# layer_names = ["Soiltype", "Slope", "water_distance", "Rainfall", "Road distance", "soil carbon composite", "Temperature"]
# available_layers = [l for l in layer_names if l not in st.session_state.uploaded_layers]

# selected_layer = st.sidebar.selectbox("Select Layer Type", available_layers)

# if selected_layer:
#     st.sidebar.markdown(f"### Define Rules for {selected_layer}")
#     rule_type = st.sidebar.radio("Select Rule Type", ["Value-Based (Range)", "Class-Based (Exact Match)"], key=f"type_{selected_layer}")
#     rules = {}
#     if rule_type == "Value-Based (Range)":
#         for category in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
#             st.sidebar.markdown(f"**{category}**")
#             min_val = st.sidebar.number_input(f"Min ({category})", key=f"min_{selected_layer}_{category}")
#             max_val = st.sidebar.number_input(f"Max ({category})", key=f"max_{selected_layer}_{category}")
#             weight = st.sidebar.number_input(f"Weight ({category})", min_value=1, max_value=100, value=5, key=f"weight_{selected_layer}_{category}")
#             rules[category] = [(min_val, max_val, weight)]
#         st.session_state.reclass_rules[selected_layer] = {
#             "type": "value",
#             "rules": rules
#         }
#     elif rule_type == "Class-Based (Exact Match)":
#         for category in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
#             st.sidebar.markdown(f"**{category}**")
#             values = st.sidebar.text_input(f"Class Values for {category} (comma-separated)", key=f"classval_{selected_layer}_{category}")
#             weight = st.sidebar.number_input(f"Weight for all values in {category}", min_value=1, max_value=100, value=5, key=f"weight_class_{selected_layer}_{category}")
#             class_values = [int(v.strip()) for v in values.split(",") if v.strip().isdigit()]
#             rules[category] = [(val, weight) for val in class_values]
#         st.session_state.reclass_rules[selected_layer] = {
#             "type": "class",
#             "rules": rules
#         }
#     weight = st.sidebar.number_input(f"⚖️ Overall Weight for {selected_layer}", min_value=1, max_value=100, value=5)
#     st.session_state.weights[selected_layer] = weight
#     uploaded_file = st.sidebar.file_uploader(f"📂 Browse and Upload Raster for {selected_layer}", type=["tif"], key=f"uploader_{selected_layer}")
#     upload_btn = st.sidebar.button("📤 Upload Layer", key=f"upload_btn_{selected_layer}")
#     if upload_btn:
#         if uploaded_file:
#             with st.spinner(f"Uploading {selected_layer}..."):
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
#                     tmp.write(uploaded_file.read())
#                     tmp_path = tmp.name
#                 with rasterio.open(tmp_path) as src:
#                     arr = src.read(1).astype(np.float32)
#                     transform=src.transform
#                     crs=src.crs
#                     st.session_state.raster_data[selected_layer] = {
#                         "array": arr,
#                         "transform": transform,
#                         "crs": crs
#                     }
#                     st.session_state.uploaded_layers.append(selected_layer)
#                     if not st.session_state.meta:
#                         st.session_state.meta = {
#                             "transform": transform,
#                             "crs": crs,
#                             "shape": arr.shape
#                         }
#                 st.sidebar.success(f"✅ {selected_layer} uploaded successfully!")
#                 os.remove(tmp_path)
#         else:
#             st.sidebar.warning("⚠️ Please upload a raster file before submitting.")

# # ---------- Main Page Layout ----------
# st.markdown("## Uploaded Layers & Previews")
# if st.session_state.uploaded_layers:
#     layers_to_delete = []
#     for layer in st.session_state.uploaded_layers:
#         col1, col2, col3 = st.columns([3, 1, 2])
#         with col1:
#             st.markdown(f"<span style='font-size:1.5em; font-weight:bold; color:#2471A3;'>{layer}</span>", unsafe_allow_html=True)
#             # Assigned Suitability Rules (moved from col3)
#             rule_info = st.session_state.reclass_rules.get(layer)
#             if rule_info:
#                 rules = rule_info.get("rules", {})
#                 rule_type = rule_info.get("type")
#                 md_table = "| Category | Rule Values | Weight |\n|---|---|---|\n"
#                 total_weight = 0
#                 for cat, rules_list in rules.items():
#                     if not rules_list:
#                         continue
#                     rule_descriptions = []
#                     for rule_item in rules_list:
#                         if rule_type == "value":
#                             min_val, max_val, w = rule_item
#                             rule_descriptions.append(f"{min_val} to {max_val}")
#                             total_weight += w
#                         else:  # class-based
#                             val, w = rule_item
#                             rule_descriptions.append(f"Value {val}")
#                     weight_val = rules_list[0][2] if rule_type == "value" else rules_list[0][1]
#                     md_table += f"| {cat} | {', '.join(rule_descriptions)} | {weight_val} |\n"
#                 overall_weight = st.session_state.weights.get(layer, 0)
#                 md_table += f"| **Overall Weight**  |*=*|**{overall_weight}** |\n"
#                 st.markdown(md_table)
#             else:
#                 st.markdown("_No rules assigned yet._")
#         with col2:
#             if st.button("Delete", key=f"delete_{layer}"):
#                 layers_to_delete.append(layer)
#         with col3:
#             # Fast raster preview: downsample and use st.image
#             arr_data = st.session_state.raster_data.get(layer)
#             if arr_data is not None and isinstance(arr_data, dict) and "array" in arr_data:
#                 arr = arr_data["array"]
#                 # Downsample to 128x128 for preview
#                 arr_small = arr
#                 if arr.shape[0] > 128 or arr.shape[1] > 128:
#                     try:
#                         arr_small = cv2.resize(arr, (128, 128), interpolation=cv2.INTER_AREA)
#                     except Exception:
#                         arr_small = arr[::arr.shape[0]//128 or 1, ::arr.shape[1]//128 or 1]
#                 # Normalize for display
#                 arr_disp = (arr_small - np.nanmin(arr_small)) / (np.nanmax(arr_small) - np.nanmin(arr_small) + 1e-8)
#                 arr_disp = np.nan_to_num(arr_disp)
#                 st.image(arr_disp, caption=f"Preview: {layer}", use_container_width=True, channels="GRAY")
#             elif arr_data is not None:
#                 st.warning(f"Layer '{layer}' is not a valid raster array and cannot be previewed.")
#     # Remove selected layers
#     for layer in layers_to_delete:
#         st.session_state.uploaded_layers.remove(layer)
#         st.session_state.raster_data.pop(layer, None)
#         st.session_state.reclass_rules.pop(layer, None)
#         st.session_state.weights.pop(layer, None)
#         st.success(f"🗑️ Deleted {layer}")

# required_layers = set(layer_names)
# uploaded_layers = set(st.session_state.raster_data.keys())

# if required_layers.issubset(uploaded_layers):
#     if st.button("🧼 Generate Suitability Map"):
#         with st.spinner("Generating suitability map..."):
#             base_transform = st.session_state.meta["transform"]
#             base_crs = st.session_state.meta["crs"]
#             base_shape = st.session_state.meta["shape"]

#             aligned_arrays = {}
#             for layer_name, data in st.session_state.raster_data.items():
#                 arr = data["array"]
#                 transform = data["transform"]
#                 crs = data["crs"]
#                 rule_info = st.session_state.reclass_rules[layer_name]
#                 rule_type = rule_info.get("type")
#                 aligned = align_raster_to_base(arr, transform, crs, base_shape, base_transform, base_crs, rule_type)
#                 aligned_arrays[layer_name] = aligned


#             result = compute_final_suitability(
#                 aligned_arrays,
#                 st.session_state.weights,
#                 st.session_state.reclass_rules,
#                 st.session_state.meta
#             )
#         if result is not None:
#             st.subheader("🗘️ Suitability Map (1 = Low, 2 = Medium, 3 = High)")
#             cmap = cm.get_cmap("viridis", 3)
#             fig, ax = plt.subplots()
#             im = ax.imshow(result, cmap=cmap, vmin=1.7, vmax=6.24)
#             plt.colorbar(im, ax=ax, ticks=[1, 2, 3], label="Suitability Level")
#             st.pyplot(fig)
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_tif:
#                 height, width = result.shape
#                 transform = st.session_state.meta["transform"]
#                 crs = st.session_state.meta["crs"]
#                 profile = {
#                     'driver': 'GTiff',
#                     'height': height,
#                     'width': width,
#                     'count': 1,
#                     'dtype': rasterio.float32,
#                     'crs': crs,
#                     'transform': transform
#                 }
#                 with rasterio.open(tmp_tif.name, 'w', **profile) as dst:
#                     dst.write(result.astype(np.float16), 1)
#                 with open(tmp_tif.name, 'rb') as f:
#                     raster_bytes = f.read()
#                 st.download_button(
#                     label="📅 Download Suitability Map (.tif)",
#                     data=raster_bytes,
#                     file_name="suitability_map.tif",
#                     mime="image/tiff"
#                 )
#                 # os.remove(tmp_tif.name)
#         else:
#             st.error("⚠️ Could not compute suitability map.")
# else:
#     missing = required_layers - uploaded_layers
#     st.info(f"📌 Please upload raster(s) for: {', '.join(missing)}")
import streamlit as st
import rasterio
import numpy as np
import tempfile
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import cv2
from compute_suitability import compute_final_suitability
from compute_suitability import align_raster_to_base


# ---------------- Custom CSS ----------------
st.set_page_config(layout="wide", page_title="Horticultural Suitability Mapper", page_icon="🌾")
st.markdown(
    """
    <style>
    .main {
        background-color: #f7fbff;
    }
    h1, h2, h3 {
        color: #2471A3;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .stButton button, .stDownloadButton button {
        background-color: #2471A3;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        transition: background 0.2s;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        background-color: #145A8A;
    }
    .stRadio label {
        font-size: 16px;
    }
    .stAlert {
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌾:rainbow[ Horticultural Suitability Mapper]")

# ---------------- Session State Initialization ----------------
if "raster_data" not in st.session_state:
    st.session_state.raster_data = {}
if "uploaded_layers" not in st.session_state:
    st.session_state.uploaded_layers = []
if "meta" not in st.session_state:
    st.session_state.meta = None
if "reclass_rules" not in st.session_state:
    st.session_state.reclass_rules = {}
if "weights" not in st.session_state:
    st.session_state.weights = {}
if "base_layer" not in st.session_state:
    st.session_state.base_layer = None

# ---------------- Sidebar Layer Upload ----------------
st.sidebar.markdown(
    "<h2 style='font-size:2em; background: linear-gradient(90deg, #ff0000, #ff9900, #ffff00, #33cc33, #3399ff, #9900cc); \
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:bold;'>Layer Management</h2>",
    unsafe_allow_html=True
)
layer_names = ["Soiltype", "Slope", "water_distance", "Rainfall", "Road distance", "soil carbon composite", "Temperature"]
available_layers = [l for l in layer_names if l not in st.session_state.uploaded_layers]

selected_layer = st.sidebar.selectbox("Select Layer Type", available_layers)

if selected_layer:
    st.sidebar.markdown(f"### Define Rules for {selected_layer}")
    rule_type = st.sidebar.radio("Select Rule Type", ["Value-Based (Range)", "Class-Based (Exact Match)"], key=f"type_{selected_layer}")
    rules = {}
    if rule_type == "Value-Based (Range)":
        for category in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
            st.sidebar.markdown(f"**{category}**")
            min_val = st.sidebar.number_input(f"Min ({category})", key=f"min_{selected_layer}_{category}")
            max_val = st.sidebar.number_input(f"Max ({category})", key=f"max_{selected_layer}_{category}")
            weight = st.sidebar.number_input(f"Weight ({category})", min_value=1, max_value=100, value=5, key=f"weight_{selected_layer}_{category}")
            rules[category] = [(min_val, max_val, weight)]
        st.session_state.reclass_rules[selected_layer] = {"type": "value", "rules": rules}

    elif rule_type == "Class-Based (Exact Match)":
        for category in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
            st.sidebar.markdown(f"**{category}**")
            values = st.sidebar.text_input(f"Class Values for {category} (comma-separated)", key=f"classval_{selected_layer}_{category}")
            weight = st.sidebar.number_input(f"Weight for all values in {category}", min_value=1, max_value=100, value=5, key=f"weight_class_{selected_layer}_{category}")
            class_values = [int(v.strip()) for v in values.split(",") if v.strip().isdigit()]
            rules[category] = [(val, weight) for val in class_values]
        st.session_state.reclass_rules[selected_layer] = {"type": "class", "rules": rules}

    weight = st.sidebar.number_input(f"⚖️ Overall Weight for {selected_layer}", min_value=1, max_value=100, value=5)
    st.session_state.weights[selected_layer] = weight

    uploaded_file = st.sidebar.file_uploader(f"📂 Browse and Upload Raster for {selected_layer}", type=["tif"], key=f"uploader_{selected_layer}")
    upload_btn = st.sidebar.button("📤 Upload Layer", key=f"upload_btn_{selected_layer}")

    if upload_btn:
        if uploaded_file:
            with st.spinner(f"Uploading {selected_layer}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                with rasterio.open(tmp_path) as src:
                    arr = src.read(1).astype(np.float32)
                    transform = src.transform
                    crs = src.crs
                    st.session_state.raster_data[selected_layer] = {
                        "array": arr,
                        "transform": transform,
                        "crs": crs
                    }
                    st.session_state.uploaded_layers.append(selected_layer)
                st.sidebar.success(f"✅ {selected_layer} uploaded successfully!")
                os.remove(tmp_path)
        else:
            st.sidebar.warning("⚠️ Please upload a raster file before submitting.")

# ---------------- Base Raster Selection ----------------
if st.session_state.uploaded_layers:
    st.sidebar.markdown("### 📌 Select Base Raster for Alignment")
    st.session_state.base_layer = st.sidebar.selectbox(
        "Choose base raster:",
        st.session_state.uploaded_layers,
        index=0,
        key="base_layer_choice"
    )
    if st.session_state.base_layer:
        base_data = st.session_state.raster_data[st.session_state.base_layer]
        st.session_state.meta = {
            "transform": base_data["transform"],
            "crs": base_data["crs"],
            "shape": base_data["array"].shape
        }
        st.sidebar.success(f"✅ Current Base Raster: {st.session_state.base_layer}")

# ---------------- Main Page: Uploaded Layers & Previews ----------------
st.markdown("## Uploaded Layers & Previews")
if st.session_state.uploaded_layers:
    layers_to_delete = []
    for layer in st.session_state.uploaded_layers:
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.markdown(f"<span style='font-size:1.5em; font-weight:bold; color:#2471A3;'>{layer}</span>", unsafe_allow_html=True)
            rule_info = st.session_state.reclass_rules.get(layer)
            if rule_info:
                rules = rule_info.get("rules", {})
                rule_type = rule_info.get("type")
                md_table = "| Category | Rule Values | Weight |\n|---|---|---|\n"
                for cat, rules_list in rules.items():
                    if not rules_list:
                        continue
                    rule_descriptions = []
                    for rule_item in rules_list:
                        if rule_type == "value":
                            min_val, max_val, w = rule_item
                            rule_descriptions.append(f"{min_val} to {max_val}")
                        else:
                            val, w = rule_item
                            rule_descriptions.append(f"Value {val}")
                    weight_val = rules_list[0][2] if rule_type == "value" else rules_list[0][1]
                    md_table += f"| {cat} | {', '.join(rule_descriptions)} | {weight_val} |\n"
                overall_weight = st.session_state.weights.get(layer, 0)
                md_table += f"| **Overall Weight**  |*=*|**{overall_weight}** |\n"
                st.markdown(md_table)
            else:
                st.markdown("_No rules assigned yet._")
        with col2:
            if st.button("Delete", key=f"delete_{layer}"):
                layers_to_delete.append(layer)
        with col3:
            arr_data = st.session_state.raster_data.get(layer)
            if arr_data is not None and isinstance(arr_data, dict) and "array" in arr_data:
                arr = arr_data["array"]
                arr_small = arr
                if arr.shape[0] > 128 or arr.shape[1] > 128:
                    try:
                        arr_small = cv2.resize(arr, (128, 128), interpolation=cv2.INTER_AREA)
                    except Exception:
                        arr_small = arr[::arr.shape[0]//128 or 1, ::arr.shape[1]//128 or 1]
                arr_disp = (arr_small - np.nanmin(arr_small)) / (np.nanmax(arr_small) - np.nanmin(arr_small) + 1e-8)
                arr_disp = np.nan_to_num(arr_disp)
                st.image(arr_disp, caption=f"Preview: {layer}", use_container_width=True, channels="GRAY")
            elif arr_data is not None:
                st.warning(f"Layer '{layer}' is not a valid raster array and cannot be previewed.")
    for layer in layers_to_delete:
        st.session_state.uploaded_layers.remove(layer)
        st.session_state.raster_data.pop(layer, None)
        st.session_state.reclass_rules.pop(layer, None)
        st.session_state.weights.pop(layer, None)
        st.success(f"🗑️ Deleted {layer}")

# ---------------- Suitability Map Generation ----------------
required_layers = set(layer_names)
uploaded_layers = set(st.session_state.raster_data.keys())

if required_layers.issubset(uploaded_layers) and st.session_state.base_layer:
    if st.button("🧼 Generate Suitability Map"):
        with st.spinner("Generating suitability map..."):
            base_transform = st.session_state.meta["transform"]
            base_crs = st.session_state.meta["crs"]
            base_shape = st.session_state.meta["shape"]

            aligned_arrays = {}
            for layer_name, data in st.session_state.raster_data.items():
                arr = data["array"]
                transform = data["transform"]
                crs = data["crs"]
                rule_info = st.session_state.reclass_rules[layer_name]
                rule_type = rule_info.get("type")
                aligned = align_raster_to_base(arr, transform, crs, base_shape, base_transform, base_crs, rule_type)
                aligned_arrays[layer_name] = aligned

            result = compute_final_suitability(
                aligned_arrays,
                st.session_state.weights,
                st.session_state.reclass_rules,
                st.session_state.meta
            )
        if result is not None:
            st.subheader("🗘️ Suitability Map (1 = Low, 3 = Medium, 6 = High)")
            cmap = cm.get_cmap("viridis", 3)
            fig, ax = plt.subplots()
            im = ax.imshow(result, cmap=cmap, vmin=1, vmax=7)
            plt.colorbar(im, ax=ax, ticks=[1, 3, 7], label="Suitability Level")
            st.pyplot(fig)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_tif:
                height, width = result.shape
                transform = st.session_state.meta["transform"]
                crs = st.session_state.meta["crs"]
                profile = {
                    'driver': 'GTiff',
                    'height': height,
                    'width': width,
                    'count': 1,
                    'dtype': rasterio.float32,
                    'crs': crs,
                    'transform': transform
                }
                with rasterio.open(tmp_tif.name, 'w', **profile) as dst:
                    dst.write(result.astype(np.float32), 1)
                with open(tmp_tif.name, 'rb') as f:
                    raster_bytes = f.read()
                st.download_button(
                    label="📅 Download Suitability Map (.tif)",
                    data=raster_bytes,
                    file_name="suitability_map.tif",
                    mime="image/tiff"
                )
                # os.remove(tmp_tif.name)
        else:
            st.error("⚠️ Could not compute suitability map.")
else:
    missing = required_layers - uploaded_layers
    if missing:
        st.info(f"📌 Please upload raster(s) for: {', '.join(missing)}")
    elif not st.session_state.base_layer:
        st.warning("⚠️ Please select a base raster before generating suitability map.")
