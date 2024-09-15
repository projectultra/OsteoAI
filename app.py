from flask import Flask, request, jsonify, send_from_directory
import tensorflow as tf
from flask_cors import CORS
from tensorflow.keras.applications.mobilenet_v3 import preprocess_input as mobilenet_preprocess_input
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input as eff_net_preprocess_input
from tensorflow.keras.applications.vgg19 import preprocess_input as vgg_preprocess_input
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, static_folder='build', static_url_path='')
# app = Flask(__name__)

CORS(app)

# Load the pre-trained TensorFlow model
mobile_net_model = load_model('models/mobile_net.keras')
efficient_net_model = load_model('models/efficient_net.keras')
vgg_model = load_model('models/vgg.keras')

# Define image size expected by the model
IMG_SIZE = (512, 512)

CLASS_NAMES = {
    0: 'Healthy',
    1: 'Osteopenia',
    2: 'Osteoporosis',
}

def process_image(file_path, model_type):
    img = Image.open(file_path)
    img = img.resize(IMG_SIZE)
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

    if model_type == 'mobile_net':
        img_array = mobilenet_preprocess_input(img_array)
    elif model_type == 'efficient_net':
        img_array = eff_net_preprocess_input(img_array)
    elif model_type == 'vgg':
        img_array = vgg_preprocess_input(img_array) 
    return img_array

ENSEMBLE_MATRIX = np.full((3, 3), 0.33)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        print(filename)
        file_path = os.path.join('src/upload', filename)
        file.save(file_path)
        return jsonify({'file_path': file_path})

    return jsonify({'message': 'File upload failed'}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if 'file_path' not in data:
        return jsonify({'error': 'No file path provided'}), 400
    use_ensemble = data.get('useEnsemble', False)
    file_path = data['file_path']
    try:
        img_array_mobile_net = process_image(file_path, 'mobile_net')
        img_array_efficient_net = process_image(file_path, 'efficient_net')
        img_array_vgg = process_image(file_path, 'vgg')

        # Predict using the TensorFlow model
        # Get predictions from all three models
        predictions_1 = mobile_net_model.predict(img_array_mobile_net)
        predictions_2 = efficient_net_model.predict(img_array_efficient_net)
        predictions_3 = vgg_model.predict(img_array_vgg)

        # Get the predicted class and probabilities for each model
        predicted_class_index_1 = np.argmax(predictions_1, axis=1)[0]
        predicted_class_name_1 = CLASS_NAMES.get(predicted_class_index_1, 'Unknown')
        probabilities_1 = predictions_1[0].tolist()

        predicted_class_index_2 = np.argmax(predictions_2, axis=1)[0]
        predicted_class_name_2 = CLASS_NAMES.get(predicted_class_index_2, 'Unknown')
        probabilities_2 = predictions_2[0].tolist()

        predicted_class_index_3 = np.argmax(predictions_3, axis=1)[0]
        predicted_class_name_3 = CLASS_NAMES.get(predicted_class_index_3, 'Unknown')
        probabilities_3 = predictions_3[0].tolist()

        # Store the results for each model
        model_1_result = {
            'Predicted_Class': predicted_class_name_1,
            'Probabilities': probabilities_1
        }
        model_2_result = {
            'Predicted_Class': predicted_class_name_2,
            'Probabilities': probabilities_2
        }
        model_3_result = {
            'Predicted_Class': predicted_class_name_3,
            'Probabilities': probabilities_3
        }

        # Combine the results from all three models
        models_data = [model_1_result, model_2_result, model_3_result]

        if use_ensemble:
            # Calculate ensemble predictions
            ensemble_probabilities = np.dot(ENSEMBLE_MATRIX, [probabilities_1, probabilities_2, probabilities_3])
            ensemble_probabilities = np.mean([probabilities_1, probabilities_2, probabilities_3], axis=0)
            ensemble_winning_class = CLASS_NAMES[np.argmax(ensemble_probabilities)]

            # Add ensemble results to the list
            models_data.append({
            'Predicted_Class': 'Ensemble',
            'Probabilities': ensemble_probabilities.tolist(),
            'Winning_Class': ensemble_winning_class
            })
        else:
            # Calculate ensemble predictions
            ensemble_probabilities = np.mean([probabilities_1, probabilities_1, probabilities_1], axis=0)
            ensemble_winning_class = CLASS_NAMES[np.argmax(ensemble_probabilities)]

            # Add ensemble results to the list
            models_data.append({
            'Predicted_Class': 'Ensemble',
            'Probabilities': ensemble_probabilities.tolist(),
            'Winning_Class': ensemble_winning_class})

        print(models_data)
        return jsonify({'models': models_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve React app's static files
@app.route('/')
def serve_react_app():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files for any other route
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)