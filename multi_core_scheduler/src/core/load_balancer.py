import numpy as np
from typing import List, Tuple
from ..core.core_manager import Core
from ..core.process_manager import Process
from ..utils.logger import Logger

class LoadBalancer:
    def __init__(self, imbalance_threshold=0.3, migration_cost_factor=0.1):
        self.logger = Logger().get_logger()
        self.imbalance_threshold = imbalance_threshold
        self.migration_cost_factor = migration_cost_factor
        self.balance_history = []
        
    def calculate_imbalance(self, cores: List[Core]) -> float:
        """Calculate load imbalance factor"""
        utilizations = [core.utilization for core in cores]
        if not utilizations:
            return 0.0
        
        mean_util = np.mean(utilizations)
        if mean_util == 0:
            return 0.0
        
        std_dev = np.std(utilizations)
        imbalance = std_dev / mean_util
        return min(imbalance, 1.0)
    
    def find_optimal_migration(self, cores: List[Core]) -> Tuple[int, int, Process]:
        """Find best process to migrate from overloaded to underloaded core"""
        # Sort cores by utilization
        sorted_cores = sorted(cores, key=lambda c: c.utilization)
        
        # Find overloaded and underloaded cores
        underloaded_cores = [c for c in sorted_cores if c.utilization < 0.5]
        overloaded_cores = [c for c in sorted_cores if c.utilization > 0.7 and c.current_process]
        
        if not underloaded_cores or not overloaded_cores:
            return None, None, None
        
        # Find best migration pair
        best_benefit = 0
        best_pair = (None, None, None)
        
        for overloaded in overloaded_cores:
            for underloaded in underloaded_cores:
                if overloaded.core_id == underloaded.core_id:
                    continue
                
                # Calculate migration benefit
                current_imbalance = self.calculate_imbalance(cores)
                benefit = (overloaded.utilization - underloaded.utilization) - self.migration_cost_factor
                
                if benefit > best_benefit and overloaded.current_process:
                    best_benefit = benefit
                    best_pair = (overloaded.core_id, underloaded.core_id, overloaded.current_process)
        
        return best_pair
    
    def should_balance(self, cores: List[Core]) -> bool:
        """Check if load balancing is needed"""
        imbalance = self.calculate_imbalance(cores)
        self.balance_history.append(imbalance)
        
        # Keep history
        if len(self.balance_history) > 10:
            self.balance_history.pop(0)
        
        # Check if imbalance exceeds threshold and is sustained
        if imbalance > self.imbalance_threshold:
            recent_avg = np.mean(self.balance_history[-3:]) if len(self.balance_history) >= 3 else imbalance
            if recent_avg > self.imbalance_threshold:
                self.logger.info(f"Load balancing triggered - Imbalance: {imbalance:.3f}")
                return True
        
        return False
    
    def get_balance_suggestion(self, cores: List[Core]) -> dict:
        """Get load balancing suggestions"""
        imbalance = self.calculate_imbalance(cores)
        
        suggestion = {
            'imbalance_factor': imbalance,
            'needs_balancing': imbalance > self.imbalance_threshold,
            'target_utilization': np.mean([c.utilization for c in cores]),
            'recommended_actions': []
        }
        
        if suggestion['needs_balancing']:
            # Find which cores need attention
            for core in cores:
                if core.utilization > 0.8:
                    suggestion['recommended_actions'].append({
                        'core_id': core.core_id,
                        'action': 'migrate_process',
                        'reason': f'Overloaded ({core.utilization:.1%})'
                    })
                elif core.utilization < 0.2 and core.current_process is None:
                    suggestion['recommended_actions'].append({
                        'core_id': core.core_id,
                        'action': 'assign_process',
                        'reason': f'Underutilized ({core.utilization:.1%})'
                    })
        
        return suggestion