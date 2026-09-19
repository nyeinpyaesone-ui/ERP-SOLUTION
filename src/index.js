/**
 * Main entry point for RL Prefix Wired Framework
 */
import PrefixWiredEventEmitter from './events/PrefixWiredEventEmitter.js';
import TaskManager from './tasks/TaskManager.js';
import { RLAgent } from './agents/RLAgent.js';
import { RLEnvironment, GridWorld } from './environments/RLEnvironment.js';
import { SimplePolicy, SimpleValueFunction } from './algorithms/PolicyNetwork.js';
import WorkflowEngine from './workflows/WorkflowEngine.js';

export {
  PrefixWiredEventEmitter,
  TaskManager,
  RLAgent,
  RLEnvironment,
  GridWorld,
  SimplePolicy,
  SimpleValueFunction,
  WorkflowEngine
};

/**
 * Create a complete RL training setup
 */
export function createRLSetup(config = {}) {
  const {
    stateSpace = 2,
    actionSpace = 4,
    learningRate = 0.01,
    discountFactor = 0.99,
    explorationRate = 0.1
  } = config;

  // Create policy and value function
  const policy = new SimplePolicy(stateSpace, actionSpace, { learningRate });
  const valueFunction = new SimpleValueFunction(stateSpace, { learningRate });

  // Create agent
  const agent = new RLAgent({
    stateSpace,
    actionSpace,
    policy,
    valueFunction,
    learningRate,
    discountFactor,
    explorationRate,
    ...config.agent
  });

  return { agent, policy, valueFunction };
}

/**
 * Create a training workflow
 */
export function createTrainingWorkflow(config = {}) {
  const workflow = new WorkflowEngine({
    id: config.id || 'training-workflow',
    stopOnError: config.stopOnError ?? false
  });

  // Step 1: Initialize environment
  workflow.addStep('init-env', 'Initialize Environment', async (context) => {
    const env = new GridWorld(config.environment || {});
    context.environment = env;
    console.log('Environment initialized');
    return env;
  });

  // Step 2: Initialize agent
  workflow.addStep('init-agent', 'Initialize Agent', async (context) => {
    const { agent } = createRLSetup({
      stateSpace: 2,
      actionSpace: 4,
      ...config.agent
    });
    context.agent = agent;
    console.log('Agent initialized');
    return agent;
  });

  // Step 3: Training loop
  workflow.addStep('train', 'Training Loop', async (context) => {
    const { environment, agent } = context;
    const episodes = config.episodes || 100;
    const results = [];

    console.log(`Starting training for ${episodes} episodes...`);

    for (let i = 0; i < episodes; i++) {
      const result = await agent.trainEpisode(environment, config.maxSteps || 1000);
      results.push(result);

      if ((i + 1) % 10 === 0) {
        const avgReward = results.slice(-10).reduce((a, b) => a + b.totalReward, 0) / 10;
        console.log(`Episode ${i + 1}/${episodes}, Avg Reward (last 10): ${avgReward.toFixed(2)}`);
      }
    }

    const finalStats = {
      totalEpisodes: episodes,
      avgReward: results.reduce((a, b) => a + b.totalReward, 0) / episodes,
      minReward: Math.min(...results.map(r => r.totalReward)),
      maxReward: Math.max(...results.map(r => r.totalReward))
    };

    console.log('Training completed:', finalStats);
    context.trainingResults = finalStats;
    return finalStats;
  });

  // Step 4: Evaluate agent
  workflow.addStep('evaluate', 'Evaluate Agent', async (context) => {
    const { environment, agent } = context;
    const evalResults = await agent.evaluate(environment, config.evalEpisodes || 10);
    context.evaluationResults = evalResults;
    console.log('Evaluation completed:', evalResults);
    return evalResults;
  });

  // Step 5: Save results
  workflow.addStep('save', 'Save Results', async (context) => {
    const results = {
      training: context.trainingResults,
      evaluation: context.evaluationResults,
      timestamp: Date.now()
    };
    context.finalResults = results;
    console.log('Results saved');
    return results;
  });

  return workflow;
}

/**
 * Run a complete training pipeline
 */
export async function runTrainingPipeline(config = {}) {
  console.log('=== RL Prefix Wired Training Pipeline ===\n');
  
  const workflow = createTrainingWorkflow(config);
  
  // Setup event listeners for monitoring
  workflow.on('workflow:start', (data) => {
    console.log(`\n[Pipeline] Starting workflow: ${data.id}`);
    console.log(`Total steps: ${data.totalSteps}\n`);
  });

  workflow.on('workflow:step-complete', (data) => {
    console.log(`[Pipeline] Step completed: ${data.stepName}`);
  });

  workflow.on('workflow:complete', (data) => {
    console.log(`\n[Pipeline] Workflow completed successfully!`);
    console.log(`Completed steps: ${data.completedSteps}\n`);
  });

  workflow.on('workflow:error', (data) => {
    console.error(`\n[Pipeline] Workflow error: ${data.error}\n`);
  });

  // Run the workflow
  await workflow.run(true);

  return workflow.getStatus();
}

export default {
  PrefixWiredEventEmitter,
  TaskManager,
  RLAgent,
  RLEnvironment,
  GridWorld,
  SimplePolicy,
  SimpleValueFunction,
  WorkflowEngine,
  createRLSetup,
  createTrainingWorkflow,
  runTrainingPipeline
};
