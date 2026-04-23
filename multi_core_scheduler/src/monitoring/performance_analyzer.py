import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict
from ..utils.logger import Logger

class PerformanceAnalyzer:
    def __init__(self):
        self.logger = Logger().get_logger()
        self.performance_history = []
        
    def analyze_scheduling_efficiency(self, scheduler_metrics: Dict) -> Dict:
        """Analyze scheduling efficiency"""
        analysis = {
            'efficiency_score': 0,
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Calculate efficiency score (0-100)
        score = 0
        max_score = 0
        
        # Throughput score (30%)
        throughput = scheduler_metrics.get('throughput', 0)
        if throughput > 0:
            throughput_score = min(30, (throughput / 10) * 30)
            score += throughput_score
        max_score += 30
        
        # Average waiting time score (30%)
        avg_waiting = scheduler_metrics.get('avg_waiting_time', float('inf'))
        if avg_waiting > 0:
            waiting_score = max(0, 30 - (avg_waiting / 10) * 30)
            score += waiting_score
        max_score += 30
        
        # Core utilization score (20%)
        avg_util = scheduler_metrics.get('avg_core_utilization', 0)
        if avg_util > 0:
            util_score = min(20, (avg_util / 0.7) * 20)  # Target 70% utilization
            score += util_score
        max_score += 20
        
        # Load balance score (20%)
        load_imbalance = scheduler_metrics.get('load_imbalance', 1)
        balance_score = max(0, 20 - (load_imbalance * 20))
        score += balance_score
        max_score += 20
        
        analysis['efficiency_score'] = (score / max_score) * 100 if max_score > 0 else 0
        
        # Identify bottlenecks
        if scheduler_metrics.get('avg_waiting_time', 0) > 5:
            analysis['bottlenecks'].append('High waiting time')
            analysis['recommendations'].append('Increase cores or optimize scheduling policy')
        
        if scheduler_metrics.get('avg_core_utilization', 0) < 0.5:
            analysis['bottlenecks'].append('Low core utilization')
            analysis['recommendations'].append('Increase process arrival rate')
        
        if scheduler_metrics.get('load_imbalance', 0) > 0.5:
            analysis['bottlenecks'].append('Severe load imbalance')
            analysis['recommendations'].append('Enable aggressive load balancing')
        
        return analysis
    
    def analyze_process_statistics(self, processes: List) -> Dict:
        """Analyze process statistics"""
        if not processes:
            return {}
        
        completed_processes = [p for p in processes if hasattr(p, 'turnaround_time') and p.turnaround_time > 0]
        
        if not completed_processes:
            return {}
        
        turnaround_times = [p.turnaround_time for p in completed_processes]
        waiting_times = [p.waiting_time for p in completed_processes]
        burst_times = [p.burst_time for p in completed_processes]
        
        analysis = {
            'total_processes': len(processes),
            'completed_count': len(completed_processes),
            'avg_turnaround_time': np.mean(turnaround_times),
            'median_turnaround_time': np.median(turnaround_times),
            'std_turnaround_time': np.std(turnaround_times),
            'avg_waiting_time': np.mean(waiting_times),
            'median_waiting_time': np.median(waiting_times),
            'avg_burst_time': np.mean(burst_times),
            'max_burst_time': np.max(burst_times),
            'min_burst_time': np.min(burst_times),
            'percentile_95_turnaround': np.percentile(turnaround_times, 95),
            'percentile_95_waiting': np.percentile(waiting_times, 95)
        }
        
        return analysis
    
    def compare_policies(self, policy_results: Dict) -> pd.DataFrame:
        """Compare different scheduling policies"""
        comparisons = []
        
        for policy, metrics in policy_results.items():
            comparisons.append({
                'Policy': policy,
                'Throughput': metrics.get('throughput', 0),
                'Avg Waiting Time': metrics.get('avg_waiting_time', 0),
                'Avg Turnaround': metrics.get('avg_turnaround_time', 0),
                'Core Utilization': metrics.get('avg_core_utilization', 0),
                'Load Imbalance': metrics.get('load_imbalance', 0),
                'Efficiency Score': metrics.get('efficiency_score', 0)
            })
        
        df = pd.DataFrame(comparisons)
        
        # Find best policy for each metric
        best_throughput = df.loc[df['Throughput'].idxmax()] if not df.empty else None
        best_waiting = df.loc[df['Avg Waiting Time'].idxmin()] if not df.empty else None
        best_utilization = df.loc[df['Core Utilization'].idxmax()] if not df.empty else None
        
        return df
    
    def generate_report(self, metrics: Dict, processes: List, output_file=None):
        """Generate comprehensive performance report"""
        import json
        from datetime import datetime
        
        # Analyze data
        scheduling_analysis = self.analyze_scheduling_efficiency(metrics)
        process_analysis = self.analyze_process_statistics(processes)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'system_metrics': metrics,
            'scheduling_analysis': scheduling_analysis,
            'process_analysis': process_analysis,
            'recommendations': scheduling_analysis['recommendations']
        }
        
        # Add scorecard
        report['scorecard'] = {
            'Overall Efficiency': f"{scheduling_analysis['efficiency_score']:.1f}/100",
            'Throughput': f"{metrics.get('throughput', 0):.2f} proc/s",
            'Avg Response Time': f"{metrics.get('avg_waiting_time', 0):.2f}s",
            'Core Utilization': f"{metrics.get('avg_core_utilization', 0)*100:.1f}%"
        }
        
        # Save to file
        if output_file is None:
            output_file = f"data/metrics/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Performance report saved to {output_file}")
        
        return report