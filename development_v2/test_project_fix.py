#!/usr/bin/env python3
"""Test the project management fix"""

from valley_calculator.core.project import ProjectManager

project_mgr = ProjectManager()
test_project = {
    "project_name": "Test Project",
    "description": "Testing the fix",
    "inputs": {"test": "data"},
}

print("Attempting to save project...")
project_id = project_mgr.save_project(test_project)
if project_id:
    print(f"SUCCESS: Project saved with ID: {project_id}")

    # Test loading
    loaded = project_mgr.load_project(project_id)
    if loaded:
        print("SUCCESS: Project loaded successfully")
        print(f'Project name: {loaded.get("project_name")}')
    else:
        print("FAILED: Could not load project")
else:
    print("FAILED: Could not save project")
