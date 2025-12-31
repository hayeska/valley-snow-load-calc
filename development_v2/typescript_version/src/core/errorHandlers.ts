// Error handling decorators and recovery mechanisms with idempotency support

import {
  logError,
  logPerformance,
  logRecoveryAction,
  getLogger,
} from "../utils/logger";
import { getDatabase } from "../data/database";
import {
  ErrorContext,
  OperationResult,
  Validator,
  ValidationResult,
} from "../types";

export function resilientOperation(
  retries: number = 3,
  backoffMs: number = 1000,
  recoverable: boolean = true,
  saveCheckpoint: boolean = false,
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const logger = getLogger();

    descriptor.value = async function (...args: any[]): Promise<any> {
      const operationName = `${target.constructor.name}.${propertyKey}`;
      const startTime = Date.now();
      let lastError: Error | null = null;
      let checkpointId: string | null = null;

      try {
        // Pre-operation validation
        await validateOperationInputs(operationName, args);

        // Generate idempotency key if method supports it
        const idempotencyKey = this.generateIdempotencyKey
          ? await safeExecute(
              () => this.generateIdempotencyKey(operationName, args),
              `generateIdempotencyKey`,
            )
          : `${operationName}_${Date.now()}_${Math.random()}`;

        // Check if operation already completed (idempotency)
        const db = getDatabase();
        const isCompleted = await safeExecute(
          () => db.isOperationCompleted(idempotencyKey),
          "idempotency_check",
        );

        if (isCompleted) {
          logger.info(
            `Operation ${operationName} already completed (idempotent)`,
            { idempotencyKey },
          );
          try {
            const stored = await db.get(
              `SELECT result FROM idempotency_keys WHERE key = ?`,
              [idempotencyKey],
            );
            return stored ? JSON.parse(stored.result) : null;
          } catch (parseError) {
            logger.logError(parseError as Error, {
              operation: "idempotency_result_parsing",
              idempotencyKey,
            });
            // Continue with operation if parsing fails
          }
        }

        // Execute operation with retry logic
        for (let attempt = 0; attempt <= retries; attempt++) {
          try {
            // Create checkpoint before operation if requested
            if (saveCheckpoint && attempt === 0) {
              checkpointId = await safeExecute(
                () => createOperationCheckpoint(operationName, args, this),
                "create_checkpoint",
              );
            }

            // Execute the original method with timeout protection
            const result = await Promise.race([
              originalMethod.apply(this, args),
              new Promise((_, reject) =>
                setTimeout(
                  () => reject(new Error(`Operation timeout after ${30000}ms`)),
                  30000,
                ),
              ),
            ]);

            const duration = Date.now() - startTime;

            // Mark operation as completed for idempotency
            await safeExecute(
              () => db.markOperationCompleted(idempotencyKey, result),
              "mark_operation_completed",
            );

            logger.logPerformance(operationName, duration, true, {
              attempt: attempt + 1,
              idempotencyKey,
              checkpointId,
            });

            return result;
          } catch (error) {
            lastError = error as Error;
            const duration = Date.now() - startTime;

            const context: ErrorContext = {
              operation: operationName,
              inputData: {
                args: args.map((arg, index) => ({
                  index,
                  type: typeof arg,
                  value:
                    typeof arg === "object"
                      ? "[Object]"
                      : String(arg).substring(0, 100),
                })),
                attempt: attempt + 1,
                maxRetries: retries,
              },
              stackTrace: lastError.stack,
            };

            logger.logError(lastError, context, recoverable);
            logger.logPerformance(operationName, duration, false, {
              attempt: attempt + 1,
              error: lastError.message,
              errorType: lastError.name,
              idempotencyKey,
            });

            // Try recovery strategy if available
            if (
              this.recoveryStrategies &&
              this.recoveryStrategies[lastError.name]
            ) {
              try {
                await safeExecute(
                  () =>
                    this.recoveryStrategies[lastError.name](lastError, ...args),
                  "recovery_strategy",
                );
                logger.logRecoveryAction(
                  `Recovery strategy applied for ${lastError.name}`,
                  true,
                  {
                    operation: operationName,
                    attempt: attempt + 1,
                  },
                );
              } catch (recoveryError) {
                logger.logError(recoveryError as Error, {
                  operation: "recovery_strategy_failed",
                  inputData: { originalError: lastError.message },
                });
              }
            }

            // Try checkpoint recovery if available
            if (checkpointId && attempt < retries) {
              try {
                const recoveredResult = await attemptCheckpointRecovery(
                  operationName,
                  checkpointId,
                  args,
                  this,
                );
                if (recoveredResult !== null) {
                  logger.logRecoveryAction(
                    "Checkpoint recovery successful",
                    true,
                    {
                      operation: operationName,
                      checkpointId,
                      attempt: attempt + 1,
                    },
                  );
                  return recoveredResult;
                }
              } catch (recoveryError) {
                logger.logError(recoveryError as Error, {
                  operation: "checkpoint_recovery_failed",
                  checkpointId,
                });
              }
            }

            // If this is the last attempt or error is not recoverable, don't retry
            if (attempt >= retries || !recoverable) {
              break;
            }

            // Exponential backoff with jitter
            const baseDelay = backoffMs * Math.pow(2, attempt);
            const jitter = Math.random() * 1000; // Add up to 1 second jitter
            const delay = Math.min(baseDelay + jitter, 30000);

            logger.info(
              `Retrying operation ${operationName} in ${Math.round(delay)}ms`,
              {
                attempt: attempt + 1,
                delay: Math.round(delay),
                error: lastError.message,
              },
            );

            await new Promise((resolve) => setTimeout(resolve, delay));
          }
        }

        // All retries exhausted or error not recoverable
        logger.logRecoveryAction(
          `Operation ${operationName} failed after ${retries + 1} attempts`,
          false,
          {
            finalError: lastError?.message,
            totalDuration: Date.now() - startTime,
          },
        );

        throw lastError;
      } catch (error) {
        // Final error handling - this catches any errors in the wrapper itself
        const wrapperError = error as Error;
        logger.logError(
          wrapperError,
          {
            operation: `${operationName}_wrapper`,
            inputData: { originalOperation: operationName },
            stackTrace: wrapperError.stack,
          },
          false,
        );

        throw wrapperError;
      }
    };

    return descriptor;
  };
}

export function withTimeout(timeoutMs: number) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const logger = getLogger();

    descriptor.value = function (...args: any[]): Promise<any> {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          const error = new Error(
            `Operation ${propertyKey} timed out after ${timeoutMs}ms`,
          );
          logger.logError(error, { operation: propertyKey });
          reject(error);
        }, timeoutMs);

        originalMethod
          .apply(this, args)
          .then((result) => {
            clearTimeout(timeout);
            resolve(result);
          })
          .catch((error) => {
            clearTimeout(timeout);
            reject(error);
          });
      });
    };

    return descriptor;
  };
}

export function validateInput(...validators: Validator<any>[]) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = function (...args: any[]): any {
      // Skip 'this' argument for validation
      const methodArgs = args.slice(1);

      for (let i = 0; i < validators.length && i < methodArgs.length; i++) {
        const validator = validators[i];
        const argValue = methodArgs[i];
        const argName = `arg${i}`;

        const result: ValidationResult = validator(argValue, argName);

        if (!result.isValid) {
          const error = new Error(
            `Validation failed for ${argName}: ${result.errors.join(", ")}`,
          );
          logError(error, {
            operation: propertyKey,
            inputData: {
              argName,
              argValue: typeof argValue === "object" ? "[Object]" : argValue,
            },
          });
          throw error;
        }
      }

      return originalMethod.apply(this, args);
    };

    return descriptor;
  };
}

export function autoSave(intervalMinutes: number = 5) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const logger = getLogger();
    let lastSave = Date.now();

    descriptor.value = async function (...args: any[]): Promise<any> {
      const result = await originalMethod.apply(this, args);

      // Check if auto-save is needed
      const now = Date.now();
      const intervalMs = intervalMinutes * 60 * 1000;

      if (now - lastSave > intervalMs) {
        try {
          if (this.saveState) {
            await this.saveState();
            lastSave = now;
            logger.logRecoveryAction("Auto-save completed", true, {
              operation: propertyKey,
              intervalMinutes,
            });
          }
        } catch (error) {
          logger.logError(error as Error, {
            operation: "auto_save",
            inputData: { triggeredBy: propertyKey },
          });
        }
      }

      return result;
    };

    return descriptor;
  };
}

export function checkpointOnChange(changeThreshold: number = 0.1) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const logger = getLogger();
    let lastDataHash: string | null = null;

    descriptor.value = async function (...args: any[]): Promise<any> {
      const result = await originalMethod.apply(this, args);

      // Calculate data hash to detect changes
      if (this.getDataForHash) {
        const currentData = this.getDataForHash();
        const currentHash = calculateSimpleHash(JSON.stringify(currentData));

        if (lastDataHash && currentHash !== lastDataHash) {
          // Significant change detected
          try {
            if (this.createCheckpoint) {
              await this.createCheckpoint("data_change");
              logger.logRecoveryAction(
                "Checkpoint created due to data change",
                true,
                {
                  operation: propertyKey,
                },
              );
            }
          } catch (error) {
            logger.logError(error as Error, {
              operation: "checkpoint_on_change",
              inputData: { triggeredBy: propertyKey },
            });
          }
        }

        lastDataHash = currentHash;
      }

      return result;
    };

    return descriptor;
  };
}

export function idempotent(operationName?: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const logger = getLogger();
    const opName = operationName || propertyKey;

    descriptor.value = async function (
      ...args: any[]
    ): Promise<OperationResult> {
      const idempotencyKey = this.generateIdempotencyKey
        ? this.generateIdempotencyKey(opName, args)
        : `${opName}_${Date.now()}_${Math.random()}`;

      const db = getDatabase();

      // Check if operation already completed
      if (await db.isOperationCompleted(idempotencyKey)) {
        logger.info(`Idempotent operation ${opName} already completed`, {
          idempotencyKey,
        });
        const stored = await db.get(
          `SELECT result FROM idempotency_keys WHERE key = ?`,
          [idempotencyKey],
        );
        return {
          success: true,
          data: stored ? JSON.parse(stored.result) : null,
          idempotencyKey,
        };
      }

      try {
        const result = await originalMethod.apply(this, args);

        // Mark as completed
        await db.markOperationCompleted(idempotencyKey, result);

        return {
          success: true,
          data: result,
          idempotencyKey,
        };
      } catch (error) {
        logger.logError(error as Error, {
          operation: opName,
          inputData: { idempotencyKey },
        });

        return {
          success: false,
          error: error as Error,
          idempotencyKey,
        };
      }
    };

    return descriptor;
  };
}

// Utility functions
function calculateSimpleHash(data: string): string {
  // Simple hash for change detection (not cryptographically secure)
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash.toString();
}

async function createOperationCheckpoint(
  operationName: string,
  args: any[],
  context: any,
): Promise<void> {
  const logger = getLogger();

  try {
    if (context.createCheckpoint) {
      await context.createCheckpoint(operationName);
    } else {
      logger.warn(
        "Checkpoint requested but createCheckpoint method not available",
        {
          operation: operationName,
        },
      );
    }
  } catch (error) {
    logger.logError(error as Error, {
      operation: "create_operation_checkpoint",
      inputData: { operationName },
    });
  }
}

// Input validation functions
export const validatePositiveNumber: Validator<number> = (
  value: any,
  fieldName: string,
): ValidationResult => {
  const num = Number(value);
  if (isNaN(num) || num <= 0) {
    return {
      isValid: false,
      errors: [`${fieldName} must be a positive number`],
    };
  }
  return { isValid: true, errors: [] };
};

export const validateNonEmptyString: Validator<string> = (
  value: any,
  fieldName: string,
): ValidationResult => {
  if (typeof value !== "string" || !value.trim()) {
    return {
      isValid: false,
      errors: [`${fieldName} must be a non-empty string`],
    };
  }
  return { isValid: true, errors: [] };
};

export const validateRange = (min: number, max: number) => {
  return (value: any, fieldName: string): ValidationResult => {
    const num = Number(value);
    if (isNaN(num) || num < min || num > max) {
      return {
        isValid: false,
        errors: [`${fieldName} must be between ${min} and ${max}`],
      };
    }
    return { isValid: true, errors: [] };
  };
};

// Recovery strategies
export interface RecoveryStrategy {
  [errorName: string]: (error: Error, ...args: any[]) => Promise<void>;
}

export function withRecoveryStrategies(strategies: RecoveryStrategy) {
  return function (target: any) {
    target.prototype.recoveryStrategies = strategies;
  };
}

// Error boundary class for complex operations
export class ErrorBoundary {
  private logger = getLogger();
  private recoveryStrategies: RecoveryStrategy;

  constructor(recoveryStrategies: RecoveryStrategy = {}) {
    this.recoveryStrategies = recoveryStrategies;
  }

  async execute<T>(
    operation: () => Promise<T>,
    context: ErrorContext,
    recoverable: boolean = true,
  ): Promise<T> {
    const startTime = Date.now();

    try {
      const result = await operation();
      const duration = Date.now() - startTime;

      this.logger.logPerformance(context.operation, duration, true);
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      const err = error as Error;

      this.logger.logError(err, context, recoverable);
      this.logger.logPerformance(context.operation, duration, false);

      // Try recovery
      if (recoverable && this.recoveryStrategies[err.name]) {
        try {
          await this.recoveryStrategies[err.name](err);
          this.logger.logRecoveryAction(
            `Recovery strategy applied for ${err.name}`,
            true,
          );
        } catch (recoveryError) {
          this.logger.logError(recoveryError as Error, {
            operation: "recovery_strategy",
            inputData: { originalError: err.message },
          });
        }
      }

      if (!recoverable) {
        throw err;
      }

      // Return default value for recoverable errors
      return null as T;
    }
  }
}

// Helper functions for comprehensive error handling

/**
 * Safely executes an operation with error logging
 */
async function safeExecute<T>(
  operation: () => Promise<T> | T,
  operationName: string,
  defaultValue?: T,
): Promise<T | undefined> {
  const logger = getLogger();

  try {
    const result = await (typeof operation === "function"
      ? operation()
      : operation);
    return result;
  } catch (error) {
    logger.logError(error as Error, {
      operation: `safe_execute_${operationName}`,
      stackTrace: (error as Error).stack,
    });

    if (defaultValue !== undefined) {
      logger.info(`Using default value for ${operationName}`, { defaultValue });
      return defaultValue;
    }

    return undefined;
  }
}

/**
 * Validates operation inputs before execution
 */
async function validateOperationInputs(
  operationName: string,
  args: any[],
): Promise<void> {
  const logger = getLogger();

  try {
    // Basic input validation
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];

      // Check for null/undefined in critical positions
      if (i === 0 && (arg === null || arg === undefined)) {
        throw new Error(
          `First argument cannot be null/undefined in ${operationName}`,
        );
      }

      // Check for obviously invalid values
      if (typeof arg === "number" && (isNaN(arg) || !isFinite(arg))) {
        throw new Error(
          `Invalid number argument at position ${i} in ${operationName}: ${arg}`,
        );
      }
    }

    // Operation-specific validation could be added here
    if (operationName.includes("save") || operationName.includes("create")) {
      // Ensure we have valid objects for save operations
      const firstArg = args[0];
      if (typeof firstArg === "object" && firstArg !== null) {
        if (!firstArg.id && !firstArg.name) {
          logger.warn(`Potentially invalid object for ${operationName}`, {
            hasId: !!firstArg.id,
            hasName: !!firstArg.name,
          });
        }
      }
    }
  } catch (error) {
    logger.logError(error as Error, {
      operation: `input_validation_${operationName}`,
      inputData: { argCount: args.length },
    });
    throw error;
  }
}

/**
 * Attempts to recover from a checkpoint
 */
async function attemptCheckpointRecovery(
  operationName: string,
  checkpointId: string,
  originalArgs: any[],
  context: any,
): Promise<any> {
  const logger = getLogger();

  try {
    // Try to get checkpoint manager from context or global
    const checkpointMgr =
      context.checkpointManager || (global as any).checkpointManager;

    if (!checkpointMgr?.restoreFromCheckpoint) {
      logger.warn("No checkpoint manager available for recovery", {
        operationName,
      });
      return null;
    }

    const recoveredData =
      await checkpointMgr.restoreFromCheckpoint(checkpointId);

    if (recoveredData) {
      logger.info(`Recovered data from checkpoint for ${operationName}`, {
        checkpointId,
      });
      return recoveredData;
    }

    return null;
  } catch (error) {
    logger.logError(error as Error, {
      operation: `checkpoint_recovery_attempt`,
      checkpointId,
      originalOperation: operationName,
    });
    return null;
  }
}

/**
 * Creates an operation checkpoint
 */
async function createOperationCheckpoint(
  operationName: string,
  args: any[],
  context: any,
): Promise<string | null> {
  const logger = getLogger();

  try {
    const checkpointMgr =
      context.checkpointManager || (global as any).checkpointManager;

    if (!checkpointMgr?.createCheckpoint) {
      return null;
    }

    // Create a checkpoint with operation context
    const checkpointData = {
      operation: operationName,
      args: args.map((arg, index) => ({
        index,
        type: typeof arg,
        preview:
          typeof arg === "object" ? "[Object]" : String(arg).substring(0, 50),
      })),
      timestamp: new Date().toISOString(),
      context: {
        hasCheckpointManager: !!context.checkpointManager,
        operationType: operationName.split(".").pop(),
      },
    };

    const checkpointId = await checkpointMgr.createCheckpoint(
      context.currentProjectId || "system",
      "operation_checkpoint",
      checkpointData,
    );

    return checkpointId;
  } catch (error) {
    logger.logError(error as Error, {
      operation: "create_operation_checkpoint",
      operationName,
    });
    return null;
  }
}

// Convenience function for error boundary usage
export async function withErrorBoundary<T>(
  operation: () => Promise<T>,
  context: ErrorContext,
  recoveryStrategies: RecoveryStrategy = {},
  recoverable: boolean = true,
): Promise<T> {
  const boundary = new ErrorBoundary(recoveryStrategies);
  return boundary.execute(operation, context, recoverable);
}
