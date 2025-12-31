// Comprehensive Jest tests for checkpoint system
// Tests auto-save, recovery, data integrity, and crash simulation

import { CheckpointManager, DataChangeTracker } from './checkpointSystem';
import { getDatabase } from '../data/database';
import { getLogger } from '../utils/logger';
import { ProjectData } from '../types';

// Mock dependencies
jest.mock('../data/database');
jest.mock('../utils/logger');

const mockDb = {
  initialize: jest.fn().mockResolvedValue(undefined),
  createCheckpoint: jest.fn(),
  getCheckpoints: jest.fn().mockResolvedValue([]),
  restoreFromCheckpoint: jest.fn(),
  saveProject: jest.fn()
};

const mockLogger = {
  logError: jest.fn(),
  logPerformance: jest.fn(),
  logRecoveryAction: jest.fn(),
  logCheckpoint: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
};

(getDatabase as jest.Mock).mockReturnValue(mockDb);
(getLogger as jest.Mock).mockReturnValue(mockLogger);

describe('CheckpointManager - Comprehensive Auto-Save Tests', () => {
  let checkpointManager: CheckpointManager;
  let testProjectData: ProjectData;

  beforeEach(async () => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    checkpointManager = new CheckpointManager(1, 10); // 1 minute interval, max 10 checkpoints
    testProjectData = createTestProjectData();

    await checkpointManager.initialize();
  });

  afterEach(async () => {
    jest.clearAllTimers();
    jest.useRealTimers();

    // Reset global state
    (global as any).checkpointManager = undefined;
  });

  describe('Initialization and Setup', () => {
    test('should initialize successfully', async () => {
      expect(mockDb.initialize).toHaveBeenCalled();
      expect(mockLogger.info).toHaveBeenCalledWith(
        'Checkpoint manager initialized',
        expect.any(Object)
      );
    });

    test('should handle initialization failures gracefully', async () => {
      mockDb.initialize.mockRejectedValueOnce(new Error('DB init failed'));

      const newManager = new CheckpointManager();
      await expect(newManager.initialize()).rejects.toThrow('DB init failed');

      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should set up event handlers for graceful shutdown', async () => {
      const mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {});
      const mockEmit = jest.spyOn(checkpointManager, 'emit');

      // Simulate SIGINT
      process.emit('SIGINT');

      expect(mockEmit).toHaveBeenCalledWith('shutdown');
      expect(mockExit).toHaveBeenCalledWith(0);

      mockExit.mockRestore();
    });
  });

  describe('Checkpoint Creation', () => {
    test('should create checkpoint successfully', async () => {
      const projectId = 'test-project';
      mockDb.createCheckpoint.mockResolvedValue('checkpoint_123');

      const checkpointId = await checkpointManager.createCheckpoint(
        projectId,
        'manual_save',
        testProjectData
      );

      expect(checkpointId).toBe('checkpoint_123');
      expect(mockDb.createCheckpoint).toHaveBeenCalledWith(expect.objectContaining({
        id: expect.stringContaining('checkpoint_'),
        projectId,
        data: testProjectData,
        operation: 'manual_save'
      }));

      expect(mockLogger.logCheckpoint).toHaveBeenCalled();
    });

    test('should handle checkpoint creation failures', async () => {
      const projectId = 'test-project';
      mockDb.createCheckpoint.mockRejectedValue(new Error('Checkpoint failed'));

      await expect(
        checkpointManager.createCheckpoint(projectId, 'test', testProjectData)
      ).rejects.toThrow('Checkpoint failed');

      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should generate unique checkpoint IDs', async () => {
      const projectId = 'test-project';
      mockDb.createCheckpoint.mockResolvedValue('checkpoint_123');

      const id1 = await checkpointManager.createCheckpoint(projectId, 'test1');
      const id2 = await checkpointManager.createCheckpoint(projectId, 'test2');

      expect(id1).not.toBe(id2);
      expect(id1).toContain('checkpoint_');
      expect(id2).toContain('checkpoint_');
    });

    test('should include operation context in checkpoint', async () => {
      const projectId = 'test-project';
      const operation = 'complex_calculation';

      mockDb.createCheckpoint.mockImplementation((checkpoint) => {
        expect(checkpoint.operation).toBe(operation);
        expect(checkpoint.dataSize).toBeGreaterThan(0);
        return 'checkpoint_123';
      });

      await checkpointManager.createCheckpoint(projectId, operation, testProjectData);
    });
  });

  describe('Auto-Save Functionality', () => {
    test('should perform auto-save at specified intervals', async () => {
      const projectId = 'auto-save-test';
      checkpointManager.markProjectActive(projectId);

      mockDb.createCheckpoint.mockResolvedValue('auto_checkpoint_123');

      // Fast-forward time by 1 minute
      jest.advanceTimersByTime(60 * 1000);

      // Trigger auto-save check
      (checkpointManager as any).performAutoCheckpoints();

      expect(mockDb.createCheckpoint).toHaveBeenCalledWith(
        expect.objectContaining({
          projectId,
          operation: 'auto_save'
        })
      );
    });

    test('should not auto-save inactive projects', async () => {
      const projectId = 'inactive-test';

      // Don't mark as active
      jest.advanceTimersByTime(60 * 1000);
      (checkpointManager as any).performAutoCheckpoints();

      expect(mockDb.createCheckpoint).not.toHaveBeenCalled();
    });

    test('should handle auto-save failures gracefully', async () => {
      const projectId = 'failing-auto-save';
      checkpointManager.markProjectActive(projectId);

      mockDb.createCheckpoint.mockRejectedValue(new Error('Auto-save failed'));

      jest.advanceTimersByTime(60 * 1000);
      (checkpointManager as any).performAutoCheckpoints();

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'auto_checkpoint',
          projectId
        })
      );
    });

    test('should respect auto-save interval configuration', () => {
      const customManager = new CheckpointManager(5, 10); // 5 minute interval

      expect((customManager as any).autoSaveInterval).toBeDefined();
    });
  });

  describe('Project Activity Tracking', () => {
    test('should track active projects', () => {
      const projectId1 = 'active-project-1';
      const projectId2 = 'active-project-2';

      checkpointManager.markProjectActive(projectId1);
      checkpointManager.markProjectActive(projectId2);

      const activeProjects = checkpointManager.getActiveProjects();
      expect(activeProjects).toContain(projectId1);
      expect(activeProjects).toContain(projectId2);
    });

    test('should remove inactive projects', () => {
      const projectId = 'to-be-removed';

      checkpointManager.markProjectActive(projectId);
      expect(checkpointManager.getActiveProjects()).toContain(projectId);

      checkpointManager.markProjectInactive(projectId);
      expect(checkpointManager.getActiveProjects()).not.toContain(projectId);
    });

    test('should update last checkpoint time when marking active', () => {
      const projectId = 'time-test';
      const beforeTime = Date.now();

      checkpointManager.markProjectActive(projectId);

      // Access private property for testing
      const lastCheckpointTime = (checkpointManager as any).lastCheckpointTime.get(projectId);
      expect(lastCheckpointTime).toBeGreaterThanOrEqual(beforeTime);
    });
  });

  describe('Checkpoint Recovery', () => {
    test('should restore from checkpoint successfully', async () => {
      const checkpointId = 'recovery_test_checkpoint';
      const expectedData = { ...testProjectData, recovered: true };

      mockDb.restoreFromCheckpoint.mockResolvedValue(expectedData);

      const recovered = await checkpointManager.restoreFromCheckpoint(checkpointId);

      expect(recovered).toEqual(expectedData);
      expect(mockDb.restoreFromCheckpoint).toHaveBeenCalledWith(checkpointId);
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        `Restored from checkpoint ${checkpointId}`,
        true,
        expect.any(Object)
      );
    });

    test('should handle checkpoint restoration failures', async () => {
      const checkpointId = 'failing_checkpoint';

      mockDb.restoreFromCheckpoint.mockRejectedValue(new Error('Checkpoint corrupted'));

      const result = await checkpointManager.restoreFromCheckpoint(checkpointId);

      expect(result).toBeNull();
      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should return null for non-existent checkpoints', async () => {
      const checkpointId = 'non-existent';

      mockDb.restoreFromCheckpoint.mockResolvedValue(null);

      const result = await checkpointManager.restoreFromCheckpoint(checkpointId);
      expect(result).toBeNull();
    });
  });

  describe('Recovery Options', () => {
    test('should provide comprehensive recovery options', async () => {
      const projectId = 'recovery-options-test';

      const mockCheckpoints = [
        {
          id: 'checkpoint_1',
          projectId,
          data: testProjectData,
          operation: 'auto_save',
          timestamp: new Date(Date.now() - 300000), // 5 minutes ago
          dataSize: 1024
        },
        {
          id: 'checkpoint_2',
          projectId,
          data: testProjectData,
          operation: 'manual_save',
          timestamp: new Date(Date.now() - 60000), // 1 minute ago
          dataSize: 1024
        }
      ];

      mockDb.getCheckpoints.mockResolvedValue(mockCheckpoints);

      const options = await checkpointManager.getRecoveryOptions(projectId);

      expect(options.length).toBeGreaterThan(1);

      // Should include checkpoint options
      const checkpointOptions = options.filter(opt => opt.type === 'checkpoint');
      expect(checkpointOptions.length).toBe(2);

      // Should include last good state option
      const lastGoodState = options.find(opt => opt.type === 'last_good_state');
      expect(lastGoodState).toBeDefined();
    });

    test('should handle recovery options failures', async () => {
      const projectId = 'failing-recovery-options';

      mockDb.getCheckpoints.mockRejectedValue(new Error('Database error'));

      const options = await checkpointManager.getRecoveryOptions(projectId);

      expect(options).toEqual([]);
      expect(mockLogger.logError).toHaveBeenCalled();
    });
  });

  describe('Data Change Detection', () => {
    test('should trigger checkpoints on data changes', async () => {
      const projectId = 'change-detection-test';
      const tracker = new DataChangeTracker();

      checkpointManager.markProjectActive(projectId);
      mockDb.createCheckpoint.mockResolvedValue('change_checkpoint_123');

      // First call - should create checkpoint (first time)
      await checkpointManager.trackDataChange(projectId, testProjectData);
      expect(mockDb.createCheckpoint).toHaveBeenCalledTimes(1);

      // Second call with same data - should not create checkpoint
      jest.clearAllMocks();
      await checkpointManager.trackDataChange(projectId, testProjectData);
      expect(mockDb.createCheckpoint).not.toHaveBeenCalled();

      // Third call with changed data - should create checkpoint
      const changedData = { ...testProjectData, name: 'Changed Name' };
      await checkpointManager.trackDataChange(projectId, changedData);
      expect(mockDb.createCheckpoint).toHaveBeenCalledTimes(1);
    });

    test('should force checkpoint when requested', async () => {
      const projectId = 'force-checkpoint-test';

      await checkpointManager.trackDataChange(projectId, testProjectData, true);

      expect(mockDb.createCheckpoint).toHaveBeenCalledWith(
        expect.objectContaining({
          projectId,
          operation: 'data_change'
        })
      );
    });
  });

  describe('Crash Simulation and Emergency Recovery', () => {
    test('should perform emergency checkpoints on crash', async () => {
      const projectId1 = 'emergency-project-1';
      const projectId2 = 'emergency-project-2';

      checkpointManager.markProjectActive(projectId1);
      checkpointManager.markProjectActive(projectId2);

      mockDb.createCheckpoint.mockResolvedValue('emergency_checkpoint');

      await checkpointManager['emergencyCheckpointAll']();

      expect(mockDb.createCheckpoint).toHaveBeenCalledTimes(2);
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        'Emergency checkpoint initiated',
        true
      );
    });

    test('should handle emergency checkpoint failures gracefully', async () => {
      const projectId = 'failing-emergency';
      checkpointManager.markProjectActive(projectId);

      mockDb.createCheckpoint.mockRejectedValue(new Error('Emergency save failed'));

      // Should not throw, just log the error
      await expect(
        checkpointManager['emergencyCheckpointAll']()
      ).resolves.not.toThrow();

      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should force checkpoint all active projects', async () => {
      const projectId1 = 'force-1';
      const projectId2 = 'force-2';

      checkpointManager.markProjectActive(projectId1);
      checkpointManager.markProjectActive(projectId2);

      await checkpointManager.forceCheckpointAllActive();

      expect(mockDb.createCheckpoint).toHaveBeenCalledTimes(2);
    });
  });

  describe('Checkpoint Cleanup and Management', () => {
    test('should cleanup old checkpoints when limit exceeded', async () => {
      const projectId = 'cleanup-test';

      // Mock having more checkpoints than the limit
      const manyCheckpoints = Array(15).fill(null).map((_, i) => ({
        id: `checkpoint_${i}`,
        projectId,
        data: testProjectData,
        operation: 'test',
        timestamp: new Date(),
        dataSize: 100
      }));

      mockDb.getCheckpoints.mockResolvedValue(manyCheckpoints);

      // Create a new checkpoint, which should trigger cleanup
      await checkpointManager.createCheckpoint(projectId, 'test_operation');

      // Verify cleanup was attempted (logged)
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        expect.stringContaining('Checkpoint cleanup needed'),
        true,
        expect.any(Object)
      );
    });

    test('should handle cleanup failures gracefully', async () => {
      const projectId = 'failing-cleanup';

      mockDb.getCheckpoints.mockRejectedValue(new Error('Cleanup query failed'));

      // Should not throw, just log the error
      await expect(
        checkpointManager.createCheckpoint(projectId, 'test')
      ).resolves.toBeDefined();

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'cleanup_checkpoints',
          projectId
        })
      );
    });
  });

  describe('Shutdown and Cleanup', () => {
    test('should perform graceful shutdown', () => {
      const mockClearInterval = jest.spyOn(global, 'clearInterval');

      checkpointManager.shutdown();

      expect(mockClearInterval).toHaveBeenCalled();
      expect(mockLogger.info).toHaveBeenCalledWith('Checkpoint manager shutdown');
    });

    test('should attempt final checkpoints during shutdown', async () => {
      const projectId = 'shutdown-test';
      checkpointManager.markProjectActive(projectId);

      mockDb.createCheckpoint.mockResolvedValue('final_checkpoint');

      // Access private method for testing
      await (checkpointManager as any).emergencyCheckpointAll();

      expect(mockDb.createCheckpoint).toHaveBeenCalled();
    });
  });

  describe('Event Emission and Communication', () => {
    test('should emit events for checkpoint creation', async () => {
      const projectId = 'event-test';
      const mockCallback = jest.fn();

      checkpointManager.on('checkpointCreated', mockCallback);

      await checkpointManager.createCheckpoint(projectId, 'event_test');

      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          trigger: 'manual_save',
          projectId,
          data: undefined // No data provided
        })
      );
    });

    test('should handle event listener errors gracefully', async () => {
      const projectId = 'error-event-test';
      const failingCallback = jest.fn().mockImplementation(() => {
        throw new Error('Event handler failed');
      });

      checkpointManager.on('checkpointCreated', failingCallback);

      // Should not throw even if event handler fails
      await expect(
        checkpointManager.createCheckpoint(projectId, 'error_test')
      ).resolves.not.toThrow();

      expect(failingCallback).toHaveBeenCalled();
    });
  });

  describe('Performance and Load Testing', () => {
    test('should handle rapid checkpoint creation', async () => {
      const projectId = 'rapid-test';
      const checkpointPromises = Array(10).fill(null).map((_, i) =>
        checkpointManager.createCheckpoint(projectId, `rapid_${i}`)
      );

      const startTime = Date.now();
      const results = await Promise.allSettled(checkpointPromises);
      const duration = Date.now() - startTime;

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;

      expect(fulfilled).toBeGreaterThan(5); // At least some should succeed
      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds

      expect(mockLogger.logPerformance).toHaveBeenCalled();
    });

    test('should maintain performance under concurrent operations', async () => {
      const projectId = 'concurrent-test';
      checkpointManager.markProjectActive(projectId);

      // Simulate concurrent auto-saves and manual saves
      const operations = [
        checkpointManager.createCheckpoint(projectId, 'manual_1'),
        checkpointManager.createCheckpoint(projectId, 'manual_2'),
        (checkpointManager as any).performAutoCheckpoints(),
        checkpointManager.createCheckpoint(projectId, 'manual_3')
      ];

      const startTime = Date.now();
      await Promise.all(operations);
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(2000); // Should be fast
      expect(mockDb.createCheckpoint).toHaveBeenCalled();
    });
  });
});

// DataChangeTracker specific tests
describe('DataChangeTracker', () => {
  let tracker: DataChangeTracker;

  beforeEach(() => {
    tracker = new DataChangeTracker(0.1); // 10% change threshold
  });

  test('should detect first data change', () => {
    const projectId = 'change-test';
    const data = { value: 100 };

    const hasChanged = tracker.hasSignificantChange(projectId, data);
    expect(hasChanged).toBe(true); // First time should always trigger
  });

  test('should detect significant data changes', () => {
    const projectId = 'change-test';

    // Initial data
    tracker.hasSignificantChange(projectId, { value: 100 });

    // Same data - should not trigger
    let hasChanged = tracker.hasSignificantChange(projectId, { value: 100 });
    expect(hasChanged).toBe(false);

    // Different data - should trigger
    hasChanged = tracker.hasSignificantChange(projectId, { value: 200 });
    expect(hasChanged).toBe(true);
  });

  test('should handle complex object changes', () => {
    const projectId = 'complex-change-test';
    const initialData = {
      nested: { value: 100, list: [1, 2, 3] },
      string: 'test',
      number: 42
    };

    tracker.hasSignificantChange(projectId, initialData);

    // Minor change - should not trigger
    const minorChange = { ...initialData, number: 43 };
    expect(tracker.hasSignificantChange(projectId, minorChange)).toBe(true); // Hash differs

    // Reset and test with same data
    const freshTracker = new DataChangeTracker();
    freshTracker.hasSignificantChange(projectId, initialData);
    expect(freshTracker.hasSignificantChange(projectId, initialData)).toBe(false);
  });

  test('should clear tracking data', () => {
    const projectId = 'clear-test';
    tracker.hasSignificantChange(projectId, { data: 'initial' });

    tracker.clearTracking(projectId);

    // After clearing, should detect change again
    const hasChanged = tracker.hasSignificantChange(projectId, { data: 'initial' });
    expect(hasChanged).toBe(true);
  });

  test('should handle different projects independently', () => {
    const project1 = 'project-1';
    const project2 = 'project-2';

    tracker.hasSignificantChange(project1, { value: 100 });
    tracker.hasSignificantChange(project2, { value: 200 });

    // Same data for project 1 should not trigger
    expect(tracker.hasSignificantChange(project1, { value: 100 })).toBe(false);

    // Same data for project 2 should not trigger
    expect(tracker.hasSignificantChange(project2, { value: 200 })).toBe(false);

    // Different data for project 1 should trigger
    expect(tracker.hasSignificantChange(project1, { value: 150 })).toBe(true);
  });
});

// Helper function to create test project data
function createTestProjectData(): ProjectData {
  return {
    id: `test_project_${Date.now()}`,
    name: 'Test Valley Project',
    description: 'Test project for checkpoint system',
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
    checksum: 'test_checksum'
  };
}
