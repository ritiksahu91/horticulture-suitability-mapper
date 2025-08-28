# import numpy as np
# from reclass_rules import reclass1_rules, weights
# from skimage.transform import resize
# import gc

# def reclassify(array, rules):
#     """Handle both range-based rules (list of tuples) and categorical (dict)."""
#     reclassified = np.zeros_like(array, dtype=np.uint8)
    
#     if isinstance(rules, dict):
#         for val, new_val in rules.items():
#             reclassified[array == val] = new_val
#     else:
#         for lower, upper, value in rules:
#             reclassified[(array >= lower) & (array < upper)] = value

#     return reclassified.astype(np.float16)

# def compute_final_suitability(layer_arrays):
#     # Step 1: Choose smallest layer as base
#     base_shape = min((arr.shape for arr in layer_arrays.values()), key=lambda s: s[0]*s[1])
#     print(f"✅ Using base shape: {base_shape} for resizing")

#     weighted_sum = np.zeros(base_shape, dtype=np.float16)
#     total_weight = 0

#     for layer_name, array in layer_arrays.items():
#         if layer_name not in reclass1_rules:
#             continue

#         print(f"🔍 Processing layer: {layer_name} | Original shape: {array.shape}")
#         rules = reclass1_rules[layer_name]
#         weight = weights.get(layer_name, 0)

#         # Resize if needed
#         if array.shape != base_shape:
#             print(f"⚠️ Resizing layer: {layer_name} from {array.shape} to {base_shape}")
#             resized_array = resize(array, base_shape, order=0, preserve_range=True, anti_aliasing=False).astype(array.dtype)
#         else:
#             resized_array = array

#         # Reclassify
#         reclassed = reclassify(resized_array, rules)
#         weighted_sum += reclassed * weight
#         total_weight += weight

#         # Free memory
#         del resized_array
#         del reclassed
#         gc.collect()

#     if total_weight == 0:
#         return None

#     final_score = weighted_sum / total_weight

#     # Convert to final categories (1 = Low, 2 = Medium, 3 = High)
#     suitability_map = np.zeros_like(final_score, dtype=np.uint8)
#     suitability_map[final_score < 3] = 1
#     suitability_map[(final_score >= 3) & (final_score < 5)] = 2
#     suitability_map[final_score >= 5] = 3

#     del weighted_sum
#     del final_score
#     gc.collect()

#     print("✅ Suitability map generated successfully.")
#     return suitability_map

# import numpy as np
# from skimage.transform import resize
# import gc

# def reclassify(array, rule_type, rules):
#     """Reclassify array based on rule type (value or class) and category-wise weights."""
#     reclassified = np.zeros_like(array, dtype=np.float16)
    
#     for category, entries in rules.items():
#         for rule in entries:
#             if rule_type == "value":
#                 min_val, max_val, weight = rule
#                 mask = (array >= min_val) & (array <= max_val)
#             elif rule_type == "class":
#                 val, weight = rule
#                 mask = array == val
#             else:
#                 continue
#             reclassified[mask] = weight
#     return reclassified

# def compute_final_suitability(layer_arrays, weights, reclass_rules, meta):
#     # Step 1: Select base shape
#     base_shape = min((arr.shape for arr in layer_arrays.values()), key=lambda s: s[0]*s[1])
#     print(f"✅ Base shape selected: {base_shape}")

#     weighted_sum = np.zeros(base_shape, dtype=np.float16)
#     total_weight = 0

#     for layer_name, array in layer_arrays.items():
#         if layer_name not in reclass_rules:
#             continue

#         rule_info = reclass_rules[layer_name]
#         rule_type = rule_info.get("type")
#         rules = rule_info.get("rules")

#         if rules is None:
#             continue

#         weight = weights.get(layer_name, 0)
#         if weight == 0:
#             continue

#         print(f"🔍 Reclassifying {layer_name} (type: {rule_type})")

#         # Resize to base shape if needed
#         if array.shape != base_shape:
#             print(f"⚠️ Resizing {layer_name} from {array.shape} to {base_shape}")
#             resized_array = resize(array, base_shape, order=0, preserve_range=True, anti_aliasing=False).astype(array.dtype)
#         else:
#             resized_array = array

#         reclassed = reclassify(resized_array, rule_type, rules)

#         # Combine into weighted sum
#         weighted_sum += reclassed * weight
#         total_weight += weight

#         del resized_array
#         del reclassed
#         gc.collect()

#     if total_weight == 0:
#         print("❌ Total weight is zero. Check rule/weight definitions.")
#         return None

#     final_score = weighted_sum / total_weight

#     # # Generate suitability map
#     # suitability_map = np.zeros_like(final_score, dtype=np.uint8)
#     # suitability_map[final_score < 3] = 1   # Low
#     # suitability_map[(final_score >= 3) & (final_score < 5)] = 2  # Medium
#     # suitability_map[final_score >= 5] = 3  # High

#     print("✅ Suitability map created.")
#     del weighted_sum
#     # del final_score
#     gc.collect()

#     # return suitability_map
#     return final_score


import numpy as np
from skimage.transform import resize
import gc
from collections import Counter
from rasterio.warp import reproject, Resampling

def align_raster_to_base(src_arr, src_transform, src_crs, base_shape, base_transform, base_crs, rule_type):
    aligned = np.zeros(base_shape, dtype=src_arr.dtype)
    resampling_method = Resampling.nearest
    reproject(
        source=src_arr,
        destination=aligned,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=base_transform,
        dst_crs=base_crs,
        resampling=resampling_method,
        num_threads=2
    )
    return aligned


def reclassify(array, rule_type, rules):
    """Reclassify array based on rule type (value or class) and category-wise weights."""
    reclassified = np.zeros_like(array, dtype=np.float16)
    
    for category, entries in rules.items():
        for rule in entries:
            if rule_type == "value":
                min_val, max_val, weight = rule
                mask = (array >= min_val) & (array <= max_val)
            elif rule_type == "class":
                val, weight = rule
                mask = array == val
            else:
                continue
            reclassified[mask] = weight
    return reclassified

def resize_layer(array, base_shape, rule_type):
    """Resize array to base_shape using appropriate interpolation."""
    if array.shape == base_shape:
        return array

    if rule_type == "class":
        order = 0   # nearest neighbor
        anti_alias = False
    elif rule_type == "value":
        order = 1   # bilinear interpolation
        anti_alias = True
    else:
        order = 0
        anti_alias = False

    print(f"⚠️ Resizing ({rule_type}) from {array.shape} → {base_shape} using order={order}")
    return resize(
        array,
        base_shape,
        order=order,
        preserve_range=True,
        anti_aliasing=anti_alias
    ).astype(array.dtype)

def compute_final_suitability(layer_arrays, weights, reclass_rules, meta):
    # Step 1: Select base shape = most frequent shape (mode), or minimum shape if no common shape
    shapes = [arr.shape for arr in layer_arrays.values()]
    shape_counts = Counter(shapes)
    if shape_counts.most_common(1)[0][1] == 1:
        # No common shape, select minimum shape
        base_shape = min(shapes, key=lambda s: s[0]*s[1])
        print(f"⚠️ No common shape found. Using minimum shape: {base_shape}")
    else:
        base_shape = shape_counts.most_common(1)[0][0]
        print(f"✅ Base shape selected (most frequent): {base_shape} (appears {shape_counts[base_shape]} times)")

    weighted_sum = np.zeros(base_shape, dtype=np.float32)
    total_weight = 0

    for layer_name, array in layer_arrays.items():
        if layer_name not in reclass_rules:
            continue

        rule_info = reclass_rules[layer_name]
        rule_type = rule_info.get("type")
        rules = rule_info.get("rules")

        if rules is None:
            continue

        weight = weights.get(layer_name, 0)
        if weight == 0:
            continue

        print(f"🔍 Reclassifying {layer_name} (type: {rule_type})")

        # Resize using rule_type-specific interpolation
        resized_array = resize_layer(array, base_shape, rule_type)

        # Reclassify
        reclassed = reclassify(resized_array, rule_type, rules)

        # Combine into weighted sum
        weighted_sum += reclassed * weight
        total_weight += weight

        del resized_array
        del reclassed
        gc.collect()

    if total_weight == 0:
        print("❌ Total weight is zero. Check rule/weight definitions.")
        return None

    final_score = weighted_sum / total_weight

    print("✅ Suitability map created.")
    del weighted_sum
    gc.collect()

    return final_score
