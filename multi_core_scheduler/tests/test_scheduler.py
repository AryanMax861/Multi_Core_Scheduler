import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.scheduler import LoadBalancingScheduler
from src.core.process_manager import Process, ProcessGenerator

class TestScheduler(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.scheduler = LoadBalancingScheduler()
        self.process_gen = ProcessGenerator()
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        self.assertIsNotNone(self.scheduler)
        self.assertEqual(self.scheduler.num_cores, 4)
        self.assertIsNotNone(self.scheduler.core_manager)
    
    def test_add_process(self):
        """Test adding process to scheduler"""
        process = self.process_gen.generate_process()
        initial_count = len(self.scheduler.ready_queue)
        
        self.scheduler.add_process(process)
        
        self.assertEqual(len(self.scheduler.ready_queue), initial_count + 1)
        self.assertIn(process, self.scheduler.ready_queue)
    
    def test_scheduler_start_stop(self):
        """Test scheduler start and stop"""
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        metrics = self.scheduler.get_metrics()
        
        self.assertIn('total_processes', metrics)
        self.assertIn('completed', metrics)
        self.assertIn('avg_core_utilization', metrics)

class TestProcessGenerator(unittest.TestCase):
    
    def setUp(self):
        self.generator = ProcessGenerator()
    
    def test_generate_process(self):
        """Test process generation"""
        process = self.generator.generate_process()
        
        self.assertIsNotNone(process.pid)
        self.assertGreater(process.burst_time, 0)
        self.assertGreaterEqual(process.priority, 1)
        self.assertLessEqual(process.priority, 10)

if __name__ == '__main__':
    unittest.main()