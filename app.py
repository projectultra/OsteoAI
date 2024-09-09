from flask import Flask, request, jsonify, send_from_directory
import tensorflow as tf
from flask_cors import CORS
from tensorflow.keras.applications.mobilenet_v3 import preprocess_input
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, static_folder='build', static_url_path='')
# app = Flask(__name__)

CORS(app)
# Load the pre-trained TensorFlow model
model = load_model('mobile_net.keras')

# Define image size expected by the model
IMG_SIZE = (512, 512)

CLASS_NAMES = {
    0: 'Healthy',
    1: 'Osteopenia',
    2: 'Osteoporosis',
}

def process_image(file_path):
    img = Image.open(file_path)
    img = img.resize(IMG_SIZE)
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array = preprocess_input(img_array)
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
        img_array = process_image(file_path)

        # Predict using the TensorFlow model
        predictions = model.predict(img_array)
        predicted_class_index = np.argmax(predictions, axis=1)[0]
        predicted_class_name = CLASS_NAMES.get(predicted_class_index, 'Unknown')
        probabilities = predictions[0].tolist()
        if use_ensemble:
            probabilities = ENSEMBLE_MATRIX.dot(probabilities)
        model_1_result = {
            'Predicted_Class': predicted_class_name,
            'Probabilities': probabilities
        }
        print(model_1_result)
        # Model 2 and Model 3 are not implemented, so return "Model not available"
        model_2_result = {
            'Predicted_Class': predicted_class_name,
            'Probabilities': probabilities
        }
        model_3_result = {
            'Predicted_Class': predicted_class_name,
            'Probabilities': probabilities
        }
        # Combine the results from all three models
        models_data = [model_1_result, model_2_result, model_3_result]
        if use_ensemble:
            # Calculate ensemble predictions
            ensemble_probabilities = ENSEMBLE_MATRIX.dot(predictions)
            ensemble_winning_class = CLASS_NAMES[np.argmax(np.mean(ensemble_probabilities, axis=0))]
            
            # Add ensemble results to the list
            models_data.append({
                'Predicted_Class': 'Ensemble',
                'Probabilities': np.mean(ensemble_probabilities, axis=0).tolist(),
                'Winning_Class': ensemble_winning_class
            })
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
    app.run(debug=True, host='0.0.0.0', port=5000)