import numpy as np
import pandas as pd
from typing import List, Dict
from ..core.process_manager import Process

class FeatureEngineer:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.process_history = []
        
    def extract_features(self, process: Process, system_state: Dict) -> np.ndarray:
        """Extract features from process and system state for ML prediction"""
        features = []
        
        # Process features
        features.append(process.burst_time)
        features.append(process.arrival_time)
        features.append(process.priority)
        features.append(process.remaining_time / process.burst_time)  # Progress ratio
        features.append(len(process.cpu_bursts))  # Number of CPU bursts
        
        # System state features
        features.append(system_state.get('total_processes', 0))
        features.append(system_state.get('avg_core_util', 0))
        features.append(system_state.get('load_imbalance', 0))
        features.append(system_state.get('queue_length', 0))
        
        # Historical features
        if len(self.process_history) >= self.window_size:
            recent_bursts = [p.burst_time for p in self.process_history[-self.window_size:]]
            features.append(np.mean(recent_bursts))
            features.append(np.std(recent_bursts))
        else:
            features.extend([0, 0])
            
        return np.array(features).reshape(1, -1)
    
    def add_to_history(self, process: Process):
        """Add completed process to history for future feature extraction"""
        self.process_history.append(process)
        if len(self.process_history) > self.window_size * 10:
            self.process_history.pop(0)