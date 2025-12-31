# test_resilience.py - Tests for resilience features
# Tests crash recovery, data integrity, and error handling

import unittest
import tempfile
import os
import shutil
import time

from ..core.calculator import ValleyCalculator
from ..core.project import ProjectManager
from ..utils.logging.logger import ResilienceLogger
from ..data.persistence.database import DatabaseManager
from ..core.recovery.error_handlers import (
    resilient_operation,
    error_boundary,
    validate_input,
    get_recovery_manager,
)


class TestResilienceFeatures(unittest.TestCase):
    """Test suite for resilience features."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()

        # Mock database path
        self.db_path = os.path.join(self.test_dir, "test.db")

        # Initialize components with test paths
        self.logger = ResilienceLogger(log_dir=self.test_dir)
        self.db = DatabaseManager(db_path=self.db_path)
        self.calculator = ValleyCalculator()
        self.project_mgr = ProjectManager(projects_dir=self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        # Close database connections
        if hasattr(self.db, "_connection"):
            self.db._connection.close()

        # Remove test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_operations(self):
        """Test basic database operations with resilience."""
        # Test project save and load
        project_data = {
            "project_name": "Test Project",
            "inputs": {"test_input": 42},
            "results": {"test_result": 84},
        }

        # Save project
        project_id = self.project_mgr.save_project(project_data)
        self.assertIsNotNone(project_id)

        # Load project
        loaded_data = self.project_mgr.load_project(project_id)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["project_name"], "Test Project")
        self.assertEqual(loaded_data["inputs"]["test_input"], 42)

    def test_checkpoint_system(self):
        """Test checkpoint creation and recovery."""
        project_id = "test_checkpoint_project"
        test_data = {"checkpoint_test": True, "value": 123}

        # Create checkpoint
        success = self.db.create_checkpoint(project_id, "test_checkpoint", test_data)
        self.assertTrue(success)

        # Retrieve checkpoint
        recovered_data = self.db.restore_from_checkpoint("test_checkpoint")
        self.assertIsNotNone(recovered_data)
        self.assertEqual(recovered_data["checkpoint_test"], True)
        self.assertEqual(recovered_data["value"], 123)

    def test_error_boundary(self):
        """Test error boundary context manager."""
        error_caught = False
        operation_success = False

        @error_boundary("test_operation", recoverable=True)
        def failing_operation():
            nonlocal operation_success
            operation_success = True
            raise ValueError("Test error")

        try:
            failing_operation()
        except Exception:
            error_caught = True

        # Error should be caught and logged, but not re-raised for recoverable operations
        self.assertTrue(operation_success)  # Operation started
        self.assertFalse(error_caught)  # Error was handled gracefully

    def test_resilient_operation_decorator(self):
        """Test resilient operation decorator with retry logic."""
        call_count = 0

        @resilient_operation(retries=2, recoverable=True)
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise ConnectionError("Temporary connection error")
            return "success"

        result = failing_operation()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)  # Should have been called 3 times

    def test_input_validation(self):
        """Test input validation decorators."""

        @validate_input(
            lambda x, name: (
                isinstance(x, (int, float)) and x > 0,
                f"{name} must be positive number",
            )
        )
        def validated_function(value):
            return value * 2

        # Valid input
        result = validated_function(5)
        self.assertEqual(result, 10)

        # Invalid input should raise ValueError
        with self.assertRaises(ValueError):
            validated_function(-1)

    def test_data_integrity(self):
        """Test data integrity checking."""
        test_data = "Test data for integrity check"
        checksum = self.db._calculate_checksum(test_data)

        # Verify checksum
        self.assertTrue(self.db._validate_data_integrity(test_data, checksum))

        # Corrupted data should fail
        self.assertFalse(
            self.db._validate_data_integrity(test_data + "corrupted", checksum)
        )

    def test_recovery_manager(self):
        """Test recovery manager functionality."""
        recovery_mgr = get_recovery_manager()

        # Test error recovery registration
        def test_recovery_handler(error, *args, **kwargs):
            return "recovered"

        recovery_mgr.register_recovery_strategy(ValueError, test_recovery_handler)

        # Verify strategy is registered
        self.assertIn(ValueError, recovery_mgr.recovery_strategies)
        self.assertEqual(
            recovery_mgr.recovery_strategies[ValueError], test_recovery_handler
        )

    def test_performance_logging(self):
        """Test performance logging functionality."""
        time.time()

        # Simulate operation with performance logging
        self.logger.log_performance(
            "test_operation", 0.5, success=True, metadata={"test": True}
        )

        # Check that performance data was recorded
        perf_stats = self.logger.get_performance_stats("test_operation")
        self.assertIn("count", perf_stats)
        self.assertIn("avg_duration", perf_stats)

    def test_project_listing_and_deletion(self):
        """Test project listing and deletion."""
        # Create test projects
        project1_data = {"project_name": "Test Project 1", "inputs": {}, "results": {}}
        project2_data = {"project_name": "Test Project 2", "inputs": {}, "results": {}}

        id1 = self.project_mgr.save_project(project1_data)
        self.project_mgr.save_project(project2_data)

        # List projects
        projects = self.project_mgr.list_projects()
        project_names = [p["name"] for p in projects]

        self.assertIn("Test Project 1", project_names)
        self.assertIn("Test Project 2", project_names)

        # Delete project
        success = self.project_mgr.delete_project(id1)
        self.assertTrue(success)

        # Verify deletion
        projects_after = self.project_mgr.list_projects()
        project_names_after = [p["name"] for p in projects_after]

        self.assertNotIn("Test Project 1", project_names_after)
        self.assertIn("Test Project 2", project_names_after)

    def test_system_health_check(self):
        """Test system health check functionality."""
        health_status = self.project_mgr.get_system_health_status()

        # Should have basic health information
        self.assertIn("database_status", health_status)
        self.assertIn("total_projects", health_status)
        self.assertIn("recovery_ready", health_status)

        # Database should be healthy for new instance
        self.assertEqual(health_status["database_status"], "healthy")

    def test_concurrent_access(self):
        """Test concurrent database access handling."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def worker(worker_id):
            try:
                # Each worker tries to save a project
                project_data = {
                    "project_name": f"Concurrent Test {worker_id}",
                    "inputs": {"worker_id": worker_id},
                    "results": {},
                }

                project_id = self.project_mgr.save_project(project_data)
                results.put((worker_id, project_id))

            except Exception as e:
                errors.put((worker_id, str(e)))

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=10)

        # Check results
        successful_saves = 0
        while not results.empty():
            worker_id, project_id = results.get()
            self.assertIsNotNone(project_id)
            successful_saves += 1

        # Should have at least some successful saves
        self.assertGreater(successful_saves, 0)

        # Errors should be minimal (SQLite handles concurrency well)
        error_count = 0
        while not errors.empty():
            error_count += 1

        self.assertLessEqual(error_count, 2)  # Allow for some race conditions


if __name__ == "__main__":
    unittest.main()
