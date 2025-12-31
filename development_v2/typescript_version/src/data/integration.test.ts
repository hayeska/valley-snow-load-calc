// Integration tests for complete data persistence workflow
// Tests real database operations, error recovery, and data integrity

import { DatabaseManager } from './database';
import { getLogger } from '../utils/logger';
import { getCheckpointManager } from '../core/checkpointSystem';
import { ValleySnowLoadCalculator } from '../core/calculator';
import { ProjectData } from '../types';
import fs from 'fs';
import path from 'path';
import os from 'os';

// Use real implementations for integration tests
jest.unmock('./database');
jest.unmock('../utils/logger');
jest.unmock('../core/checkpointSystem');
jest.unmock('../core/calculator');

describe('Data Persistence Integration Tests', () => {
  let db: DatabaseManager;
  let calculator: ValleySnowLoadCalculator;
  let checkpointManager: any;
  let testDbPath: string;
  let testProject: ProjectData;

  beforeEach(async () => {
    // Create unique test database
    const tempDir = os.tmpdir();
    testDbPath = path.join(tempDir, `integration_test_${Date.now()}_${Math.random()}.db`);

    // Ensure clean state
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    // Initialize real components
    db = new DatabaseManager(testDbPath);
    await db.initialize();

    checkpointManager = getCheckpointManager();
    await checkpointManager.initialize();

    calculator = new ValleySnowLoadCalculator();
    await calculator.initialize();

    // Store global references for error recovery
    (global as any).database = db;
    (global as any).checkpointManager = checkpointManager;

    testProject = createTestProjectData();
  });

  afterEach(async () => {
    try {
      await calculator.shutdown();
      await db.close();
    } catch (error) {
      // Ignore cleanup errors
    }

    // Clean up test database
    try {
      if (fs.existsSync(testDbPath)) {
        fs.unlinkSync(testDbPath);
      }
    } catch (error) {
      // Ignore cleanup errors
    }

    // Reset global state
    delete (global as any).database;
    delete (global as any).checkpointManager;
  });

  describe('Complete CRUD Workflow', () => {
    test('should complete full project lifecycle', async () => {
      // 1. Create project
      const projectId = await calculator.createProject(testProject.name, testProject.description);
      expect(typeof projectId).toBe('string');

      // 2. Load and verify project
      const loadedProject = await calculator.loadProject(projectId);
      expect(loadedProject?.name).toBe(testProject.name);
      expect(loadedProject?.description).toBe(testProject.description);

      // 3. Update project geometry
      const updatedGeometry = {
        ...loadedProject!.geometry,
        roofPitchN: 12,
        northSpan: 25
      };

      const updatedProject = await calculator.updateGeometry(projectId, updatedGeometry);
      expect(updatedProject.geometry.roofPitchN).toBe(12);
      expect(updatedProject.geometry.northSpan).toBe(25);

      // 4. Update inputs and calculate results
      const updatedInputs = {
        ...loadedProject!.inputs,
        groundSnowLoad: 45
      };

      const calculatedProject = await calculator.updateInputs(projectId, updatedInputs);
      expect(calculatedProject.inputs.groundSnowLoad).toBe(45);
      expect(calculatedProject.results.balancedLoads.northRoof).toBeGreaterThan(0);

      // 5. Verify checkpoints were created
      const recoveryOptions = await calculator.getRecoveryOptions(projectId);
      expect(recoveryOptions.length).toBeGreaterThan(0);

      // 6. Save explicitly
      await calculator.saveProject(calculatedProject);

      // 7. Delete project
      const deleteSuccess = await db.deleteProject(projectId);
      expect(deleteSuccess).toBe(true);

      // 8. Verify project is gone
      const deletedProject = await calculator.loadProject(projectId);
      expect(deletedProject).toBeNull();
    });

    test('should maintain data integrity through operations', async () => {
      // Create and save project
      const projectId = await calculator.createProject('Integrity Test', 'Testing data integrity');

      // Load project and verify initial integrity
      let project = await calculator.loadProject(projectId);
      expect(project).toBeDefined();

      // Perform multiple updates
      for (let i = 0; i < 5; i++) {
        const updatedInputs = {
          ...project!.inputs,
          groundSnowLoad: 30 + i * 5
        };

        project = await calculator.updateInputs(projectId, updatedInputs);
        expect(project!.inputs.groundSnowLoad).toBe(30 + i * 5);

        // Verify results are recalculated correctly
        expect(project!.results.balancedLoads.northRoof).toBeGreaterThan(0);
      }

      // Final load and verify all changes persisted
      const finalProject = await calculator.loadProject(projectId);
      expect(finalProject?.inputs.groundSnowLoad).toBe(50); // 30 + 4 * 5

      // Check that we have recovery options
      const recoveryOptions = await calculator.getRecoveryOptions(projectId);
      expect(recoveryOptions.length).toBeGreaterThan(1); // At least initial + updates
    });
  });

  describe('Crash Simulation and Recovery', () => {
    test('should recover from database disconnection', async () => {
      // Create project
      const projectId = await calculator.createProject('Recovery Test');

      // Simulate database disconnection by closing connection
      await db.close();

      // Attempt operation that should fail
      await expect(calculator.loadProject(projectId)).rejects.toThrow();

      // Reinitialize and verify recovery
      await db.initialize();
      const recoveredProject = await calculator.loadProject(projectId);
      expect(recoveredProject?.name).toBe('Recovery Test');
    });

    test('should handle checkpoint recovery', async () => {
      // Create project and make changes
      const projectId = await calculator.createProject('Checkpoint Recovery Test');

      // Make several changes to create checkpoints
      await calculator.updateGeometry(projectId, {
        ...testProject.geometry,
        roofPitchN: 10
      });

      await calculator.updateInputs(projectId, {
        ...testProject.inputs,
        groundSnowLoad: 40
      });

      // Simulate data corruption by manually modifying database
      await db['run']('UPDATE projects SET data = ? WHERE id = ?',
        ['{"corrupted": "data"}', projectId]);

      // Attempt to load should fail with corruption
      await expect(calculator.loadProject(projectId)).rejects.toThrow();

      // Recovery should work via checkpoint
      const recoveryOptions = await calculator.getRecoveryOptions(projectId);
      expect(recoveryOptions.length).toBeGreaterThan(0);

      // Find and restore from latest checkpoint
      const latestCheckpoint = recoveryOptions.find(opt => opt.type === 'checkpoint');
      if (latestCheckpoint) {
        const recovered = await calculator.recoverFromCheckpoint(latestCheckpoint.id);
        expect(recovered).toBeDefined();
        expect(recovered?.inputs.groundSnowLoad).toBe(40);
      }
    });

    test('should handle concurrent operations safely', async () => {
      const operationCount = 10;
      const operations = Array(operationCount).fill(null).map(async (_, i) => {
        const projectId = `concurrent_test_${i}`;
        await calculator.createProject(`Concurrent Project ${i}`, `Test ${i}`);

        // Perform updates
        const project = await calculator.loadProject(projectId);
        if (project) {
          await calculator.updateInputs(projectId, {
            ...project.inputs,
            groundSnowLoad: 25 + i
          });
        }

        return projectId;
      });

      // Execute all operations concurrently
      const results = await Promise.allSettled(operations);

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;
      const rejected = results.filter(r => r.status === 'rejected').length;

      expect(fulfilled + rejected).toBe(operationCount);
      expect(fulfilled).toBeGreaterThan(operationCount * 0.8); // At least 80% success

      // Verify final state of successful operations
      for (let i = 0; i < operationCount; i++) {
        const result = results[i];
        if (result.status === 'fulfilled') {
          const projectId = result.value;
          const project = await calculator.loadProject(projectId);
          expect(project).toBeDefined();
        }
      }
    });

    test('should maintain data consistency during failures', async () => {
      // Create project
      const projectId = await calculator.createProject('Consistency Test');

      // Get initial state
      const initialProject = await calculator.loadProject(projectId);
      const initialLoad = initialProject!.inputs.groundSnowLoad;

      // Attempt multiple updates, some may fail
      const updates = [35, 40, 45, 50];
      const updatePromises = updates.map(snowLoad =>
        calculator.updateInputs(projectId, {
          ...initialProject!.inputs,
          groundSnowLoad: snowLoad
        }).catch(() => null) // Ignore failures for this test
      );

      await Promise.allSettled(updatePromises);

      // Load final state
      const finalProject = await calculator.loadProject(projectId);

      // Final state should be one of the attempted updates or initial
      const finalLoad = finalProject!.inputs.groundSnowLoad;
      const validStates = [initialLoad, ...updates];

      expect(validStates).toContain(finalLoad);

      // Data should not be corrupted
      expect(typeof finalProject!.name).toBe('string');
      expect(finalProject!.geometry).toBeDefined();
    });
  });

  describe('Error Scenarios and Edge Cases', () => {
    test('should handle invalid project IDs', async () => {
      const invalidIds = ['', null, undefined, '   ', 'invalid-id-with-spaces and symbols!@#'];

      for (const invalidId of invalidIds) {
        await expect(calculator.loadProject(invalidId as string)).rejects.toThrow();
      }
    });

    test('should handle malformed geometry data', async () => {
      const projectId = await calculator.createProject('Malformed Geometry Test');

      const invalidGeometries = [
        { ...testProject.geometry, roofPitchN: -10 }, // Negative pitch
        { ...testProject.geometry, valleyAngle: 200 }, // Invalid angle
        { ...testProject.geometry, northSpan: 0 }, // Zero span
        { ...testProject.geometry, ewHalfWidth: -5 } // Negative width
      ];

      for (const invalidGeometry of invalidGeometries) {
        await expect(calculator.updateGeometry(projectId, invalidGeometry)).rejects.toThrow();
      }

      // Verify project is still loadable after failed updates
      const project = await calculator.loadProject(projectId);
      expect(project).toBeDefined();
    });

    test('should handle invalid input parameters', async () => {
      const projectId = await calculator.createProject('Invalid Input Test');

      const invalidInputs = [
        { ...testProject.inputs, groundSnowLoad: -10 }, // Negative snow load
        { ...testProject.inputs, importanceFactor: 2.5 }, // Too high importance
        { ...testProject.inputs, thermalFactor: -0.5 }, // Negative thermal
        { ...testProject.inputs, winterWindParameter: 2.0 } // Too high wind parameter
      ];

      for (const invalidInput of invalidInputs) {
        await expect(calculator.updateInputs(projectId, invalidInput)).rejects.toThrow();
      }
    });

    test('should handle database disk full scenarios', async () => {
      // Create project
      const projectId = await calculator.createProject('Disk Full Test');

      // Simulate disk full by mocking database operations to fail
      const originalRun = db['run'].bind(db);
      db['run'] = jest.fn().mockRejectedValue(new Error('disk is full'));

      // Operations should fail gracefully
      await expect(calculator.saveProject(await calculator.loadProject(projectId)!)).rejects.toThrow('disk is full');

      // Restore original method
      db['run'] = originalRun;
    });

    test('should handle network timeouts', async () => {
      // Create project
      const projectId = await calculator.createProject('Timeout Test');

      // Simulate timeout by delaying database operations
      const originalGet = db['get'].bind(db);
      db['get'] = jest.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(null), 2000))
      );

      // Load should still work (timeout is handled at decorator level)
      const project = await calculator.loadProject(projectId);
      expect(project).toBeDefined();

      // Restore original method
      db['get'] = originalGet;
    });
  });

  describe('Performance and Load Testing', () => {
    test('should handle bulk project operations', async () => {
      const projectCount = 20;
      const startTime = Date.now();

      // Create multiple projects
      const createPromises = Array(projectCount).fill(null).map((_, i) =>
        calculator.createProject(`Bulk Project ${i}`, `Bulk test project ${i}`)
      );

      const projectIds = await Promise.all(createPromises);
      const createDuration = Date.now() - startTime;

      expect(projectIds.length).toBe(projectCount);
      expect(createDuration).toBeLessThan(10000); // Should complete within 10 seconds

      // Load all projects
      const loadStartTime = Date.now();
      const loadPromises = projectIds.map(id => calculator.loadProject(id));
      const loadedProjects = await Promise.all(loadPromises);
      const loadDuration = Date.now() - loadStartTime;

      expect(loadedProjects.length).toBe(projectCount);
      expect(loadDuration).toBeLessThan(5000); // Should load within 5 seconds

      // Update all projects
      const updateStartTime = Date.now();
      const updatePromises = loadedProjects.map(project =>
        calculator.updateInputs(project!.id, {
          ...project!.inputs,
          groundSnowLoad: project!.inputs.groundSnowLoad + 10
        })
      );

      await Promise.all(updatePromises);
      const updateDuration = Date.now() - updateStartTime;

      expect(updateDuration).toBeLessThan(15000); // Should update within 15 seconds
    });

    test('should maintain performance under sustained load', async () => {
      const operationCount = 50;
      const operations: (() => Promise<any>)[] = [];

      // Mix of different operations
      for (let i = 0; i < operationCount; i++) {
        if (i % 4 === 0) {
          operations.push(() => calculator.createProject(`Perf Test ${i}`));
        } else if (i % 4 === 1) {
          operations.push(() => calculator.listProjects());
        } else if (i % 4 === 2) {
          operations.push(() => calculator.getSystemHealth());
        } else {
          operations.push(() => {
            const testProject = createTestProjectData();
            return db.saveProject(testProject);
          });
        }
      }

      const startTime = Date.now();
      const results = await Promise.allSettled(operations);
      const duration = Date.now() - startTime;

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;
      const successRate = fulfilled / operationCount;

      expect(successRate).toBeGreaterThan(0.9); // At least 90% success rate
      expect(duration).toBeLessThan(30000); // Should complete within 30 seconds

      console.log(`Load test: ${fulfilled}/${operationCount} operations succeeded in ${duration}ms`);
    });

    test('should handle memory pressure gracefully', async () => {
      // Create many projects with large data
      const largeProjectCount = 10;
      const largeProjects: ProjectData[] = [];

      for (let i = 0; i < largeProjectCount; i++) {
        const largeProject = {
          ...testProject,
          id: `large_test_${i}`,
          name: `Large Test Project ${i}`,
          // Add large description to increase data size
          description: 'x'.repeat(10000) // 10KB of data
        };
        largeProjects.push(largeProject);
      }

      // Save large projects
      const savePromises = largeProjects.map(project => db.saveProject(project));
      const saveResults = await Promise.allSettled(savePromises);

      const saveSuccess = saveResults.filter(r => r.status === 'fulfilled').length;
      expect(saveSuccess).toBe(largeProjectCount);

      // Load and verify large projects
      const loadPromises = largeProjects.map(project => calculator.loadProject(project.id));
      const loadResults = await Promise.allSettled(loadPromises);

      const loadSuccess = loadResults.filter(r => r.status === 'fulfilled').length;
      expect(loadSuccess).toBe(largeProjectCount);

      // Verify data integrity
      for (const result of loadResults) {
        if (result.status === 'fulfilled') {
          const project = result.value;
          expect(project?.description?.length).toBe(10000);
        }
      }
    });
  });

  describe('System Health and Monitoring', () => {
    test('should provide accurate system health metrics', async () => {
      // Create some test data
      await calculator.createProject('Health Test 1');
      await calculator.createProject('Health Test 2');

      const health = await calculator.getSystemHealth();

      expect(health.databaseStatus).toBe('healthy');
      expect(health.totalProjects).toBeGreaterThanOrEqual(2);
      expect(typeof health.uptime).toBe('number');
      expect(health.uptime).toBeGreaterThan(0);
      expect(typeof health.recoveryReady).toBe('boolean');
    });

    test('should detect database issues', async () => {
      // Close database to simulate issues
      await db.close();

      const health = await calculator.getSystemHealth();

      // Health check should detect the issue
      expect(health.databaseStatus).toBe('error');
      expect(health.recoveryReady).toBe(false);
    });

    test('should track error metrics', async () => {
      const logger = getLogger();

      // Simulate some errors
      logger.logError(new Error('Test error 1'), { operation: 'test' });
      logger.logError(new Error('Test error 2'), { operation: 'test' });
      logger.logError(new Error('Test error 1'), { operation: 'test' }); // Duplicate

      const errorSummary = logger.getErrorSummary();

      expect(errorSummary.totalErrors).toBeGreaterThanOrEqual(3);
      expect(errorSummary.mostCommonError).toBeDefined();
    });

    test('should provide performance metrics', async () => {
      const logger = getLogger();

      // Simulate some performance data
      logger.logPerformance('test_operation', 100, true);
      logger.logPerformance('test_operation', 150, true);
      logger.logPerformance('test_operation', 200, false);

      const perfStats = logger.getPerformanceStats('test_operation');

      expect(perfStats.count).toBe(3);
      expect(perfStats.avgDuration).toBe(150);
      expect(perfStats.successRate).toBe(2/3);
    });
  });
});

// Helper function to create test project data
function createTestProjectData(): ProjectData {
  return {
    id: `test_project_${Date.now()}_${Math.random()}`,
    name: 'Integration Test Valley Project',
    description: 'Test project for integration testing',
    geometry: {
      roofPitchN: 8,
      roofPitchW: 10,
      northSpan: 20,
      southSpan: 18,
      ewHalfWidth: 45,
      valleyOffset: 15,
      valleyAngle: 90
    },
    inputs: {
      groundSnowLoad: 35,
      importanceFactor: 1.1,
      exposureFactor: 1.0,
      thermalFactor: 0.9,
      winterWindParameter: 0.4
    },
    results: {
      balancedLoads: { northRoof: 38.5, westRoof: 38.5 },
      unbalancedLoads: { northRoof: 42.35, westRoof: 42.35 },
      driftLoads: { leeSide: 24.5, windwardSide: 10.5 },
      valleyLoads: { horizontalLoad: 46.75, verticalLoad: 0 }
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    version: '2.0.0',
    checksum: '' // Will be calculated during save
  };
}
