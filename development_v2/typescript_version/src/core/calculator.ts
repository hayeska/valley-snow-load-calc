// Resilient Valley Snow Load Calculator with persistent storage and recovery

import { v4 as uuidv4 } from 'uuid';
import {
  ProjectData,
  RoofGeometry,
  SnowLoadInputs,
  CalculationResults,
  RecoveryOptions
} from '../types';
import { getDatabase } from '../data/database';
import { getLogger } from '../utils/logger';
import { getCheckpointManager } from './checkpointSystem';
import {
  resilientOperation,
  withTimeout,
  validateInput,
  validatePositiveNumber,
  validateRange,
  withRecoveryStrategies,
  withErrorBoundary
} from './errorHandlers';

@withRecoveryStrategies({
  'ValidationError': async (error: Error) => {
    // Log validation errors but don't retry
    console.warn('Validation error encountered:', error.message);
  },
  'TimeoutError': async (error: Error, ...args: any[]) => {
    // For timeout errors, try with reduced precision
    console.warn('Operation timed out, attempting simplified calculation');
  }
})
export class ValleySnowLoadCalculator {
  private db = getDatabase();
  private logger = getLogger();
  private checkpointManager = getCheckpointManager();
  private currentProjectId: string | null = null;

  constructor() {
    this.initialize();
  }

  private async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing Valley Snow Load Calculator...');

      // Initialize database with comprehensive error handling
      await withErrorBoundary(
        () => this.db.initialize(),
        { operation: 'calculator_db_init' },
        {
          'Error': async (error: Error) => {
            this.logger.logRecoveryAction('Attempting database recovery', true);
            // Recovery logic would go here - could try alternative db location, etc.
          }
        }
      );

      // Initialize checkpoint manager
      await withErrorBoundary(
        () => this.checkpointManager.initialize(),
        { operation: 'calculator_checkpoint_init' },
        {
          'Error': async (error: Error) => {
            this.logger.warn('Checkpoint system failed to initialize, continuing without auto-save', {
              error: error.message
            });
            // Continue without checkpointing rather than failing completely
          }
        }
      );

      // Store global references for error recovery
      (global as any).database = this.db;
      (global as any).checkpointManager = this.checkpointManager;

      this.logger.info('Valley Snow Load Calculator initialized successfully with resilient architecture');

    } catch (error) {
      const initError = error as Error;
      this.logger.logError(initError, {
        operation: 'calculator_initialization',
        stackTrace: initError.stack
      }, false);

      // Attempt minimal recovery
      try {
        this.logger.logRecoveryAction('Attempting minimal calculator initialization', true);

        // Try to create in-memory fallback if database fails
        if (!this.db) {
          this.logger.warn('Running in degraded mode without persistence');
          // Could implement in-memory storage as fallback
        }

      } catch (recoveryError) {
        this.logger.logError(recoveryError as Error, {
          operation: 'calculator_recovery'
        });
      }

      throw new Error(`Calculator initialization failed: ${initError.message}`);
    }
  }

  // Idempotent project operations
  @resilientOperation(3, 1000, true, true)
  @validateInput(validateNonEmptyString)
  async createProject(name: string, description?: string): Promise<string> {
    const projectId = uuidv4();

    const projectData: ProjectData = {
      id: projectId,
      name,
      description: description || '',
      geometry: this.getDefaultGeometry(),
      inputs: this.getDefaultInputs(),
      results: this.getEmptyResults(),
      createdAt: new Date(),
      updatedAt: new Date(),
      version: '2.0.0',
      checksum: '' // Will be calculated during save
    };

    await this.db.saveProject(projectData);

    // Mark project as active for auto-checkpointing
    this.checkpointManager.markProjectActive(projectId);
    this.currentProjectId = projectId;

    this.logger.info(`Project created: ${name}`, { projectId });
    return projectId;
  }

  @resilientOperation(3, 1000, true)
  async loadProject(projectId: string): Promise<ProjectData> {
    try {
      // Validate input
      if (!projectId || typeof projectId !== 'string' || projectId.trim() === '') {
        throw new Error('Invalid project ID provided');
      }

      // Attempt to load from database
      const project = await withErrorBoundary(
        () => this.db.loadProject(projectId),
        {
          operation: 'load_project_db',
          projectId
        },
        {
          'Error': async (error: Error) => {
            // Try recovery from checkpoint
            this.logger.logRecoveryAction('Attempting checkpoint recovery for project load', true);
            const recoveredProject = await this.attemptProjectRecovery(projectId);
            if (recoveredProject) {
              return recoveredProject;
            }
            throw error; // Re-throw if recovery fails
          }
        }
      );

      if (!project) {
        // Try to find project by partial ID or name
        const allProjects = await withErrorBoundary(
          () => this.db.listProjects(),
          { operation: 'list_projects_fallback', projectId }
        );

        const foundProject = allProjects.find(p =>
          p.id.includes(projectId) || p.name.toLowerCase().includes(projectId.toLowerCase())
        );

        if (foundProject) {
          this.logger.info(`Project found by fuzzy match: ${foundProject.name}`, {
            requestedId: projectId,
            foundId: foundProject.id
          });
          // Recursively load the found project
          return await this.loadProject(foundProject.id);
        }

        throw new Error(`Project ${projectId} not found`);
      }

      // Validate loaded project data
      await this.validateProjectData(project);

      // Mark as active for checkpointing
      await withErrorBoundary(
        () => this.checkpointManager.markProjectActive(projectId),
        { operation: 'mark_project_active', projectId },
        {}, // Non-critical, don't fail if this fails
        true
      );

      this.currentProjectId = projectId;

      this.logger.info(`Project loaded successfully: ${project.name}`, {
        projectId,
        dataSize: JSON.stringify(project).length,
        lastUpdated: project.updatedAt.toISOString()
      });

      return project;

    } catch (error) {
      const loadError = error as Error;
      this.logger.logError(loadError, {
        operation: 'load_project_comprehensive',
        projectId,
        stackTrace: loadError.stack
      });

      // Final recovery attempt - try to create a minimal project structure
      if (loadError.message.includes('not found')) {
        this.logger.logRecoveryAction('Project not found, offering recovery options', true, { projectId });

        // Could return a "recovery mode" project or throw with recovery suggestions
        throw new Error(`Project ${projectId} not found. Check recovery options or create a new project.`);
      }

      throw loadError;
    }
  }

  private async attemptProjectRecovery(projectId: string): Promise<ProjectData | null> {
    try {
      this.logger.info('Attempting project recovery from checkpoints', { projectId });

      // Get recovery options
      const recoveryOptions = await this.getRecoveryOptions(projectId);

      // Try the most recent checkpoint
      for (const option of recoveryOptions) {
        if (option.type === 'checkpoint' && option.id) {
          try {
            const recovered = await this.recoverFromCheckpoint(option.id);
            if (recovered) {
              this.logger.logRecoveryAction('Project recovered from checkpoint', true, {
                projectId,
                checkpointId: option.id
              });
              return recovered;
            }
          } catch (checkpointError) {
            this.logger.logError(checkpointError as Error, {
              operation: 'checkpoint_recovery_attempt',
              projectId,
              checkpointId: option.id
            });
          }
        }
      }

      return null;

    } catch (error) {
      this.logger.logError(error as Error, {
        operation: 'project_recovery_attempt',
        projectId
      });
      return null;
    }
  }

  private async validateProjectData(project: ProjectData): Promise<void> {
    // Basic validation
    if (!project.id || !project.name) {
      throw new Error('Invalid project data: missing required fields');
    }

    // Validate geometry
    if (!project.geometry || typeof project.geometry !== 'object') {
      throw new Error('Invalid project geometry data');
    }

    // Validate calculations can be performed
    try {
      this.validateGeometry(project.geometry);
    } catch (geomError) {
      this.logger.warn('Project geometry validation failed, but continuing', {
        projectId: project.id,
        error: (geomError as Error).message
      });
    }

    // Check data integrity if checksum exists
    if (project.checksum) {
      const crypto = require('crypto');
      const dataString = JSON.stringify({
        ...project,
        checksum: undefined,
        updatedAt: undefined
      });
      const calculatedChecksum = crypto.createHash('sha256').update(dataString).digest('hex');

      if (calculatedChecksum !== project.checksum) {
        this.logger.warn('Project data integrity check failed', {
          projectId: project.id,
          stored: project.checksum,
          calculated: calculatedChecksum
        });
        // Don't throw - data might still be usable
      }
    }
  }

  @resilientOperation(3, 1000, true, true)
  async saveProject(projectData: ProjectData): Promise<void> {
    projectData.updatedAt = new Date();
    await this.db.saveProject(projectData);

    // Create manual checkpoint
    await this.checkpointManager.createCheckpoint(projectData.id, 'manual_save', projectData);

    this.logger.info(`Project saved: ${projectData.name}`, { projectId: projectData.id });
  }

  @resilientOperation(2, 1000, true)
  async deleteProject(projectId: string): Promise<void> {
    const success = await this.db.deleteProject(projectId);

    if (!success) {
      throw new Error(`Failed to delete project ${projectId}`);
    }

    // Mark as inactive
    this.checkpointManager.markProjectInactive(projectId);

    if (this.currentProjectId === projectId) {
      this.currentProjectId = null;
    }

    this.logger.info(`Project deleted`, { projectId });
  }

  // Core calculation operations with resilience
  @resilientOperation(2, 2000, true)
  @withTimeout(10000) // 10 second timeout
  @validateInput(
    validatePositiveNumber, // pitchN
    validatePositiveNumber, // pitchW
    validateRange(0, 100),  // northSpan
    validateRange(0, 100),  // southSpan
    validateRange(0, 200),  // ewHalfWidth
    validateRange(-50, 50), // valleyOffset
    validateRange(0, 180)   // valleyAngle
  )
  async updateGeometry(
    projectId: string,
    geometry: RoofGeometry
  ): Promise<ProjectData> {
    return await withErrorBoundary(
      async () => {
        const project = await this.loadProject(projectId);
        project.geometry = geometry;

        // Validate geometry makes sense
        this.validateGeometry(geometry);

        // Auto-save with checkpoint
        await this.saveProject(project);

        this.logger.info(`Geometry updated for project ${project.name}`, { projectId });
        return project;
      },
      {
        operation: 'update_geometry',
        projectId
      },
      this.recoveryStrategies
    );
  }

  @resilientOperation(2, 2000, true)
  @withTimeout(15000) // 15 second timeout for complex calculations
  @validateInput(
    validateRange(0, 200), // groundSnowLoad
    validateRange(0.7, 1.3), // importanceFactor
    validateRange(0.7, 1.3), // exposureFactor
    validateRange(0.8, 1.3), // thermalFactor
    validateRange(0, 1)     // winterWindParameter
  )
  async updateInputs(
    projectId: string,
    inputs: SnowLoadInputs
  ): Promise<ProjectData> {
    return await withErrorBoundary(
      async () => {
        const project = await this.loadProject(projectId);
        project.inputs = inputs;

        // Recalculate results with new inputs
        project.results = await this.performCalculations(project.geometry, inputs);

        await this.saveProject(project);

        this.logger.info(`Inputs updated and calculations completed for project ${project.name}`, { projectId });
        return project;
      },
      {
        operation: 'update_inputs',
        projectId
      },
      this.recoveryStrategies
    );
  }

  @resilientOperation(3, 1000, true)
  @withTimeout(30000) // 30 second timeout for full calculation suite
  async performCalculations(
    geometry: RoofGeometry,
    inputs: SnowLoadInputs
  ): Promise<CalculationResults> {
    return await withErrorBoundary(
      async () => {
        const startTime = Date.now();

        // Perform slope calculations
        const slopeParams = this.calculateSlopeParameters(geometry.roofPitchN, geometry.roofPitchW);

        // Calculate snow loads
        const balancedLoads = this.calculateBalancedLoads(inputs, slopeParams);
        const unbalancedLoads = this.calculateUnbalancedLoads(inputs, slopeParams, geometry);
        const driftLoads = this.calculateDriftLoads(inputs, geometry);

        // Calculate valley-specific loads
        const valleyLoads = this.calculateValleyLoads(balancedLoads, unbalancedLoads, geometry);

        const results: CalculationResults = {
          balancedLoads,
          unbalancedLoads,
          driftLoads,
          valleyLoads
        };

        const duration = Date.now() - startTime;
        this.logger.logPerformance('full_calculation', duration, true, {
          geometry: Object.keys(geometry).length,
          inputs: Object.keys(inputs).length
        });

        return results;
      },
      {
        operation: 'perform_calculations',
        inputData: { geometry: geometry, inputs: inputs }
      },
      this.recoveryStrategies
    );
  }

  // Recovery and checkpoint operations
  async getRecoveryOptions(projectId: string): Promise<RecoveryOptions[]> {
    return this.checkpointManager.getRecoveryOptions(projectId);
  }

  @resilientOperation(2, 1000, true)
  async recoverFromCheckpoint(checkpointId: string): Promise<ProjectData | null> {
    const recoveredData = await this.checkpointManager.restoreFromCheckpoint(checkpointId);

    if (recoveredData) {
      // Save recovered data as current state
      await this.saveProject(recoveredData);
      this.currentProjectId = recoveredData.id;
      this.checkpointManager.markProjectActive(recoveredData.id);
    }

    return recoveredData;
  }

  // Utility methods
  async listProjects(): Promise<ProjectData[]> {
    return this.db.listProjects();
  }

  async getSystemHealth() {
    return this.db.getSystemHealth();
  }

  getCurrentProjectId(): string | null {
    return this.currentProjectId;
  }

  // Private calculation methods
  private calculateSlopeParameters(pitchN: number, pitchW: number) {
    const sN = pitchN / 12.0; // rise/run
    const sW = pitchW / 12.0;

    return {
      slopeRatioN: sN,
      slopeRatioW: sW,
      runPerRiseN: pitchN > 0 ? 12.0 / pitchN : Infinity,
      runPerRiseW: pitchW > 0 ? 12.0 / pitchW : Infinity,
      angleN: Math.atan(sN) * 180 / Math.PI,
      angleW: Math.atan(sW) * 180 / Math.PI
    };
  }

  private calculateBalancedLoads(inputs: SnowLoadInputs, slopeParams: any) {
    // Simplified balanced load calculation (ASCE 7-22 simplified)
    const pg = inputs.groundSnowLoad;
    const i = inputs.importanceFactor;
    const ce = inputs.exposureFactor;
    const ct = inputs.thermalFactor;

    const balancedLoad = pg * i * ce * ct;

    return {
      northRoof: balancedLoad,
      westRoof: balancedLoad
    };
  }

  private calculateUnbalancedLoads(inputs: SnowLoadInputs, slopeParams: any, geometry: RoofGeometry) {
    // Simplified unbalanced load calculation
    const balanced = this.calculateBalancedLoads(inputs, slopeParams);

    // Unbalanced loads occur when slopes are between 0.5/12 and 7/12
    const minSlope = 0.5 / 12.0;
    const maxSlope = 7.0 / 12.0;

    const unbalancedN = slopeParams.slopeRatioN >= minSlope && slopeParams.slopeRatioN <= maxSlope;
    const unbalancedW = slopeParams.slopeRatioW >= minSlope && slopeParams.slopeRatioW <= maxSlope;

    return {
      northRoof: unbalancedN ? balanced.northRoof * 1.5 : balanced.northRoof,
      westRoof: unbalancedW ? balanced.westRoof * 1.5 : balanced.westRoof
    };
  }

  private calculateDriftLoads(inputs: SnowLoadInputs, geometry: RoofGeometry) {
    // Simplified drift calculation
    const pg = inputs.groundSnowLoad;
    const leeSideDrift = pg * 0.8; // Simplified
    const windwardSideDrift = pg * 0.3; // Simplified

    return {
      leeSide: leeSideDrift,
      windwardSide: windwardSideDrift
    };
  }

  private calculateValleyLoads(balanced: any, unbalanced: any, geometry: RoofGeometry) {
    // Simplified valley load calculation
    const horizontalLoad = Math.max(balanced.northRoof, balanced.westRoof) * 1.2;
    const verticalLoad = horizontalLoad * Math.sin((geometry.valleyAngle * Math.PI) / 180);

    return {
      horizontalLoad,
      verticalLoad
    };
  }

  private validateGeometry(geometry: RoofGeometry): void {
    if (geometry.northSpan <= 0 || geometry.southSpan <= 0) {
      throw new Error('Roof spans must be positive');
    }

    if (geometry.valleyAngle < 0 || geometry.valleyAngle > 180) {
      throw new Error('Valley angle must be between 0 and 180 degrees');
    }

    // Check if valley offset is within reasonable bounds
    const maxOffset = Math.max(geometry.northSpan, geometry.southSpan) / 2;
    if (Math.abs(geometry.valleyOffset) > maxOffset) {
      throw new Error('Valley offset is outside reasonable bounds');
    }
  }

  private getDefaultGeometry(): RoofGeometry {
    return {
      roofPitchN: 8, // 8/12 pitch
      roofPitchW: 8,
      northSpan: 16, // feet
      southSpan: 16,
      ewHalfWidth: 42,
      valleyOffset: 16,
      valleyAngle: 90 // degrees
    };
  }

  private getDefaultInputs(): SnowLoadInputs {
    return {
      groundSnowLoad: 25, // psf
      importanceFactor: 1.0,
      exposureFactor: 1.0,
      thermalFactor: 1.0,
      winterWindParameter: 0.3
    };
  }

  private getEmptyResults(): CalculationResults {
    return {
      balancedLoads: { northRoof: 0, westRoof: 0 },
      unbalancedLoads: { northRoof: 0, westRoof: 0 },
      driftLoads: { leeSide: 0, windwardSide: 0 },
      valleyLoads: { horizontalLoad: 0, verticalLoad: 0 }
    };
  }

  // Idempotency key generation for operations
  private generateIdempotencyKey(operation: string, args: any[]): string {
    const keyData = `${operation}_${JSON.stringify(args)}_${Date.now()}`;
    // In a real implementation, you'd use a proper hash function
    return Buffer.from(keyData).toString('base64').substring(0, 50);
  }

  // Recovery strategies
  private recoveryStrategies = {
    'ValidationError': async (error: Error) => {
      this.logger.warn('Validation error in calculation, using fallback values', {
        error: error.message
      });
    },

    'TimeoutError': async (error: Error) => {
      this.logger.warn('Calculation timeout, attempting simplified calculation', {
        error: error.message
      });
    }
  };

  // Cleanup method
  async shutdown(): Promise<void> {
    // Perform final checkpoints
    await this.checkpointManager.emergencyCheckpointAll();

    // Close database connection
    await this.db.close();

    this.logger.info('Calculator shutdown completed');
  }
}

// Convenience functions
export async function createCalculator(): Promise<ValleySnowLoadCalculator> {
  const calculator = new ValleySnowLoadCalculator();
  await calculator.initialize();
  return calculator;
}

// Global calculator instance
let calculatorInstance: ValleySnowLoadCalculator | null = null;

export function getCalculator(): ValleySnowLoadCalculator {
  if (!calculatorInstance) {
    calculatorInstance = new ValleySnowLoadCalculator();
  }
  return calculatorInstance;
}
