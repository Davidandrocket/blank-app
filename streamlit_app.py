import streamlit as st
from PIL import Image
import numpy as np
import random
import json
import io

WIDTH, HEIGHT = 16, 16

st.set_page_config(page_title="Perlin Noise Generator", layout="wide")
st.title("16x Perlin Noise Generator")

# --- Initialization ---
if 'palette' not in st.session_state:
    st.session_state.palette = ["#ffffff", "#bfbfbf", "#7f7f7f", "#3f3f3f", "#000000"]
if 'seed' not in st.session_state:
    st.session_state.seed = random.randint(0, 10000)

# --- Display Controls ---
st.subheader("Preview")
col_display, col_seed = st.columns([3, 1])

with col_seed:
    st.session_state.show_tiled = st.checkbox("Show Tiled (3x3)", value=st.session_state.get("show_tiled", False))
    seed_input = st.text_input("Seed", value=str(st.session_state.seed))
    if st.button("Random Seed"):
        st.session_state.seed = random.randint(0, 10000)
        st.rerun()
    try:
        st.session_state.seed = int(seed_input)
    except ValueError:
        pass

# --- Noise Settings ---
col1, col2 = st.columns(2)

with col1:
    st.header("Noise Settings")
    scale = st.slider("Scale", 1, 16, 1)
    grid_x = st.slider("Grid Size X", 2, 32, 5)
    grid_y = st.slider("Grid Size Y", 2, 32, 5)
    falloff_power = st.slider("Falloff Power", 0.2, 3.0, 1.0, 0.1)
    thresh_min = st.slider("Min Threshold", 0.0, 1.0, 0.0, 0.01)
    thresh_max = st.slider("Max Threshold", 0.0, 1.0, 1.0, 0.01)
    interp_mode = st.selectbox("Interpolation Mode", ["Linear", "Smoothstep"])

with col2:
    st.header("Color Palette")
    palette = st.session_state.palette.copy()
    reorder_index = None

    for i in range(len(palette)):
        cols = st.columns([3, 1, 1])
        palette[i] = cols[0].color_picker(f"Color {i+1}", palette[i], label_visibility="collapsed")

        if cols[1].button("↑", key=f"up_{i}") and i > 0:
            palette[i-1], palette[i] = palette[i], palette[i-1]
            st.session_state.palette = palette
            st.rerun()

        if cols[1].button("↓", key=f"down_{i}") and i < len(palette) - 1:
            palette[i], palette[i+1] = palette[i+1], palette[i]
            st.session_state.palette = palette
            st.rerun()

        if cols[2].button("✕", key=f"remove_{i}") and len(palette) > 1:
            palette.pop(i)
            st.session_state.palette = palette
            st.rerun()
            break

    if st.button("Add Color"):
        palette.append("#ffffff")
        st.session_state.palette = palette
        st.rerun()

    st.session_state.palette = palette

# --- Noise Generation ---
rng = np.random.default_rng(st.session_state.seed)
grid = rng.random((grid_y, grid_x))

noise = np.zeros((HEIGHT, WIDTH))
for y in range(HEIGHT):
    for x in range(WIDTH):
        fx = x / scale
        fy = y / scale
        cx = fx * grid_x / WIDTH
        cy = fy * grid_y / HEIGHT
        x0 = int(cx)
        y0 = int(cy)
        dx = cx - x0
        dy = cy - y0
        tl = grid[y0 % grid_y][x0 % grid_x]
        tr = grid[y0 % grid_y][(x0 + 1) % grid_x]
        bl = grid[(y0 + 1) % grid_y][x0 % grid_x]
        br = grid[(y0 + 1) % grid_y][(x0 + 1) % grid_x]
        if interp_mode == "Smoothstep":
            dx = dx * dx * (3 - 2 * dx)
            dy = dy * dy * (3 - 2 * dy)
        top = tl + (tr - tl) * dx
        bot = bl + (br - bl) * dx
        val = (top + (bot - top) * dy) ** falloff_power
        val = max(0.0, min(1.0, val))
        val = (val - thresh_min) / (thresh_max - thresh_min) if thresh_max > thresh_min else 0
        val = max(0.0, min(1.0, val))
        noise[y][x] = val

img = Image.new("RGB", (WIDTH, HEIGHT))
for y in range(HEIGHT):
    for x in range(WIDTH):
        val = noise[y][x]
        idx = min(int(val * len(palette)), len(palette) - 1)
        hex_code = palette[idx].lstrip('#')
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        img.putpixel((x, y), rgb)

if st.session_state.get("show_tiled"):
    tiled = Image.new("RGB", (WIDTH * 3, HEIGHT * 3))
    for ty in range(3):
        for tx in range(3):
            tiled.paste(img, (tx * WIDTH, ty * HEIGHT))
    preview = tiled.resize((WIDTH * 16 * 3, HEIGHT * 16 * 3), Image.NEAREST)
else:
    preview = img.resize((WIDTH * 16, HEIGHT * 16), Image.NEAREST)

with col_display:
    st.image(preview, caption="Generated Noise", use_container_width=False)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    st.download_button("Download PNG", data=buffer.getvalue(), file_name="perlin_noise.png", mime="image/png")
