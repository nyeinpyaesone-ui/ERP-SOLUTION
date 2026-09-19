# RL Prefix Wired Framework

A reinforcement learning framework with prefix wired asynchronous event handling, submodule backfill integration, and workflow-based training pipelines.

## Features

- **Prefix Wired Asynchronous Event System**: Event emitter with prefix-based handlers that execute before matching events
- **Task Management with Backfill**: Handle unfinished tasks with automatic retry and backfill capabilities
- **RL Agent Implementation**: Complete agent with policy network, value function, and experience replay
- **Environment Interface**: Extensible environment base class with GridWorld example
- **Workflow Engine**: Step-by-step execution pipeline with pause/resume and error recovery
- **Event-Driven Architecture**: All components emit detailed events for monitoring and debugging

## Project Structure

```
/workspace
├── src/
│   ├── index.js                 # Main entry point and exports
│   ├── runner.js                # CLI runner for train/evaluate/backfill
│   ├── events/
│   │   └── PrefixWiredEventEmitter.js  # Core event system
│   ├── tasks/
│   │   └── TaskManager.js       # Task management with backfill
│   ├── agents/
│   │   └── RLAgent.js           # RL agent implementation
│   ├── environments/
│   │   └── RLEnvironment.js     # Environment base & GridWorld
│   ├── algorithms/
│   │   └── PolicyNetwork.js     # Policy and value function
│   └── workflows/
│       └── WorkflowEngine.js    # Workflow pipeline engine
├── package.json
└── README.md
```

## Installation

```bash
npm install
```

## Usage

### Training Pipeline

Run a complete training pipeline with 50 episodes:

```bash
npm run train
# or
node src/runner.js train
```

### Evaluation

Evaluate a trained agent:

```bash
node src/runner.js evaluate
```

### Backfill Unfinished Tasks

Backfill and retry failed or unfinished tasks:

```bash
node src/runner.js backfill
```

### Programmatic Usage

```javascript
import { 
  RLAgent, 
  GridWorld, 
  SimplePolicy, 
  SimpleValueFunction,
  WorkflowEngine,
  TaskManager,
  runTrainingPipeline
} from './src/index.js';

// Run complete training pipeline
const status = await runTrainingPipeline({
  episodes: 100,
  environment: { gridSize: 5 },
  agent: { learningRate: 0.05 }
});

// Or build custom workflow
const workflow = new WorkflowEngine();
workflow
  .addStep('init', 'Initialize', async (ctx) => { ... })
  .addStep('train', 'Train', async (ctx) => { ... })
  .addStep('evaluate', 'Evaluate', async (ctx) => { ... });

await workflow.run();
```

## Core Concepts

### Prefix Wired Events

The `PrefixWiredEventEmitter` allows registering handlers that execute before any event matching a prefix:

```javascript
const emitter = new PrefixWiredEventEmitter();

// Register prefix handler
emitter.addPrefixWire('task:', async (event, ...args) => {
  console.log(`Task event: ${event}`);
});

// This will trigger the prefix handler first
emitter.emit('task:created', taskId, data);
```

### Task Backfill

Tasks that fail or remain unfinished can be backfilled:

```javascript
const taskManager = new TaskManager();

// Create and queue tasks
taskManager.createTask('task-1', 'type', { execute: ... });
await taskManager.queueTask('task-1');

// Backfill any unfinished tasks
const count = await taskManager.backfillUnfinishedTasks();
```

### Workflow Steps

Workflows execute steps sequentially with full state tracking:

```javascript
const workflow = new WorkflowEngine();

workflow.addStep('step-1', 'First Step', async (context) => {
  // Do something
  return result;
});

// Run from start
await workflow.run(true);

// Pause and resume
workflow.pause();
await workflow.resume();

// Backfill unfinished steps
await workflow.backfillUnfinishedSteps();
```

## API Reference

### PrefixWiredEventEmitter

- `addPrefixWire(prefix, handler, priority)` - Register prefix handler
- `removePrefixWire(prefix, handler)` - Remove prefix handler
- `emit(event, ...args)` - Emit event with prefix wiring
- `emitAsync(event, ...args)` - Emit event asynchronously

### TaskManager

- `createTask(id, type, payload)` - Create a new task
- `queueTask(taskId)` - Queue task for execution
- `getUnfinishedTasks()` - Get all unfinished tasks
- `backfillUnfinishedTasks()` - Reset and requeue unfinished tasks
- `getStatus()` - Get task statistics

### RLAgent

- `selectAction(state)` - Select action with exploration
- `storeExperience(state, action, reward, nextState, done)` - Store experience
- `trainEpisode(env, maxSteps)` - Train for one episode
- `evaluate(env, episodes)` - Evaluate agent performance

### WorkflowEngine

- `addStep(id, name, executeFn, config)` - Add workflow step
- `run(fromStart)` - Execute workflow
- `pause()` / `resume()` - Control execution
- `backfillUnfinishedSteps()` - Reset failed steps
- `getStatus()` - Get workflow status

## Event Flow

All components emit events with prefix wiring:

```
task:created → task:queued → task:started → task:completed/failed
agent:episode-start → agent:action-selected → agent:episode-complete
env:reset → env:step-start → env:step-complete
workflow:start → workflow:step-start → workflow:complete
```

## License

MIT
