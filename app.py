import base64
import io
import os
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "AI Image Filter Studio"
MODEL = "gpt-image-2"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎨",
    layout="wide",
)


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Create a .env file from .env.example and add your API key."
        )
    return OpenAI(api_key=api_key)


def build_edit_prompt(user_prompt: str) -> str:
    return f"""
Edit the provided input image according to the user's instructions below.

USER EDIT INSTRUCTIONS:
{user_prompt.strip()}

IMPORTANT EDITING RULES:
- Treat the uploaded image as the source image, not merely as inspiration.
- Preserve the identity, main subjects, composition, geometry, and important details unless the user explicitly asks to change them.
- Make only the requested visual changes and keep unrelated areas as faithful to the original as possible.
- Produce a polished, natural-looking result with coherent lighting, shadows, perspective, textures, and edges.
- Do not add extra objects, text, people, logos, or visual elements that the user did not request.
- If the request describes a visual style, apply that style while preserving the original subject and scene structure.
""".strip()


def generate_edit(uploaded_file, user_prompt: str, quality: str, size: str) -> bytes:
    suffix = Path(uploaded_file.name).suffix.lower() or ".png"
    data = uploaded_file.getvalue()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        temp_path = tmp.name

    try:
        client = get_client()
        with open(temp_path, "rb") as image_file:
            result = client.images.edit(
                model=MODEL,
                image=image_file,
                prompt=build_edit_prompt(user_prompt),
                quality=quality,
                size=size,
                output_format="png",
            )

        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("The image API returned no image data.")

        return base64.b64decode(result.data[0].b64_json)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def load_pil(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


st.title("🎨 AI Image Filter Studio")
st.caption("Upload an image + describe the change you want. The AI edits the image for you.")

with st.sidebar:
    st.header("Generation settings")
    quality = st.selectbox("Quality", ["low", "medium", "high"], index=1)
    size = st.selectbox(
        "Output size",
        ["auto", "1024x1024", "1536x1024", "1024x1536"],
        index=0,
        help="Use auto to let the model choose an appropriate output size.",
    )

    st.divider()
    st.subheader("Example prompts")
    examples = [
        "Give this photo a warm cinematic Instagram look with soft highlights and subtle film grain.",
        "Make the sky look like a dramatic golden-hour sunset while keeping the person unchanged.",
        "Turn this into a clean vintage film photograph with muted colors and natural skin tones.",
        "Blur the background strongly while keeping the main person sharp and natural.",
        "Make the image look like a premium fashion editorial with balanced contrast and soft studio lighting.",
    ]
    for example in examples:
        st.write(f"• {example}")

uploaded = st.file_uploader(
    "Upload your image",
    type=["png", "jpg", "jpeg", "webp"],
    help="Supported formats: PNG, JPG/JPEG, WEBP. Maximum upload size is controlled by Streamlit settings.",
)

prompt = st.text_area(
    "Describe what you want to change",
    height=130,
    placeholder=(
        "Example: Make the photo look cinematic and moody, with cooler shadows, warmer skin tones, "
        "slightly stronger contrast, and a subtle film grain. Keep the person and background composition unchanged."
    ),
)

if uploaded:
    input_image = Image.open(uploaded)
    st.subheader("Preview")
    st.image(input_image, caption=f"Input: {uploaded.name}", use_container_width=True)

    if prompt.strip():
        if st.button("✨ Apply AI Filter", type="primary", use_container_width=True):
            with st.spinner("Editing image with AI…"):
                try:
                    output_bytes = generate_edit(uploaded, prompt, quality, size)
                    output_image = load_pil(output_bytes)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = OUTPUT_DIR / f"edited_{timestamp}.png"
                    output_path.write_bytes(output_bytes)

                    st.session_state["output_bytes"] = output_bytes
                    st.session_state["output_path"] = str(output_path)
                    st.session_state["output_image"] = output_image
                except Exception as exc:
                    st.error(f"Image editing failed: {exc}")

if "output_image" in st.session_state:
    st.divider()
    st.subheader("Result")
    left, right = st.columns(2)
    with left:
        st.image(input_image, caption="Original", use_container_width=True)
    with right:
        st.image(st.session_state["output_image"], caption="AI-edited", use_container_width=True)

    st.download_button(
        "⬇️ Download edited image",
        data=st.session_state["output_bytes"],
        file_name="ai_filtered_image.png",
        mime="image/png",
        use_container_width=True,
    )

    st.info(f"Saved locally at: {st.session_state['output_path']}")
else:
    st.info("Upload an image, describe the change, and click **Apply AI Filter**.")
