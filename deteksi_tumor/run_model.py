import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Load model
try:
    model = load_model("brain_tumor_model.keras")
    print("Model loaded successfully!")
    
    classes = ['glioma', 'meningioma', 'notumor', 'pituitary']

    # Load image
    img_path = "Te-gl_1.jpg"
    print(f"Loading image: {img_path}")
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Predict
    pred = model.predict(img_array)
    predicted_class = classes[np.argmax(pred)]
    confidence = float(np.max(pred)) * 100

    print("====================================")
    print("Prediksi:", predicted_class)
    print("Confidence:", f"{confidence:.2f}%")
    print("====================================")

except Exception as e:
    print(f"An error occurred: {e}")
