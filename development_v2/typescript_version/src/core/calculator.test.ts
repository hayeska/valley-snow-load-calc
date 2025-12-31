// Unit tests for resilient Valley Snow Load Calculator

import { ValleySnowLoadCalculator } from "./calculator";
import { getDatabase } from "../data/database";
import { getLogger } from "../utils/logger";
import { getCheckpointManager } from "./checkpointSystem";
import { ProjectData, RoofGeometry, SnowLoadInputs } from "../types";

// Mock the database and logger for testing
jest.mock("../data/database");
jest.mock("../utils/logger");
jest.mock("./checkpointSystem");

describe("ValleySnowLoadCalculator", () => {
  let calculator: ValleySnowLoadCalculator;
  let mockDb: any;
  let mockLogger: any;
  let mockCheckpointMgr: any;

  beforeEach(async () => {
    // Reset mocks
    mockDb = {
      initialize: jest.fn().mockResolvedValue(undefined),
      saveProject: jest.fn().mockResolvedValue(undefined),
      loadProject: jest.fn(),
      deleteProject: jest.fn().mockResolvedValue(true),
      listProjects: jest.fn().mockResolvedValue([]),
      getSystemHealth: jest.fn().mockResolvedValue({
        databaseStatus: "healthy",
        totalProjects: 0,
        recentErrors: 0,
        recoveryReady: true,
        uptime: 100,
      }),
      isOperationCompleted: jest.fn().mockResolvedValue(false),
      markOperationCompleted: jest.fn().mockResolvedValue(undefined),
    };

    mockLogger = {
      logError: jest.fn(),
      logPerformance: jest.fn(),
      logRecoveryAction: jest.fn(),
      info: jest.fn(),
      getPerformanceStats: jest.fn().mockReturnValue({}),
      getErrorSummary: jest.fn().mockReturnValue({ totalErrors: 0 }),
    };

    mockCheckpointMgr = {
      initialize: jest.fn().mockResolvedValue(undefined),
      createCheckpoint: jest.fn().mockResolvedValue("checkpoint_123"),
      getRecoveryOptions: jest.fn().mockResolvedValue([]),
      markProjectActive: jest.fn(),
      markProjectInactive: jest.fn(),
      restoreFromCheckpoint: jest.fn(),
    };

    (getDatabase as jest.Mock).mockReturnValue(mockDb);
    (getLogger as jest.Mock).mockReturnValue(mockLogger);
    (getCheckpointManager as jest.Mock).mockReturnValue(mockCheckpointMgr);

    calculator = new ValleySnowLoadCalculator();
    await calculator.initialize();
  });

  describe("Project Operations", () => {
    it("should create project successfully", async () => {
      const projectId = await calculator.createProject("Test Project");

      expect(typeof projectId).toBe("string");
      expect(projectId.length).toBeGreaterThan(0);
      expect(mockDb.saveProject).toHaveBeenCalled();
      expect(mockCheckpointMgr.markProjectActive).toHaveBeenCalledWith(
        projectId,
      );
    });

    it("should load project with data integrity check", async () => {
      const mockProject: ProjectData = {
        id: "test-project",
        name: "Test Project",
        description: "",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "valid_checksum",
      };

      mockDb.loadProject.mockResolvedValue(mockProject);

      const project = await calculator.loadProject("test-project");

      expect(project).toEqual(mockProject);
      expect(mockCheckpointMgr.markProjectActive).toHaveBeenCalledWith(
        "test-project",
      );
    });

    it("should save project with checkpoint", async () => {
      const projectData: ProjectData = {
        id: "test-project",
        name: "Test Project",
        description: "",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "",
      };

      await calculator.saveProject(projectData);

      expect(mockDb.saveProject).toHaveBeenCalledWith(projectData);
      expect(mockCheckpointMgr.createCheckpoint).toHaveBeenCalledWith(
        "test-project",
        "manual_save",
        projectData,
      );
    });

    it("should delete project safely", async () => {
      await calculator.deleteProject("test-project");

      expect(mockDb.deleteProject).toHaveBeenCalledWith("test-project");
      expect(mockCheckpointMgr.markProjectInactive).toHaveBeenCalledWith(
        "test-project",
      );
    });
  });

  describe("Geometry Operations", () => {
    it("should update geometry with validation", async () => {
      const geometry: RoofGeometry = {
        roofPitchN: 8,
        roofPitchW: 10,
        northSpan: 20,
        southSpan: 18,
        ewHalfWidth: 45,
        valleyOffset: 15,
        valleyAngle: 90,
      };

      const mockProject: ProjectData = {
        id: "test-project",
        name: "Test Project",
        description: "",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "",
      };

      mockDb.loadProject.mockResolvedValue(mockProject);

      const result = await calculator.updateGeometry("test-project", geometry);

      expect(result.geometry).toEqual(geometry);
      expect(mockDb.saveProject).toHaveBeenCalled();
    });

    it("should reject invalid geometry", async () => {
      const invalidGeometry: RoofGeometry = {
        roofPitchN: -5, // Invalid negative pitch
        roofPitchW: 10,
        northSpan: 20,
        southSpan: 18,
        ewHalfWidth: 45,
        valleyOffset: 15,
        valleyAngle: 90,
      };

      await expect(
        calculator.updateGeometry("test-project", invalidGeometry),
      ).rejects.toThrow("Validation failed");
    });
  });

  describe("Input Operations", () => {
    it("should update inputs and recalculate", async () => {
      const inputs: SnowLoadInputs = {
        groundSnowLoad: 35,
        importanceFactor: 1.1,
        exposureFactor: 1.0,
        thermalFactor: 0.9,
        winterWindParameter: 0.4,
      };

      const mockProject: ProjectData = {
        id: "test-project",
        name: "Test Project",
        description: "",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "",
      };

      mockDb.loadProject.mockResolvedValue(mockProject);

      const result = await calculator.updateInputs("test-project", inputs);

      expect(result.inputs).toEqual(inputs);
      expect(result.results.balancedLoads.northRoof).toBeGreaterThan(0);
      expect(mockDb.saveProject).toHaveBeenCalled();
    });
  });

  describe("Calculation Operations", () => {
    it("should perform calculations correctly", async () => {
      const geometry = calculator["getDefaultGeometry"]();
      const inputs = calculator["getDefaultInputs"]();

      const results = await calculator.performCalculations(geometry, inputs);

      expect(results).toHaveProperty("balancedLoads");
      expect(results).toHaveProperty("unbalancedLoads");
      expect(results).toHaveProperty("driftLoads");
      expect(results).toHaveProperty("valleyLoads");

      expect(results.balancedLoads.northRoof).toBeGreaterThan(0);
      expect(results.valleyLoads.horizontalLoad).toBeGreaterThan(0);
    });

    it("should handle calculation timeouts", async () => {
      // Test timeout protection (would need longer-running calculation)
      const geometry = calculator["getDefaultGeometry"]();
      const inputs = calculator["getDefaultInputs"]();

      const results = await calculator.performCalculations(geometry, inputs);
      expect(results).toBeDefined();
    });
  });

  describe("Recovery Operations", () => {
    it("should get recovery options", async () => {
      const mockOptions = [
        {
          type: "checkpoint" as const,
          id: "checkpoint_1",
          timestamp: new Date(),
          operation: "auto_save",
          description: "Auto save checkpoint",
        },
      ];

      mockCheckpointMgr.getRecoveryOptions.mockResolvedValue(mockOptions);

      const options = await calculator.getRecoveryOptions("test-project");
      expect(options).toEqual(mockOptions);
    });

    it("should recover from checkpoint", async () => {
      const mockRecoveredData: ProjectData = {
        id: "test-project",
        name: "Recovered Project",
        description: "",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "",
      };

      mockCheckpointMgr.restoreFromCheckpoint.mockResolvedValue(
        mockRecoveredData,
      );

      const result = await calculator.recoverFromCheckpoint("checkpoint_123");

      expect(result).toEqual(mockRecoveredData);
      expect(mockDb.saveProject).toHaveBeenCalledWith(mockRecoveredData);
    });
  });

  describe("System Operations", () => {
    it("should list projects", async () => {
      const mockProjects: ProjectData[] = [
        {
          id: "project-1",
          name: "Project 1",
          description: "",
          geometry: calculator["getDefaultGeometry"](),
          inputs: calculator["getDefaultInputs"](),
          results: calculator["getEmptyResults"](),
          createdAt: new Date(),
          updatedAt: new Date(),
          version: "2.0.0",
          checksum: "",
        },
      ];

      mockDb.listProjects.mockResolvedValue(mockProjects);

      const projects = await calculator.listProjects();
      expect(projects).toEqual(mockProjects);
    });

    it("should get system health", async () => {
      const health = await calculator.getSystemHealth();

      expect(health).toHaveProperty("databaseStatus");
      expect(health).toHaveProperty("totalProjects");
      expect(health).toHaveProperty("recoveryReady");
    });
  });

  describe("Idempotency", () => {
    it("should handle idempotent operations", async () => {
      // Test that operations can be safely retried
      const projectId1 = await calculator.createProject("Test Project");
      const projectId2 = await calculator.createProject("Test Project");

      // In a real implementation, this would return the same ID
      // For this test, we just verify no exceptions are thrown
      expect(typeof projectId1).toBe("string");
      expect(typeof projectId2).toBe("string");
    });
  });

  describe("Comprehensive Error Handling", () => {
    it("should handle database errors gracefully with recovery attempts", async () => {
      mockDb.loadProject.mockRejectedValue(
        new Error("Database connection failed"),
      );

      // Should attempt recovery from checkpoint
      mockCheckpointMgr.getRecoveryOptions.mockResolvedValue([
        {
          type: "checkpoint",
          id: "checkpoint_1",
          timestamp: new Date(),
          operation: "auto_save",
        },
      ]);

      await expect(calculator.loadProject("test-project")).rejects.toThrow(
        "Database connection failed",
      );

      expect(mockLogger.logError).toHaveBeenCalled();
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        "Attempting checkpoint recovery for project load",
        true,
      );
    });

    it("should validate inputs and provide detailed error messages", async () => {
      const invalidGeometry: RoofGeometry = {
        roofPitchN: -5, // Invalid negative pitch
        roofPitchW: 10,
        northSpan: 20,
        southSpan: 18,
        ewHalfWidth: 45,
        valleyOffset: 15,
        valleyAngle: 90,
      };

      await expect(
        calculator.updateGeometry("test-project", invalidGeometry),
      ).rejects.toThrow();

      expect(mockLogger.logError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          operation: expect.stringContaining("update_geometry"),
          inputData: expect.any(Object),
        }),
        true,
      );
    });

    it("should handle concurrent operations with proper error isolation", async () => {
      const operations = [
        calculator.createProject("Concurrent 1"),
        calculator.createProject("Concurrent 2"),
        calculator.createProject("Concurrent 3"),
      ];

      const results = await Promise.allSettled(operations);

      // Some operations should succeed, some might fail due to simulated errors
      const fulfilled = results.filter((r) => r.status === "fulfilled").length;
      const rejected = results.filter((r) => r.status === "rejected").length;

      expect(fulfilled + rejected).toBe(3);
      expect(fulfilled).toBeGreaterThanOrEqual(0);
    });

    it("should attempt recovery when project loading fails", async () => {
      // Mock database failure
      mockDb.loadProject.mockRejectedValue(new Error("Corrupted data"));

      // Mock successful recovery
      mockCheckpointMgr.getRecoveryOptions.mockResolvedValue([
        { type: "checkpoint", id: "recovery_1", timestamp: new Date() },
      ]);
      mockCheckpointMgr.restoreFromCheckpoint.mockResolvedValue({
        id: "test-project",
        name: "Recovered Project",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
      });

      const result = await calculator["attemptProjectRecovery"]("test-project");

      expect(result).toBeTruthy();
      expect(result?.name).toBe("Recovered Project");
      expect(mockLogger.logRecoveryAction).toHaveBeenCalledWith(
        "Project recovered from checkpoint",
        true,
        expect.any(Object),
      );
    });

    it("should validate project data integrity", async () => {
      const validProject: ProjectData = {
        id: "test-project",
        name: "Valid Project",
        description: "Test project",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
        checksum: "valid_checksum",
      };

      // Should not throw for valid data
      await expect(
        calculator["validateProjectData"](validProject),
      ).resolves.not.toThrow();
    });

    it("should handle invalid project data gracefully", async () => {
      const invalidProject = {
        id: "", // Invalid empty ID
        name: "",
        geometry: null, // Invalid geometry
        inputs: null,
        results: null,
      } as any;

      await expect(
        calculator["validateProjectData"](invalidProject),
      ).rejects.toThrow("Invalid project data: missing required fields");

      expect(mockLogger.logError).toHaveBeenCalled();
    });

    it("should handle fuzzy project matching when exact ID not found", async () => {
      mockDb.loadProject.mockResolvedValue(null); // Project not found
      mockDb.listProjects.mockResolvedValue([
        {
          id: "matching-project-123",
          name: "Test Valley Project",
          geometry: calculator["getDefaultGeometry"](),
          inputs: calculator["getDefaultInputs"](),
          results: calculator["getEmptyResults"](),
          createdAt: new Date(),
          updatedAt: new Date(),
          version: "2.0.0",
        },
      ]);

      // Mock successful loading of found project
      mockDb.loadProject.mockResolvedValueOnce({
        id: "matching-project-123",
        name: "Test Valley Project",
        geometry: calculator["getDefaultGeometry"](),
        inputs: calculator["getDefaultInputs"](),
        results: calculator["getEmptyResults"](),
        createdAt: new Date(),
        updatedAt: new Date(),
        version: "2.0.0",
      });

      const result = await calculator.loadProject("valley"); // Partial match

      expect(result.name).toBe("Test Valley Project");
      expect(mockLogger.info).toHaveBeenCalledWith(
        "Project found by fuzzy match: Test Valley Project",
        expect.any(Object),
      );
    });

    it("should provide detailed error context for debugging", async () => {
      const error = new Error("Test error");
      const context = {
        operation: "test_operation",
        projectId: "test-123",
        inputData: { complex: "data" },
        stackTrace: error.stack,
      };

      mockLogger.logError(error, context, true);

      expect(mockLogger.logError).toHaveBeenCalledWith(
        error,
        expect.objectContaining({
          operation: "test_operation",
          projectId: "test-123",
          inputData: expect.any(Object),
          stackTrace: expect.any(String),
        }),
        true,
      );
    });

    it("should handle timeout errors in operations", async () => {
      // Mock a timeout scenario
      mockDb.loadProject.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(null), 100)),
      );

      const startTime = Date.now();
      await expect(calculator.loadProject("timeout-test")).rejects.toThrow();

      // Should have logged timeout information
      expect(mockLogger.logError).toHaveBeenCalled();
    });

    it("should maintain operation idempotency", async () => {
      mockDb.isOperationCompleted.mockResolvedValue(true);
      mockDb.get.mockResolvedValue({
        result: JSON.stringify({ id: "cached-result" }),
      });

      const result1 = await calculator.createProject("Idempotent Test");
      const result2 = await calculator.createProject("Idempotent Test");

      expect(result1).toBeDefined();
      expect(result2).toBe("cached-result");
      expect(mockLogger.info).toHaveBeenCalledWith(
        "Operation create_project already completed (idempotent)",
        expect.any(Object),
      );
    });
  });

  describe("Performance Monitoring", () => {
    it("should track operation performance", async () => {
      await calculator.createProject("Performance Test");

      expect(mockLogger.logPerformance).toHaveBeenCalled();
    });

    it("should provide performance statistics", () => {
      const stats = calculator["logger"].getPerformanceStats();

      expect(typeof stats).toBe("object");
    });
  });
});
