import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from typing import List, Dict
import joblib
import os

class LoadPredictor:
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=50,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_data = []
        self.targets = []
        
    def extract_load_features(self, core_history: List[Dict]) -> np.ndarray:
        """Extract features from core load history"""
        if not core_history:
            return np.zeros(10)
        
        utilizations = [h['utilization'] for h in core_history[-20:]]
        temperatures = [h.get('temperature', 40) for h in core_history[-20:]]
        
        features = [
            np.mean(utilizations),           # Average utilization
            np.std(utilizations),             # Utilization variance
            np.max(utilizations),             # Peak utilization
            np.min(utilizations),             # Minimum utilization
            utilizations[-1] if utilizations else 0,  # Current utilization
            utilizations[-2] if len(utilizations) > 1 else 0,  # Previous utilization
            np.mean(temperatures),            # Average temperature
            len([u for u in utilizations if u > 0.7]),  # Time in overload
            len([u for u in utilizations if u < 0.2]),  # Time in underload
            np.gradient(utilizations)[-1] if len(utilizations) > 1 else 0  # Trend
        ]
        
        return np.array(features)
    
    def predict_future_load(self, core_history: List[Dict], horizon: int = 5) -> List[float]:
        """Predict future load for next N time steps"""
        if not self.is_trained or len(core_history) < 10:
            # Return simple moving average if not trained
            if len(core_history) >= 3:
                recent_loads = [h['utilization'] for h in core_history[-3:]]
                return [np.mean(recent_loads)] * horizon
            return [0.5] * horizon
        
        features = self.extract_load_features(core_history)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        predictions = []
        current_load = core_history[-1]['utilization'] if core_history else 0.5
        
        for i in range(horizon):
            pred = self.model.predict(features_scaled)[0]
            # Add some noise and trend
            pred = pred + (i * 0.02)  # Simple trend
            pred = max(0, min(1, pred))  # Clamp between 0 and 1
            predictions.append(pred)
            
            # Update features for next prediction (simplified)
            features_scaled = features_scaled * 0.9 + pred * 0.1
        
        return predictions
    
    def train(self, features_list: List[np.ndarray], targets: List[float]):
        """Train the load prediction model"""
        if len(features_list) < 20:
            return False
        
        X = np.array(features_list)
        y = np.array(targets)
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        return True
    
    def add_training_sample(self, core_history: List[Dict], future_load: float):
        """Add training sample for online learning"""
        features = self.extract_load_features(core_history)
        self.training_data.append(features)
        self.targets.append(future_load)
        
        # Keep only recent data
        max_samples = 2000
        if len(self.training_data) > max_samples:
            self.training_data = self.training_data[-max_samples:]
            self.targets = self.targets[-max_samples:]
    
    def save_model(self, path='data/models/load_predictor.pkl'):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)
    
    def load_model(self, path='data/models/load_predictor.pkl'):
        """Load model from disk"""
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = data['is_trained']
            return True
        return False