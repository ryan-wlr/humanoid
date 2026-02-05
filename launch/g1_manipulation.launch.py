#!/usr/bin/env python3
"""
Launch script for Unitree G1 Apple Grabbing simulation in Isaac Sim.

This script provides an easy way to launch the simulation with proper
configuration and error handling.

Usage:
    python launch/g1_manipulation.launch.py
    
Or from Isaac Sim:
    ./python.sh launch/g1_manipulation.launch.py
"""

import sys
import os

# Add scripts directory to path
script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, script_dir)

import argparse


def main():
    """Main launch function."""
    parser = argparse.ArgumentParser(
        description="Launch Unitree G1 Apple Grabbing simulation"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run simulation in headless mode (no GUI)",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Unitree G1 Apple Grabbing Simulation")
    print("=" * 60)
    print()
    print("Launching Isaac Sim...")
    print(f"Headless mode: {args.headless}")
    print()
    
    # Import and run simulation
    try:
        from simulation import main as run_simulation
        run_simulation()
    except ImportError as e:
        print(f"Error: Could not import simulation module: {e}")
        print()
        print("Make sure Isaac Sim is properly installed and configured.")
        print("Required: NVIDIA Omniverse Isaac Sim")
        print()
        print("Installation instructions:")
        print("1. Download Omniverse Launcher from NVIDIA")
        print("2. Install Isaac Sim through Omniverse")
        print("3. Run this script using Isaac Sim's Python:")
        print("   ~/.local/share/ov/pkg/isaac_sim-*/python.sh launch/g1_manipulation.launch.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
