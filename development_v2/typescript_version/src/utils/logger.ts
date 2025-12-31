// Winston-based logging system with error tracking and performance monitoring

import winston from "winston";
import DailyRotateFile from "winston-daily-rotate-file";
import path from "path";
import os from "os";
import { ErrorContext, PerformanceMetrics } from "../types";

export class ResilienceLogger {
  private logger: winston.Logger;
  private performanceData: Map<string, PerformanceMetrics[]> = new Map();
  private errorPatterns: Map<string, number> = new Map();

  constructor(logDir?: string) {
    const baseLogDir =
      logDir ||
      path.join(os.homedir(), "AppData", "Local", "ValleySnowLoadCalc", "logs");

    // Create logs directory if it doesn't exist
    const fs = require("fs");
    if (!fs.existsSync(baseLogDir)) {
      fs.mkdirSync(baseLogDir, { recursive: true });
    }

    // Configure Winston with multiple transports
    this.logger = winston.createLogger({
      level: "info",
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json(),
      ),
      defaultMeta: { service: "valley-snow-calc" },
      transports: [
        // Error log - only errors and above
        new DailyRotateFile({
          filename: path.join(baseLogDir, "error-%DATE%.log"),
          datePattern: "YYYY-MM-DD",
          level: "error",
          maxSize: "20m",
          maxFiles: "14d",
        }),

        // Combined log - all levels
        new DailyRotateFile({
          filename: path.join(baseLogDir, "combined-%DATE%.log"),
          datePattern: "YYYY-MM-DD",
          maxSize: "20m",
          maxFiles: "30d",
        }),

        // Performance log
        new DailyRotateFile({
          filename: path.join(baseLogDir, "performance-%DATE%.log"),
          datePattern: "YYYY-MM-DD",
          level: "info",
          maxSize: "20m",
          maxFiles: "30d",
        }),

        // Console log for development
        new winston.transports.Console({
          level: "info",
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple(),
          ),
        }),
      ],
    });

    // Handle uncaught exceptions and unhandled rejections
    this.setupGlobalErrorHandlers();
  }

  private setupGlobalErrorHandlers(): void {
    // Enhanced uncaught exception handler with emergency recovery
    process.on("uncaughtException", async (error: Error) => {
      console.error("🚨 CRITICAL: Uncaught Exception detected!");
      console.error(error);

      try {
        // Log the critical error with full context
        await this.logCriticalError(error, "uncaught_exception");

        // Attempt emergency recovery
        await this.performEmergencyRecovery(error);

        console.log(
          "📝 Critical error logged and emergency recovery attempted",
        );
      } catch (loggingError) {
        // Last resort - write to stderr if logging fails
        console.error("💥 FAILED TO LOG CRITICAL ERROR:", loggingError);
        console.error("Original error:", error);
      }

      // Give time for async logging to complete, then exit
      setTimeout(() => {
        console.error("💀 Process terminating due to uncaught exception");
        process.exit(1);
      }, 2000);
    });

    // Enhanced unhandled rejection handler
    process.on(
      "unhandledRejection",
      async (reason: any, promise: Promise<any>) => {
        console.warn("⚠️  Unhandled Promise Rejection detected!");

        try {
          const error =
            reason instanceof Error ? reason : new Error(String(reason));
          await this.logUnhandledRejection(error, promise);

          // Attempt to prevent crash by resolving the promise
          if (typeof promise?.catch === "function") {
            promise.catch((err) => {
              console.warn("🔧 Promise rejection handled:", err.message);
            });
          }
        } catch (loggingError) {
          console.error("❌ Failed to log unhandled rejection:", loggingError);
          console.error("Original rejection:", reason);
        }
      },
    );

    // Enhanced graceful shutdown
    const shutdownHandler = async (signal: string) => {
      console.log(`📴 Received ${signal}, initiating graceful shutdown...`);

      try {
        // Perform final emergency checkpoint
        await this.performGracefulShutdown();

        // Flush all pending logs
        await this.flushLogs();

        console.log("✅ Graceful shutdown completed");
        process.exit(0);
      } catch (error) {
        console.error("❌ Error during graceful shutdown:", error);
        process.exit(1);
      }
    };

    process.on("SIGINT", () => shutdownHandler("SIGINT"));
    process.on("SIGTERM", () => shutdownHandler("SIGTERM"));
    process.on("SIGUSR2", () => shutdownHandler("SIGUSR2")); // nodemon restart

    // Handle Windows-specific signals
    process.on("SIGBREAK", () => shutdownHandler("SIGBREAK"));

    // Handle process warnings
    process.on("warning", (warning) => {
      this.logger.warn("Process warning detected", {
        message: warning.message,
        name: warning.name,
        stack: warning.stack,
        code: (warning as any).code,
      });
    });
  }

  private async logCriticalError(
    error: Error,
    operation: string,
  ): Promise<void> {
    const criticalContext = {
      operation,
      stackTrace: error.stack,
      timestamp: new Date().toISOString(),
      processInfo: {
        pid: process.pid,
        platform: process.platform,
        version: process.version,
        uptime: process.uptime(),
        memory: process.memoryUsage(),
      },
      environment: {
        node_env: process.env.NODE_ENV,
        cwd: process.cwd(),
        execPath: process.execPath,
      },
    };

    // Log to all available transports
    this.logger.error("🚨 CRITICAL UNCAUGHT EXCEPTION", {
      error: {
        message: error.message,
        name: error.name,
        stack: error.stack,
      },
      context: criticalContext,
    });

    // Also write to stderr for immediate visibility
    console.error("\n" + "=".repeat(80));
    console.error("🚨 CRITICAL ERROR - APPLICATION CRASH DETECTED");
    console.error("=".repeat(80));
    console.error(`Time: ${new Date().toISOString()}`);
    console.error(`Error: ${error.name}: ${error.message}`);
    console.error(`Stack Trace:\n${error.stack}`);
    console.error("=".repeat(80));
  }

  private async logUnhandledRejection(
    error: Error,
    promise: Promise<any>,
  ): Promise<void> {
    this.logger.error("Unhandled Promise Rejection", {
      error: {
        message: error.message,
        name: error.name,
        stack: error.stack,
      },
      promise: {
        toString: promise.toString(),
        constructor: promise.constructor?.name,
      },
      timestamp: new Date().toISOString(),
    });
  }

  private async performEmergencyRecovery(error: Error): Promise<void> {
    try {
      console.log("🔧 Attempting emergency recovery...");

      // Get checkpoint manager and perform emergency checkpoints
      const checkpointMgr = (global as any).checkpointManager;
      if (checkpointMgr?.emergencyCheckpointAll) {
        await checkpointMgr.emergencyCheckpointAll();
        console.log("✅ Emergency checkpoints created");
      }

      // Log recovery attempt
      this.logger.info("Emergency recovery completed", {
        error: error.message,
        timestamp: new Date().toISOString(),
      });
    } catch (recoveryError) {
      console.error("❌ Emergency recovery failed:", recoveryError);
      this.logger.error("Emergency recovery failed", {
        originalError: error.message,
        recoveryError:
          recoveryError instanceof Error
            ? recoveryError.message
            : String(recoveryError),
      });
    }
  }

  private async performGracefulShutdown(): Promise<void> {
    console.log("🧹 Performing graceful shutdown tasks...");

    // Close database connections
    const db = (global as any).database;
    if (db?.close) {
      await db.close();
      console.log("✅ Database connections closed");
    }

    // Final checkpoint
    const checkpointMgr = (global as any).checkpointManager;
    if (checkpointMgr?.shutdown) {
      await checkpointMgr.shutdown();
      console.log("✅ Checkpoint system shut down");
    }

    // Log shutdown
    this.logger.info("Application shutdown completed", {
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    });
  }

  private async flushLogs(): Promise<void> {
    // Give winston time to flush all logs
    return new Promise((resolve) => {
      this.logger.end(() => {
        setTimeout(resolve, 500);
      });
    });
  }

  logError(
    error: Error,
    context: ErrorContext,
    recoverable: boolean = true,
  ): void {
    const errorInfo = {
      message: error.message,
      name: error.name,
      stack: error.stack,
      context,
      recoverable,
      timestamp: new Date().toISOString(),
    };

    // Track error patterns
    const errorKey = `${error.name}:${context.operation}`;
    const currentCount = this.errorPatterns.get(errorKey) || 0;
    this.errorPatterns.set(errorKey, currentCount + 1);

    // Log based on severity
    if (recoverable) {
      this.logger.warn("Error occurred", errorInfo);
    } else {
      this.logger.error("Critical error occurred", errorInfo);
    }
  }

  logPerformance(
    operation: string,
    duration: number,
    success: boolean = true,
    metadata?: Record<string, any>,
  ): void {
    const metrics: PerformanceMetrics = {
      operation,
      duration,
      success,
      timestamp: new Date(),
      metadata,
    };

    // Store in memory for analysis
    if (!this.performanceData.has(operation)) {
      this.performanceData.set(operation, []);
    }

    const operationData = this.performanceData.get(operation)!;
    operationData.push(metrics);

    // Keep only last 100 entries per operation
    if (operationData.length > 100) {
      operationData.shift();
    }

    // Log to performance transport
    this.logger.info("Performance metrics", {
      operation,
      duration,
      success,
      metadata,
      timestamp: metrics.timestamp.toISOString(),
    });
  }

  logRecoveryAction(
    action: string,
    success: boolean,
    details?: Record<string, any>,
  ): void {
    this.logger.info("Recovery action", {
      action,
      success,
      details,
      timestamp: new Date().toISOString(),
    });
  }

  logCheckpoint(
    checkpointId: string,
    dataSize: number,
    operation: string,
  ): void {
    this.logger.info("Checkpoint created", {
      checkpointId,
      dataSize,
      operation,
      timestamp: new Date().toISOString(),
    });
  }

  logDatabaseOperation(
    operation: string,
    success: boolean,
    duration: number,
    metadata?: Record<string, any>,
  ): void {
    this.logger.info("Database operation", {
      operation,
      success,
      duration,
      metadata,
      timestamp: new Date().toISOString(),
    });
  }

  getPerformanceStats(operation?: string): Record<string, any> {
    if (operation) {
      const data = this.performanceData.get(operation) || [];
      if (data.length === 0) return {};

      const durations = data.map((d) => d.duration);
      const successCount = data.filter((d) => d.success).length;

      return {
        operation,
        count: data.length,
        avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
        minDuration: Math.min(...durations),
        maxDuration: Math.max(...durations),
        successRate: successCount / data.length,
        lastExecution: data[data.length - 1]?.timestamp,
      };
    } else {
      // Return stats for all operations
      const stats: Record<string, any> = {};
      for (const [op, data] of this.performanceData.entries()) {
        if (data.length > 0) {
          const durations = data.map((d) => d.duration);
          stats[op] = {
            count: data.length,
            avgDuration:
              durations.reduce((a, b) => a + b, 0) / durations.length,
            successRate: data.filter((d) => d.success).length / data.length,
          };
        }
      }
      return stats;
    }
  }

  getErrorSummary(): Record<string, any> {
    const errorArray = Array.from(this.errorPatterns.entries());
    const totalErrors = errorArray.reduce((sum, [, count]) => sum + count, 0);

    return {
      totalErrors,
      errorPatterns: Object.fromEntries(errorArray),
      mostCommonError:
        errorArray.length > 0
          ? errorArray.reduce((prev, current) =>
              current[1] > prev[1] ? current : prev,
            )
          : null,
    };
  }

  cleanupOldLogs(daysToKeep: number = 30): void {
    // This would be implemented to clean up old log files
    // For now, Winston's DailyRotateFile handles this automatically
    this.logger.info("Log cleanup requested", { daysToKeep });
  }

  // Convenience methods
  info(message: string, meta?: any): void {
    this.logger.info(message, meta);
  }

  warn(message: string, meta?: any): void {
    this.logger.warn(message, meta);
  }

  error(message: string, meta?: any): void {
    this.logger.error(message, meta);
  }

  debug(message: string, meta?: any): void {
    this.logger.debug(message, meta);
  }
}

// Global logger instance
let loggerInstance: ResilienceLogger | null = null;

export function getLogger(): ResilienceLogger {
  if (!loggerInstance) {
    loggerInstance = new ResilienceLogger();
  }
  return loggerInstance;
}

// Convenience functions
export function logError(
  error: Error,
  context: ErrorContext,
  recoverable: boolean = true,
): void {
  getLogger().logError(error, context, recoverable);
}

export function logPerformance(
  operation: string,
  duration: number,
  success?: boolean,
  metadata?: Record<string, any>,
): void {
  getLogger().logPerformance(operation, duration, success, metadata);
}

export function logRecoveryAction(
  action: string,
  success: boolean,
  details?: Record<string, any>,
): void {
  getLogger().logRecoveryAction(action, success, details);
}
