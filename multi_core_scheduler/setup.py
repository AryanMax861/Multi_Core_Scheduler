from setuptools import setup, find_packages

setup(
    name="multi_core_scheduler",
    version="1.0.0",
    author="Your Name",
    description="Industry-grade Multi-Core Load Balancing Scheduler with ML",
    packages=find_packages(),
    install_requires=[
        'numpy>=1.24.3',
        'pandas>=2.0.3',
        'scikit-learn>=1.3.0',
        'matplotlib>=3.7.2',
        'customtkinter>=5.2.1',
        'pyyaml>=6.0',
        'psutil>=5.9.5',
        'joblib>=1.3.2',
        'colorlog>=6.7.0',
        'pillow>=10.0.0'
    ],
    python_requires='>=3.8',
)