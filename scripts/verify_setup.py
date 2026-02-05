#!/usr/bin/env python3
"""
Verification script to check that all components are properly set up.

This script performs basic checks without requiring Isaac Sim to be running.
"""

import os
import sys


def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists and report."""
    if os.path.isdir(dirpath):
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {dirpath}")
        return False


def main():
    """Run verification checks."""
    print("=" * 70)
    print("Unitree G1 Apple Grabbing - Project Verification")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)  # Go up from scripts/
    
    print("Project Structure Checks:")
    print("-" * 70)
    
    # Check directories
    dirs_to_check = [
        ("scripts", "Scripts directory"),
        ("config", "Config directory"),
        ("launch", "Launch directory"),
        ("assets", "Assets directory"),
    ]
    
    for dirname, description in dirs_to_check:
        path = os.path.join(project_root, dirname)
        if not check_directory_exists(path, description):
            all_checks_passed = False
    
    print()
    print("Core Files Checks:")
    print("-" * 70)
    
    # Check files
    files_to_check = [
        ("scripts/simulation.py", "Main simulation script"),
        ("scripts/robot_controller.py", "Robot controller"),
        ("scripts/object_detection.py", "Object detection module"),
        ("config/robot_config.yaml", "Robot configuration"),
        ("config/scene_config.yaml", "Scene configuration"),
        ("launch/g1_manipulation.launch.py", "Launch script"),
        ("requirements.txt", "Requirements file"),
        ("README.md", "README documentation"),
    ]
    
    for filename, description in files_to_check:
        path = os.path.join(project_root, filename)
        if not check_file_exists(path, description):
            all_checks_passed = False
    
    print()
    print("=" * 70)
    
    if all_checks_passed:
        print("✓ All checks passed! Project structure is complete.")
        print()
        print("Next steps:")
        print("1. Install Isaac Sim from NVIDIA Omniverse")
        print("2. Run the simulation:")
        print(f"   cd {project_root}")
        print("   <isaac-sim-path>/python.sh launch/g1_manipulation.launch.py")
    else:
        print("✗ Some checks failed. Please review the missing components above.")
        return 1
    
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
