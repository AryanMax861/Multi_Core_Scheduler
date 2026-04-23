import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.burst_predictor import BurstPredictor
from src.ml.feature_engineering import FeatureEngineer
from src.core.process_manager import ProcessGenerator

class TestMLPredictor(unittest.TestCase):
    
    def setUp(self):
        self.predictor = BurstPredictor()
        self.feature_engineer = FeatureEngineer()
        self.process_gen = ProcessGenerator()
    
    def test_prediction_without_training(self):
        """Test prediction without training"""
        process = self.process_gen.generate_process()
        features = self.feature_engineer.extract_features(process, {})
        
        prediction = self.predictor.predict(features)
        
        self.assertGreater(prediction, 0)
        self.assertEqual(prediction, features[0][0])  # Should return original
    
    def test_training_and_prediction(self):
        """Test training and prediction"""
        # Create training data
        features_list = []
        targets = []
        
        for _ in range(20):
            process = self.process_gen.generate_process()
            features = self.feature_engineer.extract_features(process, {})
            features_list.append(features.flatten())
            targets.append(process.burst_time)
            
            self.feature_engineer.add_to_history(process)
        
        # Train model
        success = self.predictor.train(features_list, targets)
        
        if success:
            # Test prediction
            test_process = self.process_gen.generate_process()
            test_features = self.feature_engineer.extract_features(test_process, {})
            prediction = self.predictor.predict(test_features)
            
            self.assertGreater(prediction, 0)
            self.assertIsInstance(prediction, float)
    
    def test_model_save_load(self):
        """Test model persistence"""
        # Train with some data
        features = [[1, 2, 3, 4, 5]]
        targets = [10]
        self.predictor.train(features, targets)
        
        # Save model
        self.predictor.save_model('test_model.pkl')
        
        # Create new predictor and load
        new_predictor = BurstPredictor()
        success = new_predictor.load_model('test_model.pkl')
        
        self.assertTrue(success)
        self.assertTrue(new_predictor.is_trained)
        
        # Clean up
        if os.path.exists('test_model.pkl'):
            os.remove('test_model.pkl')

if __name__ == '__main__':
    unittest.main()