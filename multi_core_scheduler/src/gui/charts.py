import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import List, Dict
import customtkinter as ctk

class RealTimeChart:
    def __init__(self, parent, title="Real-Time Chart", height=400, width=600):
        self.parent = parent
        self.title = title
        
        # Create figure
        self.fig = Figure(figsize=(width/100, height/100), dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.set_title(title, color='white', fontsize=12)
        self.ax.tick_params(colors='white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Data storage
        self.data_series = {}
        self.time_data = []
        
    def add_series(self, name: str, color: str = None):
        """Add a new data series"""
        if color is None:
            color = plt.cm.tab10(len(self.data_series) % 10)
        self.data_series[name] = {
            'data': [],
            'color': color,
            'line': None
        }
    
    def update_data(self, name: str, value: float):
        """Update data for a series"""
        if name not in self.data_series:
            self.add_series(name)
        
        self.data_series[name]['data'].append(value)
        
        # Keep only last 50 points
        if len(self.data_series[name]['data']) > 50:
            self.data_series[name]['data'].pop(0)
    
    def update_time(self, time_value: float):
        """Update time axis"""
        self.time_data.append(time_value)
        if len(self.time_data) > 50:
            self.time_data.pop(0)
    
    def refresh(self):
        """Refresh the chart"""
        self.ax.clear()
        
        for name, series in self.data_series.items():
            if series['data']:
                self.ax.plot(
                    self.time_data[-len(series['data']):],
                    series['data'],
                    label=name,
                    color=series['color'],
                    linewidth=2
                )
        
        self.ax.set_title(self.title, color='white', fontsize=12)
        self.ax.set_xlabel("Time (s)", color='white')
        self.ax.set_ylabel("Value", color='white')
        self.ax.tick_params(colors='white')
        self.ax.legend(loc='upper right', facecolor='#2b2b2b', labelcolor='white')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#2b2b2b')
        
        self.canvas.draw()

class GaugeWidget(ctk.CTkFrame):
    """Circular gauge widget for metrics display"""
    
    def __init__(self, parent, title="Gauge", min_value=0, max_value=100, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = 0
        
        # Create figure
        self.fig = Figure(figsize=(2, 2), dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111, projection='polar')
        self.ax.set_facecolor('#2b2b2b')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Title label
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=10))
        self.title_label.pack(pady=(5, 0))
        
        # Value label
        self.value_label = ctk.CTkLabel(self, text="0", font=ctk.CTkFont(size=16, weight="bold"))
        self.value_label.pack()
        
    def update_value(self, value):
        """Update gauge value"""
        self.current_value = value
        self.value_label.configure(text=f"{value:.1f}")
        
        # Update gauge
        self.ax.clear()
        
        # Normalize value to angle (0 to 2π)
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        angle = normalized * 2 * np.pi
        
        # Draw gauge
        self.ax.barh(0, angle, color='#2ecc71', alpha=0.8)
        self.ax.set_theta_zero_location('N')
        self.ax.set_theta_direction(-1)
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_ylim(0, 1)
        
        self.canvas.draw()