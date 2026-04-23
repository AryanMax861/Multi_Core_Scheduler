import customtkinter as ctk
from tkinter import ttk
import tkinter as tk

class ProcessCard(ctk.CTkFrame):
    """Card widget for displaying process information"""
    
    def __init__(self, parent, process, **kwargs):
        super().__init__(parent, **kwargs)
        self.process = process
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the process card UI"""
        self.configure(fg_color="#2b2b2b", corner_radius=10)
        
        # Process name and PID
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text=f"{self.process.name}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_frame,
            text=f"PID: {self.process.pid}",
            font=ctk.CTkFont(size=10)
        ).pack(side="right")
        
        # Process details
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # Progress bar for burst time
        burst_percent = (self.process.remaining_time / self.process.burst_time) * 100 if self.process.burst_time > 0 else 0
        
        progress_bar = ctk.CTkProgressBar(details_frame, height=10)
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(burst_percent / 100)
        
        # Metrics
        metrics_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        metrics_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            metrics_frame,
            text=f"⏱ Remaining: {self.process.remaining_time:.0f}ms",
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            metrics_frame,
            text=f"⭐ Priority: {self.process.priority}",
            font=ctk.CTkFont(size=10)
        ).pack(side="right", padx=5)
        
        # State indicator
        state_colors = {
            "Running": "#2ecc71",
            "Ready": "#3498db",
            "Waiting": "#f39c12",
            "Completed": "#95a5a6"
        }
        
        state_frame = ctk.CTkFrame(self, fg_color="transparent")
        state_frame.pack(fill="x", padx=10, pady=5)
        
        indicator = ctk.CTkFrame(
            state_frame,
            width=10,
            height=10,
            fg_color=state_colors.get(self.process.state.value, "#ecf0f1"),
            corner_radius=5
        )
        indicator.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            state_frame,
            text=f"State: {self.process.state.value}",
            font=ctk.CTkFont(size=10)
        ).pack(side="left")

class CoreWidget(ctk.CTkFrame):
    """Widget for displaying core information with animation"""
    
    def __init__(self, parent, core_id, **kwargs):
        super().__init__(parent, **kwargs)
        self.core_id = core_id
        self.utilization = 0
        self.setup_ui()
    
    def setup_ui(self):
        """Setup core widget UI"""
        self.configure(fg_color="#1e1e1e", corner_radius=10)
        
        # Core header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text=f"CPU Core {self.core_id}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Utilization bar
        self.bar_frame = ctk.CTkFrame(self, height=30)
        self.bar_frame.pack(fill="x", padx=10, pady=5)
        self.bar_frame.pack_propagate(False)
        
        self.util_bar = ctk.CTkProgressBar(self.bar_frame, height=25)
        self.util_bar.pack(fill="x")
        self.util_bar.set(0)
        
        # Temperature gauge
        temp_frame = ctk.CTkFrame(self, fg_color="transparent")
        temp_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(temp_frame, text="Temperature:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.temp_label = ctk.CTkLabel(temp_frame, text="40°C", font=ctk.CTkFont(size=11, weight="bold"))
        self.temp_label.pack(side="left", padx=5)
    
    def update_utilization(self, utilization, temperature):
        """Update core utilization and temperature"""
        self.utilization = utilization
        self.util_bar.set(utilization)
        
        # Change color based on utilization
        if utilization > 0.8:
            self.util_bar.configure(progress_color="#e74c3c")
        elif utilization > 0.5:
            self.util_bar.configure(progress_color="#f39c12")
        else:
            self.util_bar.configure(progress_color="#2ecc71")
        
        self.temp_label.configure(text=f"{temperature:.1f}°C")
        
        # Change bar frame color based on temperature
        if temperature > 80:
            self.configure(fg_color="#3a1a1a")
        elif temperature > 60:
            self.configure(fg_color="#3a2a1a")
        else:
            self.configure(fg_color="#1e1e1e")