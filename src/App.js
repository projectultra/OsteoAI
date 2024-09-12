import React, { useState } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Spinner,Form, Button, Table  } from 'react-bootstrap';

function App() {
  const [file, setFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState('');
  const [message, setMessage] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useEnsemble, setUseEnsemble] = useState(false);
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreviewUrl(reader.result);
    };
    reader.readAsDataURL(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setMessage('Please select a file first.');
      return;
    }

    setLoading(true);  // Start loading spinner
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
      const uploadResponse = await axios.post('https://osteoai-hsbgbsepgxfzdgf5.eastus-01.azurewebsites.net/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const filePath = uploadResponse.data.file_path;
      
      const predictResponse = await axios.post('https://osteoai-hsbgbsepgxfzdgf5.eastus-01.azurewebsites.net/predict', { file_path: filePath });
      const modelsData = predictResponse.data.models;
      
      const formattedPredictions = modelsData.map((model, index) => {
        const probabilities = Array.isArray(model.Probabilities) ? model.Probabilities : [];
        const predictedClass = model.Predicted_Class || 'Model not available';
        
        return {
          model: `Model ${index + 1}`,
          predictedClass: predictedClass,
          probabilities: probabilities,
          winningClass: predictedClass !== 'Model not available' ? CLASS_NAMES[probabilities.indexOf(Math.max(...probabilities))] : 'N/A'
        };
      });

      setPredictions(formattedPredictions);
      setMessage('Prediction received');
      
    } catch (error) {
      console.error('Error:', error);
      setMessage('Failed to upload and predict');
    } finally {
      setLoading(false);  // Stop loading spinner
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Upload an Image for Prediction</h1>
      
      <Form onSubmit={handleSubmit} className="rounded p-4 shadow-sm bg-light">
        <div className="form-group">
          <input type="file" className="form-control-file mb-3 rounded" onChange={handleFileChange} />
        </div>
        {imagePreviewUrl && (
        <div className="text-center mt-4">
          <h2>Image Preview:</h2>
          <img src={imagePreviewUrl} alt="Uploaded" className="img-thumbnail rounded" style={{ maxWidth: '100%', height: 'auto' }} />
        </div>
      )}
        <Form.Group controlId="formUseEnsemble" className="d-flex align-items-center">
          <Form.Check
            type="checkbox"
            label="Use Evolutionary Ensemble"
            checked={useEnsemble}
            onChange={(e) => setUseEnsemble(e.target.checked)}
          />
          <Button type="submit" className="ml-auto btn btn-primary rounded-pill">
            {loading ? <Spinner animation="border" size="sm" /> : 'Submit'}
          </Button>
        </Form.Group>
      </Form>

      

      {message && <p className="text-center mt-3">{message}</p>}

      {predictions.length > 0 && (
        <div className="mt-5">
          <h2>Predictions:</h2>
          <table className="table table-bordered table-hover mt-3">
            <thead className="thead-light">
              <tr>
                <th>Model</th>
                <th>Probabilities</th>
                <th>Winning Class</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((prediction, index) => (
                <tr key={index}>
                  <td>{prediction.model}</td>
                  <td>
                    <ul className="list-unstyled">
                      <li><strong>Normal:</strong> {prediction.probabilities[0]?.toFixed(2) || 'N/A'}</li>
                      <li><strong>Osteopenia:</strong> {prediction.probabilities[1]?.toFixed(2) || 'N/A'}</li>
                      <li><strong>Osteoporosis:</strong> {prediction.probabilities[2]?.toFixed(2) || 'N/A'}</li>
                    </ul>
                  </td>
                  <td>{prediction.winningClass}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {useEnsemble && predictions.find(pred => pred.model === 'Ensemble') && (
            <div className="mt-4">
              <h2>Ensemble Weights:</h2>
              <Table bordered>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Predicted Class</th>
                    <th>Probabilities</th>
                    <th>Winning Class</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.filter(pred => pred.model === 'Ensemble').map((ensemble, index) => (
                    <tr key={index}>
                      <td>{ensemble.model}</td>
                      <td>{ensemble.predictedClass}</td>
                      <td>{ensemble.probabilities}</td>
                      <td>{ensemble.winningClass}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </div>
    
      )}
    </div>
  );
}

const CLASS_NAMES = ['Normal', 'Osteopenia', 'Osteoporosis'];
export default App;
