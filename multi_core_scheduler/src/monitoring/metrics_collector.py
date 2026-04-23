import time
import pandas as pd
from datetime import datetime
from collections import deque
from typing import List, Dict
import threading
import os
from ..utils.logger import Logger

class MetricsCollector:
    def __init__(self, save_interval=10, max_history=1000):
        self.logger = Logger().get_logger()
        self.save_interval = save_interval
        self.max_history = max_history
        
        self.metrics_history = deque(maxlen=max_history)
        self.current_metrics = {}
        self.is_collecting = False
        self.collector_thread = None
        
        # Create metrics directory
        os.makedirs('data/metrics', exist_ok=True)
        
    def start_collection(self):
        """Start metrics collection"""
        self.is_collecting = True
        self.collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collector_thread.start()
        self.logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collector_thread:
            self.collector_thread.join(timeout=2)
        self.save_metrics()
        self.logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop"""
        last_save = time.time()
        
        while self.is_collecting:
            try:
                # Record current metrics
                if self.current_metrics:
                    self._record_metrics()
                
                # Save periodically
                current_time = time.time()
                if current_time - last_save >= self.save_interval:
                    self.save_metrics()
                    last_save = current_time
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
    
    def _record_metrics(self):
        """Record current metrics to history"""
        timestamp = datetime.now()
        record = {
            'timestamp': timestamp,
            **self.current_metrics
        }
        self.metrics_history.append(record)
    
    def update_metrics(self, metrics: Dict):
        """Update current metrics"""
        self.current_metrics = metrics
    
    def save_metrics(self):
        """Save metrics to CSV file"""
        if not self.metrics_history:
            return
        
        df = pd.DataFrame(list(self.metrics_history))
        filename = f"data/metrics/metrics_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Append or create new file
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(filename, index=False)
        self.logger.debug(f"Metrics saved to {filename}")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary from collected metrics"""
        if not self.metrics_history:
            return {}
        
        df = pd.DataFrame(list(self.metrics_history))
        
        summary = {
            'avg_throughput': df['throughput'].mean() if 'throughput' in df else 0,
            'max_throughput': df['throughput'].max() if 'throughput' in df else 0,
            'avg_waiting_time': df['avg_waiting_time'].mean() if 'avg_waiting_time' in df else 0,
            'avg_turnaround_time': df['avg_turnaround_time'].mean() if 'avg_turnaround_time' in df else 0,
            'avg_core_utilization': df['avg_core_utilization'].mean() if 'avg_core_utilization' in df else 0,
            'avg_load_imbalance': df['load_imbalance'].mean() if 'load_imbalance' in df else 0,
            'total_processes_completed': df['completed'].max() if 'completed' in df else 0,
            'collection_duration': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() if len(df) > 1 else 0
        }
        
        return summary
    
    def export_to_excel(self, filename=None):
        """Export metrics to Excel with multiple sheets"""
        if not self.metrics_history:
            self.logger.warning("No metrics to export")
            return
        
        if filename is None:
            filename = f"data/metrics/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Raw data sheet
            df = pd.DataFrame(list(self.metrics_history))
            df.to_excel(writer, sheet_name='Raw Metrics', index=False)
            
            # Summary sheet
            summary = self.get_performance_summary()
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Statistics sheet
            stats = df.describe()
            stats.to_excel(writer, sheet_name='Statistics')
        
        self.logger.info(f"Metrics exported to {filename}")
        return filename