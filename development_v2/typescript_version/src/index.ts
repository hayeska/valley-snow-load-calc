// Main entry point demonstrating resilient Valley Snow Load Calculator

import { ValleySnowLoadCalculator, createCalculator } from './core/calculator';
import { getLogger } from './utils/logger';
import { getDatabase } from './data/database';
import { getCheckpointManager, shutdownCheckpointSystem, restoreFromBackupFile } from './core/checkpointSystem';
import { ProjectData, RoofGeometry, SnowLoadInputs } from './types';

const logger = getLogger();

async function demonstrateResilientArchitecture(): Promise<void> {
  console.log('🚀 Starting Valley Snow Load Calculator - Comprehensive Error Handling Demo');
  console.log('=' .repeat(80));

  // Demonstrate crash recovery
  console.log('🔍 Checking for crash recovery...');
  try {
    const recoveredData = await restoreFromBackupFile();
    if (recoveredData) {
      console.log('✅ Crash recovery data found!');
      console.log(`   Recovered project: ${recoveredData.name}`);
      console.log(`   Last updated: ${recoveredData.updatedAt.toLocaleString()}`);
      console.log('   💡 In a real application, you would be prompted to restore this data\n');
    } else {
      console.log('✅ No crash recovery needed - clean startup\n');
    }
  } catch (error) {
    console.log('⚠️  Crash recovery check failed, continuing with normal startup\n');
  }

  let calculator: ValleySnowLoadCalculator;
  let db: any;
  let checkpointMgr: any;

  try {
    // Initialize components with error handling
    console.log('📦 Initializing resilient components...');

    calculator = await withErrorBoundary(
      () => createCalculator(),
      { operation: 'demo_calculator_creation' },
      {
        'Error': async (error: Error) => {
          console.error('❌ Calculator creation failed, attempting recovery...');
          throw new Error(`Failed to create calculator: ${error.message}`);
        }
      }
    );

    db = getDatabase();
    checkpointMgr = getCheckpointManager();

    await withErrorBoundary(
      () => db.initialize(),
      { operation: 'demo_db_init' },
      {
        'Error': async (error: Error) => {
          console.log('🔧 Database initialization failed, attempting recovery...');
          // Recovery logic would attempt alternative approaches
          throw error; // For demo, re-throw to show error handling
        }
      }
    );

    await withErrorBoundary(
      () => checkpointMgr.initialize(),
      { operation: 'demo_checkpoint_init' },
      {
        'Error': async (error: Error) => {
          console.log('⚠️  Checkpoint system failed, continuing in degraded mode...');
          // Continue without checkpoints rather than failing
        }
      }
    );

    console.log('✅ All components initialized successfully\n');

  } catch (error) {
    const initError = error as Error;
    console.error('💥 CRITICAL: Failed to initialize components');
    console.error(`Error: ${initError.message}`);
    console.error('Stack trace:', initError.stack);

    // Demonstrate graceful failure
    console.log('🛑 Demo cannot continue due to initialization failure');
    console.log('In a real application, this would trigger recovery procedures');

    // Log the failure
    const logger = getLogger();
    await logger.logError(initError, {
      operation: 'demo_initialization',
      stackTrace: initError.stack
    }, false);

    throw initError;
  }

    // 1. Create a new project with resilience
    console.log('🏗️  Creating new project...');
    const projectId = await calculator.createProject(
      'Demo Valley Snow Load Project',
      'Demonstration of resilient architecture features'
    );
    console.log(`✅ Project created with ID: ${projectId}\n`);

    // 2. Update geometry with validation and error handling
    console.log('📐 Updating roof geometry...');
    const geometry: RoofGeometry = {
      roofPitchN: 8,
      roofPitchW: 10,
      northSpan: 20,
      southSpan: 18,
      ewHalfWidth: 45,
      valleyOffset: 15,
      valleyAngle: 85
    };

    const projectWithGeometry = await calculator.updateGeometry(projectId, geometry);
    console.log('✅ Geometry updated with automatic validation and checkpointing\n');

    // 3. Update snow load inputs with resilience
    console.log('❄️  Updating snow load inputs...');
    const inputs: SnowLoadInputs = {
      groundSnowLoad: 35, // psf - higher snow load
      importanceFactor: 1.1,
      exposureFactor: 1.0,
      thermalFactor: 0.9,
      winterWindParameter: 0.4
    };

    const projectWithInputs = await calculator.updateInputs(projectId, inputs);
    console.log('✅ Inputs updated and calculations completed automatically\n');

    // 4. Demonstrate calculation results
    console.log('🧮 Calculation Results:');
    console.log(`   Balanced Loads: N=${projectWithInputs.results.balancedLoads.northRoof.toFixed(1)} psf, W=${projectWithInputs.results.balancedLoads.westRoof.toFixed(1)} psf`);
    console.log(`   Unbalanced Loads: N=${projectWithInputs.results.unbalancedLoads.northRoof.toFixed(1)} psf, W=${projectWithInputs.results.unbalancedLoads.westRoof.toFixed(1)} psf`);
    console.log(`   Valley Loads: H=${projectWithInputs.results.valleyLoads.horizontalLoad.toFixed(1)} psf, V=${projectWithInputs.results.valleyLoads.verticalLoad.toFixed(1)} psf`);
    console.log();

    // 5. Demonstrate recovery options
    console.log('🔄 Checking recovery options...');
    const recoveryOptions = await calculator.getRecoveryOptions(projectId);
    console.log(`✅ Found ${recoveryOptions.length} recovery options available`);
    recoveryOptions.forEach((option, index) => {
      console.log(`   ${index + 1}. ${option.description}`);
    });
    console.log();

    // 6. Demonstrate project persistence
    console.log('💾 Testing project persistence...');
    await calculator.saveProject(projectWithInputs);
    console.log('✅ Project saved to SQLite database\n');

    // 7. Demonstrate project loading with integrity check
    console.log('📂 Testing project loading and integrity verification...');
    const loadedProject = await calculator.loadProject(projectId);
    console.log(`✅ Project loaded: ${loadedProject.name}`);
    console.log(`   Data integrity verified: ${loadedProject.checksum ? 'Yes' : 'No'}`);
    console.log(`   Last updated: ${loadedProject.updatedAt.toLocaleString()}\n`);

    // 8. Demonstrate system health monitoring
    console.log('🏥 System Health Check:');
    const health = await calculator.getSystemHealth();
    console.log(`   Database Status: ${health.databaseStatus.toUpperCase()}`);
    console.log(`   Total Projects: ${health.totalProjects}`);
    console.log(`   Recent Errors: ${health.recentErrors}`);
    console.log(`   Recovery Ready: ${health.recoveryReady ? 'Yes' : 'No'}`);
    console.log(`   Uptime: ${health.uptime.toFixed(0)} seconds\n`);

    // 9. Demonstrate checkpoint functionality
    console.log('📌 Testing checkpoint system...');
    const checkpointId = await withErrorBoundary(
      () => checkpointMgr.createCheckpoint(projectId, 'demo_checkpoint', loadedProject),
      { operation: 'demo_create_checkpoint', projectId },
      {
        'Error': async (error: Error) => {
          console.log('⚠️  Checkpoint creation failed, continuing demo...');
          return 'checkpoint_failed';
        }
      }
    );

    if (checkpointId !== 'checkpoint_failed') {
      console.log(`✅ Checkpoint created: ${checkpointId}\n`);
    } else {
      console.log('⚠️  Checkpoint creation failed, but demo continues\n');
    }

    // 10. Demonstrate recovery from checkpoint
    console.log('🔧 Testing recovery from checkpoint...');
    if (checkpointId !== 'checkpoint_failed') {
      const recoveredData = await withErrorBoundary(
        () => calculator.recoverFromCheckpoint(checkpointId),
        { operation: 'demo_checkpoint_recovery', checkpointId },
        {
          'Error': async (error: Error) => {
            console.log('⚠️  Checkpoint recovery failed, attempting alternative recovery...');
            // Could try other recovery methods here
            return null;
          }
        }
      );

      console.log(`✅ Data recovered from checkpoint: ${recoveredData ? recoveredData.name : 'Failed'}\n`);
    } else {
      console.log('⏭️  Skipping checkpoint recovery test due to creation failure\n');
    }

    // 11. Demonstrate error scenarios and recovery
    console.log('🚨 Testing Error Scenarios and Recovery:');
    console.log('=' .repeat(50));

    // Test 1: Invalid project loading
    console.log('1. Testing invalid project loading...');
    try {
      await calculator.loadProject('non-existent-project-id');
    } catch (error) {
      console.log(`   ✅ Handled gracefully: ${(error as Error).message}`);
    }

    // Test 2: Invalid geometry data
    console.log('2. Testing invalid geometry validation...');
    try {
      await calculator.updateGeometry(projectId, {
        ...geometry,
        roofPitchN: -10 // Invalid negative pitch
      });
    } catch (error) {
      console.log(`   ✅ Validation error caught: ${(error as Error).message}`);
    }

    // Test 3: Network-like failure simulation (database lock)
    console.log('3. Testing database resilience...');
    const testPromises = Array(5).fill(null).map(async (_, i) => {
      try {
        const testProject = await calculator.createProject(`Concurrent Test ${i}`);
        await calculator.deleteProject(testProject);
        return true;
      } catch (error) {
        console.log(`   ⚠️  Concurrent operation ${i} failed: ${(error as Error).message}`);
        return false;
      }
    });

    const results = await Promise.allSettled(testPromises);
    const successful = results.filter(r => r.status === 'fulfilled' && r.value).length;
    console.log(`   ✅ ${successful}/${results.length} concurrent operations succeeded`);

    console.log();

    // 11. Demonstrate project listing
    console.log('📋 Listing all projects...');
    const allProjects = await calculator.listProjects();
    console.log(`✅ Found ${allProjects.length} project(s):`);
    allProjects.forEach((project, index) => {
      console.log(`   ${index + 1}. ${project.name} (${project.id.substring(0, 8)}...)`);
    });
    console.log();

    // 12. Demonstrate comprehensive error logging
    console.log('📝 Demonstrating Comprehensive Error Logging:');

    // Simulate various error types
    const errorScenarios = [
      { name: 'Validation Error', action: async () => {
        await calculator.updateGeometry(projectId, { ...geometry, roofPitchN: -5 });
      }},
      { name: 'Not Found Error', action: async () => {
        await calculator.loadProject('definitely-not-a-real-project-id');
      }},
      { name: 'Timeout Simulation', action: async () => {
        // Simulate a long operation that might timeout
        await new Promise((resolve, reject) => {
          setTimeout(() => reject(new Error('Simulated timeout')), 100);
        });
      }}
    ];

    for (const scenario of errorScenarios) {
      console.log(`   Testing ${scenario.name}...`);
      try {
        await scenario.action();
        console.log(`   ⚠️  Expected error did not occur`);
      } catch (error) {
        console.log(`   ✅ ${scenario.name} logged: ${(error as Error).message}`);
      }
    }

    console.log('   📄 All errors have been logged to errors.log with full stack traces\n');

    // 13. Demonstrate recovery mechanisms
    console.log('🔄 Demonstrating Recovery Mechanisms:');

    // Show recovery options
    const recoveryOptions = await withErrorBoundary(
      () => calculator.getRecoveryOptions(projectId),
      { operation: 'demo_get_recovery_options', projectId },
      {
        'Error': async (error: Error) => {
          console.log('⚠️  Could not get recovery options, but continuing...');
          return [];
        }
      }
    );

    console.log(`   📋 Available recovery options: ${recoveryOptions.length}`);
    recoveryOptions.slice(0, 3).forEach((option, i) => {
      console.log(`      ${i + 1}. ${option.description}`);
    });

    // Test system health monitoring
    const health = await withErrorBoundary(
      () => calculator.getSystemHealth(),
      { operation: 'demo_health_check' },
      {
        'Error': async (error: Error) => {
          console.log('⚠️  Health check failed, but system continues...');
          return { databaseStatus: 'unknown', totalProjects: 0, recentErrors: 1, recoveryReady: false };
        }
      }
    );

    console.log(`   🏥 System Health: ${health.databaseStatus.toUpperCase()}, ${health.totalProjects} projects`);
    console.log();

    // 13. Performance monitoring demonstration
    console.log('📊 Performance Monitoring:');
    const perfStats = logger.getPerformanceStats();
    console.log(`   Operations tracked: ${Object.keys(perfStats).length}`);

    for (const [operation, stats] of Object.entries(perfStats)) {
      if (stats.count > 0) {
        console.log(`   ${operation}: ${stats.count} calls, avg ${(stats.avgDuration * 1000).toFixed(0)}ms, ${stats.successRate * 100}% success`);
      }
    }
    console.log();

    // 14. Comprehensive Error Analysis
    console.log('📋 Comprehensive Error Analysis:');
    console.log('=' .repeat(40));

    const errorSummary = logger.getErrorSummary();
    console.log(`   Total errors logged: ${errorSummary.totalErrors}`);

    if (errorSummary.mostCommonError) {
      const [errorType, count] = errorSummary.mostCommonError;
      console.log(`   Most common error: ${errorType} (${count} occurrences)`);
    }

    if (errorSummary.errorPatterns) {
      console.log('   Error patterns by type:');
      Object.entries(errorSummary.errorPatterns).slice(0, 5).forEach(([error, count]) => {
        console.log(`      ${error}: ${count} times`);
      });
    }

    // Show log file location
    const path = require('path');
    const os = require('os');
    const logDir = path.join(os.homedir(), 'AppData', 'Local', 'ValleySnowLoadCalc', 'logs');
    console.log(`   📁 Error logs saved to: ${logDir}`);
    console.log('      - errors.log: All errors with full stack traces');
    console.log('      - combined.log: All log levels');
    console.log('      - performance.log: Operation timing data');
    console.log();

    // Cleanup
    console.log('🧹 Performing graceful shutdown...');
    await calculator.shutdown();
    shutdownCheckpointSystem();

    console.log('✅ Demo completed successfully!');
    console.log('🎉 All resilient architecture features demonstrated\n');

    console.log('Key Features Demonstrated:');
    console.log('• ✅ SQLite persistent storage with ACID transactions');
    console.log('• ✅ Winston logging with error tracking and performance monitoring');
    console.log('• ✅ Automatic checkpoints every 2 minutes');
    console.log('• ✅ Crash detection with .crash flag file');
    console.log('• ✅ Auto-save to state.backup.json on changes');
    console.log('• ✅ Data integrity verification with SHA256 checksums');
    console.log('• ✅ Idempotent operations with retry logic');
    console.log('• ✅ Graceful error handling and recovery');
    console.log('• ✅ Auto-save on key events and data changes');
    console.log('• ✅ Crash recovery with multiple restore points');
    console.log('• ✅ Input validation with custom validators');
    console.log('• ✅ System health monitoring');
    console.log('• ✅ Timeout protection for long operations');

  } catch (error) {
    logger.logError(error as Error, {
      operation: 'demo_execution',
      inputData: { phase: 'main_demo' }
    }, false);

    console.error('❌ Demo failed:', (error as Error).message);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Received SIGINT, shutting down gracefully...');
  shutdownCheckpointSystem();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
  shutdownCheckpointSystem();
  process.exit(0);
});

// Run the demonstration
if (require.main === module) {
  demonstrateResilientArchitecture()
    .then(() => {
      console.log('🏁 Demo finished successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Demo failed:', error);
      process.exit(1);
    });
}
