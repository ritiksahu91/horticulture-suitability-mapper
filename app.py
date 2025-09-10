
import streamlit as st
import rasterio
import numpy as np
import tempfile
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import cv2
from compute_suitability import compute_final_suitability, align_raster_to_base

st.set_page_config(layout="wide", page_title="Horticultural Suitability Mapper", page_icon="🌾")

# --- CSS
st.markdown("""
<style>
.main {background-color: #f7fbff;}
h1, h2, h3 {color: #2471A3; font-family: 'Helvetica Neue', Arial, sans-serif;}
.stButton button, .stDownloadButton button {
    background-color: #2471A3; color: white; font-weight: bold; border-radius: 5px; transition: background 0.2s;}
.stButton button:hover, .stDownloadButton button:hover {background-color: #145A8A;}
.stRadio label {font-size: 16px;}
.stAlert {font-size: 16px;}
</style>
""", unsafe_allow_html=True)

st.title("🌾:rainbow[ Horticultural Suitability Mapper]")

# --- Init state
layer_names = [
    "Soiltype", "Slope", "water_distance", "Rainfall",
    "Road distance", "soil carbon composite", "Temperature"
]
if "uploaded_layers" not in st.session_state:
    st.session_state.uploaded_layers = []
if "raster_data" not in st.session_state:
    st.session_state.raster_data = {}
if "reclass_rules" not in st.session_state:
    st.session_state.reclass_rules = {}
if "weights" not in st.session_state:
    st.session_state.weights = {}
if "base_layer" not in st.session_state:
    st.session_state.base_layer = None
if "meta" not in st.session_state:
    st.session_state.meta = None

# --- Sidebar: Add Layers only
st.sidebar.header("Add Layers")
available_layers = [l for l in layer_names if l not in st.session_state.uploaded_layers]
for layer in available_layers:
    if st.sidebar.button(f"➕ Add {layer}", key=f"add_{layer}"):
        st.session_state.uploaded_layers.append(layer)

# base raster select shown only if layers exist
if st.session_state.uploaded_layers:
    st.sidebar.markdown("---")
    st.sidebar.header("Base Raster")
    st.session_state.base_layer = st.sidebar.selectbox(
        "Select base raster for alignment",
        st.session_state.uploaded_layers,
        index=0,
        key="base_layer_select"
    )
    if st.session_state.base_layer and st.session_state.base_layer in st.session_state.raster_data:
        base_data = st.session_state.raster_data[st.session_state.base_layer]
        st.session_state.meta = {
            "transform": base_data["transform"],
            "crs": base_data["crs"],
            "shape": base_data["array"].shape
        }
        st.sidebar.success(f"Current Base Raster: {st.session_state.base_layer}")
else:
    st.sidebar.info("Add layers to select base raster")

# --- Main Page: Show Upload & Edit for Each Layer
st.header("Layers: Edit rules, upload raster, preview")

if not st.session_state.uploaded_layers:
    st.info("Use the sidebar to add layers")
else:
    for layer in st.session_state.uploaded_layers:
        with st.expander(f"{layer} Settings", expanded=True):
            cols = st.columns([3, 2])
            with cols[0]:
                # Editable rule type
                rule_type = st.radio(
                    "Rule Type",
                    ["Value-Based (Range)", "Class-Based (Exact Match)"],
                    index=0 if st.session_state.reclass_rules.get(layer, {}).get("type", "") == "value" else 1,
                    key=f"type_{layer}"
                )
                rules = {}
                if rule_type == "Value-Based (Range)":
                    for cat in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
                        min_val = st.number_input(f"Min ({cat})", key=f"min_{layer}_{cat}", value=0.0)
                        max_val = st.number_input(f"Max ({cat})", key=f"max_{layer}_{cat}", value=1.0)
                        weight = st.number_input(f"Weight ({cat})", min_value=1, max_value=8, value=5, key=f"weight_{layer}_{cat}")
                        rules[cat] = [(min_val, max_val, weight)]
                else:
                    for cat in ["Highly Suitable", "Moderately Suitable", "Less Suitable"]:
                        values = st.text_input(f"Class Values ({cat}) (comma separated)", key=f"classval_{layer}_{cat}")
                        weight = st.number_input(f"Weight ({cat})", min_value=1, max_value=8, value=5, key=f"weight_class_{layer}_{cat}")
                        class_values = [int(v.strip()) for v in values.split(",") if v.strip().isdigit()]
                        rules[cat] = [(val, weight) for val in class_values]

                st.session_state.reclass_rules[layer] = {"type": rule_type.lower().replace(" ", ""), "rules": rules}

                st.session_state.weights[layer] = st.number_input(
                    f"Overall Weight for {layer}",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.weights.get(layer, 5),
                    key=f"overall_weight_{layer}"
                )

                # Raster uploader
                uploaded_file = st.file_uploader(f"Upload/Renew Raster (.tif) for {layer}", type=["tif"], key=f"uploader_{layer}")
                if uploaded_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name
                    with rasterio.open(tmp_path) as src:
                        arr = src.read(1).astype(np.float32)
                        transform = src.transform
                        crs = src.crs
                        st.session_state.raster_data[layer] = {
                            "array": arr,
                            "transform": transform,
                            "crs": crs
                        }
                    st.success(f"Uploaded raster for {layer}")
                    os.remove(tmp_path)

            # Preview and rule summary side by side
            with cols[1]:
                arr_data = st.session_state.raster_data.get(layer)
                if arr_data and "array" in arr_data:
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
                else:
                    st.warning("No raster uploaded for preview.")

                # Show rules summary below preview
                rule_info = st.session_state.reclass_rules.get(layer)
                if rule_info:
                    rules = rule_info.get("rules", {})
                    rule_type_val = rule_info.get("type")
                    md_table = "| Category | Rule Values | Weight |\n|---|---|---|\n"
                    for cat, rules_list in rules.items():
                        if not rules_list:
                            continue
                        rule_descriptions = []
                        for rule_item in rules_list:
                            if rule_type_val == "value":
                                min_val, max_val, w = rule_item
                                rule_descriptions.append(f"{min_val} to {max_val}")
                            else:
                                val, w = rule_item
                                rule_descriptions.append(f"Value {val}")
                        weight_val = rules_list[0][2] if rule_type_val == "value" else rules_list[0][1]
                        md_table += f"| {cat} | {', '.join(rule_descriptions)} | {weight_val} |\n"
                    overall_weight = st.session_state.weights.get(layer, 0)
                    md_table += f"| **Overall Weight** |*=*|**{overall_weight}** |\n"
                    st.markdown(md_table)
                else:
                    st.markdown("_No rules assigned yet._")

                if st.button(f"Delete Layer '{layer}'", key=f"delete_{layer}"):
                    st.session_state.uploaded_layers.remove(layer)
                    st.session_state.raster_data.pop(layer, None)
                    st.session_state.reclass_rules.pop(layer, None)
                    st.session_state.weights.pop(layer, None)
                    st.success(f"Deleted {layer}")

# --- Suitability Map Generation ---
required_layers = set(layer_names)
uploaded_layers = set(st.session_state.raster_data.keys())
base_layer_set = st.session_state.base_layer in st.session_state.raster_data if st.session_state.base_layer else False

if required_layers.issubset(uploaded_layers) and base_layer_set:
    if st.button("🧼 Generate Suitability Map"):
        with st.spinner("Generating suitability map..."):
            meta = st.session_state.meta
            base_transform = meta["transform"]
            base_crs = meta["crs"]
            base_shape = meta["shape"]
            aligned_arrays = {}
            for layer_name, data in st.session_state.raster_data.items():
                arr = data["array"]
                transform = data["transform"]
                crs = data["crs"]
                rule_info = st.session_state.reclass_rules[layer_name]
                rule_type = rule_info.get("type")
                aligned_arrays[layer_name] = align_raster_to_base(
                    arr, transform, crs, base_shape, base_transform, base_crs, rule_type
                )
            result = compute_final_suitability(
                aligned_arrays,
                st.session_state.weights,
                st.session_state.reclass_rules,
                st.session_state.meta
            )
        if result is not None:
            st.subheader("🗘️ Suitability Map (1=Low, 3=Medium, 6=High)")
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
        else:
            st.error("⚠️ Could not compute suitability map.")
else:
    missing = required_layers - uploaded_layers
    if missing:
        st.info(f"📌 Please upload raster(s) for: {', '.join(missing)}")
    elif not base_layer_set:
        st.warning("⚠️ Please select a base raster before generating suitability map.")
