from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os

class BurstPredictor:
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_data = []
        self.targets = []
        
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        
    def train(self, features, targets):
        """Train the ML model"""
        if len(features) < 10:
            return False
        
        X = np.array(features)
        y = np.array(targets)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        return True
    
    def predict(self, features):
        """Predict burst time for a process"""
        if not self.is_trained:
            return features[0][0]  # Return original burst time if not trained
        
        X_scaled = self.scaler.transform(features)
        prediction = self.model.predict(X_scaled)
        return max(prediction[0], 1)  # Ensure positive prediction
    
    def add_training_sample(self, features, actual_burst):
        """Add a training sample for online learning"""
        self.training_data.append(features.flatten())
        self.targets.append(actual_burst)
        
        # Keep only recent data
        max_samples = 1000
        if len(self.training_data) > max_samples:
            self.training_data = self.training_data[-max_samples:]
            self.targets = self.targets[-max_samples:]
    
    def save_model(self, path='data/models/burst_predictor.pkl'):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)
    
    def load_model(self, path='data/models/burst_predictor.pkl'):
        """Load trained model from disk"""
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = data['is_trained']
            return True
        return False