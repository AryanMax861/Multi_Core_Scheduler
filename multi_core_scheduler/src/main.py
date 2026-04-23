import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_core_scheduler.src.gui.dashboard_complete import ModernDashboard

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     Multi-Core Load Balancing Scheduler - Industry Edition   ║
    ║                      Version 1.0.0                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    app = ModernDashboard()
    app.run()