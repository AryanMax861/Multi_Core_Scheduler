import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.load_balancer import LoadBalancer
from src.core.core_manager import CoreManager

class TestLoadBalancer(unittest.TestCase):
    
    def setUp(self):
        self.load_balancer = LoadBalancer()
        self.core_manager = CoreManager(4)
    
    def test_imbalance_calculation(self):
        """Test load imbalance calculation"""
        # Set different utilizations
        for i, core in enumerate(self.core_manager.cores):
            core.utilization = 0.2 + (i * 0.2)
        
        imbalance = self.load_balancer.calculate_imbalance(self.core_manager.cores)
        
        self.assertGreaterEqual(imbalance, 0)
        self.assertLessEqual(imbalance, 1)
    
    def test_balance_check(self):
        """Test if balancing is needed"""
        # Balanced cores
        for core in self.core_manager.cores:
            core.utilization = 0.5
        
        should_balance = self.load_balancer.should_balance(self.core_manager.cores)
        self.assertFalse(should_balance)
        
        # Imbalanced cores
        self.core_manager.cores[0].utilization = 0.9
        self.core_manager.cores[1].utilization = 0.1
        
        should_balance = self.load_balancer.should_balance(self.core_manager.cores)
        self.assertTrue(should_balance)
    
    def test_migration_suggestion(self):
        """Test migration suggestion finding"""
        # Create imbalance scenario
        self.core_manager.cores[0].utilization = 0.9
        self.core_manager.cores[0].is_idle = False
        self.core_manager.cores[3].utilization = 0.1
        
        from_core, to_core, process = self.load_balancer.find_optimal_migration(self.core_manager.cores)
        
        # Should find a migration suggestion
        self.assertIsNotNone(from_core)

if __name__ == '__main__':
    unittest.main()