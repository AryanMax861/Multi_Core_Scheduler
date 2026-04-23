from dataclasses import dataclass
from typing import Optional, List
from ..core.process_manager import Process, ProcessState

@dataclass
class Core:
    core_id: int
    current_process: Optional[Process] = None
    utilization: float = 0.0
    is_idle: bool = True
    total_busy_time: float = 0
    total_idle_time: float = 0
    temperature: float = 40.0  # Celsius
    frequency: int = 2400  # MHz
    process_history: List = None
    
    def __post_init__(self):
        if self.process_history is None:
            self.process_history = []
    
    def update_utilization(self, elapsed_time: float):
        """Update core utilization based on elapsed time"""
        if self.current_process and not self.is_idle:
            self.total_busy_time += elapsed_time
            self.utilization = self.total_busy_time / (self.total_busy_time + self.total_idle_time + 0.001)
        else:
            self.total_idle_time += elapsed_time
            self.utilization = self.total_busy_time / (self.total_busy_time + self.total_idle_time + 0.001)
        
        # Update temperature based on utilization
        self.temperature = 40 + (self.utilization * 30)

class CoreManager:
    def __init__(self, num_cores: int):
        self.cores = [Core(core_id=i) for i in range(num_cores)]
        self.core_load_history = []
        
    def get_available_core(self) -> Optional[int]:
        """Find the first idle core"""
        for core in self.cores:
            if core.is_idle:
                return core.core_id
        return None
    
    def get_least_loaded_core(self) -> int:
        """Get the core with minimum utilization"""
        return min(self.cores, key=lambda c: c.utilization).core_id
    
    def assign_process(self, core_id: int, process: Process):
        """Assign a process to a specific core"""
        core = self.cores[core_id]
        core.current_process = process
        core.is_idle = False
        process.core_id = core_id
        process.state = ProcessState.RUNNING
        
    def remove_process(self, core_id: int):
        """Remove current process from core"""
        core = self.cores[core_id]
        if core.current_process:
            core.process_history.append(core.current_process)
            core.current_process = None
        core.is_idle = True
        
    def get_utilization_stats(self) -> dict:
        """Get utilization statistics for all cores"""
        utilizations = [core.utilization for core in self.cores]
        return {
            'individual': utilizations,
            'average': sum(utilizations) / len(utilizations),
            'max': max(utilizations),
            'min': min(utilizations),
            'std_dev': self._calculate_std_dev(utilizations)
        }
    
    def _calculate_std_dev(self, values):
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def get_load_imbalance(self) -> float:
        """Calculate load imbalance factor (0 = perfect balance, 1 = max imbalance)"""
        stats = self.get_utilization_stats()
        if stats['average'] == 0:
            return 0
        return stats['std_dev'] / stats['average']