// Auto-save checkpoint system with change detection and recovery points

import { EventEmitter } from 'events';
import * as fs from 'fs';
import * as path from 'path';
import { getDatabase } from '../data/database';
import { getLogger } from '../utils/logger';
import {
  CheckpointData,
  CheckpointEvent,
  RecoveryOptions,
  ProjectData
} from '../types';

export class CheckpointManager extends EventEmitter {
  private db = getDatabase();
  private logger = getLogger();
  private autoSaveInterval: NodeJS.Timeout | null = null;
  private activeProjects = new Set<string>();
  private lastCheckpointTime = new Map<string, number>();
  private changeDetector = new DataChangeTracker();
  private isInitialized = false;
  private crashFlagFile = '.crash';
  private stateBackupFile = 'state.backup.json';

  constructor(
    private autoSaveMinutes: number = 2, // Changed to 2 minutes
    private maxCheckpointsPerProject: number = 50
  ) {
    super();
    this.setupEventHandlers();
    this.checkCrashRecovery();
    this.createCrashFlag();
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    await this.db.initialize();
    this.startAutoSaveTimer();
    this.isInitialized = true;

    this.logger.info('Checkpoint manager initialized', {
      autoSaveMinutes: this.autoSaveMinutes,
      maxCheckpointsPerProject: this.maxCheckpointsPerProject
    });
  }

  private setupEventHandlers(): void {
    // Handle process termination for emergency checkpoints
    process.on('SIGINT', () => this.handleShutdown());
    process.on('SIGTERM', () => this.handleShutdown());

    // Handle uncaught exceptions
    process.on('uncaughtException', () => this.handleShutdown());
    process.on('unhandledRejection', () => this.handleShutdown());
  }

  private createCrashFlag(): void {
    try {
      fs.writeFileSync(this.crashFlagFile, new Date().toISOString());
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'create_crash_flag'
      });
    }
  }

  private removeCrashFlag(): void {
    try {
      if (fs.existsSync(this.crashFlagFile)) {
        fs.unlinkSync(this.crashFlagFile);
      }
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'remove_crash_flag'
      });
    }
  }

  private checkCrashRecovery(): void {
    if (fs.existsSync(this.crashFlagFile) && fs.existsSync(this.stateBackupFile)) {
      try {
        const crashTime = fs.readFileSync(this.crashFlagFile, 'utf8').trim();
        console.log(`\n🚨 Crash detected from ${crashTime}`);
        console.log('💾 Auto-recovery system is active');
        console.log('   Backup file available: state.backup.json\n');
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'check_crash_recovery'
        });
      }
    }
  }

  private handleShutdown(): void {
    // Remove crash flag since we're shutting down normally
    this.removeCrashFlag();

    // Remove backup file on normal exit
    try {
      if (fs.existsSync(this.stateBackupFile)) {
        fs.unlinkSync(this.stateBackupFile);
      }
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'cleanup_backup_on_exit'
      });
    }
  }

  private startAutoSaveTimer(): void {
    this.autoSaveInterval = setInterval(() => {
      this.performAutoCheckpoints();
    }, this.autoSaveMinutes * 60 * 1000);
  }

  private async performAutoCheckpoints(): Promise<void> {
    const activeProjects = Array.from(this.activeProjects);

    for (const projectId of activeProjects) {
      try {
        const lastCheckpoint = this.lastCheckpointTime.get(projectId) || 0;
        const timeSinceLastCheckpoint = Date.now() - lastCheckpoint;

        if (timeSinceLastCheckpoint >= this.autoSaveMinutes * 60 * 1000) {
          await this.createCheckpoint(projectId, 'auto_save');
          await this.saveToBackupFile(projectId);
        }
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'auto_checkpoint',
          projectId
        });
      }
    }
  }

  async createCheckpoint(
    projectId: string,
    operation: string,
    data?: Partial<ProjectData>
  ): Promise<string> {
    const checkpointId = `checkpoint_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Get current project data if not provided
      let checkpointData = data;
      if (!checkpointData) {
        const project = await this.db.loadProject(projectId);
        if (project) {
          checkpointData = project;
        } else {
          throw new Error(`Project ${projectId} not found for checkpoint`);
        }
      }

      const jsonData = JSON.stringify(checkpointData);
      const dataSize = Buffer.byteLength(jsonData, 'utf8');

      const checkpoint: CheckpointData = {
        id: checkpointId,
        projectId,
        data: checkpointData,
        dataSize,
        operation,
        timestamp: new Date()
      };

      await this.db.createCheckpoint(checkpoint);

      // Update tracking
      this.lastCheckpointTime.set(projectId, Date.now());

      // Cleanup old checkpoints
      await this.cleanupOldCheckpoints(projectId);

      // Emit event
      const event: CheckpointEvent = {
        trigger: 'manual_save',
        projectId,
        data: checkpointData
      };
      this.emit('checkpointCreated', event);

      this.logger.logCheckpoint(checkpointId, dataSize, operation);

      return checkpointId;

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'create_checkpoint',
        projectId,
        checkpointId
      });
      throw error;
    }
  }

  private async cleanupOldCheckpoints(projectId: string): Promise<void> {
    try {
      const checkpoints = await this.db.getCheckpoints(projectId, this.maxCheckpointsPerProject + 10);

      if (checkpoints.length > this.maxCheckpointsPerProject) {
        const excessCount = checkpoints.length - this.maxCheckpointsPerProject;

        // In a full implementation, you would delete excess checkpoints
        // For now, just log the need for cleanup
        this.logger.logRecoveryAction(
          `Checkpoint cleanup needed: ${excessCount} excess checkpoints`,
          true,
          { projectId }
        );
      }
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'cleanup_checkpoints',
        projectId
      });
    }
  }

  async restoreFromCheckpoint(checkpointId: string): Promise<ProjectData | null> {
    try {
      const checkpoint = await this.db.get(`SELECT * FROM checkpoints WHERE id = ?`, [checkpointId]);

      if (!checkpoint) {
        return null;
      }

      const checkpointData: CheckpointData = {
        id: checkpoint.id,
        projectId: checkpoint.project_id,
        data: JSON.parse(checkpoint.data),
        dataSize: checkpoint.data_size,
        operation: checkpoint.operation,
        timestamp: new Date(checkpoint.created_at)
      };

      this.logger.logRecoveryAction(
        `Restored from checkpoint ${checkpointId}`,
        true,
        { checkpointId, operation: checkpointData.operation }
      );

      return checkpointData.data as ProjectData;

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'restore_from_checkpoint',
        checkpointId
      });
      return null;
    }
  }

  async getRecoveryOptions(projectId: string): Promise<RecoveryOptions[]> {
    const options: RecoveryOptions[] = [];

    try {
      // Check for backup file first
      if (fs.existsSync(this.stateBackupFile)) {
        try {
          const backupContent = JSON.parse(fs.readFileSync(this.stateBackupFile, 'utf8'));
          options.push({
            type: 'backup_file',
            id: 'state_backup',
            timestamp: new Date(backupContent.project_info.auto_saved),
            operation: 'auto_save',
            description: `Restore from auto-saved state (${new Date(backupContent.project_info.auto_saved).toLocaleString()})`
          });
        } catch (error) {
          // Backup file corrupted, skip it
        }
      }

      // Get checkpoints
      const checkpoints = await this.db.getCheckpoints(projectId, 5);

      for (const checkpoint of checkpoints) {
        options.push({
          type: 'checkpoint',
          id: checkpoint.id,
          timestamp: checkpoint.timestamp,
          operation: checkpoint.operation,
          description: `Restore from ${checkpoint.operation || 'checkpoint'} (${checkpoint.timestamp.toLocaleString()})`,
          dataSize: checkpoint.dataSize
        });
      }

      // Add last good state option
      const project = await this.db.loadProject(projectId);
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

  async restoreFromBackupFile(): Promise<ProjectData | null> {
    try {
      if (!fs.existsSync(this.stateBackupFile)) {
        return null;
      }

      const backupContent = JSON.parse(fs.readFileSync(this.stateBackupFile, 'utf8'));
      const projectData = backupContent.project_data;

      if (projectData) {
        this.logger.logRecoveryAction(
          'Restored from auto-save backup file',
          true,
          { backupTime: backupContent.project_info.auto_saved }
        );
        return projectData;
      }

      return null;
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'restore_from_backup_file'
      });
      return null;
    }
  }

  async trackDataChange(projectId: string, newData: ProjectData, forceCheckpoint: boolean = false): Promise<void> {
    const hasSignificantChange = this.changeDetector.hasSignificantChange(projectId, newData);

    if (forceCheckpoint || hasSignificantChange) {
      await this.createCheckpoint(projectId, 'data_change', newData);
      await this.saveToBackupFile(projectId, newData);
    }
  }

  private async saveToBackupFile(projectId: string, data?: ProjectData): Promise<void> {
    try {
      let backupData = data;
      if (!backupData) {
        backupData = await this.db.loadProject(projectId);
      }

      if (backupData) {
        const backupContent = {
          project_info: {
            name: 'Auto-saved Valley Snow Load State',
            version: '1.0',
            auto_saved: new Date().toISOString(),
            description: 'Automatic backup for crash recovery'
          },
          project_data: backupData
        };

        fs.writeFileSync(this.stateBackupFile, JSON.stringify(backupContent, null, 2));
        console.log(`💾 Auto-saved state at ${new Date().toLocaleTimeString()}`);
      }
    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'save_to_backup_file',
        projectId
      });
    }
  }

  markProjectActive(projectId: string): void {
    this.activeProjects.add(projectId);
    this.lastCheckpointTime.set(projectId, Date.now());
  }

  markProjectInactive(projectId: string): void {
    this.activeProjects.delete(projectId);
    this.lastCheckpointTime.delete(projectId);
  }

  async emergencyCheckpointAll(): Promise<void> {
    this.logger.logRecoveryAction('Emergency checkpoint initiated', true);

    const activeProjects = Array.from(this.activeProjects);

    for (const projectId of activeProjects) {
      try {
        await this.createCheckpoint(projectId, 'emergency_save');
        await this.saveToBackupFile(projectId);
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'emergency_checkpoint',
          projectId
        });
      }
    }
  }

  getActiveProjects(): string[] {
    return Array.from(this.activeProjects);
  }

  async forceCheckpointAllActive(): Promise<void> {
    const activeProjects = Array.from(this.activeProjects);

    for (const projectId of activeProjects) {
      try {
        await this.createCheckpoint(projectId, 'forced_save');
      } catch (error) {
        this.logger.logError(error as Error, {
          operation: 'force_checkpoint',
          projectId
        });
      }
    }
  }

  shutdown(): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }

    this.handleShutdown();
    this.logger.info('Checkpoint manager shutdown');
  }
}

class DataChangeTracker {
  private lastHashes = new Map<string, string>();
  private changeThreshold: number;

  constructor(changeThreshold: number = 0.1) {
    this.changeThreshold = changeThreshold;
  }

  hasSignificantChange(projectId: string, newData: ProjectData): boolean {
    const currentHash = this.calculateDataHash(newData);
    const lastHash = this.lastHashes.get(projectId);

    if (!lastHash) {
      this.lastHashes.set(projectId, currentHash);
      return true; // First time seeing this project
    }

    const hasChanged = currentHash !== lastHash;

    if (hasChanged) {
      this.lastHashes.set(projectId, currentHash);
    }

    return hasChanged;
  }

  private calculateDataHash(data: ProjectData): string {
    // Simple hash for change detection
    const dataString = JSON.stringify(data, Object.keys(data).sort());
    let hash = 0;

    for (let i = 0; i < dataString.length; i++) {
      const char = dataString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return hash.toString();
  }

  clearTracking(projectId: string): void {
    this.lastHashes.delete(projectId);
  }
}

// Decorators for checkpoint integration
export function checkpointOnChange(projectId?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    const logger = getLogger();

    descriptor.value = async function(...args: any[]): Promise<any> {
      const result = await originalMethod.apply(this, args);

      // Try to create checkpoint if project data changed
      try {
        if (this.checkpointManager && this.getCurrentProjectData) {
          const currentData = this.getCurrentProjectData();
          const projId = projectId || this.currentProjectId;

          if (projId && currentData) {
            await this.checkpointManager.trackDataChange(projId, currentData);
          }
        }
      } catch (error) {
        logger.logError(error as Error, {
          operation: 'checkpoint_on_change_decorator',
          inputData: { method: propertyKey }
        });
      }

      return result;
    };

    return descriptor;
  };
}

// Global checkpoint manager instance
let checkpointManagerInstance: CheckpointManager | null = null;

export function getCheckpointManager(): CheckpointManager {
  if (!checkpointManagerInstance) {
    checkpointManagerInstance = new CheckpointManager();
  }
  return checkpointManagerInstance;
}

export function initializeCheckpointSystem(): Promise<void> {
  return getCheckpointManager().initialize();
}

// Convenience functions
export async function createCheckpoint(projectId: string, operation: string, data?: Partial<ProjectData>): Promise<string> {
  return getCheckpointManager().createCheckpoint(projectId, operation, data);
}

export async function getRecoveryOptions(projectId: string): Promise<RecoveryOptions[]> {
  return getCheckpointManager().getRecoveryOptions(projectId);
}

export async function restoreFromBackupFile(): Promise<ProjectData | null> {
  return getCheckpointManager().restoreFromBackupFile();
}

export function shutdownCheckpointSystem(): void {
  if (checkpointManagerInstance) {
    checkpointManagerInstance.shutdown();
  }
}
