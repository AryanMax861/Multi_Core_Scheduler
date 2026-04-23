import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
import random
from datetime import datetime
import numpy as np
from collections import deque

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Custom color scheme
COLORS = {
    'bg_dark': '#0a0e27',
    'bg_card': '#141a33',
    'bg_hover': '#1e2748',
    'primary': '#5b8cff',
    'primary_dark': '#4a75e6',
    'success': '#2ecc71',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#3498db',
    'purple': '#9b59b6',
    'orange': '#e67e22',
    'text': '#ffffff',
    'text_secondary': '#a0a8c0',
    'border': '#2a3254'
}

class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, title="", value="0", icon="📊", color=COLORS['primary'], **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_card'], corner_radius=12, **kwargs)
        
        icon_frame = ctk.CTkFrame(self, fg_color=color, width=45, height=45, corner_radius=10)
        icon_frame.pack(side="left", padx=12, pady=12)
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(icon_frame, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(expand=True)
        
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            text_frame, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        title_label.pack(anchor="w")
        
        self.value_label = ctk.CTkLabel(
            text_frame, text=value,
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS['text']
        )
        self.value_label.pack(anchor="w")
    
    def set_value(self, value):
        self.value_label.configure(text=value)

class WorkingScheduler:
    def __init__(self, num_cores=4):
        self.num_cores = num_cores
        self.cores = []
        for i in range(num_cores):
            self.cores.append({
                'id': i,
                'utilization': 0.0,
                'temperature': 40.0,
                'frequency': 2400,
                'current_process': None,
                'is_idle': True,
                'total_busy_time': 0,
                'total_idle_time': 0
            })
        self.ready_queue = deque()
        self.completed_processes = []
        self.running = False
        self.process_counter = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.policy = "ml_balanced"
        
    def add_process(self, burst_time=None, priority=None, name=None):
        with self.lock:
            self.process_counter += 1
            if burst_time is None:
                burst_time = random.uniform(100, 500)
            if priority is None:
                priority = random.randint(1, 10)
            if name is None:
                name = f"P{self.process_counter}"
                
            process = {
                'pid': self.process_counter,
                'name': name,
                'burst_time': burst_time,
                'remaining_time': burst_time,
                'priority': priority,
                'state': "Ready",
                'core_id': None,
                'arrival_time': time.time(),
                'start_time': None,
                'end_time': None,
                'waiting_time': 0,
                'turnaround_time': 0,
            }
            self.ready_queue.append(process)
            return process
    
    def start(self):
        self.running = True
        self.start_time = time.time()
        threading.Thread(target=self._scheduler_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def change_policy(self, policy):
        self.policy = policy
    
    def _scheduler_loop(self):
        while self.running:
            with self.lock:
                # Assign processes to idle cores
                for core in self.cores:
                    if core['is_idle'] and self.ready_queue:
                        process = self.ready_queue.popleft()
                        core['current_process'] = process
                        core['is_idle'] = False
                        process['state'] = "Running"
                        process['core_id'] = core['id']
                        process['start_time'] = time.time()
                        threading.Thread(target=self._execute_process, args=(core['id'], process), daemon=True).start()
                
                # Update core utilization
                for core in self.cores:
                    if not core['is_idle']:
                        core['total_busy_time'] += 0.1
                        core['utilization'] = min(1.0, core['total_busy_time'] / (core['total_busy_time'] + core['total_idle_time'] + 0.001))
                        core['temperature'] = min(90, 40 + core['utilization'] * 35)
                        core['frequency'] = int(2400 + (core['utilization'] * 800))
                    else:
                        core['total_idle_time'] += 0.1
                        core['utilization'] = max(0.0, core['total_busy_time'] / (core['total_busy_time'] + core['total_idle_time'] + 0.001))
                        core['temperature'] = max(40, core['temperature'] - 0.3)
                        core['frequency'] = max(1600, core['frequency'] - 20)
            
            time.sleep(0.1)
    
    def _execute_process(self, core_id, process):
        time.sleep(process['remaining_time'] / 1000.0)
        
        with self.lock:
            process['end_time'] = time.time()
            process['state'] = "Completed"
            process['turnaround_time'] = process['end_time'] - process['arrival_time']
            process['waiting_time'] = max(0, process['turnaround_time'] - (process['burst_time'] / 1000.0))
            self.completed_processes.append(process)
            
            for core in self.cores:
                if core['id'] == core_id:
                    core['current_process'] = None
                    core['is_idle'] = True
    
    def get_system_state(self):
        with self.lock:
            running_count = sum(1 for c in self.cores if not c['is_idle'])
            utilizations = [c['utilization'] for c in self.cores]
            avg_util = sum(utilizations) / len(utilizations) if utilizations else 0
            std_dev = np.std(utilizations) if len(utilizations) > 1 else 0
            load_imbalance = std_dev / (avg_util + 0.001)
            
            elapsed = max(1, time.time() - self.start_time)
            throughput = len(self.completed_processes) / elapsed
            
            avg_waiting = 0
            avg_turnaround = 0
            if self.completed_processes:
                avg_waiting = sum(p['waiting_time'] for p in self.completed_processes) / len(self.completed_processes)
                avg_turnaround = sum(p['turnaround_time'] for p in self.completed_processes) / len(self.completed_processes)
            
            return {
                'cores': self.cores.copy(),
                'ready_queue': list(self.ready_queue),
                'completed_count': len(self.completed_processes),
                'total_processes': self.process_counter,
                'running_count': running_count,
                'pending_count': len(self.ready_queue),
                'avg_utilization': avg_util,
                'load_imbalance': load_imbalance,
                'throughput': throughput,
                'utilizations': utilizations,
                'avg_waiting_time': avg_waiting,
                'avg_turnaround_time': avg_turnaround
            }

class WorkingDashboard:
    def __init__(self):
        self.scheduler = WorkingScheduler(4)
        self.setup_gui()
        self.update_ui()
        
    def setup_gui(self):
        self.root = ctk.CTk()
        self.root.title("Multi-Core Load Balancing Scheduler")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=COLORS['bg_dark'])
        
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        self.setup_header()
        
        # Content
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=15)
        
        # Left panel - Cores
        self.left_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 7))
        self.setup_cores_panel()
        
        # Right panel - Metrics and Queue
        self.right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(7, 0))
        self.setup_right_panel()
        
        # Status bar
        self.setup_status_bar()
    
    def setup_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_card'], height=70, corner_radius=15)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=25, pady=15)
        
        ctk.CTkLabel(
            title_frame, text="⚡ MULTI-CORE LOAD BALANCING SCHEDULER",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS['primary']
        ).pack(side="left")
        
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20)
        
        # Policy selector
        policy_frame = ctk.CTkFrame(button_frame, fg_color=COLORS['bg_dark'], corner_radius=8)
        policy_frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(policy_frame, text="Policy:", font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
        self.policy_var = ctk.StringVar(value="ml_balanced")
        policy_combo = ctk.CTkComboBox(
            policy_frame, values=["round_robin", "shortest_job", "priority", "ml_balanced"],
            variable=self.policy_var, width=120, command=self.change_policy
        )
        policy_combo.pack(side="left", padx=8, pady=5)
        
        self.start_btn = ctk.CTkButton(
            button_frame, text="▶ START", command=self.start_scheduler,
            fg_color=COLORS['success'], hover_color="#27ae60", width=100, height=35
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏸ STOP", command=self.stop_scheduler,
            fg_color=COLORS['danger'], hover_color="#c0392b", width=100, height=35, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        self.add_btn = ctk.CTkButton(
            button_frame, text="+ ADD", command=self.add_process,
            fg_color=COLORS['info'], hover_color="#2980b9", width=100, height=35
        )
        self.add_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            button_frame, text="CLEAR", command=self.clear_all,
            fg_color=COLORS['warning'], hover_color="#e67e22", width=100, height=35
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def setup_cores_panel(self):
        # Title
        title_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            title_frame, text="CPU Core Visualization",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS['primary']
        ).pack(side="left")
        
        # Cores grid
        cores_grid = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        cores_grid.pack(fill="both", expand=True)
        
        self.core_cards = []
        for i in range(4):
            card = self.create_core_card(cores_grid, i)
            row, col = i // 2, i % 2
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.core_cards.append(card)
        
        cores_grid.grid_columnconfigure(0, weight=1)
        cores_grid.grid_columnconfigure(1, weight=1)
        cores_grid.grid_rowconfigure(0, weight=1)
        cores_grid.grid_rowconfigure(1, weight=1)
        
        # Chart section - FIXED with better visibility
        chart_frame = ctk.CTkFrame(self.left_panel, fg_color=COLORS['bg_card'], corner_radius=15)
        chart_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        ctk.CTkLabel(
            chart_frame, text="📈 Utilization History",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['primary']
        ).pack(pady=(10, 5))
        
        # Create figure with larger size and better colors
        self.fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=COLORS['bg_card'])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1a1f3a')  # Visible background
        self.ax.set_title("CPU Core Utilization Over Time", color='white', fontsize=12, pad=10)
        self.ax.set_xlabel("Time (seconds)", color=COLORS['text_secondary'], fontsize=10)
        self.ax.set_ylabel("Utilization (%)", color=COLORS['text_secondary'], fontsize=10)
        self.ax.tick_params(colors=COLORS['text_secondary'], labelsize=9)
        self.ax.grid(True, alpha=0.3, color='gray', linestyle='--')
        self.ax.set_ylim(0, 100)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)
        
        # Data storage
        self.chart_data = {0: deque(maxlen=60), 1: deque(maxlen=60), 2: deque(maxlen=60), 3: deque(maxlen=60)}
        self.time_data = deque(maxlen=60)
    
    def create_core_card(self, parent, core_id):
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=15)
        
        # Header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text=f"CORE {core_id}",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS['primary']
        ).pack(side="left")
        
        # Status indicator
        status = ctk.CTkFrame(header_frame, width=12, height=12, corner_radius=6, fg_color=COLORS['success'])
        status.pack(side="right")
        
        # Utilization bar
        util_bar = ctk.CTkProgressBar(card, width=250, height=30, corner_radius=15)
        util_bar.pack(pady=10)
        util_bar.set(0)
        
        # Stats
        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=10)
        
        util_label = ctk.CTkLabel(
            stats_frame, text="Utilization: 0%",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text']
        )
        util_label.pack(anchor="w")
        
        temp_label = ctk.CTkLabel(
            stats_frame, text="Temperature: 40°C",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        temp_label.pack(anchor="w")
        
        proc_label = ctk.CTkLabel(
            card, text="Process: Idle",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS['text_secondary']
        )
        proc_label.pack(pady=(5, 15))
        
        # Store widgets as attributes
        card.status = status
        card.util_bar = util_bar
        card.util_label = util_label
        card.temp_label = temp_label
        card.proc_label = proc_label
        
        return card
    
    def setup_right_panel(self):
        # Metrics section
        metrics_frame = ctk.CTkFrame(self.right_panel, fg_color=COLORS['bg_card'], corner_radius=15)
        metrics_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            metrics_frame, text="📊 Performance Metrics",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['primary']
        ).pack(pady=(10, 5))
        
        metrics_grid = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        metrics_grid.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.metric_cards = {}
        metrics = [
            ("Total", "0", "📊", COLORS['info']),
            ("Completed", "0", "✅", COLORS['success']),
            ("Pending", "0", "⏳", COLORS['warning']),
            ("Running", "0", "⚡", COLORS['danger']),
            ("Throughput", "0/s", "🚀", COLORS['purple']),
            ("Avg Util", "0%", "💻", COLORS['primary']),
            ("Imbalance", "0", "⚖️", COLORS['orange']),
            ("Avg Wait", "0s", "⏱️", COLORS['info'])
        ]
        
        for i, (title, default, icon, color) in enumerate(metrics):
            card = MetricCard(metrics_grid, title, default, icon, color)
            row, col = i // 2, i % 2
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.metric_cards[title] = card
        
        metrics_grid.grid_columnconfigure(0, weight=1)
        metrics_grid.grid_columnconfigure(1, weight=1)
        
        # Process Queue section - FIXED with better display
        queue_frame = ctk.CTkFrame(self.right_panel, fg_color=COLORS['bg_card'], corner_radius=15)
        queue_frame.pack(fill="both", expand=True)
        
        queue_header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            queue_header, text="📋 Process Queue",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['primary']
        ).pack(side="left")
        
        self.queue_count = ctk.CTkLabel(
            queue_header, text="(0)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        self.queue_count.pack(side="left", padx=(5, 0))
        
        # Treeview for processes - More reliable
        tree_frame = ctk.CTkFrame(queue_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.process_tree = ttk.Treeview(
            tree_frame, 
            columns=("ID", "Name", "State", "Burst", "Remaining", "Priority", "Core"),
            show="headings",
            height=12
        )
        
        # Configure columns
        columns_width = {"ID": 60, "Name": 100, "State": 80, "Burst": 80, "Remaining": 80, "Priority": 70, "Core": 70}
        for col, width in columns_width.items():
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=width, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        self.process_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=COLORS['bg_dark'], foreground="white", fieldbackground=COLORS['bg_dark'])
        style.configure("Treeview.Heading", background=COLORS['bg_card'], foreground="white", font=('Segoe UI', 10, 'bold'))
        
        # Avg times
        times_frame = ctk.CTkFrame(queue_frame, fg_color="transparent")
        times_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.waiting_label = ctk.CTkLabel(
            times_frame, text="⏱️ Avg Waiting: 0.00s",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        self.waiting_label.pack(side="left", padx=5)
        
        self.turnaround_label = ctk.CTkLabel(
            times_frame, text="🔄 Avg Turnaround: 0.00s",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        self.turnaround_label.pack(side="left", padx=15)
    
    def setup_status_bar(self):
        status_bar = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_card'], height=35, corner_radius=10)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_bar, text="✅ System Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(side="left", padx=15)
        
        self.time_label = ctk.CTkLabel(
            status_bar, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_secondary']
        )
        self.time_label.pack(side="right", padx=15)
        
        self.update_time()
    
    def update_time(self):
        self.time_label.configure(text=f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.root.after(1000, self.update_time)
    
    def start_scheduler(self):
        self.scheduler.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="▶ Scheduler Running")
    
    def stop_scheduler(self):
        self.scheduler.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="⏸ Scheduler Paused")
    
    def add_process(self):
        process = self.scheduler.add_process()
        self.status_label.configure(text=f"✅ Added {process['name']}")
    
    def clear_all(self):
        self.scheduler.stop()
        self.scheduler = WorkingScheduler(4)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="🔄 System Reset")
    
    def change_policy(self, choice):
        self.scheduler.change_policy(choice)
        self.status_label.configure(text=f"📋 Policy: {choice}")
    
    def update_ui(self):
        try:
            state = self.scheduler.get_system_state()
            
            # Update cores
            for i, core in enumerate(state['cores']):
                if i < len(self.core_cards):
                    card = self.core_cards[i]
                    util = core['utilization']
                    
                    card.util_bar.set(util)
                    card.util_label.configure(text=f"Utilization: {util*100:.1f}%")
                    card.temp_label.configure(text=f"Temperature: {core['temperature']:.0f}°C")
                    
                    if core['current_process']:
                        card.proc_label.configure(text=f"Process: {core['current_process']['name']}")
                        card.status.configure(fg_color=COLORS['success'])
                    else:
                        card.proc_label.configure(text="Process: Idle")
                        card.status.configure(fg_color=COLORS['text_secondary'])
                    
                    # Color based on utilization
                    if util > 0.8:
                        card.util_bar.configure(progress_color=COLORS['danger'])
                    elif util > 0.5:
                        card.util_bar.configure(progress_color=COLORS['warning'])
                    else:
                        card.util_bar.configure(progress_color=COLORS['success'])
            
            # Update chart - CLEARLY VISIBLE
            current_time = time.time() - self.scheduler.start_time
            self.time_data.append(current_time)
            
            for i, util in enumerate(state['utilizations']):
                self.chart_data[i].append(util * 100)
            
            # Clear and redraw chart
            self.ax.clear()
            self.ax.set_facecolor('#1a1f3a')
            
            # Plot with distinct colors
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            for i in range(4):
                if len(self.chart_data[i]) > 1:
                    x_data = list(self.time_data)[-len(self.chart_data[i]):]
                    y_data = list(self.chart_data[i])
                    self.ax.plot(x_data, y_data, label=f'Core {i}', color=colors[i], linewidth=2.5, marker='o', markersize=3)
            
            self.ax.set_title("📈 CPU Core Utilization History", color='white', fontsize=12, fontweight='bold', pad=10)
            self.ax.set_xlabel("Time (seconds)", color=COLORS['text_secondary'], fontsize=10)
            self.ax.set_ylabel("Utilization (%)", color=COLORS['text_secondary'], fontsize=10)
            self.ax.tick_params(colors=COLORS['text_secondary'], labelsize=9)
            self.ax.legend(loc='upper right', facecolor='#1a1f3a', labelcolor='white', fontsize=9)
            self.ax.grid(True, alpha=0.3, color='white', linestyle='--', linewidth=0.5)
            self.ax.set_ylim(0, 100)
            self.ax.set_xlim(0, max(60, current_time) if self.time_data else 60)
            
            self.canvas.draw()
            
            # Update metrics
            self.metric_cards["Total"].set_value(str(state['total_processes']))
            self.metric_cards["Completed"].set_value(str(state['completed_count']))
            self.metric_cards["Pending"].set_value(str(state['pending_count']))
            self.metric_cards["Running"].set_value(str(state['running_count']))
            self.metric_cards["Throughput"].set_value(f"{state['throughput']:.2f}/s")
            self.metric_cards["Avg Util"].set_value(f"{state['avg_utilization']*100:.1f}%")
            self.metric_cards["Imbalance"].set_value(f"{state['load_imbalance']:.3f}")
            self.metric_cards["Avg Wait"].set_value(f"{state['avg_waiting_time']:.2f}s")
            
            # Update waiting times
            self.waiting_label.configure(text=f"⏱️ Avg Waiting: {state['avg_waiting_time']:.2f}s")
            self.turnaround_label.configure(text=f"🔄 Avg Turnaround: {state['avg_turnaround_time']:.2f}s")
            self.queue_count.configure(text=f"({state['pending_count']})")
            
            # Update process tree - FIXED
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            # Show ready queue + running processes
            all_processes = list(state['ready_queue']) + [c['current_process'] for c in state['cores'] if c['current_process']]
            for p in all_processes:
                core_str = f"Core {p['core_id']}" if p['core_id'] is not None else "Queue"
                self.process_tree.insert("", "end", values=(
                    f"P{p['pid']}", 
                    p['name'][:10], 
                    p['state'],
                    f"{p['burst_time']:.0f}",
                    f"{p['remaining_time']:.0f}",
                    p['priority'],
                    core_str
                ))
            
            self.status_label.configure(
                text=f"✅ Running | Completed: {state['completed_count']} | Throughput: {state['throughput']:.2f}/s | Policy: {self.scheduler.policy}"
            )
            
        except Exception as e:
            print(f"Update error: {e}")
        
        self.root.after(500, self.update_ui)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("Starting Multi-Core Load Balancing Scheduler...")
    app = WorkingDashboard()
    app.run()
