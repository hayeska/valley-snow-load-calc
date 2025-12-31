// Jest test setup and global test utilities

import { jest } from '@jest/globals';

// Global test timeouts
jest.setTimeout(10000);

// Mock console methods to reduce noise during testing
const originalConsole = { ...console };
beforeAll(() => {
  console.log = jest.fn();
  console.info = jest.fn();
  console.warn = jest.fn();
  console.error = jest.fn();
});

afterAll(() => {
  // Restore console methods
  Object.assign(console, originalConsole);
});

// Global test utilities
global.testUtils = {
  // Create a delay for testing async operations
  delay: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  // Create test project data
  createTestProject: (overrides = {}) => ({
    id: `test-project-${Date.now()}-${Math.random()}`,
    name: 'Test Valley Project',
    description: 'Test project for unit tests',
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
    checksum: 'test_checksum',
    ...overrides
  }),

  // Mock database operations
  createMockDb: () => ({
    initialize: jest.fn().mockResolvedValue(undefined),
    saveProject: jest.fn().mockResolvedValue('test-project-id'),
    loadProject: jest.fn(),
    deleteProject: jest.fn().mockResolvedValue(true),
    listProjects: jest.fn().mockResolvedValue([]),
    createCheckpoint: jest.fn().mockResolvedValue('checkpoint-id'),
    getCheckpoints: jest.fn().mockResolvedValue([]),
    restoreFromCheckpoint: jest.fn(),
    getSystemHealth: jest.fn().mockResolvedValue({
      databaseStatus: 'healthy',
      totalProjects: 0,
      recentErrors: 0,
      recoveryReady: true,
      uptime: 100
    }),
    isOperationCompleted: jest.fn().mockResolvedValue(false),
    markOperationCompleted: jest.fn().mockResolvedValue(undefined),
    close: jest.fn().mockResolvedValue(undefined)
  }),

  // Mock logger operations
  createMockLogger: () => ({
    logError: jest.fn(),
    logPerformance: jest.fn(),
    logRecoveryAction: jest.fn(),
    logCheckpoint: jest.fn(),
    logDatabaseOperation: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    getPerformanceStats: jest.fn().mockReturnValue({}),
    getErrorSummary: jest.fn().mockReturnValue({
      totalErrors: 0,
      errorPatterns: {},
      mostCommonError: null
    })
  }),

  // Mock checkpoint manager
  createMockCheckpointManager: () => ({
    initialize: jest.fn().mockResolvedValue(undefined),
    createCheckpoint: jest.fn().mockResolvedValue('checkpoint-id'),
    getRecoveryOptions: jest.fn().mockResolvedValue([]),
    restoreFromCheckpoint: jest.fn(),
    markProjectActive: jest.fn(),
    markProjectInactive: jest.fn(),
    emergencyCheckpointAll: jest.fn().mockResolvedValue(undefined),
    forceCheckpointAllActive: jest.fn().mockResolvedValue(undefined),
    getActiveProjects: jest.fn().mockReturnValue([]),
    shutdown: jest.fn()
  }),

  // Utility to test async operations with timeout
  withTimeout: <T>(promise: Promise<T>, timeoutMs: number = 5000): Promise<T> => {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
  },

  // Utility to test retry logic
  simulateFailures: (failureCount: number, successValue: any) => {
    let callCount = 0;
    return jest.fn().mockImplementation(() => {
      callCount++;
      if (callCount <= failureCount) {
        throw new Error(`Simulated failure ${callCount}`);
      }
      return successValue;
    });
  },

  // Utility to test concurrent operations
  runConcurrent: async <T>(
    operations: (() => Promise<T>)[],
    expectedSuccessRate: number = 0.8
  ): Promise<{ results: PromiseSettledResult<T>[], successRate: number }> => {
    const results = await Promise.allSettled(operations);
    const fulfilled = results.filter(r => r.status === 'fulfilled').length;
    const successRate = fulfilled / results.length;

    expect(successRate).toBeGreaterThanOrEqual(expectedSuccessRate);

    return { results, successRate };
  }
};

// Extend Jest matchers for better error testing
expect.extend({
  toHaveBeenCalledWithError(received: jest.MockedFunction<any>, errorMessage: string) {
    const calls = received.mock.calls;
    const errorCalls = calls.filter(call =>
      call[0] instanceof Error && call[0].message.includes(errorMessage)
    );

    if (errorCalls.length > 0) {
      return {
        message: () => `Expected not to find error with message "${errorMessage}"`,
        pass: true
      };
    }

    return {
      message: () => `Expected to find error with message "${errorMessage}", but found: ${calls.map(call => call[0]?.message).join(', ')}`,
      pass: false
    };
  }
});

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveBeenCalledWithError(errorMessage: string): R;
    }
  }

  const testUtils: typeof global.testUtils;
}
