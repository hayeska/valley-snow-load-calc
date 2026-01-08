# test_integration.py - Integration tests for Valley Calculator V2.0

import tempfile
import os
from ..core.calculator import ValleyCalculator
from ..core.project import ProjectManager
from ..core.state import StateManager
from ..calculations.engine import CalculationEngine
from ..core.config import ConfigurationManager


class TestSystemIntegration:
    """Test integration between major system components."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Initialize components
        self.calculator = ValleyCalculator()
        self.project_manager = ProjectManager(self.temp_dir)
        self.state_manager = StateManager()
        self.calculation_engine = CalculationEngine()
        self.config_manager = ConfigurationManager()

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_calculation_workflow(self):
        """Test complete calculation workflow from input to results."""
        # Define test inputs
        test_inputs = {
            "ground_snow_load": 25.0,
            "winter_wind_parameter": 0.3,
            "exposure_factor": 1.0,
            "thermal_factor": 1.0,
            "importance_factor": 1.0,
            "north_roof_pitch": 8.0,
            "west_roof_pitch": 8.0,
            "north_span": 16.0,
            "south_span": 16.0,
            "ew_half_width": 20.0,
            "valley_offset": 16.0,
            "valley_angle": 90.0,
            "dead_load": 15.0,
            "beam_width": 3.5,
            "beam_depth": 9.5,
            "modulus_e": 1600000.0,
            "fb_allowable": 1600.0,
            "fv_allowable": 125.0,
            "deflection_snow_limit": 240.0,
            "deflection_total_limit": 180.0,
            "jack_spacing_inches": 24.0,
            "slippery_roof": False,
        }

        # Update state with inputs
        success = self.state_manager.update_inputs(**test_inputs)
        assert success

        # Verify state was updated
        state = self.state_manager.get_current_state()
        assert state["inputs"]["ground_snow_load"] == 25.0
        assert state["inputs"]["north_roof_pitch"] == 8.0

        # Perform calculation
        results, error = self.calculation_engine.perform_complete_analysis(test_inputs)
        assert error is None
        assert results is not None

        # Update state with results
        from ..core.state import CalculationResults

        calc_results = CalculationResults(**results)
        success = self.state_manager.update_results(calc_results)
        assert success

        # Verify results in state
        state = self.state_manager.get_current_state()
        assert state["results"]["status"] == "completed"

    def test_project_save_load_workflow(self):
        """Test complete project save and load workflow."""
        # Create test project data
        project_data = {
            "project_name": "Test Valley Project",
            "description": "Integration test project",
            "inputs": {
                "ground_snow_load": 30.0,
                "north_roof_pitch": 6.0,
                "west_roof_pitch": 6.0,
                "north_span": 20.0,
                "south_span": 20.0,
                "ew_half_width": 25.0,
            },
            "results": {
                "status": "completed",
                "pf_flat": 21.0,
                "ps_balanced": 16.8,
            },
        }

        # Save project
        project_id = self.project_manager.save_project(project_data)
        assert project_id is not None
        assert isinstance(project_id, str)

        # Load project
        loaded_project = self.project_manager.load_project(project_id)
        assert loaded_project is not None

        # Verify data integrity
        assert loaded_project["project_name"] == "Test Valley Project"
        assert loaded_project["inputs"]["ground_snow_load"] == 30.0
        assert loaded_project["results"]["pf_flat"] == 21.0

    def test_state_persistence_workflow(self):
        """Test state persistence and restoration."""
        # Set up initial state
        self.state_manager.update_inputs(ground_snow_load=35.0, north_roof_pitch=10.0)

        self.state_manager.update_project_metadata(
            project_name="State Test Project", description="Testing state persistence"
        )

        # Get state snapshot
        initial_state = self.state_manager.get_current_state()

        # Modify state
        self.state_manager.update_inputs(north_span=18.0)
        modified_state = self.state_manager.get_current_state()

        # Verify changes
        assert modified_state["inputs"]["north_span"] == 18.0
        assert initial_state["inputs"]["north_span"] != 18.0

        # Restore original state
        success = self.state_manager.restore_state(initial_state)
        assert success

        # Verify restoration
        restored_state = self.state_manager.get_current_state()
        assert restored_state["inputs"]["north_span"] != 18.0
        assert restored_state["project"]["project_name"] == "State Test Project"

    def test_configuration_integration(self):
        """Test configuration system integration."""
        # Test default configuration
        timeout = self.config_manager.get("calculation", "calculation_timeout")
        assert isinstance(timeout, float)
        assert timeout > 0

        # Test configuration update
        self.config_manager.set("calculation", "calculation_timeout", 45.0)
        updated_timeout = self.config_manager.get("calculation", "calculation_timeout")
        assert updated_timeout == 45.0

        # Test configuration save/load
        self.config_manager.save_configuration()

        # Create new config manager to test persistence
        new_config = ConfigurationManager()
        loaded_timeout = new_config.get("calculation", "calculation_timeout")
        assert loaded_timeout == 45.0

    def test_error_handling_integration(self):
        """Test error handling across components."""

        # Test invalid inputs
        invalid_inputs = {
            "ground_snow_load": -10.0,  # Invalid
            "north_roof_pitch": 8.0,
        }

        # Should fail validation
        is_valid, errors = self.calculation_engine.validate_inputs(invalid_inputs)
        assert not is_valid
        assert len(errors) > 0

        # Test with state manager
        success = self.state_manager.update_inputs(**invalid_inputs)
        assert not success

        # Check error state
        state = self.state_manager.get_current_state()
        assert len(state["ui_state"]["error_messages"]) > 0

    def test_undo_redo_functionality(self):
        """Test undo/redo functionality in state management."""
        # Initial state
        self.state_manager.update_inputs(ground_snow_load=25.0)
        initial_state = self.state_manager.get_current_state()

        # Make change 1
        self.state_manager.update_inputs(north_roof_pitch=8.0)
        after_change1 = self.state_manager.get_current_state()

        # Make change 2
        self.state_manager.update_inputs(north_span=16.0)
        after_change2 = self.state_manager.get_current_state()

        # Verify changes
        assert after_change1["inputs"]["north_roof_pitch"] == 8.0
        assert after_change2["inputs"]["north_span"] == 16.0

        # Undo last change
        success = self.state_manager.undo_last_change()
        assert success

        # Verify undo
        after_undo = self.state_manager.get_current_state()
        assert after_undo["inputs"]["north_span"] != 16.0
        assert after_undo["inputs"]["north_roof_pitch"] == 8.0

    def test_performance_monitoring(self):
        """Test performance monitoring integration."""
        # Perform calculation to generate performance data
        inputs = {
            "ground_snow_load": 25.0,
            "north_roof_pitch": 8.0,
            "west_roof_pitch": 8.0,
            "north_span": 16.0,
            "south_span": 16.0,
            "ew_half_width": 20.0,
        }

        results, error = self.calculation_engine.calculate_snow_loads(inputs)
        assert error is None

        # Check that performance was logged (indirect test)
        # In real implementation, we'd check the logger for performance metrics
        assert results is not None

    def test_resource_cleanup(self):
        """Test proper resource cleanup."""
        # Create multiple projects
        project_ids = []
        for i in range(3):
            project_data = {
                "project_name": f"Test Project {i}",
                "inputs": {"ground_snow_load": 25.0 + i},
            }
            project_id = self.project_manager.save_project(project_data)
            project_ids.append(project_id)

        # Verify projects exist
        projects = self.project_manager.list_projects()
        assert len(projects) >= 3

        # Delete projects
        for project_id in project_ids:
            success = self.project_manager.delete_project(project_id)
            assert success

        # Verify projects are deleted
        projects_after = self.project_manager.list_projects()
        initial_count = len(projects) - 3
        assert len(projects_after) == initial_count


class TestEndToEndWorkflows:
    """Test complete end-to-end user workflows."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManager(self.temp_dir)
        self.calculation_engine = CalculationEngine()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_typical_engineering_workflow(self):
        """Test a typical engineering workflow."""
        # Step 1: Define project
        project_data = {
            "project_name": "Residential Valley Roof",
            "description": "Two-story residential with valley roof",
            "location": "Denver, CO",
        }

        project_id = self.project_manager.save_project(project_data)

        # Step 2: Input building parameters
        building_inputs = {
            "ground_snow_load": 25.0,  # Denver ground snow load
            "winter_wind_parameter": 0.3,
            "exposure_factor": 1.0,
            "thermal_factor": 1.1,  # Warm roof
            "importance_factor": 1.0,
            "north_roof_pitch": 8.0,  # 8/12 pitch
            "west_roof_pitch": 8.0,
            "north_span": 24.0,  # 24 ft span
            "south_span": 24.0,
            "ew_half_width": 30.0,  # 60 ft total width
            "valley_offset": 24.0,
            "valley_angle": 90.0,
            "dead_load": 15.0,  # psf
        }

        # Step 3: Run calculations
        results, error = self.calculation_engine.perform_complete_analysis(
            building_inputs
        )
        assert error is None
        assert results["status"] == "completed"

        # Step 4: Update project with results
        updated_project = dict(project_data)
        updated_project["inputs"] = building_inputs
        updated_project["results"] = results

        self.project_manager.save_project(updated_project, project_id)

        # Step 5: Verify final project
        final_project = self.project_manager.load_project(project_id)
        assert final_project["project_name"] == "Residential Valley Roof"
        assert "inputs" in final_project
        assert "results" in final_project
        assert final_project["results"]["status"] == "completed"

        # Step 6: Export results
        export_path = self.project_manager.export_results(results, "json")
        assert os.path.exists(export_path)

        # Verify exported data
        with open(export_path, "r") as f:
            exported_data = f.read()
            assert "Residential Valley Roof" in exported_data
            assert "completed" in exported_data

    def test_design_iteration_workflow(self):
        """Test iterative design workflow."""
        base_inputs = {
            "ground_snow_load": 30.0,
            "north_roof_pitch": 6.0,
            "west_roof_pitch": 6.0,
            "north_span": 20.0,
            "south_span": 20.0,
            "ew_half_width": 25.0,
            "dead_load": 12.0,
        }

        # Iteration 1: Initial design
        design1_inputs = dict(base_inputs)
        design1_inputs.update(
            {
                "beam_width": 3.5,
                "beam_depth": 9.25,
            }
        )

        results1, error1 = self.calculation_engine.perform_complete_analysis(
            design1_inputs
        )
        assert error1 is None

        # Iteration 2: Optimize beam size
        design2_inputs = dict(design1_inputs)
        design2_inputs.update(
            {
                "beam_depth": 11.875,  # Larger beam
            }
        )

        results2, error2 = self.calculation_engine.perform_complete_analysis(
            design2_inputs
        )
        assert error2 is None

        # Verify design improvement
        # (In real implementation, we'd check deflection and stress values)
        assert results1["beam_analysis"] is not None
        assert results2["beam_analysis"] is not None

    def test_batch_processing_workflow(self):
        """Test batch processing of multiple load cases."""
        # Define multiple load cases
        load_cases = [
            {"name": "Normal", "ground_snow_load": 25.0, "importance_factor": 1.0},
            {"name": "Heavy Snow", "ground_snow_load": 35.0, "importance_factor": 1.0},
            {"name": "Seismic", "ground_snow_load": 25.0, "importance_factor": 1.25},
        ]

        base_inputs = {
            "winter_wind_parameter": 0.3,
            "exposure_factor": 1.0,
            "thermal_factor": 1.0,
            "north_roof_pitch": 8.0,
            "west_roof_pitch": 8.0,
            "north_span": 20.0,
            "south_span": 20.0,
            "ew_half_width": 24.0,
            "valley_offset": 20.0,
            "dead_load": 15.0,
            "beam_width": 3.5,
            "beam_depth": 9.5,
        }

        results_batch = {}

        # Process each load case
        for load_case in load_cases:
            case_inputs = dict(base_inputs)
            case_inputs.update(load_case)

            results, error = self.calculation_engine.perform_complete_analysis(
                case_inputs
            )
            assert error is None

            results_batch[load_case["name"]] = results

        # Verify batch results
        assert len(results_batch) == 3
        assert "Normal" in results_batch
        assert "Heavy Snow" in results_batch
        assert "Seismic" in results_batch

        # Verify load case differences
        normal_load = results_batch["Normal"]["snow_loads"]["pf_flat"]
        heavy_load = results_batch["Heavy Snow"]["snow_loads"]["pf_flat"]
        seismic_load = results_batch["Seismic"]["snow_loads"]["pf_flat"]

        assert heavy_load > normal_load  # Higher ground snow
        assert seismic_load > normal_load  # Higher importance factor
