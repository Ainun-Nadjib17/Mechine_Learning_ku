import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

# buat arsitektur model dulu
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224,224,3),
    include_top=False,
    weights=None
)

x = base_model.output
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dense(128, activation='relu')(x)
output = tf.keras.layers.Dense(4, activation='softmax')(x)

model = tf.keras.Model(inputs=base_model.input, outputs=output)

# load weights
model.load_weights("coffee_model.h5")

class_names = ["Dark","Green","Light","Medium"]

def predict(img_path):

    img = image.load_img(img_path, target_size=(224,224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img/255.0

    pred = model.predict(img)

    idx = np.argmax(pred)
    conf = np.max(pred)*100

    return class_names[idx], conf