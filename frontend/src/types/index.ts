// Core types for Valley Snow Load Calculator

export interface RoofGeometry {
  northPitch: number; // degrees
  westPitch: number; // degrees
  northSpan: number; // feet
  southSpan: number; // feet
  ewHalfWidth: number; // feet
  valleyOffset: number; // feet
  valleyAngle: number; // degrees
}

export interface SnowLoadInputs {
  groundSnowLoad: number; // psf
  importanceFactor: number;
  exposureFactor: number;
  thermalFactor: number;
  winterWindParameter: number;
  isSlipperySurface: boolean; // slippery surface for Cs calculation
}

export interface BeamDesignInputs {
  beamWidth: number; // inches
  beamDepth: number; // inches
  materialType:
    | "Douglas Fir"
    | "Southern Pine"
    | "Spruce-Pine-Fir"
    | "Hem-Fir"
    | "Redwood"
    | "Cedar";
  allowableFb: number; // psi
  allowableFv: number; // psi
  modulusE: number; // psi
  deflectionLimitSnow: number; // L/n
  deflectionLimitTotal: number; // L/n
  roofDeadLoad: number; // psf
}

export interface BeamDesignResults {
  requiredSectionModulus: number;
  requiredMomentCapacity: number;
  actualMomentCapacity: number;
  momentUtilization: number;
  requiredShearCapacity: number;
  actualShearCapacity: number;
  shearUtilization: number;
  deflectionSnow: number;
  deflectionTotal: number;
  deflectionUtilization: number;
  beamWeight: number;
  totalLoad: number;
}

export interface DiagramData {
  roofProfile: Array<{ x: number; y: number }>;
  snowLoads: Array<{ x: number; load: number }>;
  shearForce: Array<{ x: number; force: number }>;
  bendingMoment: Array<{ x: number; moment: number }>;
}

export interface CalculationResults {
  balancedLoads: {
    northRoof: number;
    westRoof: number;
  };
  unbalancedLoads: {
    northRoof: number;
    westRoof: number;
  };
  driftLoads: {
    leeSide: number;
    windwardSide: number;
  };
  valleyLoads: {
    horizontalLoad: number;
    verticalLoad: number;
  };
  beamDesign?: BeamDesignResults;
  diagrams?: DiagramData;
}

export interface ProjectData {
  id: string;
  name: string;
  description?: string;
  geometry: RoofGeometry;
  inputs: SnowLoadInputs;
  results: CalculationResults;
  createdAt: Date;
  updatedAt: Date;
  version: string;
  checksum: string;
}

export interface CheckpointData {
  id: string;
  projectId: string;
  data: Partial<ProjectData>;
  operation: string;
  timestamp: Date;
  dataSize: number;
}

export interface ErrorContext {
  operation: string;
  projectId?: string;
  checkpointId?: string;
  userId?: string;
  inputData?: any;
  stackTrace?: string;
}

export interface PerformanceMetrics {
  operation: string;
  duration: number;
  success: boolean;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface RecoveryOptions {
  type: "checkpoint" | "backup" | "last_good_state";
  id: string;
  timestamp: Date;
  operation?: string;
  description: string;
  dataSize?: number;
}

export interface SystemHealth {
  databaseStatus: "healthy" | "warning" | "error";
  totalProjects: number;
  recentErrors: number;
  lastBackup?: Date;
  recoveryReady: boolean;
  uptime: number;
}

// Idempotency types
export interface IdempotencyKey {
  key: string;
  operation: string;
  expiresAt: Date;
  result?: any;
}

export interface OperationResult<T = any> {
  success: boolean;
  data?: T;
  error?: Error;
  idempotencyKey?: string;
}

// Validation types
export type ValidationResult = {
  isValid: boolean;
  errors: string[];
};

export type Validator<T> = (value: T, fieldName: string) => ValidationResult;

// Database transaction types
export interface DatabaseTransaction {
  begin(): Promise<void>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
  isActive(): boolean;
}

// Event types for checkpoint triggers
export type CheckpointTrigger =
  | "manual_save"
  | "auto_save"
  | "data_change"
  | "operation_complete"
  | "error_recovery";

export interface CheckpointEvent {
  trigger: CheckpointTrigger;
  projectId: string;
  data: any;
  operation?: string;
}
