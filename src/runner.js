/**
 * Runner script for RL training and evaluation
 * Usage: node src/runner.js [train|evaluate|backfill]
 */
import { runTrainingPipeline, createTrainingWorkflow, TaskManager } from './index.js';

async function main() {
  const command = process.argv[2] || 'train';
  
  console.log(`\n========================================`);
  console.log(`RL Prefix Wired Framework Runner`);
  console.log(`Command: ${command}`);
  console.log(`========================================\n`);

  switch (command) {
    case 'train':
      await runTrain();
      break;
    case 'evaluate':
      await runEvaluate();
      break;
    case 'backfill':
      await runBackfill();
      break;
    default:
      console.log('Usage: node src/runner.js [train|evaluate|backfill]');
      process.exit(1);
  }
}

async function runTrain() {
  console.log('Starting training pipeline...\n');
  
  const config = {
    episodes: 50,
    maxSteps: 500,
    evalEpisodes: 5,
    environment: {
      gridSize: 5,
      goalPosition: [4, 4],
      obstacles: [[2, 2], [3, 2], [1, 3]],
      rewardGoal: 10,
      rewardObstacle: -5,
      rewardStep: -0.1
    },
    agent: {
      learningRate: 0.05,
      discountFactor: 0.95,
      explorationRate: 0.3
    },
    stopOnError: false
  };

  try {
    const status = await runTrainingPipeline(config);
    
    console.log('\n========================================');
    console.log('Training Pipeline Status');
    console.log('========================================');
    console.log(`Status: ${status.status}`);
    console.log(`Total Steps: ${status.totalSteps}`);
    console.log(`Completed: ${status.completed}`);
    console.log(`Pending: ${status.pending}`);
    console.log(`Failed: ${status.failed}`);
    
    if (status.finalResults) {
      console.log('\nFinal Results:');
      console.log(JSON.stringify(status.finalResults, null, 2));
    }
    
    process.exit(status.status === 'completed' ? 0 : 1);
  } catch (error) {
    console.error('Training failed:', error.message);
    process.exit(1);
  }
}

async function runEvaluate() {
  console.log('Starting evaluation...\n');
  
  const workflow = createTrainingWorkflow({
    episodes: 10,
    environment: {
      gridSize: 5,
      goalPosition: [4, 4],
      obstacles: [[2, 2]]
    }
  });

  // Only run the evaluate step by skipping others
  for (const [id, step] of workflow.steps) {
    if (id !== 'init-env' && id !== 'init-agent') {
      step.skip();
    }
  }

  workflow.currentStepIndex = 0;
  
  try {
    await workflow.run(false);
    const status = workflow.getStatus();
    
    console.log('\nEvaluation Results:');
    console.log(JSON.stringify(status, null, 2));
    
    process.exit(0);
  } catch (error) {
    console.error('Evaluation failed:', error.message);
    process.exit(1);
  }
}

async function runBackfill() {
  console.log('Running backfill for unfinished tasks...\n');
  
  const taskManager = new TaskManager();
  
  // Create some sample tasks to demonstrate backfill
  taskManager.createTask('task-1', 'training', {
    execute: async () => {
      console.log('Executing task 1...');
      return { success: true };
    }
  });
  
  taskManager.createTask('task-2', 'evaluation', {
    execute: async () => {
      console.log('Executing task 2...');
      return { success: true };
    }
  });
  
  taskManager.createTask('task-3', 'save', {
    execute: async () => {
      console.log('Executing task 3...');
      return { saved: true };
    }
  });

  // Queue all tasks
  await Promise.all([
    taskManager.queueTask('task-1'),
    taskManager.queueTask('task-2'),
    taskManager.queueTask('task-3')
  ]);

  // Wait a bit for tasks to process
  await new Promise(resolve => setTimeout(resolve, 500));

  console.log('\nInitial Status (all completed):');
  console.log(JSON.stringify(taskManager.getStatus(), null, 2));

  // Simulate some tasks becoming unfinished (failed)
  const task2 = taskManager.getTask('task-2');
  if (task2) {
    task2.status = 'failed';
    task2.error = 'Simulated failure for backfill demo';
    task2.completedAt = null;
  }

  console.log('\nAfter simulating failure on task-2:');
  console.log(JSON.stringify(taskManager.getStatus(), null, 2));

  // Backfill unfinished tasks
  console.log('\nBackfilling unfinished tasks...');
  const backfilled = await taskManager.backfillUnfinishedTasks();
  console.log(`Backfilled ${backfilled} tasks`);

  // Wait for backfilled tasks to complete
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.log('\nFinal Status:');
  console.log(JSON.stringify(taskManager.getStatus(), null, 2));

  process.exit(0);
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
