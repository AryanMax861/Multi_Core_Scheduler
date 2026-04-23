import uuid
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import random

class ProcessState(Enum):
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    COMPLETED = "Completed"
    SUSPENDED = "Suspended"

class ProcessPriority(Enum):
    REAL_TIME = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class Process:
    pid: str
    name: str
    burst_time: float
    arrival_time: float
    priority: int
    memory_required: int = 1024  # MB
    state: ProcessState = ProcessState.NEW
    remaining_time: float = None
    core_id: Optional[int] = None
    waiting_time: float = 0
    turnaround_time: float = 0
    response_time: float = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    io_wait_time: float = 0
    cpu_bursts: list = None
    
    def __post_init__(self):
        if self.remaining_time is None:
            self.remaining_time = self.burst_time
        if self.cpu_bursts is None:
            self.cpu_bursts = []
        
    def __lt__(self, other):
        return self.priority < other.priority
    
    def to_dict(self):
        return {
            'pid': self.pid,
            'name': self.name,
            'burst_time': self.burst_time,
            'arrival_time': self.arrival_time,
            'priority': self.priority,
            'state': self.state.value,
            'remaining_time': self.remaining_time,
            'core_id': self.core_id,
            'waiting_time': self.waiting_time
        }

class ProcessGenerator:
    def __init__(self, arrival_rate=0.5, burst_range=(50, 500), priority_range=(1, 10)):
        self.arrival_rate = arrival_rate
        self.burst_range = burst_range
        self.priority_range = priority_range
        self.process_counter = 0
        
    def generate_process(self) -> Process:
        """Generate a new random process"""
        self.process_counter += 1
        burst_time = random.uniform(*self.burst_range)
        
        # Generate realistic CPU bursts (I/O intervals)
        num_bursts = random.randint(1, 5)
        cpu_bursts = []
        remaining = burst_time
        for i in range(num_bursts):
            if i == num_bursts - 1:
                burst = remaining
            else:
                burst = random.uniform(remaining * 0.1, remaining * 0.5)
            cpu_bursts.append(burst)
            remaining -= burst
        
        return Process(
            pid=f"P{self.process_counter:04d}",
            name=f"Process-{self.process_counter}",
            burst_time=burst_time,
            arrival_time=time.time(),
            priority=random.randint(*self.priority_range),
            memory_required=random.randint(512, 4096),
            cpu_bursts=cpu_bursts
        )