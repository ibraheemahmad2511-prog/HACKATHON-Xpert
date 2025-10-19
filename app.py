# app.py
from flask import Flask, request, jsonify
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
import numpy as np
from google.genai import Client as LLMClient
from google.genai import types
import os
import re

app = Flask(__name__)
# ------------------- LLM Client Initialization -------------------
LLM_CLIENT = None
# Retrieve the secret API key from the terminal environment variable
# CHANGE VARIABLE NAME:
LLM_API_KEY = os.environ.get("GEMINI_API_KEY") 
# CHANGE SERVICE NAME:
LLM_MODEL = "gemini-2.5-flash" # <-- Use a fast, stable model for the demo

if LLM_API_KEY:
    try:
        # Initialize the client object
        LLM_CLIENT = LLMClient(api_key=LLM_API_KEY)
        print("LLM Client initialized successfully.")
    except Exception as e:
        print(f"WARNING: LLM Client failed to initialize: {e}")
# -----------------------------------------------------------------
@app.route("/v1/chat/completions", methods=['POST'])
def chat_completions():
    # --- 1. Get Input and Context ---
    try:
        data = request.get_json(force=True)
        
        # NOTE: This assumes Chatbox sends the prompt as the last message in 'messages' list
        # This will fail if your Streamlit app sends a different format, adjust if needed!
        user_message = data.get('messages')[-1]['content']
        
        # --- IMPORTANT: Determine the Role ---
        # The true way to get the role is from session state or the initial /diagnose request.
        # For this test, we rely on the system message being the first in the list
        role_message = data.get('messages')[0]['content']
        user_role = "doctor" if "doctor" in role_message.lower() else "student"
        
    except Exception as e:
        # Catch errors from missing data (e.g., during the initial Chatbox 'Check')
        return jsonify({"choices": [{"message": {"role": "assistant", "content": f"ERROR: Invalid Request Format. {e}"}}]}), 400

    # --- 2. Construct the Adaptive Prompt ---
    if user_role == "student":
        system_prompt = "You are Xpert, a friendly medical tutor AI. Explain findings simply and break down the diagnostic process."
        
    else:
        system_prompt = "You are Xpert, an expert radiologist AI assistant. Respond concisely using technical terminology."
        
    
    # Send the full system instruction with the user's latest message
    full_prompt_messages = [
    {
        "role": "user", # Using 'user' for system/instruction content in the first turn
        "parts": [{"text": system_prompt + user_message}] # Concatenate system instruction and user input into one Part
    }
]
    
    # --- 3. Call the LLM (Assuming LLM_CLIENT is globally initialized) ---
    try:
        full_prompt_text = system_prompt + " " + user_message
        contents_list = [types.Content(role="user", parts=[types.Part.from_text(full_prompt_text), types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')])]

        if LLM_CLIENT is None:
            raise RuntimeError("LLM Client not initialized. Check API Key.")
            
        # Call the Gemini API with the messages
        response = LLM_CLIENT.models.generate_content(
            model=LLM_MODEL,
            contents=contents_list
        )
        # Extract the response text
        ai_response_text = response.text # Gemini's response object structure
        
    except Exception as e:
        print(f"LLM API Call Failed: {e}")
        ai_response_text = f"LLM Integration Error: External AI failed to respond. Details: {e}"

    # --- 4. Format the Output for Chatbox (OpenAI Format) ---
    return jsonify({
        "id": "chatcmpl-final",
        "object": "chat.completion",
        "model": 'gemini-2.5-flash',
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": ai_response_text,
                },
                "finish_reason": "stop",
            }
        ],
    })


# ---------------------------
# Load pretrained classifier (Keras + VGG16)
# This matches the design of the uploaded Keras Flask app: it loads a .h5 with 2-class softmax:contentReference[oaicite:10]{index=10}.
# ---------------------------
MODEL_PATH = "model/vgg_tuned.h5"   # put your .h5 file here with this exact name
try:
    model = load_model(MODEL_PATH)
    print("Loaded model:", MODEL_PATH)
except Exception as e:
    model = None
    print(f"Warning: could not load model at {MODEL_PATH}: {e}")

# ---------------------------
# Role detection (very simple NLP)
# If you want to force the role from the client, pass ?role=student or ?role=doctor
# ---------------------------
def detect_role(text):
    if not text:
        return "student"
    t = text.lower()
    if re.search(r"\b(doctor|dr|radiologist|consultant|specialist)\b", t):
        return "doctor"
    if re.search(r"\b(student|learner|exam|study|college|uni)\b", t):
        return "student"
    return "student"

# ---------------------------
# Image preprocessing + prediction
# ---------------------------
def prepare(img_path):
    # determine target size from model input shape when available
    target_h, target_w = 224, 224
    try:
        mh, mw = get_model_input_size()
        if mh and mw:
            target_h, target_w = mh, mw
    except Exception:
        pass

    # force RGB mode when loading to avoid single-channel images
    try:
        img = image.load_img(img_path, target_size=(target_h, target_w), color_mode="rgb")
    except Exception:
        raise ValueError("Uploaded file is not a valid image or could not be opened")
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)  # same family API used in the reference app:contentReference[oaicite:11]{index=11}
    return x

def predict(img_path):
    if model is None:
        raise RuntimeError(f"Model not loaded. Expected model at: {MODEL_PATH}")
    x = prepare(img_path)
    preds = model.predict(x)             # shape [1, 2]
    pneu_prob = float(preds[0][1])       # assume index 1 = Pneumonia (as in the reference code):contentReference[oaicite:12]{index=12}
    label = "Pneumonia" if pneu_prob > 0.5 else "Normal"
    return label, pneu_prob


def mock_predict(img_path):
    """Deterministic mock prediction for testing: uses filename hash to alternate results.
    This helps test the UI without a trained model."""
    try:
        # use file size to vary the mock result deterministically
        size = os.path.getsize(img_path) if img_path and os.path.exists(img_path) else 0
        if size % 3 == 0:
            return "Pneumonia", 0.9
        elif size % 3 == 1:
            return "Pneumonia", 0.6
        else:
            return "Normal", 0.12
    except Exception:
        return "Normal", 0.5


def get_model_input_size():
    """Return (height, width) expected by the loaded model.
    Falls back to (224,224) if unavailable."""
    if model is None:
        return 224, 224
    try:
        # Prefer model.inputs[0].shape if available
        if hasattr(model, 'inputs') and getattr(model, 'inputs'):
            shp = model.inputs[0].shape
            # shp may be a TensorShape; convert to list
            try:
                dims = list(shp.as_list())
            except Exception:
                dims = list(shp)
        else:
            dims = list(model.input_shape)

        # Expect dims like [None, H, W, C] (channels-last) or [None, C, H, W]
        if len(dims) == 4:
            # channels-last when last dim is 1 or 3
            if dims[3] in (1, 3):
                h = dims[1] or 224
                w = dims[2] or 224
            else:
                # assume channels-first
                h = dims[2] or 224
                w = dims[3] or 224
            return int(h), int(w)
    except Exception:
        pass
    return 224, 224


# Health endpoint to report model load status
def is_model_loaded():
    return model is not None


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        model_loaded=is_model_loaded(),
        model_path=MODEL_PATH,
        message=("Model loaded" if is_model_loaded() else "Model not loaded")
    )

# ---------------------------
# Simple HTML form (optional) & JSON API
# ---------------------------
@app.route("/", methods=["GET"])
def index():
    return """
    <h3>Pneumonia Detector (VGG16-Keras)</h3>
    <form action="/analyze" method="post" enctype="multipart/form-data">
      <p><input type="file" name="file" accept="image/*" required></p>
      <p><input type="text" name="message" placeholder="e.g., I'm a student. What does this show?" style="width:320px;"></p>
      <p><button type="submit">Analyze</button></p>
      <p>Tip: add <code>?role=doctor</code> or <code>?role=student</code> to the URL to force role.</p>
    </form>
    """

@app.route("/analyze", methods=["POST"])
def analyze():
    # --- 1) read uploaded image ---
    if "file" not in request.files:
        return jsonify(error="Upload an image in form field 'file'"), 400
    f = request.files["file"]
    os.makedirs("uploads", exist_ok=True)
    save_path = os.path.join("uploads", f.filename)
    f.save(save_path)

    # --- 2) detect user role ---
    forced_role = request.args.get("role", "").strip().lower()
    message = request.form.get("message", "")
    role = forced_role if forced_role in {"student", "doctor"} else detect_role(message)

    # --- 3) choose prediction mode ---
    # mock can be forced via ?mock=1 or a form field 'mock'
    mock_q = request.args.get("mock", "0").strip()
    mock_form = request.form.get("mock", "0").strip()
    use_mock = mock_q == "1" or mock_form == "1"

    if model is None and not use_mock:
        return jsonify(error="Model not loaded on server. Use ?mock=1 to test without a model."), 503

    try:
        if use_mock:
            label, prob = mock_predict(save_path)
        else:
            # support debug to include raw preds
            debug = request.args.get("debug", "0") == "1"
            x = prepare(save_path)
            preds = model.predict(x)
            try:
                pneu_prob = float(preds[0][1])
            except Exception:
                pneu_prob = float(preds[0]) if preds.shape[-1] == 1 else 0.0
            label = "Pneumonia" if pneu_prob > 0.5 else "Normal"
            prob = pneu_prob
    except ValueError as ve:
        # image couldn't be read
        return jsonify(error=str(ve)), 400
    except Exception as e:
        return jsonify(error=f"Prediction failed: {e}"), 500

    # --- 4) craft role-based answer (simple & clear) ---
    if role == "student":
        if label == "Pneumonia":
            text = f"As a student: this likely shows pneumonia (confidence {prob:.2f}). Pneumonia often looks like white cloudy patches on the lungs."
        else:
            text = f"As a student: this looks normal (confidence {(1-prob):.2f}). Lungs appear relatively clear without consolidation."
    else:  # doctor
        if label == "Pneumonia":
            text = f"Pneumonia predicted (prob {prob*100:.1f}%). Correlate with clinical picture and consider further evaluation as indicated."
        else:
            text = f"No pneumonia predicted (prob {(1-prob)*100:.1f}%). If symptoms persist, correlate clinically."

    resp = dict(
        role=role,
        prediction=label,
        pneumonia_probability=round(prob, 3),
        message=text
    )
    if not use_mock and request.args.get("debug", "0") == "1":
        # attach raw prediction array if available
        try:
            resp["raw_preds"] = preds.tolist()
        except Exception:
            pass
    return jsonify(resp)

