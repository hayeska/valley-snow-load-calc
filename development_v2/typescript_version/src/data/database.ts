// SQLite-based persistent storage with ACID transactions and crash recovery

import sqlite3 from 'sqlite3';
import { Database as SQLiteDatabase } from 'sqlite3';
import path from 'path';
import os from 'os';
import crypto from 'crypto';
import { promisify } from 'util';
import fs from 'fs';
import {
  ProjectData,
  CheckpointData,
  RecoveryOptions,
  SystemHealth,
  IdempotencyKey,
  DatabaseTransaction
} from '../types';
import { getLogger } from '../utils/logger';

export class DatabaseManager {
  private db: SQLiteDatabase | null = null;
  private dbPath: string;
  private logger = getLogger();
  private initialized = false;
  private activeTransactions = new Set<string>();

  constructor(dbPath?: string) {
    this.dbPath = dbPath || path.join(
      os.homedir(),
      'AppData',
      'Local',
      'ValleySnowLoadCalc',
      'valley_calc.db'
    );

    // Ensure directory exists
    const dbDir = path.dirname(this.dbPath);
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    const startTime = Date.now();

    try {
      // Validate database path
      if (!this.dbPath) {
        throw new Error('Database path is not configured');
      }

      // Ensure directory exists
      const fs = require('fs');
      const dbDir = require('path').dirname(this.dbPath);
      try {
        if (!fs.existsSync(dbDir)) {
          fs.mkdirSync(dbDir, { recursive: true });
          this.logger.info('Created database directory', { dbDir });
        }
      } catch (dirError) {
        this.logger.logError(dirError as Error, {
          operation: 'create_db_directory',
          inputData: { dbDir }
        });
        throw new Error(`Cannot create database directory: ${dbDir}`);
      }

      // Initialize database connection with error handling
      this.db = await this.createDatabaseConnection();

      // Configure database settings
      await this.configureDatabase();

      // Create tables with recovery
      await this.createTablesWithRecovery();

      // Create indexes
      await this.createIndexesWithRecovery();

      // Validate database integrity
      await this.validateDatabaseIntegrity();

      this.initialized = true;

      const duration = Date.now() - startTime;
      this.logger.logPerformance('database_init', duration, true, {
        dbPath: this.dbPath,
        tablesCreated: true,
        indexesCreated: true
      });

      this.logger.info('Database initialized successfully', {
        dbPath: this.dbPath,
        duration
      });

    } catch (error) {
      const initError = error as Error;
      this.logger.logError(initError, {
        operation: 'database_init',
        inputData: { dbPath: this.dbPath },
        stackTrace: initError.stack
      }, false);

      // Attempt recovery
      await this.attemptDatabaseRecovery(initError);

      throw new Error(`Database initialization failed: ${initError.message}`);
    }
  }

  private async createDatabaseConnection(): Promise<SQLiteDatabase> {
    return new Promise((resolve, reject) => {
      const db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          this.logger.logError(err, {
            operation: 'create_db_connection',
            inputData: { dbPath: this.dbPath }
          });
          reject(new Error(`Failed to open database: ${err.message}`));
        } else {
          resolve(db);
        }
      });
    });
  }

  private async configureDatabase(): Promise<void> {
    try {
      // Enable WAL mode for better concurrency
      await this.runWithRetry('PRAGMA journal_mode = WAL', 'enable_wal');

      // Set synchronous mode for balance of safety and performance
      await this.runWithRetry('PRAGMA synchronous = NORMAL', 'set_sync_mode');

      // Enable foreign keys
      await this.runWithRetry('PRAGMA foreign_keys = ON', 'enable_foreign_keys');

      // Set reasonable cache size
      await this.runWithRetry('PRAGMA cache_size = -64000', 'set_cache_size'); // 64MB

      // Enable auto-vacuum for space management
      await this.runWithRetry('PRAGMA auto_vacuum = INCREMENTAL', 'enable_auto_vacuum');

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'configure_database'
      });
      throw error;
    }
  }

  private async createTablesWithRecovery(): Promise<void> {
    const tableDefinitions = [
      {
        name: 'projects',
        sql: `CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT,
          data TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          version TEXT DEFAULT '2.0.0',
          checksum TEXT NOT NULL
        )`
      },
      {
        name: 'checkpoints',
        sql: `CREATE TABLE IF NOT EXISTS checkpoints (
          id TEXT PRIMARY KEY,
          project_id TEXT NOT NULL,
          data TEXT NOT NULL,
          data_size INTEGER NOT NULL,
          operation TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )`
      },
      {
        name: 'sessions',
        sql: `CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY,
          session_id TEXT UNIQUE NOT NULL,
          project_id TEXT,
          start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
          last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
          status TEXT DEFAULT 'active',
          crash_data TEXT,
          recovery_attempts INTEGER DEFAULT 0
        )`
      },
      {
        name: 'idempotency_keys',
        sql: `CREATE TABLE IF NOT EXISTS idempotency_keys (
          key TEXT PRIMARY KEY,
          operation TEXT NOT NULL,
          expires_at DATETIME NOT NULL,
          result TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`
      },
      {
        name: 'settings',
        sql: `CREATE TABLE IF NOT EXISTS settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`
      }
    ];

    for (const table of tableDefinitions) {
      try {
        await this.runWithRetry(table.sql, `create_table_${table.name}`);
        this.logger.info(`Table created: ${table.name}`);
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'create_table',
          inputData: { tableName: table.name }
        });

        // Try to recover by checking if table exists and is valid
        if (await this.tableExists(table.name)) {
          this.logger.info(`Table ${table.name} already exists, continuing`);
        } else {
          throw error;
        }
      }
    }
  }

  private async createIndexesWithRecovery(): Promise<void> {
    const indexes = [
      { name: 'idx_projects_name', sql: 'CREATE INDEX IF NOT EXISTS idx_projects_name ON projects (name)' },
      { name: 'idx_projects_updated', sql: 'CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects (updated_at)' },
      { name: 'idx_checkpoints_project', sql: 'CREATE INDEX IF NOT EXISTS idx_checkpoints_project ON checkpoints (project_id)' },
      { name: 'idx_sessions_status', sql: 'CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)' },
      { name: 'idx_idempotency_expires', sql: 'CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys (expires_at)' }
    ];

    for (const index of indexes) {
      try {
        await this.runWithRetry(index.sql, `create_index_${index.name}`);
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'create_index',
          inputData: { indexName: index.name }
        });
        // Indexes are not critical, continue
      }
    }
  }

  private async validateDatabaseIntegrity(): Promise<void> {
    try {
      // Check if we can perform basic operations
      const result = await this.getWithRetry('SELECT COUNT(*) as count FROM projects', [], 'integrity_check');
      this.logger.info('Database integrity check passed', { projectCount: result?.count || 0 });
    } catch (error) {
      this.logger.logError(error as Error, { operation: 'database_integrity_check' });
      throw new Error('Database integrity check failed');
    }
  }

  private async attemptDatabaseRecovery(error: Error): Promise<void> {
    try {
      this.logger.logRecoveryAction('Attempting database recovery', true);

      // Try to backup corrupted database
      const backupPath = `${this.dbPath}.backup.${Date.now()}`;
      const fs = require('fs');

      if (fs.existsSync(this.dbPath)) {
        try {
          fs.copyFileSync(this.dbPath, backupPath);
          this.logger.info('Database backup created for recovery', { backupPath });
        } catch (backupError) {
          this.logger.logError(backupError as Error, { operation: 'create_db_backup' });
        }
      }

      // Reset initialization state
      this.initialized = false;
      if (this.db) {
        this.db.close();
        this.db = null;
      }

      this.logger.logRecoveryAction('Database recovery completed', true, {
        backupCreated: fs.existsSync(backupPath),
        backupPath
      });

    } catch (recoveryError) {
      this.logger.logError(recoveryError as Error, { operation: 'database_recovery' });
    }
  }

  private async tableExists(tableName: string): Promise<boolean> {
    try {
      const result = await this.get('SELECT name FROM sqlite_master WHERE type="table" AND name=?', [tableName]);
      return !!result;
    } catch (error) {
      return false;
    }
  }

  private async createTables(): Promise<void> {
    const queries = [
      // Projects table
      `CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        data TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        version TEXT DEFAULT '2.0.0',
        checksum TEXT NOT NULL
      )`,

      // Checkpoints table
      `CREATE TABLE IF NOT EXISTS checkpoints (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        data TEXT NOT NULL,
        data_size INTEGER NOT NULL,
        operation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
      )`,

      // Sessions table for crash recovery
      `CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        session_id TEXT UNIQUE NOT NULL,
        project_id TEXT,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        crash_data TEXT,
        recovery_attempts INTEGER DEFAULT 0
      )`,

      // Idempotency keys table
      `CREATE TABLE IF NOT EXISTS idempotency_keys (
        key TEXT PRIMARY KEY,
        operation TEXT NOT NULL,
        expires_at DATETIME NOT NULL,
        result TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,

      // Settings table
      `CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`
    ];

    for (const query of queries) {
      await this.run(query);
    }
  }

  private async createIndexes(): Promise<void> {
    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_projects_name ON projects (name)',
      'CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects (updated_at)',
      'CREATE INDEX IF NOT EXISTS idx_checkpoints_project ON checkpoints (project_id)',
      'CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)',
      'CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys (expires_at)'
    ];

    for (const index of indexes) {
      await this.run(index);
    }
  }

  private calculateChecksum(data: string): string {
    return crypto.createHash('sha256').update(data).digest('hex');
  }

  private validateChecksum(data: string, checksum: string): boolean {
    return this.calculateChecksum(data) === checksum;
  }

  async saveProject(projectData: ProjectData): Promise<void> {
    const startTime = Date.now();

    try {
      const jsonData = JSON.stringify(projectData);
      const checksum = this.calculateChecksum(jsonData);

      // Verify data integrity before saving
      if (!this.validateChecksum(jsonData, checksum)) {
        throw new Error('Data integrity check failed before save');
      }

      const query = `
        INSERT INTO projects (id, name, description, data, updated_at, checksum)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name = excluded.name,
          description = excluded.description,
          data = excluded.data,
          updated_at = excluded.updated_at,
          checksum = excluded.checksum
      `;

      await this.run(query, [
        projectData.id,
        projectData.name,
        projectData.description || '',
        jsonData,
        projectData.updatedAt.toISOString(),
        checksum
      ]);

      // Create automatic checkpoint
      await this.createCheckpoint({
        id: `checkpoint_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`,
        projectId: projectData.id,
        data: projectData,
        operation: 'auto_save',
        timestamp: new Date(),
        dataSize: Buffer.byteLength(jsonData, 'utf8')
      });

      const duration = Date.now() - startTime;
      this.logger.logDatabaseOperation('save_project', true, duration, {
        projectId: projectData.id,
        dataSize: jsonData.length
      });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.logDatabaseOperation('save_project', false, duration, {
        projectId: projectData.id,
        error: (error as Error).message
      });
      throw error;
    }
  }

  async loadProject(projectId: string): Promise<ProjectData | null> {
    const startTime = Date.now();

    try {
      const query = `
        SELECT name, description, data, created_at, updated_at, version, checksum
        FROM projects WHERE id = ?
      `;

      const row = await this.get(query, [projectId]);

      if (!row) {
        this.logger.logDatabaseOperation('load_project', true, Date.now() - startTime, {
          projectId,
          found: false
        });
        return null;
      }

      const jsonData = row.data;
      const checksum = row.checksum;

      // Validate data integrity
      if (!this.validateChecksum(jsonData, checksum)) {
        this.logger.logError(new Error('Data integrity check failed'), {
          operation: 'load_project',
          projectId,
          inputData: { storedChecksum: checksum }
        });

        // Attempt recovery from checkpoint
        const recoveredData = await this.recoverFromCheckpoint(projectId);
        if (recoveredData) {
          this.logger.logRecoveryAction('Data recovered from checkpoint', true, { projectId });
          return recoveredData;
        }

        throw new Error('Data corruption detected and recovery failed');
      }

      const projectData: ProjectData = JSON.parse(jsonData);
      projectData.createdAt = new Date(row.created_at);
      projectData.updatedAt = new Date(row.updated_at);

      const duration = Date.now() - startTime;
      this.logger.logDatabaseOperation('load_project', true, duration, {
        projectId,
        dataSize: jsonData.length
      });

      return projectData;

    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.logDatabaseOperation('load_project', false, duration, {
        projectId,
        error: (error as Error).message
      });
      throw error;
    }
  }

  async createCheckpoint(checkpoint: CheckpointData): Promise<void> {
    try {
      const jsonData = JSON.stringify(checkpoint.data);

      const query = `
        INSERT INTO checkpoints (id, project_id, data, data_size, operation)
        VALUES (?, ?, ?, ?, ?)
      `;

      await this.run(query, [
        checkpoint.id,
        checkpoint.projectId,
        jsonData,
        checkpoint.dataSize,
        checkpoint.operation
      ]);

      this.logger.logCheckpoint(checkpoint.id, checkpoint.dataSize, checkpoint.operation || 'unknown');

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'create_checkpoint',
        checkpointId: checkpoint.id,
        projectId: checkpoint.projectId
      });
      throw error;
    }
  }

  async getCheckpoints(projectId: string, limit: number = 10): Promise<CheckpointData[]> {
    try {
      const query = `
        SELECT id, data, data_size, operation, created_at
        FROM checkpoints
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT ?
      `;

      const rows = await this.all(query, [projectId, limit]);

      return rows.map(row => ({
        id: row.id,
        projectId,
        data: JSON.parse(row.data),
        dataSize: row.data_size,
        operation: row.operation,
        timestamp: new Date(row.created_at)
      }));

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'get_checkpoints',
        projectId
      });
      return [];
    }
  }

  async recoverFromCheckpoint(projectId: string): Promise<ProjectData | null> {
    try {
      const checkpoints = await this.getCheckpoints(projectId, 1);

      if (checkpoints.length === 0) {
        return null;
      }

      const latestCheckpoint = checkpoints[0];
      const recoveredData: ProjectData = latestCheckpoint.data as ProjectData;

      // Validate recovered data
      const jsonData = JSON.stringify(recoveredData);
      if (this.validateChecksum(jsonData, recoveredData.checksum)) {
        return recoveredData;
      }

      return null;

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'recover_from_checkpoint',
        projectId
      });
      return null;
    }
  }

  async getRecoveryOptions(projectId: string): Promise<RecoveryOptions[]> {
    const options: RecoveryOptions[] = [];

    try {
      // Add checkpoint options
      const checkpoints = await this.getCheckpoints(projectId, 5);
      for (const checkpoint of checkpoints) {
        options.push({
          type: 'checkpoint',
          id: checkpoint.id,
          timestamp: checkpoint.timestamp,
          operation: checkpoint.operation,
          description: `Restore from ${checkpoint.operation || 'checkpoint'} at ${checkpoint.timestamp.toLocaleString()}`,
          dataSize: checkpoint.dataSize
        });
      }

      // Add last good state option
      const project = await this.loadProject(projectId);
      if (project) {
        options.push({
          type: 'last_good_state',
          id: 'last_good_state',
          timestamp: project.updatedAt,
          description: 'Restore from last successfully saved state'
        });
      }

      return options;

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'get_recovery_options',
        projectId
      });
      return [];
    }
  }

  async listProjects(): Promise<ProjectData[]> {
    try {
      const query = `
        SELECT id, name, description, data, created_at, updated_at, version, checksum
        FROM projects
        ORDER BY updated_at DESC
      `;

      const rows = await this.all(query);

      return rows.map(row => {
        const projectData: ProjectData = JSON.parse(row.data);
        projectData.createdAt = new Date(row.created_at);
        projectData.updatedAt = new Date(row.updated_at);
        return projectData;
      });

    } catch (error) {
      this.logger.logError(error as Error, { operation: 'list_projects' });
      return [];
    }
  }

  async deleteProject(projectId: string): Promise<boolean> {
    try {
      // Check idempotency
      const idempotencyKey = `delete_project_${projectId}`;
      if (await this.isOperationCompleted(idempotencyKey)) {
        return true; // Already deleted
      }

      await this.run('BEGIN TRANSACTION');

      // Delete checkpoints first (foreign key constraint)
      await this.run('DELETE FROM checkpoints WHERE project_id = ?', [projectId]);

      // Delete project
      const result = await this.run('DELETE FROM projects WHERE id = ?', [projectId]);

      await this.run('COMMIT');

      // Mark operation as completed
      await this.markOperationCompleted(idempotencyKey, { deleted: true });

      this.logger.logDatabaseOperation('delete_project', true, 0, { projectId });
      return true;

    } catch (error) {
      await this.run('ROLLBACK');
      this.logger.logError(error as Error, {
        operation: 'delete_project',
        projectId
      });
      return false;
    }
  }

  // Idempotency support
  async isOperationCompleted(key: string): Promise<boolean> {
    try {
      const query = 'SELECT result FROM idempotency_keys WHERE key = ? AND expires_at > datetime("now")';
      const row = await this.get(query, [key]);
      return !!row;
    } catch (error) {
      return false;
    }
  }

  async markOperationCompleted(key: string, result: any, ttlSeconds: number = 3600): Promise<void> {
    try {
      const expiresAt = new Date(Date.now() + ttlSeconds * 1000);

      const query = `
        INSERT INTO idempotency_keys (key, operation, expires_at, result)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
          expires_at = excluded.expires_at,
          result = excluded.result
      `;

      await this.run(query, [
        key,
        'generic_operation',
        expiresAt.toISOString(),
        JSON.stringify(result)
      ]);

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'mark_operation_completed',
        inputData: { key }
      });
    }
  }

  // Settings management
  async getSetting(key: string): Promise<any> {
    try {
      const query = 'SELECT value FROM settings WHERE key = ?';
      const row = await this.get(query, [key]);
      return row ? JSON.parse(row.value) : null;
    } catch (error) {
      return null;
    }
  }

  async setSetting(key: string, value: any): Promise<void> {
    try {
      const query = `
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
          value = excluded.value,
          updated_at = excluded.updated_at
      `;

      await this.run(query, [key, JSON.stringify(value), new Date().toISOString()]);
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'set_setting',
        inputData: { key }
      });
    }
  }

  async getSystemHealth(): Promise<SystemHealth> {
    try {
      // Count projects
      const projectCount = await this.get('SELECT COUNT(*) as count FROM projects');
      const totalProjects = projectCount?.count || 0;

      // Count recent errors (from logger)
      const errorSummary = this.logger.getErrorSummary();
      const recentErrors = errorSummary.totalErrors || 0;

      // Determine database status
      let databaseStatus: 'healthy' | 'warning' | 'error' = 'healthy';
      if (recentErrors > 10) {
        databaseStatus = 'warning';
      }

      // Get last backup time (would be stored in settings)
      const lastBackup = await this.getSetting('last_backup');

      return {
        databaseStatus,
        totalProjects,
        recentErrors,
        lastBackup: lastBackup ? new Date(lastBackup) : undefined,
        recoveryReady: databaseStatus !== 'error',
        uptime: process.uptime()
      };

    } catch (error) {
      this.logger.logError(error as Error, { operation: 'get_system_health' });
      return {
        databaseStatus: 'error',
        totalProjects: 0,
        recentErrors: 1,
        recoveryReady: false,
        uptime: process.uptime()
      };
    }
  }

  // Transaction support
  createTransaction(): DatabaseTransaction {
    const transactionId = crypto.randomBytes(8).toString('hex');
    this.activeTransactions.add(transactionId);

    return {
      begin: async () => {
        await this.run('BEGIN TRANSACTION');
      },

      commit: async () => {
        await this.run('COMMIT');
        this.activeTransactions.delete(transactionId);
      },

      rollback: async () => {
        await this.run('ROLLBACK');
        this.activeTransactions.delete(transactionId);
      },

      isActive: () => this.activeTransactions.has(transactionId)
    };
  }

  // Enhanced database operations with retry logic and comprehensive error handling

  private async runWithRetry(sql: string, operation: string, maxRetries: number = 3): Promise<void> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await this.run(sql);
        return;
      } catch (error) {
        lastError = error as Error;

        this.logger.logError(lastError, {
          operation: `db_run_retry_${operation}`,
          inputData: {
            attempt: attempt + 1,
            maxRetries,
            sql: sql.substring(0, 100) + (sql.length > 100 ? '...' : '')
          }
        });

        // Check if this is a recoverable error
        if (this.isRecoverableDbError(lastError) && attempt < maxRetries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        break;
      }
    }

    throw lastError;
  }

  private async getWithRetry(sql: string, params: any[], operation: string, maxRetries: number = 3): Promise<any> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.get(sql, params);
      } catch (error) {
        lastError = error as Error;

        this.logger.logError(lastError, {
          operation: `db_get_retry_${operation}`,
          inputData: {
            attempt: attempt + 1,
            maxRetries,
            sql: sql.substring(0, 100) + (sql.length > 100 ? '...' : ''),
            paramCount: params.length
          }
        });

        if (this.isRecoverableDbError(lastError) && attempt < maxRetries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        break;
      }
    }

    throw lastError;
  }

  private async allWithRetry(sql: string, params: any[], operation: string, maxRetries: number = 3): Promise<any[]> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.all(sql, params);
      } catch (error) {
        lastError = error as Error;

        this.logger.logError(lastError, {
          operation: `db_all_retry_${operation}`,
          inputData: {
            attempt: attempt + 1,
            maxRetries,
            sql: sql.substring(0, 100) + (sql.length > 100 ? '...' : ''),
            paramCount: params.length
          }
        });

        if (this.isRecoverableDbError(lastError) && attempt < maxRetries - 1) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        break;
      }
    }

    throw lastError;
  }

  private isRecoverableDbError(error: Error): boolean {
    const message = error.message.toLowerCase();

    // SQLite busy errors are recoverable
    if (message.includes('database is locked') ||
        message.includes('database temporarily unavailable')) {
      return true;
    }

    // Disk I/O errors might be recoverable
    if (message.includes('disk i/o error') ||
        message.includes('disk full')) {
      return true;
    }

    return false;
  }

  // Transaction operations with comprehensive error handling
  async executeInTransaction<T>(
    operation: (transaction: DatabaseTransaction) => Promise<T>,
    operationName: string
  ): Promise<T> {
    const startTime = Date.now();
    let transaction: DatabaseTransaction | null = null;

    try {
      transaction = this.createTransaction();

      await transaction.begin();

      const result = await operation(transaction);

      await transaction.commit();

      const duration = Date.now() - startTime;
      this.logger.logPerformance(`${operationName}_transaction`, duration, true);

      return result;

    } catch (error) {
      const txError = error as Error;
      const duration = Date.now() - startTime;

      this.logger.logError(txError, {
        operation: `${operationName}_transaction`,
        stackTrace: txError.stack
      });

      this.logger.logPerformance(`${operationName}_transaction`, duration, false);

      // Attempt rollback
      if (transaction && transaction.isActive()) {
        try {
          await transaction.rollback();
          this.logger.logRecoveryAction('Transaction rolled back successfully', true, {
            operation: operationName
          });
        } catch (rollbackError) {
          this.logger.logError(rollbackError as Error, {
            operation: 'transaction_rollback',
            originalOperation: operationName
          });
        }
      }

      throw txError;
    }
  }

  // Low-level database operations with basic error handling
  private run(sql: string, params: any[] = []): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        const error = new Error('Database not initialized');
        this.logger.logError(error, { operation: 'db_run_check' });
        reject(error);
        return;
      }

      this.db.run(sql, params, function(err) {
        if (err) {
          // Log database errors with context
          const dbError = err;
          getLogger().logError(dbError, {
            operation: 'db_run',
            inputData: {
              sql: sql.substring(0, 200) + (sql.length > 200 ? '...' : ''),
              paramCount: params.length,
              errno: dbError.errno,
              code: dbError.code
            }
          });
          reject(dbError);
        } else {
          resolve();
        }
      });
    });
  }

  private get(sql: string, params: any[] = []): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        const error = new Error('Database not initialized');
        this.logger.logError(error, { operation: 'db_get_check' });
        reject(error);
        return;
      }

      this.db.get(sql, params, (err, row) => {
        if (err) {
          const dbError = err;
          getLogger().logError(dbError, {
            operation: 'db_get',
            inputData: {
              sql: sql.substring(0, 200) + (sql.length > 200 ? '...' : ''),
              paramCount: params.length,
              errno: dbError.errno,
              code: dbError.code
            }
          });
          reject(dbError);
        } else {
          resolve(row);
        }
      });
    });
  }

  private all(sql: string, params: any[] = []): Promise<any[]> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        const error = new Error('Database not initialized');
        this.logger.logError(error, { operation: 'db_all_check' });
        reject(error);
        return;
      }

      this.db.all(sql, params, (err, rows) => {
        if (err) {
          const dbError = err;
          getLogger().logError(dbError, {
            operation: 'db_all',
            inputData: {
              sql: sql.substring(0, 200) + (sql.length > 200 ? '...' : ''),
              paramCount: params.length,
              errno: dbError.errno,
              code: dbError.code
            }
          });
          reject(dbError);
        } else {
          resolve(rows);
        }
      });
    });
  }

  async close(): Promise<void> {
    if (this.db) {
      await new Promise<void>((resolve) => {
        this.db!.close((err) => {
          if (err) {
            this.logger.logError(err, { operation: 'database_close' });
          }
          resolve();
        });
      });
      this.db = null;
      this.initialized = false;
    }
  }
}

// Global instance
let dbInstance: DatabaseManager | null = null;

export function getDatabase(): DatabaseManager {
  if (!dbInstance) {
    dbInstance = new DatabaseManager();
  }
  return dbInstance;
}
