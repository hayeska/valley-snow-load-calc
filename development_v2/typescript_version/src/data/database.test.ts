// Comprehensive Jest tests for SQLite database persistence layer
// Tests save/load operations, error scenarios, crash simulations, and data integrity

import { DatabaseManager } from './database';
import { ProjectData } from '../types';
import { getLogger } from '../utils/logger';
import fs from 'fs';
import path from 'path';
import os from 'os';

// Mock the logger to avoid actual logging during tests
jest.mock('../utils/logger');
const mockLogger = {
  logError: jest.fn(),
  logPerformance: jest.fn(),
  logDatabaseOperation: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};
(getLogger as jest.Mock).mockReturnValue(mockLogger);

describe('DatabaseManager - Comprehensive Data Persistence Tests', () => {
  let db: DatabaseManager;
  let testDbPath: string;
  let testData: ProjectData;

  beforeEach(async () => {
    // Create unique test database path
    const tempDir = os.tmpdir();
    testDbPath = path.join(tempDir, `test_valley_calc_${Date.now()}_${Math.random()}.db`);

    // Ensure clean state
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    db = new DatabaseManager(testDbPath);
    testData = createTestProjectData();

    // Reset mocks
    jest.clearAllMocks();
  });

  afterEach(async () => {
    try {
      await db.close();
    } catch (error) {
      // Ignore close errors in cleanup
    }

    // Clean up test database
    try {
      if (fs.existsSync(testDbPath)) {
        fs.unlinkSync(testDbPath);
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('Initialization and Setup', () => {
    test('should initialize database successfully', async () => {
      await expect(db.initialize()).resolves.not.toThrow();
      expect(mockLogger.logPerformance).toHaveBeenCalledWith(
        'database_init',
        expect.any(Number),
        true,
        expect.any(Object)
      );
    });

    test('should handle initialization errors gracefully', async () => {
      // Mock fs.mkdirSync to throw error
      const originalMkdirSync = fs.mkdirSync;
      fs.mkdirSync = jest.fn().mockImplementation(() => {
        throw new Error('Permission denied');
      });

      const dbWithBadPath = new DatabaseManager('/invalid/path/test.db');

      await expect(dbWithBadPath.initialize()).rejects.toThrow('Permission denied');
      expect(mockLogger.logError).toHaveBeenCalled();

      // Restore original function
      fs.mkdirSync = originalMkdirSync;
    });

    test('should create all required tables', async () => {
      await db.initialize();

      // Verify tables exist by attempting operations
      const result = await db['get']('SELECT name FROM sqlite_master WHERE type="table"');
      expect(result).toBeDefined();
    });

    test('should handle database corruption gracefully', async () => {
      // Create database then corrupt it
      await db.initialize();

      // Close and manually corrupt the file
      await db.close();

      // Write invalid data to corrupt the database
      fs.writeFileSync(testDbPath, 'corrupted data');

      // Try to reinitialize - should attempt recovery
      const freshDb = new DatabaseManager(testDbPath);
      await expect(freshDb.initialize()).rejects.toThrow();

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({ operation: 'database_init' }),
        false
      );

      await freshDb.close();
    });
  });

  describe('Project Save Operations', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should save project successfully', async () => {
      const projectId = await db.saveProject(testData);

      expect(typeof projectId).toBe('string');
      expect(projectId.length).toBeGreaterThan(0);
      expect(mockLogger.logDatabaseOperation).toHaveBeenCalledWith(
        'save_project',
        true,
        expect.any(Number),
        expect.objectContaining({ projectId })
      );
    });

    test('should update existing project', async () => {
      // Save initial project
      const projectId = await db.saveProject(testData);

      // Modify and save again
      const updatedData = { ...testData, name: 'Updated Project Name' };
      const updatedId = await db.saveProject(updatedData);

      expect(updatedId).toBe(projectId);

      // Verify update
      const loaded = await db.loadProject(projectId);
      expect(loaded?.name).toBe('Updated Project Name');
    });

    test('should handle save with data integrity verification', async () => {
      const projectId = await db.saveProject(testData);

      // Load and verify checksum
      const loaded = await db.loadProject(projectId);
      expect(loaded).toBeDefined();
      expect(loaded?.checksum).toBeDefined();
    });

    test('should reject invalid project data', async () => {
      const invalidData = { ...testData, id: '' }; // Invalid empty ID

      await expect(db.saveProject(invalidData as any)).rejects.toThrow();
      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should handle concurrent save operations', async () => {
      const savePromises = Array(5).fill(null).map((_, i) =>
        db.saveProject({
          ...testData,
          id: `concurrent-project-${i}`,
          name: `Concurrent Project ${i}`
        })
      );

      const results = await Promise.allSettled(savePromises);

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;
      const rejected = results.filter(r => r.status === 'rejected').length;

      expect(fulfilled + rejected).toBe(5);
      expect(fulfilled).toBeGreaterThan(0); // At least some should succeed

      // SQLite should handle concurrency reasonably well
      expect(rejected).toBeLessThan(3); // Allow some race conditions
    });
  });

  describe('Project Load Operations', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should load project successfully', async () => {
      const saveId = await db.saveProject(testData);
      const loaded = await db.loadProject(saveId);

      expect(loaded).toBeDefined();
      expect(loaded?.id).toBe(saveId);
      expect(loaded?.name).toBe(testData.name);
      expect(loaded?.geometry).toEqual(testData.geometry);
      expect(loaded?.inputs).toEqual(testData.inputs);
    });

    test('should return null for non-existent project', async () => {
      const result = await db.loadProject('non-existent-id');
      expect(result).toBeNull();
    });

    test('should handle data corruption detection', async () => {
      const projectId = await db.saveProject(testData);

      // Manually corrupt the data in database
      await db['run']('UPDATE projects SET data = ? WHERE id = ?',
        ['corrupted json data', projectId]);

      const result = await db.loadProject(projectId);
      expect(result).toBeNull(); // Should fail integrity check

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'load_project',
          projectId
        })
      );
    });

    test('should handle database connection failures during load', async () => {
      const projectId = await db.saveProject(testData);

      // Mock database get to throw error
      const originalGet = db['get'].bind(db);
      db['get'] = jest.fn().mockRejectedValue(new Error('Connection lost'));

      await expect(db.loadProject(projectId)).rejects.toThrow('Connection lost');
      expect(mockLogger.logError).toHaveBeenCalled();

      // Restore original method
      db['get'] = originalGet;
    });
  });

  describe('Error Scenarios and Crash Simulations', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should handle database lock errors with retry', async () => {
      const projectId = await db.saveProject(testData);

      // Mock runWithRetry to simulate database lock
      const originalRunWithRetry = db['runWithRetry'].bind(db);
      let callCount = 0;
      db['runWithRetry'] = jest.fn().mockImplementation(async (sql, operation) => {
        callCount++;
        if (callCount === 1) {
          throw new Error('database is locked');
        }
        return originalRunWithRetry(sql, operation);
      });

      // This should succeed after retry
      const result = await db.loadProject(projectId);
      expect(result).toBeDefined();
      expect(callCount).toBe(2); // Should have retried once

      // Restore original method
      db['runWithRetry'] = originalRunWithRetry;
    });

    test('should simulate disk full error during save', async () => {
      // Mock run to throw disk full error
      const originalRun = db['run'].bind(db);
      db['run'] = jest.fn().mockRejectedValue(new Error('disk is full'));

      await expect(db.saveProject(testData)).rejects.toThrow('disk is full');
      expect(mockLogger.logError).toHaveBeenCalled();

      // Restore original method
      db['run'] = originalRun;
    });

    test('should handle transaction rollback on failure', async () => {
      const projectId = 'transaction-test';

      // Use transaction that will fail
      await expect(
        db['executeInTransaction'](async (transaction) => {
          await transaction.begin();
          // This should work
          await db['run']('INSERT INTO projects (id, name, data, checksum) VALUES (?, ?, ?, ?)',
            [projectId, 'Test', JSON.stringify(testData), 'checksum']);

          // Simulate failure
          throw new Error('Simulated transaction failure');
        })
      ).rejects.toThrow('Simulated transaction failure');

      // Verify rollback - project should not exist
      const result = await db.loadProject(projectId);
      expect(result).toBeNull();
    });

    test('should handle partial write failures', async () => {
      // Simulate a scenario where save starts but fails midway
      const originalRun = db['run'].bind(db);
      let callCount = 0;
      db['run'] = jest.fn().mockImplementation(async (sql) => {
        callCount++;
        if (callCount === 2) { // Fail on second SQL call
          throw new Error('Partial write failure');
        }
        return originalRun(sql);
      });

      await expect(db.saveProject(testData)).rejects.toThrow('Partial write failure');

      // Verify no partial data was saved
      const projects = await db.listProjects();
      const savedProject = projects.find(p => p.name === testData.name);
      expect(savedProject).toBeUndefined();

      // Restore original method
      db['run'] = originalRun;
    });

    test('should handle connection timeout during operation', async () => {
      const projectId = await db.saveProject(testData);

      // Mock get to simulate timeout
      const originalGet = db['get'].bind(db);
      db['get'] = jest.fn().mockImplementation(
        () => new Promise((resolve, reject) => {
          setTimeout(() => reject(new Error('Connection timeout')), 100);
        })
      );

      await expect(db.loadProject(projectId)).rejects.toThrow('Connection timeout');
      expect(mockLogger.logError).toHaveBeenCalled();

      // Restore original method
      db['get'] = originalGet;
    });
  });

  describe('Retry Logic and Data Loss Prevention', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should not lose data on retry after transient failure', async () => {
      const projectId = await db.saveProject(testData);

      // Verify initial save
      let loaded = await db.loadProject(projectId);
      expect(loaded?.name).toBe(testData.name);

      // Simulate transient failure on update
      const originalRun = db['run'].bind(db);
      let failureCount = 0;
      db['run'] = jest.fn().mockImplementation(async (sql, params) => {
        if (sql.includes('UPDATE') && failureCount < 2) {
          failureCount++;
          throw new Error('Temporary network issue');
        }
        return originalRun(sql, params);
      });

      // Update should eventually succeed
      const updatedData = { ...testData, name: 'Updated After Retry' };
      const updateId = await db.saveProject(updatedData);

      expect(updateId).toBe(projectId);

      // Verify data integrity after retry
      loaded = await db.loadProject(projectId);
      expect(loaded?.name).toBe('Updated After Retry');

      // Restore original method
      db['run'] = originalRun;
    });

    test('should maintain data consistency across retry attempts', async () => {
      // Save initial data
      const projectId = await db.saveProject(testData);

      // Simulate intermittent failures during multiple operations
      const originalRun = db['run'].bind(db);
      let operationCount = 0;
      db['run'] = jest.fn().mockImplementation(async (sql, params) => {
        operationCount++;
        if (operationCount % 3 === 0) { // Fail every 3rd operation
          throw new Error('Intermittent failure');
        }
        return originalRun(sql, params);
      });

      // Perform multiple operations that should eventually succeed
      const operations = [
        () => db.saveProject({ ...testData, name: 'Retry Test 1' }),
        () => db.loadProject(projectId),
        () => db.saveProject({ ...testData, name: 'Retry Test 2' }),
        () => db.loadProject(projectId)
      ];

      for (const operation of operations) {
        await expect(operation()).resolves.not.toThrow();
      }

      // Verify final state
      const final = await db.loadProject(projectId);
      expect(final?.name).toBe('Retry Test 2');

      // Restore original method
      db['run'] = originalRun;
    });

    test('should handle idempotent operations correctly', async () => {
      const operationId = 'test_operation_123';
      const resultData = { success: true, data: 'test' };

      // Mark operation as completed
      await db['markOperationCompleted'](operationId, resultData);

      // Verify idempotency check works
      const isCompleted = await db['isOperationCompleted'](operationId);
      expect(isCompleted).toBe(true);

      // Should be able to retrieve stored result
      const stored = await db['get']('SELECT result FROM idempotency_keys WHERE key = ?', [operationId]);
      expect(stored).toBeDefined();
      expect(JSON.parse(stored.result)).toEqual(resultData);
    });

    test('should clean up expired idempotency keys', async () => {
      const expiredId = 'expired_operation';
      const validId = 'valid_operation';

      // Add expired key (1 minute ago)
      const expiredTime = new Date(Date.now() - 60 * 1000);
      await db['run']('INSERT INTO idempotency_keys (key, operation, expires_at, result) VALUES (?, ?, ?, ?)',
        [expiredId, 'test', expiredTime.toISOString(), JSON.stringify({})]);

      // Add valid key (1 hour from now)
      const validTime = new Date(Date.now() + 60 * 60 * 1000);
      await db['run']('INSERT INTO idempotency_keys (key, operation, expires_at, result) VALUES (?, ?, ?, ?)',
        [validId, 'test', validTime.toISOString(), JSON.stringify({})]);

      // Expired key should not be considered completed
      const expiredCompleted = await db['isOperationCompleted'](expiredId);
      expect(expiredCompleted).toBe(false);

      // Valid key should be considered completed
      const validCompleted = await db['isOperationCompleted'](validId);
      expect(validCompleted).toBe(true);
    });
  });

  describe('Data Integrity and Validation', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should validate data integrity on load', async () => {
      const projectId = await db.saveProject(testData);

      // Manually modify checksum to simulate corruption
      await db['run']('UPDATE projects SET checksum = ? WHERE id = ?',
        ['invalid_checksum', projectId]);

      const result = await db.loadProject(projectId);
      expect(result).toBeNull(); // Should fail integrity check

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'load_project',
          projectId
        })
      );
    });

    test('should handle malformed JSON data', async () => {
      const projectId = 'malformed_test';

      // Insert malformed JSON directly
      await db['run']('INSERT INTO projects (id, name, data, checksum) VALUES (?, ?, ?, ?)',
        [projectId, 'Malformed Test', '{invalid json', 'checksum']);

      const result = await db.loadProject(projectId);
      expect(result).toBeNull(); // Should fail JSON parsing

      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should maintain referential integrity', async () => {
      const projectId = await db.saveProject(testData);

      // Create checkpoints
      await db['createCheckpoint']({
        id: 'checkpoint_1',
        projectId,
        data: testData,
        operation: 'test',
        timestamp: new Date(),
        dataSize: 100
      });

      // Try to delete project (should cascade delete checkpoints)
      const deleteResult = await db['deleteProject'](projectId);
      expect(deleteResult).toBe(true);

      // Verify project is gone
      const project = await db.loadProject(projectId);
      expect(project).toBeNull();

      // Verify checkpoints are gone (cascade delete)
      const checkpoints = await db['getCheckpoints'](projectId);
      expect(checkpoints.length).toBe(0);
    });
  });

  describe('System Health and Monitoring', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should provide system health status', async () => {
      // Add some test data
      await db.saveProject(testData);
      await db.saveProject({ ...testData, id: 'test2', name: 'Test Project 2' });

      const health = await db['getSystemHealth']();

      expect(health).toHaveProperty('databaseStatus');
      expect(health).toHaveProperty('totalProjects');
      expect(health).toHaveProperty('recentErrors');
      expect(health).toHaveProperty('recoveryReady');
      expect(health).toHaveProperty('uptime');

      expect(health.totalProjects).toBeGreaterThanOrEqual(2);
      expect(typeof health.uptime).toBe('number');
    });

    test('should detect database issues in health check', async () => {
      // Close database to simulate connection issue
      await db.close();

      const health = await db['getSystemHealth']();

      expect(health.databaseStatus).toBe('error');
      expect(health.recoveryReady).toBe(false);
    });

    test('should handle settings operations', async () => {
      // Test setting and getting values
      await db['setSetting']('test_key', { value: 42, text: 'test' });

      const retrieved = await db['getSetting']('test_key');
      expect(retrieved).toEqual({ value: 42, text: 'test' });

      // Test non-existent key
      const missing = await db['getSetting']('non_existent');
      expect(missing).toBeNull();
    });
  });

  describe('Recovery and Backup Operations', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should create and restore from checkpoints', async () => {
      const projectId = await db.saveProject(testData);

      // Create checkpoint
      const checkpointData = { ...testData, name: 'Checkpoint Version' };
      await db['createCheckpoint']({
        id: 'recovery_test_checkpoint',
        projectId,
        data: checkpointData,
        operation: 'test_recovery',
        timestamp: new Date(),
        dataSize: JSON.stringify(checkpointData).length
      });

      // Restore from checkpoint
      const recovered = await db['restoreFromCheckpoint']('recovery_test_checkpoint');
      expect(recovered).toBeDefined();
      expect(recovered?.name).toBe('Checkpoint Version');
    });

    test('should provide recovery options', async () => {
      const projectId = await db.saveProject(testData);

      // Create multiple checkpoints
      const checkpoint1 = {
        id: 'checkpoint_1',
        projectId,
        data: testData,
        operation: 'auto_save',
        timestamp: new Date(Date.now() - 10000), // 10 seconds ago
        dataSize: 100
      };

      const checkpoint2 = {
        id: 'checkpoint_2',
        projectId,
        data: testData,
        operation: 'manual_save',
        timestamp: new Date(Date.now() - 5000), // 5 seconds ago
        dataSize: 100
      };

      await db['createCheckpoint'](checkpoint1);
      await db['createCheckpoint'](checkpoint2);

      const recoveryOptions = await db['getRecoveryOptions'](projectId);

      expect(recoveryOptions.length).toBeGreaterThan(0);
      expect(recoveryOptions.some(opt => opt.type === 'checkpoint')).toBe(true);
      expect(recoveryOptions.some(opt => opt.type === 'last_good_state')).toBe(true);
    });
  });

  describe('Performance and Load Testing', () => {
    beforeEach(async () => {
      await db.initialize();
    });

    test('should handle bulk operations efficiently', async () => {
      const startTime = Date.now();

      // Create multiple projects
      const bulkPromises = Array(10).fill(null).map((_, i) =>
        db.saveProject({
          ...testData,
          id: `bulk_test_${i}`,
          name: `Bulk Test Project ${i}`
        })
      );

      await Promise.all(bulkPromises);

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds

      // Verify all projects were created
      const allProjects = await db.listProjects();
      const bulkProjects = allProjects.filter(p => p.name.startsWith('Bulk Test'));
      expect(bulkProjects.length).toBe(10);

      expect(mockLogger.logPerformance).toHaveBeenCalled();
    });

    test('should maintain performance under concurrent load', async () => {
      const concurrentOperations = 20;
      const operations = Array(concurrentOperations).fill(null).map((_, i) =>
        db.saveProject({
          ...testData,
          id: `concurrent_load_${i}`,
          name: `Concurrent Load Test ${i}`
        })
      );

      const startTime = Date.now();
      const results = await Promise.allSettled(operations);
      const duration = Date.now() - startTime;

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;
      const rejected = results.filter(r => r.status === 'rejected').length;

      expect(fulfilled + rejected).toBe(concurrentOperations);
      expect(fulfilled).toBeGreaterThan(concurrentOperations * 0.8); // At least 80% success rate
      expect(duration).toBeLessThan(10000); // Should complete within 10 seconds

      console.log(`Concurrent load test: ${fulfilled}/${concurrentOperations} succeeded in ${duration}ms`);
    });
  });
});

// Helper function to create test project data
function createTestProjectData(): ProjectData {
  return {
    id: `test_project_${Date.now()}_${Math.random()}`,
    name: 'Test Valley Project',
    description: 'Comprehensive test project for database operations',
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
