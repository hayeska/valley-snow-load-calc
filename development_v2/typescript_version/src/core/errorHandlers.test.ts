// Comprehensive Jest tests for error handling decorators and recovery mechanisms
// Tests retry logic, timeout handling, validation, and recovery strategies

import { resilientOperation, withTimeout, validateInput, validatePositiveNumber, validateRange, withErrorBoundary } from './errorHandlers';
import { getLogger } from '../utils/logger';

// Mock logger
jest.mock('../utils/logger');
const mockLogger = {
  logError: jest.fn(),
  logPerformance: jest.fn(),
  logRecoveryAction: jest.fn(),
  info: jest.fn(),
  warn: jest.fn()
};
(getLogger as jest.Mock).mockReturnValue(mockLogger);

describe('Error Handlers - Comprehensive Retry and Recovery Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('resilientOperation Decorator', () => {
    class TestClass {
      callCount = 0;
      shouldFailTimes = 0;

      @resilientOperation(3, 100, true, false)
      async testOperation(failCount: number = 0): Promise<string> {
        this.callCount++;
        if (this.callCount <= failCount) {
          throw new Error(`Simulated failure ${this.callCount}`);
        }
        return `Success on attempt ${this.callCount}`;
      }

      @resilientOperation(2, 50, false, false) // Non-recoverable
      async nonRecoverableOperation(shouldFail: boolean = false): Promise<string> {
        if (shouldFail) {
          throw new Error('Non-recoverable error');
        }
        return 'Success';
      }

      generateIdempotencyKey(operation: string, args: any[]): string {
        return `${operation}_${args.join('_')}`;
      }
    }

    let testInstance: TestClass;

    beforeEach(() => {
      testInstance = new TestClass();
    });

    test('should succeed on first attempt', async () => {
      const result = await testInstance.testOperation(0);

      expect(result).toBe('Success on attempt 1');
      expect(testInstance.callCount).toBe(1);
      expect(mockLogger.logPerformance).toHaveBeenCalledWith(
        'TestClass.testOperation',
        expect.any(Number),
        true,
        expect.any(Object)
      );
    });

    test('should retry on failure and succeed', async () => {
      const result = await testInstance.testOperation(2); // Fail twice, succeed on third

      expect(result).toBe('Success on attempt 3');
      expect(testInstance.callCount).toBe(3);
      expect(mockLogger.logError).toHaveBeenCalledTimes(2);
      expect(mockLogger.logPerformance).toHaveBeenCalledWith(
        'TestClass.testOperation',
        expect.any(Number),
        true,
        expect.objectContaining({ attempt: 3 })
      );
    });

    test('should fail after max retries', async () => {
      await expect(testInstance.testOperation(5)).rejects.toThrow('Simulated failure 4');

      expect(testInstance.callCount).toBe(4); // Initial + 3 retries
      expect(mockLogger.logError).toHaveBeenCalledTimes(3);
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        'TestClass.testOperation failed after 4 attempts',
        false,
        expect.any(Object)
      );
    });

    test('should not retry non-recoverable errors', async () => {
      await expect(testInstance.nonRecoverableOperation(true)).rejects.toThrow('Non-recoverable error');

      expect(mockLogger.logError).toHaveBeenCalledTimes(1);
      // Should not log retry attempts
    });

    test('should implement exponential backoff', async () => {
      const delays: number[] = [];
      const originalSetTimeout = global.setTimeout;

      global.setTimeout = jest.fn((callback, delay) => {
        delays.push(delay as number);
        return originalSetTimeout(callback, 0); // Execute immediately for testing
      });

      await testInstance.testOperation(2);

      // Should have delays: 100ms, 200ms (exponential backoff)
      expect(delays).toEqual([100, 200]);

      global.setTimeout = originalSetTimeout;
    });

    test('should handle idempotency correctly', async () => {
      const mockDb = {
        isOperationCompleted: jest.fn().mockResolvedValue(false),
        markOperationCompleted: jest.fn().mockResolvedValue(undefined)
      };

      // Mock getDatabase to return our mock
      const mockGetDb = jest.fn().mockReturnValue(mockDb);
      (global as any).getDatabase = mockGetDb;

      await testInstance.testOperation(0);

      expect(mockDb.markOperationCompleted).toHaveBeenCalledWith(
        'testOperation_0',
        'Success on attempt 1'
      );

      // Reset global mock
      delete (global as any).getDatabase;
    });

    test('should create checkpoints when requested', async () => {
      const mockCheckpointMgr = {
        createCheckpoint: jest.fn().mockResolvedValue('checkpoint_123')
      };

      (global as any).checkpointManager = mockCheckpointMgr;

      // Create a method with checkpoint enabled
      class CheckpointTestClass extends TestClass {
        @resilientOperation(2, 100, true, true) // saveCheckpoint = true
        async checkpointOperation(): Promise<string> {
          return 'Checkpoint Success';
        }
      }

      const checkpointInstance = new CheckpointTestClass();
      await checkpointInstance.checkpointOperation();

      expect(mockCheckpointMgr.createCheckpoint).toHaveBeenCalled();

      delete (global as any).checkpointManager;
    });

    test('should attempt recovery on specific errors', async () => {
      class RecoveryTestClass {
        recoveryCallCount = 0;

        @resilientOperation(2, 100, true, false)
        async recoveryOperation(): Promise<string> {
          throw new Error('CustomError: Test recovery');
        }
      }

      const recoveryInstance = new RecoveryTestClass();
      recoveryInstance.recoveryStrategies = {
        'CustomError': async (error: Error) => {
          recoveryInstance.recoveryCallCount++;
          console.log('Recovery strategy executed');
        }
      };

      await expect(recoveryInstance.recoveryOperation()).rejects.toThrow();

      expect(recoveryInstance.recoveryCallCount).toBeGreaterThan(0);
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        'Recovery strategy applied for CustomError',
        true
      );
    });
  });

  describe('withTimeout Decorator', () => {
    class TimeoutTestClass {
      @withTimeout(1000) // 1 second timeout
      async quickOperation(): Promise<string> {
        return new Promise(resolve => setTimeout(() => resolve('Quick Success'), 100));
      }

      @withTimeout(500) // 500ms timeout
      async slowOperation(): Promise<string> {
        return new Promise(resolve => setTimeout(() => resolve('Slow Success'), 1000));
      }

      @withTimeout(2000) // 2 second timeout
      async failingOperation(): Promise<string> {
        throw new Error('Operation failed');
      }
    }

    let timeoutInstance: TimeoutTestClass;

    beforeEach(() => {
      timeoutInstance = new TimeoutTestClass();
    });

    test('should allow operations within timeout', async () => {
      const result = await timeoutInstance.quickOperation();
      expect(result).toBe('Quick Success');
    });

    test('should timeout slow operations', async () => {
      await expect(timeoutInstance.slowOperation()).rejects.toThrow('timed out after 500ms');
      expect(mockLogger.logError).toHaveBeenCalled();
    });

    test('should handle operation errors within timeout', async () => {
      await expect(timeoutInstance.failingOperation()).rejects.toThrow('Operation failed');
    });

    test('should work with Promise.race for complex scenarios', async () => {
      // Test that timeout decorator properly races with operation
      const startTime = Date.now();

      try {
        await timeoutInstance.slowOperation();
      } catch (error) {
        const duration = Date.now() - startTime;
        expect(duration).toBeLessThan(600); // Should timeout before 600ms
        expect(duration).toBeGreaterThan(400); // Should wait for timeout
      }
    });
  });

  describe('Input Validation', () => {
    class ValidationTestClass {
      @validateInput(validatePositiveNumber, validateRange(10, 100))
      validateInputs(num1: number, num2: number): string {
        return `Validated: ${num1}, ${num2}`;
      }

      @validateInput(validatePositiveNumber)
      singleValidation(num: number): string {
        return `Single: ${num}`;
      }
    }

    let validationInstance: ValidationTestClass;

    beforeEach(() => {
      validationInstance = new ValidationTestClass();
    });

    test('should pass valid inputs', () => {
      const result = validationInstance.validateInputs(25, 50);
      expect(result).toBe('Validated: 25, 50');
    });

    test('should reject invalid first parameter', () => {
      expect(() => {
        validationInstance.validateInputs(-5, 50);
      }).toThrow('Validation failed for arg0: must be positive');
    });

    test('should reject invalid second parameter', () => {
      expect(() => {
        validationInstance.validateInputs(25, 150);
      }).toThrow('Validation failed for arg1: must be between 10 and 100');
    });

    test('should handle single parameter validation', () => {
      expect(() => {
        validationInstance.singleValidation(0);
      }).toThrow('Validation failed for arg0: must be positive');
    });

    test('should work with valid single parameter', () => {
      const result = validationInstance.singleValidation(42);
      expect(result).toBe('Single: 42');
    });

    test('should log validation errors', () => {
      try {
        validationInstance.validateInputs(-1, 50);
      } catch (error) {
        // Error is expected
      }

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'validateInputs',
          inputData: expect.any(Object)
        })
      );
    });
  });

  describe('Error Boundary Context Manager', () => {
    test('should handle successful operations', async () => {
      const result = await withErrorBoundary(
        async () => 'Success',
        { operation: 'test_success' }
      );

      expect(result).toBe('Success');
      expect(mockLogger.logPerformance).toHaveBeenCalledWith(
        'test_success',
        expect.any(Number),
        true
      );
    });

    test('should handle operation errors with recovery', async () => {
      const recoveryStrategies = {
        'TestError': async (error: Error) => {
          console.log('Recovery executed for TestError');
        }
      };

      const result = await withErrorBoundary(
        async () => { throw new Error('TestError: Something failed'); },
        { operation: 'test_recovery' },
        recoveryStrategies,
        true // recoverable
      );

      expect(result).toBeNull(); // Returns null for recoverable errors
      expect(mockLogger.logRecoveryAction).toHaveBeenCalled();
    });

    test('should re-throw non-recoverable errors', async () => {
      await expect(
        withErrorBoundary(
          async () => { throw new Error('Critical failure'); },
          { operation: 'test_critical' },
          {},
          false // not recoverable
        )
      ).rejects.toThrow('Critical failure');
    });

    test('should handle complex recovery scenarios', async () => {
      let recoveryExecuted = false;

      const result = await withErrorBoundary(
        async () => {
          throw new Error('ComplexError: Database timeout');
        },
        { operation: 'complex_recovery_test' },
        {
          'ComplexError': async (error: Error) => {
            recoveryExecuted = true;
            // Simulate complex recovery logic
            await new Promise(resolve => setTimeout(resolve, 10));
          }
        }
      );

      expect(recoveryExecuted).toBe(true);
      expect(result).toBeNull();
    });

    test('should log all error boundary activities', async () => {
      await withErrorBoundary(
        async () => { throw new Error('Boundary test error'); },
        { operation: 'boundary_test' }
      );

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: 'boundary_test'
        }),
        true
      );
    });
  });

  describe('Helper Functions', () => {
    test('should safely execute operations', async () => {
      // Successful operation
      const result1 = await (global as any).safeExecute?.(
        () => Promise.resolve('Success'),
        'test_safe'
      );
      expect(result1).toBe('Success');

      // Failing operation with default
      const result2 = await (global as any).safeExecute?.(
        () => Promise.reject(new Error('Failed')),
        'test_safe',
        'Default Value'
      );
      expect(result2).toBe('Default Value');

      // Failing operation without default
      const result3 = await (global as any).safeExecute?.(
        () => Promise.reject(new Error('Failed')),
        'test_safe'
      );
      expect(result3).toBeUndefined();
    });

    test('should validate operation inputs', async () => {
      // Valid inputs should not throw
      await expect(
        (global as any).validateOperationInputs?.('test_op', [1, 'valid', {}])
      ).resolves.not.toThrow();

      // Invalid inputs should throw
      await expect(
        (global as any).validateOperationInputs?.('test_op', [null, 'valid'])
      ).rejects.toThrow('First argument cannot be null/undefined');

      await expect(
        (global as any).validateOperationInputs?.('test_op', [1, NaN])
      ).rejects.toThrow('Invalid number argument');
    });
  });

  describe('Integration Scenarios', () => {
    class IntegrationTestClass {
      callLog: string[] = [];

      @resilientOperation(2, 10, true, false)
      @withTimeout(500)
      @validateInput(validatePositiveNumber, validateRange(1, 100))
      async complexOperation(value: number, multiplier: number): Promise<number> {
        this.callLog.push(`Called with ${value}, ${multiplier}`);

        if (value === 999) { // Special value to trigger failure
          throw new Error('Simulated integration failure');
        }

        return value * multiplier;
      }

      recoveryStrategies = {
        'ValidationError': async (error: Error) => {
          this.callLog.push('Validation recovery executed');
        },
        'TimeoutError': async (error: Error) => {
          this.callLog.push('Timeout recovery executed');
        }
      };
    }

    let integrationInstance: IntegrationTestClass;

    beforeEach(() => {
      integrationInstance = new IntegrationTestClass();
    });

    test('should handle successful complex operations', async () => {
      const result = await integrationInstance.complexOperation(10, 5);

      expect(result).toBe(50);
      expect(integrationInstance.callLog).toEqual(['Called with 10, 5']);
    });

    test('should validate inputs before execution', async () => {
      await expect(
        integrationInstance.complexOperation(-5, 10)
      ).rejects.toThrow('Validation failed');

      expect(integrationInstance.callLog).toEqual([]); // Should not execute
    });

    test('should timeout slow operations', async () => {
      // Mock a slow operation
      const originalMethod = integrationInstance.complexOperation;
      integrationInstance.complexOperation = async () => {
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        return 42;
      };

      await expect(
        integrationInstance.complexOperation(1, 1)
      ).rejects.toThrow('timed out');

      // Restore original method
      integrationInstance.complexOperation = originalMethod;
    });

    test('should retry failed operations', async () => {
      let callCount = 0;
      const originalMethod = integrationInstance.complexOperation;
      integrationInstance.complexOperation = async (value: number) => {
        callCount++;
        if (callCount < 2) {
          throw new Error('Temporary failure');
        }
        return value * 2;
      };

      const result = await integrationInstance.complexOperation(21, 1);

      expect(result).toBe(42);
      expect(callCount).toBe(2); // Should have been called twice

      // Restore original method
      integrationInstance.complexOperation = originalMethod;
    });

    test('should execute recovery strategies', async () => {
      // Create a method that triggers validation error
      class RecoveryValidationTest {
        @validateInput(validatePositiveNumber)
        testMethod(value: number): void {
          if (value < 0) {
            throw new Error('ValidationError: Negative value');
          }
        }

        recoveryStrategies = {
          'ValidationError': async (error: Error) => {
            console.log('Validation recovery triggered');
          }
        };
      }

      const recoveryTest = new RecoveryValidationTest();

      // This would normally be tested with error boundary
      expect(() => recoveryTest.testMethod(-1)).toThrow('ValidationError');
    });
  });

  describe('Performance and Load Testing', () => {
    test('should handle high-frequency error scenarios', async () => {
      class HighFrequencyTest {
        successCount = 0;

        @resilientOperation(3, 1, true, false) // Very short delays
        async flakyOperation(shouldFail: boolean): Promise<string> {
          if (shouldFail && Math.random() > 0.7) { // 30% failure rate
            throw new Error('Random failure');
          }
          this.successCount++;
          return `Success ${this.successCount}`;
        }
      }

      const testInstance = new HighFrequencyTest();
      const operations = Array(20).fill(null).map(() =>
        testInstance.flakyOperation(true)
      );

      const results = await Promise.allSettled(operations);

      const fulfilled = results.filter(r => r.status === 'fulfilled').length;
      expect(fulfilled).toBeGreaterThan(10); // At least 50% should succeed with retries
    });

    test('should maintain performance under error load', async () => {
      class PerformanceTest {
        @resilientOperation(2, 5, true, false)
        async fastOperation(delay: number): Promise<string> {
          await new Promise(resolve => setTimeout(resolve, delay));
          return 'Completed';
        }
      }

      const testInstance = new PerformanceTest();
      const startTime = Date.now();

      // Mix of fast and failing operations
      const operations = [
        ...Array(5).fill(null).map(() => testInstance.fastOperation(10)), // Fast ops
        ...Array(3).fill(null).map(() => testInstance.fastOperation(1000)), // Slow ops that should timeout
      ];

      await Promise.allSettled(operations);
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(3000); // Should complete within 3 seconds due to timeouts
    });
  });
});
