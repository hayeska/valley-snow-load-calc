# Valley Snow Load Calculator - TypeScript Resilient Architecture

A complete TypeScript implementation of the Valley Snow Load Calculator featuring **SQLite persistent storage**, **Winston logging**, **automatic checkpoints**, and **comprehensive error recovery** to prevent data loss from crashes.

## 🚀 Features

### **Persistent Storage**

- **SQLite database** with ACID transactions
- **Data integrity** verification with SHA256 checksums
- **Automatic backups** and point-in-time recovery
- **Concurrent access** protection

### **Comprehensive Logging**

- **Winston logging** with multiple transports
- **Performance monitoring** with operation timing
- **Error tracking** with context and stack traces
- **Crash recovery** logging

### **Auto-Save & Checkpoints**

- **Automatic checkpoints** every 5 minutes
- **Change-based saves** when data is modified
- **Manual checkpoints** on key operations
- **Emergency checkpoints** on application errors

### **Error Handling & Recovery**

- **Resilient operations** with automatic retry
- **Input validation** with custom validators
- **Timeout protection** for long-running calculations
- **Graceful degradation** during failures

### **Idempotent Operations**

- **Idempotency keys** prevent duplicate operations
- **Transaction safety** ensures data consistency
- **Operation deduplication** with TTL-based cleanup

## 📦 Installation

```bash
cd typescript_version
npm install
npm run build
```

## 🏃‍♂️ Quick Start

```typescript
import { ValleySnowLoadCalculator } from "./dist/core/calculator";

async function main() {
  const calculator = new ValleySnowLoadCalculator();

  // Create project with automatic persistence
  const projectId = await calculator.createProject("My Valley Project");

  // Update geometry with validation and auto-save
  await calculator.updateGeometry(projectId, {
    roofPitchN: 8,
    roofPitchW: 10,
    northSpan: 20,
    southSpan: 18,
    ewHalfWidth: 45,
    valleyOffset: 15,
    valleyAngle: 90,
  });

  // Update inputs and auto-calculate results
  await calculator.updateInputs(projectId, {
    groundSnowLoad: 35,
    importanceFactor: 1.1,
    exposureFactor: 1.0,
    thermalFactor: 0.9,
    winterWindParameter: 0.4,
  });

  // Data is automatically saved and checkpointed
  console.log("Project saved with automatic resilience features!");
}
```

## 🏗️ Architecture

```
src/
├── core/
│   ├── calculator.ts      # Main calculator with resilience
│   ├── errorHandlers.ts   # Decorators and recovery logic
│   └── checkpointSystem.ts # Auto-save and checkpointing
├── data/
│   └── database.ts        # SQLite persistence layer
├── utils/
│   └── logger.ts          # Winston logging system
└── types/
    └── index.ts           # TypeScript type definitions
```

## 💾 Persistent Storage Features

### **SQLite Database Schema**

- **Projects table**: Project metadata and JSON data
- **Checkpoints table**: Incremental saves and recovery points
- **Sessions table**: Crash recovery tracking
- **Idempotency keys**: Operation deduplication

### **Data Integrity**

```typescript
// Automatic checksum calculation and verification
const checksum = crypto.createHash("sha256").update(jsonData).digest("hex");

// Data corruption detection
if (!validateChecksum(data, checksum)) {
  // Automatic recovery from checkpoint
  const recovered = await recoverFromCheckpoint(projectId);
}
```

### **Transaction Safety**

```typescript
// ACID transactions for data consistency
await db.run("BEGIN TRANSACTION");
try {
  await db.saveProject(projectData);
  await db.createCheckpoint(checkpointData);
  await db.run("COMMIT");
} catch (error) {
  await db.run("ROLLBACK");
  throw error;
}
```

## 📊 Logging & Monitoring

### **Winston Configuration**

```typescript
const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json(),
  ),
  transports: [
    new winston.transports.DailyRotateFile({
      filename: "logs/error-%DATE%.log",
      level: "error",
    }),
    new winston.transports.Console(),
  ],
});
```

### **Performance Monitoring**

```typescript
// Automatic performance tracking
logger.logPerformance("calculation", duration, success, {
  inputSize: data.length,
  operation: "slope_calculation",
});
```

## 🔄 Auto-Save & Checkpoint System

### **Automatic Checkpoints**

```typescript
// Auto-save every 5 minutes for active projects
const autoSaveInterval = setInterval(
  () => {
    activeProjects.forEach((projectId) => {
      checkpointManager.createCheckpoint(projectId, "auto_save");
    });
  },
  5 * 60 * 1000,
);
```

### **Change-Based Saves**

```typescript
@checkpointOnChange()
async updateProject(projectId: string, data: ProjectData) {
  // Data changes automatically trigger checkpoints
  this.projectData = data;
}
```

### **Recovery Options**

```typescript
const recoveryOptions = await calculator.getRecoveryOptions(projectId);
// Returns: checkpoints, backups, last good state options
```

## 🛡️ Error Handling & Resilience

### **Resilient Operations**

```typescript
@resilientOperation(3, 1000, true, true) // 3 retries, 1s backoff, recoverable, save checkpoint
async performComplexCalculation(inputs: any): Promise<Result> {
  // Operation automatically retried on failure
  // Checkpoint created before execution
  return await riskyCalculation(inputs);
}
```

### **Input Validation**

```typescript
@validateInput(validatePositiveNumber, validateRange(0, 100))
async updateGeometry(geometry: RoofGeometry): Promise<void> {
  // Inputs automatically validated before processing
}
```

### **Timeout Protection**

```typescript
@withTimeout(10000) // 10 second timeout
async performCalculations(): Promise<Results> {
  // Long-running operations automatically timeout
}
```

### **Idempotent Operations**

```typescript
@idempotent('create_project')
async createProject(name: string): Promise<string> {
  // Duplicate calls return same result
  // Automatic deduplication with TTL
}
```

## 🎯 Idempotency Implementation

### **Operation Deduplication**

```typescript
// Generate idempotency key
const key = this.generateIdempotencyKey(operation, args);

// Check if already completed
if (await db.isOperationCompleted(key)) {
  return cachedResult;
}

// Execute operation
const result = await operation();

// Mark as completed with TTL
await db.markOperationCompleted(key, result, 3600); // 1 hour TTL
```

### **Database-Level Idempotency**

```sql
CREATE TABLE idempotency_keys (
  key TEXT PRIMARY KEY,
  operation TEXT NOT NULL,
  expires_at DATETIME NOT NULL,
  result TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Comprehensive Testing Suite

### **Test Coverage Overview**

The test suite provides **enterprise-grade validation** of all data persistence, error handling, and recovery mechanisms:

#### **Database Layer Tests** (`database.test.ts`)

- ✅ **Initialization & Setup**: Database creation, table setup, integrity validation
- ✅ **CRUD Operations**: Save, load, update, delete with data integrity checks
- ✅ **Error Scenarios**: Connection failures, disk full, corruption, timeouts
- ✅ **Retry Logic**: Automatic retries with exponential backoff
- ✅ **Transaction Safety**: Rollback on failures, no data loss
- ✅ **Idempotency**: Operation deduplication, safe retries
- ✅ **System Health**: Status monitoring, diagnostics

#### **Checkpoint System Tests** (`checkpointSystem.test.ts`)

- ✅ **Auto-Save Functionality**: Interval-based checkpoints, activity tracking
- ✅ **Manual Checkpoints**: On-demand saves with operation context
- ✅ **Change Detection**: Data change tracking, threshold-based saves
- ✅ **Recovery Operations**: Checkpoint restoration, recovery options
- ✅ **Crash Simulation**: Emergency checkpoints, graceful shutdown
- ✅ **Performance**: Concurrent operations, memory management

#### **Error Handler Tests** (`errorHandlers.test.ts`)

- ✅ **Resilient Operations**: Retry logic, backoff strategies, timeout handling
- ✅ **Input Validation**: Pre-operation validation, error boundaries
- ✅ **Recovery Strategies**: Custom error recovery, fallback operations
- ✅ **Decorator Integration**: Multiple decorators working together
- ✅ **Performance**: Load testing, concurrent error scenarios

#### **Calculator Integration Tests** (`calculator.test.ts`)

- ✅ **Business Logic**: Project CRUD, geometry/input updates, calculations
- ✅ **Error Resilience**: Validation, recovery, graceful degradation
- ✅ **Idempotent Operations**: Safe duplicate calls
- ✅ **Performance**: Operation timing, success rates

#### **Integration Tests** (`integration.test.ts`)

- ✅ **End-to-End Workflows**: Complete project lifecycles
- ✅ **Real Database Operations**: File-based SQLite testing
- ✅ **Crash Recovery**: Data integrity through failures
- ✅ **Concurrent Load**: Multi-user scenarios, race conditions
- ✅ **Performance Under Load**: Sustained operation testing

### **Running Tests**

```bash
# Run all tests
npm test

# Run with coverage report
npm run test:coverage

# Run specific test suites
npm run test:db           # Database layer tests
npm run test:checkpoint   # Checkpoint system tests
npm run test:error        # Error handler tests
npm run test:calculator   # Calculator integration tests

# Run in watch mode during development
npm run test:watch

# Run with verbose output
npm test -- --verbose
```

### **Test Scenarios Covered**

#### **Data Loss Prevention**

- **Save/Load Operations**: Verify data persistence and integrity
- **Retry Validation**: Ensure no data loss during transient failures
- **Transaction Atomicity**: Partial failures don't corrupt data
- **Backup Recovery**: Data restoration from checkpoints

#### **Crash Simulation**

- **Database Disconnection**: Connection loss mid-operation
- **Disk Full**: Storage exhaustion handling
- **Corruption Detection**: Data integrity validation
- **Timeout Handling**: Long-running operation failures
- **Memory Pressure**: Large dataset handling

#### **Error Recovery Validation**

- **Automatic Retries**: Failed operations retry with backoff
- **Checkpoint Restoration**: Data recovery from save points
- **Graceful Degradation**: System continues with reduced functionality
- **Error Boundary Testing**: Operations fail safely without cascading

#### **Concurrent Access Testing**

- **Race Condition Prevention**: Multiple users accessing same data
- **Lock Contention**: Database-level concurrency handling
- **Transaction Isolation**: Changes don't interfere between operations
- **Performance Scaling**: Maintain speed under load

### **Test Data Integrity**

All tests validate:

- **Checksum Verification**: Data corruption detection
- **Referential Integrity**: Foreign key constraints maintained
- **Data Consistency**: Related data stays synchronized
- **Recovery Completeness**: All data recoverable after failures

### **Performance Benchmarks**

Tests include performance validation:

- **Operation Timing**: Individual operations complete within time limits
- **Throughput Testing**: Bulk operations handle expected load
- **Memory Usage**: No memory leaks during extended testing
- **Concurrent Performance**: Maintain speed with multiple operations

### **CI/CD Integration**

Tests are designed for automated testing:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    npm ci
    npm run build
    npm run test:coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage/lcov.info
```

### **Debugging Failed Tests**

When tests fail, detailed logging helps identify issues:

```bash
# Run with detailed output
npm test -- --verbose

# Run single failing test
npm test -- --testNamePattern="should handle database lock errors"

# Debug with Node inspector
npm test -- --inspect-brk
```

### **Test Environment Setup**

Tests use isolated environments:

- **Temporary Databases**: Each test gets clean SQLite database
- **Mock Dependencies**: Logger, checkpoint manager mocked where needed
- **Real Integration**: Full stack testing with real components
- **Cleanup**: Automatic cleanup prevents test interference

### **Coverage Requirements**

Tests maintain high coverage standards:

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 70,
      "functions": 80,
      "lines": 80,
      "statements": 80
    }
  }
}
```

### **Continuous Testing**

Tests validate the resilience claims:

- **No Data Loss**: Verified through retry and transaction testing
- **Error Recovery**: All error paths lead to valid system states
- **Performance**: Operations complete within expected time bounds
- **Reliability**: System maintains functionality under adverse conditions

## 📈 Performance & Reliability

### **Performance Metrics**

- **Operation timing** automatically tracked
- **Success rates** calculated per operation type
- **Bottleneck identification** through logging analysis

### **Reliability Features**

- **Crash detection** and automatic recovery
- **Data integrity** verification on load
- **Backup creation** and validation
- **Graceful degradation** during partial failures

## 🛡️ Comprehensive Error Handling

### **Global Error Management**

```typescript
// Automatic global error handling
process.on("uncaughtException", async (error) => {
  await logger.logCriticalError(error, "uncaught_exception");
  await performEmergencyRecovery(error);
  setTimeout(() => process.exit(1), 2000);
});

process.on("unhandledRejection", async (reason, promise) => {
  await logger.logUnhandledRejection(reason, promise);
  // Handle without crashing
});
```

### **Resilient Operation Wrappers**

```typescript
@resilientOperation(3, 1000, true, true)
async function riskyOperation(data: any): Promise<Result> {
  // Operation automatically retried on failure
  // Checkpoint created before execution
  // Errors logged with full context
  return await performRiskyCalculation(data);
}
```

### **Error Boundary Contexts**

```typescript
const result = await withErrorBoundary(
  () => riskyDatabaseOperation(),
  { operation: "db_query", userId },
  {
    TimeoutError: async (error) => {
      // Custom recovery for timeouts
      return await fallbackQuery();
    },
    ConnectionError: async (error) => {
      // Custom recovery for connection issues
      await reconnectDatabase();
      return await retryQuery();
    },
  },
);
```

### **Recovery Strategies**

```typescript
// Define recovery strategies for different error types
const recoveryStrategies = {
  ValidationError: async (error: Error) => {
    console.warn("Validation failed, using defaults");
  },
  DatabaseError: async (error: Error) => {
    await attemptDatabaseReconnect();
  },
  TimeoutError: async (error: Error) => {
    return await simplifiedCalculation();
  },
};
```

### **Input Validation with Error Logging**

```typescript
@validateInput(validatePositiveNumber, validateNonEmptyString)
async function processUserInput(value: number, name: string) {
  // Invalid inputs automatically logged and rejected
  return await processValidData(value, name);
}

// Custom validators
const validatePositiveNumber: Validator<number> = (value, fieldName) => {
  if (value <= 0) {
    return { isValid: false, errors: [`${fieldName} must be positive`] };
  }
  return { isValid: true, errors: [] };
};
```

### **Timeout Protection**

```typescript
@withTimeout(5000) // 5 second timeout
async function longRunningCalculation(): Promise<Result> {
  // Automatically times out and logs timeout errors
  return await complexEngineeringCalculation();
}
```

### **Idempotent Operations**

```typescript
@idempotent('create_project')
async function createProject(name: string): Promise<Project> {
  // Duplicate calls return same result safely
  // Automatic deduplication prevents side effects
  return await doCreateProject(name);
}
```

## 🔧 Configuration

### **Environment Variables**

```bash
# Database
DB_PATH=./data/valley_calc.db

# Logging
LOG_LEVEL=info
LOG_DIR=./logs

# Checkpoints
AUTO_SAVE_INTERVAL=300000  # 5 minutes in ms
MAX_CHECKPOINTS=50

# Timeouts
CALCULATION_TIMEOUT=30000  # 30 seconds
```

### **Runtime Configuration**

```typescript
const calculator = new ValleySnowLoadCalculator({
  autoSaveInterval: 5 * 60 * 1000, // 5 minutes
  maxRetries: 3,
  checkpointOnChange: true,
  enablePerformanceLogging: true,
});
```

## 🚀 Production Deployment

### **Build**

```bash
npm run build
```

### **Run**

```bash
# Development
npm run dev

# Production
npm start
```

### **Monitoring**

```typescript
// Health check endpoint
app.get("/health", async (req, res) => {
  const health = await calculator.getSystemHealth();
  res.json(health);
});

// Metrics endpoint
app.get("/metrics", async (req, res) => {
  const performance = logger.getPerformanceStats();
  const errors = logger.getErrorSummary();
  res.json({ performance, errors });
});
```

## 🔍 Troubleshooting

### **Common Issues**

**Database Connection Failed**

```bash
# Check database file permissions
ls -la data/valley_calc.db

# Reinitialize database
rm data/valley_calc.db
npm run build && npm start
```

**High Memory Usage**

```typescript
// Adjust checkpoint settings
const calculator = new ValleySnowLoadCalculator({
  maxCheckpoints: 25, // Reduce from default 50
  autoSaveInterval: 10 * 60 * 1000, // Increase to 10 minutes
});
```

**Slow Performance**

```typescript
// Enable performance logging to identify bottlenecks
const logger = getLogger();
const stats = logger.getPerformanceStats("slow_operation");
// Analyze stats to optimize
```

## 📚 API Reference

### **ValleySnowLoadCalculator**

#### **Project Operations**

- `createProject(name, description?)` - Create new project
- `loadProject(projectId)` - Load existing project
- `saveProject(projectData)` - Save project with auto-checkpoint
- `deleteProject(projectId)` - Delete project safely

#### **Calculation Operations**

- `updateGeometry(projectId, geometry)` - Update with validation
- `updateInputs(projectId, inputs)` - Update and recalculate
- `performCalculations(geometry, inputs)` - Core calculations

#### **Recovery Operations**

- `getRecoveryOptions(projectId)` - List recovery options
- `recoverFromCheckpoint(checkpointId)` - Restore from checkpoint

#### **System Operations**

- `listProjects()` - List all projects
- `getSystemHealth()` - System health status

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add** comprehensive tests
4. **Ensure** all resilience features work
5. **Submit** a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues with the resilient architecture:

1. Check system health: `calculator.getSystemHealth()`
2. Review logs in `./logs/` directory
3. Run recovery: `calculator.getRecoveryOptions(projectId)`
4. Contact support with health check results
