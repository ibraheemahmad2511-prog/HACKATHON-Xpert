# make_dummy_model.py
# Creates a tiny Keras model and saves it to models/vgg_tuned.h5 for testing the Flask app.
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten, Dense, InputLayer
import os

os.makedirs("models", exist_ok=True)

model = Sequential([
    InputLayer(input_shape=(224,224,3)),
    Flatten(),
    Dense(64, activation="relu"),
    Dense(2, activation="softmax")
])
model.compile(optimizer="adam", loss="categorical_crossentropy")
model.save("models/vgg_tuned.h5")
print("Saved dummy model to models/vgg_tuned.h5")
