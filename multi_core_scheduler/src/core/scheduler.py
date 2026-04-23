import threading
import time
import heapq
from collections import deque
from typing import List, Optional
from ..core.process_manager import Process, ProcessState, ProcessGenerator
from ..core.core_manager import CoreManager
from ..ml.burst_predictor import BurstPredictor
from ..ml.feature_engineering import FeatureEngineer
from ..utils.logger import Logger
from ..utils.config_loader import ConfigLoader

class LoadBalancingScheduler:
    def __init__(self):
        self.config = ConfigLoader()
        self.logger = Logger().get_logger()
        
        # Core components
        self.num_cores = self.config.get('system.num_cores', 4)
        self.core_manager = CoreManager(self.num_cores)
        self.process_generator = ProcessGenerator()
        
        # Scheduling queues
        self.ready_queue = deque()
        self.waiting_queue = deque()
        self.completed_processes = []
        
        # ML components
        self.burst_predictor = BurstPredictor()
        self.feature_engineer = FeatureEngineer()
        
        # Performance metrics
        self.total_processes = 0
        self.completed_count = 0
        self.total_waiting_time = 0
        self.total_turnaround_time = 0
        self.scheduling_policy = self.config.get('system.scheduling_policy', 'ml_balanced')
        
        # Control flags
        self.is_running = False
        self.scheduler_thread = None
        
        # Callbacks for GUI
        self.on_process_update = None
        self.on_core_update = None
        self.on_metrics_update = None
        
        self.logger.info(f"Scheduler initialized with {self.num_cores} cores using {self.scheduling_policy} policy")
    
    def start(self):
        """Start the scheduler"""
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        self.logger.info("Scheduler stopped")
    
    def add_process(self, process: Process):
        """Add a new process to the ready queue"""
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        self.total_processes += 1
        self.logger.debug(f"Process {process.pid} added to ready queue")
        
        if self.on_process_update:
            self.on_process_update(self.get_all_processes())
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        last_load_balance = time.time()
        load_balance_interval = self.config.get('load_balancing.load_balancing_interval', 2.0)
        
        while self.is_running:
            try:
                # Check for newly arrived processes (simulated)
                if self.config.get('simulation.auto_generate_processes', True):
                    if len(self.ready_queue) < self.num_cores * 2:
                        new_process = self.process_generator.generate_process()
                        self.add_process(new_process)
                
                # Schedule processes to available cores
                self._schedule_processes()
                
                # Update core utilizations
                self._update_core_utilizations()
                
                # Periodic load balancing
                current_time = time.time()
                if current_time - last_load_balance >= load_balance_interval:
                    self._balance_load()
                    last_load_balance = current_time
                
                # Update GUI
                if self.on_core_update:
                    self.on_core_update(self.core_manager.cores)
                if self.on_metrics_update:
                    self.on_metrics_update(self.get_metrics())
                
                time.sleep(0.1)  # Scheduler quantum
                
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
    
    def _schedule_processes(self):
        """Schedule processes to available cores using selected policy"""
        for core in self.core_manager.cores:
            if core.is_idle and self.ready_queue:
                process = self._select_process()
                if process:
                    self._dispatch_process(core.core_id, process)
    
    def _select_process(self) -> Optional[Process]:
        """Select the next process based on scheduling policy"""
        if not self.ready_queue:
            return None
        
        if self.scheduling_policy == 'round_robin':
            return self.ready_queue.popleft()
        
        elif self.scheduling_policy == 'shortest_job':
            return min(self.ready_queue, key=lambda p: p.remaining_time)
        
        elif self.scheduling_policy == 'priority':
            return min(self.ready_queue, key=lambda p: p.priority)
        
        elif self.scheduling_policy == 'ml_balanced':
            return self._ml_based_selection()
        
        else:
            return self.ready_queue.popleft()
    
    def _ml_based_selection(self):
        """Use ML to select the best process for scheduling"""
        if not self.ready_queue:
            return None
        
        # Get system state
        system_state = {
            'total_processes': len(self.ready_queue),
            'avg_core_util': self.core_manager.get_utilization_stats()['average'],
            'load_imbalance': self.core_manager.get_load_imbalance(),
            'queue_length': len(self.ready_queue)
        }
        
        # Score each process using ML prediction
        scored_processes = []
        for process in list(self.ready_queue):
            features = self.feature_engineer.extract_features(process, system_state)
            predicted_burst = self.burst_predictor.predict(features)
            
            # Score: lower predicted burst time and higher priority = better
            score = predicted_burst / (process.priority + 1)
            scored_processes.append((score, process))
        
        # Select process with lowest score
        scored_processes.sort(key=lambda x: x[0])
        best_process = scored_processes[0][1]
        self.ready_queue.remove(best_process)
        
        return best_process
    
    def _dispatch_process(self, core_id: int, process: Process):
        """Dispatch a process to a core"""
        if process.start_time is None:
            process.start_time = time.time()
            process.response_time = process.start_time - process.arrival_time
        
        self.core_manager.assign_process(core_id, process)
        self.logger.info(f"Process {process.pid} dispatched to Core {core_id}")
        
        # Simulate process execution in background
        threading.Thread(target=self._execute_process, args=(core_id, process), daemon=True).start()
    
    def _execute_process(self, core_id: int, process: Process):
        """Simulate process execution on a core"""
        start_time = time.time()
        
        # Simulate CPU bursts
        for burst in process.cpu_bursts:
            if not self.is_running:
                break
            time.sleep(burst / 1000.0)  # Convert ms to seconds
        
        # Process completed
        end_time = time.time()
        process.end_time = end_time
        process.turnaround_time = end_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time / 1000.0
        process.state = ProcessState.COMPLETED
        
        # Update metrics
        self.completed_count += 1
        self.total_waiting_time += process.waiting_time
        self.total_turnaround_time += process.turnaround_time
        
        # Add to ML training data
        system_state = {
            'total_processes': len(self.ready_queue),
            'avg_core_util': self.core_manager.get_utilization_stats()['average'],
            'load_imbalance': self.core_manager.get_load_imbalance(),
            'queue_length': len(self.ready_queue)
        }
        features = self.feature_engineer.extract_features(process, system_state)
        self.burst_predictor.add_training_sample(features, process.burst_time)
        
        # Retrain ML model periodically
        if self.completed_count % self.config.get('ml.retrain_interval', 100) == 0:
            if len(self.burst_predictor.training_data) > 50:
                self.burst_predictor.train(
                    self.burst_predictor.training_data,
                    self.burst_predictor.targets
                )
                self.logger.info("ML model retrained")
        
        # Remove from core and add to completed list
        self.core_manager.remove_process(core_id)
        self.completed_processes.append(process)
        
        self.logger.info(f"Process {process.pid} completed on Core {core_id} (Turnaround: {process.turnaround_time:.2f}s)")
        
        if self.on_process_update:
            self.on_process_update(self.get_all_processes())
    
    def _update_core_utilizations(self):
        """Update utilization metrics for all cores"""
        for core in self.core_manager.cores:
            core.update_utilization(0.1)  # Update with 100ms quantum
    
    def _balance_load(self):
        """Balance load across cores using migration"""
        stats = self.core_manager.get_utilization_stats()
        imbalance = self.core_manager.get_load_imbalance()
        
        if imbalance > self.config.get('load_balancing.imbalance_threshold', 0.3):
            self.logger.info(f"Load imbalance detected: {imbalance:.2f}. Rebalancing...")
            
            # Find most and least loaded cores
            sorted_cores = sorted(self.core_manager.cores, key=lambda c: c.utilization)
            least_loaded = sorted_cores[0]
            most_loaded = sorted_cores[-1]
            
            # Migrate process if beneficial
            if most_loaded.current_process and least_loaded.is_idle:
                process = most_loaded.current_process
                migration_cost = self.config.get('load_balancing.migration_cost_factor', 0.1)
                
                # Only migrate if benefit outweighs cost
                if (most_loaded.utilization - least_loaded.utilization) > migration_cost:
                    self.core_manager.remove_process(most_loaded.core_id)
                    self.core_manager.assign_process(least_loaded.core_id, process)
                    self.logger.info(f"Migrated process {process.pid} from Core {most_loaded.core_id} to Core {least_loaded.core_id}")
    
    def get_all_processes(self) -> List[Process]:
        """Get all processes in the system"""
        all_processes = []
        all_processes.extend(self.ready_queue)
        all_processes.extend(self.waiting_queue)
        all_processes.extend(self.completed_processes)
        
        for core in self.core_manager.cores:
            if core.current_process:
                all_processes.append(core.current_process)
        
        return all_processes
    
    def get_metrics(self) -> dict:
        """Get current system metrics"""
        avg_waiting = self.total_waiting_time / self.completed_count if self.completed_count > 0 else 0
        avg_turnaround = self.total_turnaround_time / self.completed_count if self.completed_count > 0 else 0
        throughput = self.completed_count / (time.time() - self.process_generator.process_generator_start_time 
                                            if hasattr(self.process_generator, 'process_generator_start_time') else 1)
        
        # Set start time for throughput calculation
        if not hasattr(self.process_generator, 'process_generator_start_time'):
            self.process_generator.process_generator_start_time = time.time()
            throughput = 0
        
        return {
            'total_processes': self.total_processes,
            'completed': self.completed_count,
            'pending': len(self.ready_queue) + len(self.waiting_queue),
            'running': sum(1 for core in self.core_manager.cores if not core.is_idle),
            'avg_waiting_time': avg_waiting,
            'avg_turnaround_time': avg_turnaround,
            'throughput': throughput,
            'avg_core_utilization': self.core_manager.get_utilization_stats()['average'],
            'load_imbalance': self.core_manager.get_load_imbalance(),
            'core_utilizations': [core.utilization for core in self.core_manager.cores]
        }