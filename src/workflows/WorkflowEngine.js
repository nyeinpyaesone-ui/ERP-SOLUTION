/**
 * Workflow Engine for RL Training Pipelines
 * Implements step-by-step execution with event tracking
 */
import PrefixWiredEventEmitter from '../events/PrefixWiredEventEmitter.js';
import TaskManager from '../tasks/TaskManager.js';

export class WorkflowStep {
  constructor(id, name, executeFn, config = {}) {
    this.id = id;
    this.name = name;
    this.executeFn = executeFn;
    this.config = config;
    this.status = 'pending'; // pending, running, completed, failed, skipped
    this.startedAt = null;
    this.completedAt = null;
    this.result = null;
    this.error = null;
    this.retries = 0;
    this.maxRetries = config.maxRetries || 3;
  }

  async execute(context) {
    this.status = 'running';
    this.startedAt = Date.now();
    
    try {
      const result = await this.executeFn(context, this);
      this.status = 'completed';
      this.completedAt = Date.now();
      this.result = result;
      return result;
    } catch (error) {
      this.error = error.message;
      if (this.retries < this.maxRetries) {
        this.retries++;
        this.status = 'pending';
        throw error;
      }
      this.status = 'failed';
      this.completedAt = Date.now();
      throw error;
    }
  }

  skip() {
    this.status = 'skipped';
    this.completedAt = Date.now();
  }

  toJSON() {
    return {
      id: this.id,
      name: this.name,
      status: this.status,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
      result: this.result,
      error: this.error,
      retries: this.retries
    };
  }
}

export class WorkflowEngine extends PrefixWiredEventEmitter {
  constructor(config = {}) {
    super();
    this.id = config.id || `workflow-${Date.now()}`;
    this.steps = new Map();
    this.stepOrder = [];
    this.context = {};
    this.status = 'idle'; // idle, running, paused, completed, failed
    this.currentStepIndex = 0;
    this.taskManager = new TaskManager();
    
    // Setup prefix wires for workflow events
    this.addPrefixWire('workflow:', async (event, data) => {
      await this.handleWorkflowEvent(event, data);
    });

    // Connect task manager events
    this.taskManager.on('task:needs-backfill', (taskId) => {
      this.emitAsync('workflow:step-needs-backfill', { taskId });
    });
  }

  async handleWorkflowEvent(event, data) {
    console.log(`[Workflow Event] ${event}:`, data ? JSON.stringify(data) : '');
  }

  /**
   * Add a step to the workflow
   */
  addStep(id, name, executeFn, config = {}) {
    const step = new WorkflowStep(id, name, executeFn, config);
    this.steps.set(id, step);
    this.stepOrder.push(id);
    this.emitAsync('workflow:step-added', { id, name });
    return this;
  }

  /**
   * Get step by ID
   */
  getStep(id) {
    return this.steps.get(id);
  }

  /**
   * Get all steps
   */
  getAllSteps() {
    return this.stepOrder.map(id => this.steps.get(id));
  }

  /**
   * Get unfinished steps
   */
  getUnfinishedSteps() {
    return this.getAllSteps().filter(s => 
      s.status === 'pending' || s.status === 'running' || s.status === 'failed'
    );
  }

  /**
   * Set context value
   */
  setContext(key, value) {
    this.context[key] = value;
    return this;
  }

  /**
   * Get context value
   */
  getContext(key) {
    return this.context[key];
  }

  /**
   * Run workflow from current position
   */
  async run(fromStart = false) {
    if (this.status === 'running') {
      console.warn('Workflow is already running');
      return;
    }

    if (fromStart) {
      this.currentStepIndex = 0;
    }

    this.status = 'running';
    this.emitAsync('workflow:start', { 
      id: this.id, 
      totalSteps: this.stepOrder.length,
      startIndex: this.currentStepIndex 
    });

    try {
      while (this.currentStepIndex < this.stepOrder.length && this.status === 'running') {
        const stepId = this.stepOrder[this.currentStepIndex];
        const step = this.steps.get(stepId);

        if (!step) {
          this.currentStepIndex++;
          continue;
        }

        if (step.status === 'completed' || step.status === 'skipped') {
          this.currentStepIndex++;
          continue;
        }

        // Execute step
        await this.executeStep(step);

        if (step.status === 'failed') {
          if (step.retries >= step.maxRetries) {
            if (this.config.stopOnError) {
              this.status = 'failed';
              this.emitAsync('workflow:fail', { 
                failedStep: stepId, 
                error: step.error 
              });
              return;
            }
            // Continue to next step if stopOnError is false
          } else {
            // Will retry on next run
            break;
          }
        }

        this.currentStepIndex++;
      }

      if (this.status !== 'failed') {
        this.status = 'completed';
        this.emitAsync('workflow:complete', { 
          id: this.id,
          completedSteps: this.getAllSteps().filter(s => s.status === 'completed').length
        });
      }
    } catch (error) {
      this.status = 'failed';
      this.emitAsync('workflow:error', { error: error.message });
      throw error;
    }
  }

  /**
   * Execute a single step
   */
  async executeStep(step) {
    this.emitAsync('workflow:step-start', { 
      stepId: step.id, 
      stepName: step.name,
      attempt: step.retries + 1 
    });

    try {
      const result = await step.execute(this.context);
      this.emitAsync('workflow:step-complete', { 
        stepId: step.id, 
        result 
      });
      return result;
    } catch (error) {
      this.emitAsync('workflow:step-fail', { 
        stepId: step.id, 
        error: step.error 
      });
      throw error;
    }
  }

  /**
   * Pause workflow execution
   */
  pause() {
    if (this.status === 'running') {
      this.status = 'paused';
      this.emitAsync('workflow:pause', { currentStep: this.currentStepIndex });
    }
  }

  /**
   * Resume workflow execution
   */
  async resume() {
    if (this.status === 'paused') {
      await this.run(false);
    }
  }

  /**
   * Backfill unfinished steps
   */
  async backfillUnfinishedSteps() {
    const unfinished = this.getUnfinishedSteps();
    console.log(`[Backfill] Found ${unfinished.length} unfinished steps`);

    for (const step of unfinished) {
      if (step.status === 'failed' || step.status === 'running') {
        step.status = 'pending';
        step.retries = 0;
        step.error = null;
        step.startedAt = null;
        this.emitAsync('workflow:step-backfilled', { stepId: step.id });
      }
      
      // Reset index to this step
      const index = this.stepOrder.indexOf(step.id);
      if (index < this.currentStepIndex) {
        this.currentStepIndex = index;
      }
    }

    return unfinished.length;
  }

  /**
   * Reset workflow to initial state
   */
  reset() {
    for (const step of this.getAllSteps()) {
      step.status = 'pending';
      step.startedAt = null;
      step.completedAt = null;
      step.result = null;
      step.error = null;
      step.retries = 0;
    }
    this.currentStepIndex = 0;
    this.status = 'idle';
    this.context = {};
    this.emitAsync('workflow:reset', { id: this.id });
  }

  /**
   * Get workflow status
   */
  getStatus() {
    const allSteps = this.getAllSteps();
    return {
      id: this.id,
      status: this.status,
      totalSteps: allSteps.length,
      currentStepIndex: this.currentStepIndex,
      completed: allSteps.filter(s => s.status === 'completed').length,
      pending: allSteps.filter(s => s.status === 'pending').length,
      failed: allSteps.filter(s => s.status === 'failed').length,
      skipped: allSteps.filter(s => s.status === 'skipped').length,
      steps: allSteps.map(s => s.toJSON())
    };
  }
}

export default WorkflowEngine;
