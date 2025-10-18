# test_load_model.py
from tensorflow.keras.models import load_model
MODEL_PATH = "models/vgg_tuned.h5"
try:
    m = load_model(MODEL_PATH)
    print("Model loaded OK:", MODEL_PATH)
except Exception as e:
    print("Failed to load model:", e)
