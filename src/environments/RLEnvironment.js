/**
 * Generic RL Environment Interface
 */
import PrefixWiredEventEmitter from '../events/PrefixWiredEventEmitter.js';

export class RLEnvironment extends PrefixWiredEventEmitter {
  constructor(config = {}) {
    super();
    this.id = config.id || `env-${Date.now()}`;
    this.stateSpace = config.stateSpace || null;
    this.actionSpace = config.actionSpace || null;
    this.maxSteps = config.maxSteps || 1000;
    this.currentStep = 0;
    this.done = false;
    
    // Setup prefix wires for environment events
    this.addPrefixWire('env:', async (event, data) => {
      await this.handleEnvEvent(event, data);
    });
  }

  async handleEnvEvent(event, data) {
    console.log(`[Env Event] ${event}:`, data ? JSON.stringify(data) : '');
  }

  /**
   * Reset environment to initial state
   * @returns {Array} Initial state
   */
  async reset() {
    this.currentStep = 0;
    this.done = false;
    this.emitAsync('env:reset', { id: this.id });
    return this.getInitialState();
  }

  /**
   * Get initial state (to be implemented by subclasses)
   * @returns {Array} Initial state vector
   */
  getInitialState() {
    throw new Error('getInitialState must be implemented by subclass');
  }

  /**
   * Execute action in environment
   * @param {number} action - Action to take
   * @returns {Object} { nextState, reward, terminated, truncated, info }
   */
  async step(action) {
    if (this.done) {
      throw new Error('Environment is done. Call reset() first.');
    }

    this.currentStep++;
    this.emitAsync('env:step-start', { action, step: this.currentStep });

    const result = this.executeAction(action);
    
    // Check termination conditions
    result.terminated = this.isTerminal(result.nextState);
    result.truncated = this.currentStep >= this.maxSteps;
    this.done = result.terminated || result.truncated;

    this.emitAsync('env:step-complete', { 
      ...result, 
      step: this.currentStep,
      done: this.done 
    });

    return result;
  }

  /**
   * Execute action and return result (to be implemented by subclasses)
   * @param {number} action 
   * @returns {Object} { nextState, reward, info }
   */
  executeAction(action) {
    throw new Error('executeAction must be implemented by subclass');
  }

  /**
   * Check if state is terminal (to be implemented by subclasses)
   * @param {Array} state 
   * @returns {boolean}
   */
  isTerminal(state) {
    return false;
  }

  /**
   * Render environment (optional)
   */
  render() {
    console.log(`Environment ${this.id} at step ${this.currentStep}`);
  }

  /**
   * Get current state
   * @returns {Array}
   */
  getState() {
    throw new Error('getState must be implemented by subclass');
  }

  toJSON() {
    return {
      id: this.id,
      stateSpace: this.stateSpace,
      actionSpace: this.actionSpace,
      maxSteps: this.maxSteps,
      currentStep: this.currentStep,
      done: this.done
    };
  }
}

/**
 * Simple Grid World Environment Example
 */
export class GridWorld extends RLEnvironment {
  constructor(config = {}) {
    super({
      ...config,
      stateSpace: config.gridSize || 5,
      actionSpace: 4 // up, down, left, right
    });
    this.gridSize = config.gridSize || 5;
    this.goalPosition = config.goalPosition || [this.gridSize - 1, this.gridSize - 1];
    this.obstacles = config.obstacles || [];
    this.agentPosition = [0, 0];
    this.rewardGoal = config.rewardGoal || 10;
    this.rewardObstacle = config.rewardObstacle || -5;
    this.rewardStep = config.rewardStep || -0.1;
  }

  getInitialState() {
    this.agentPosition = [0, 0];
    return [...this.agentPosition];
  }

  getState() {
    return [...this.agentPosition];
  }

  executeAction(action) {
    const [x, y] = this.agentPosition;
    let newX = x;
    let newY = y;

    // Action mapping: 0=up, 1=down, 2=left, 3=right
    switch (action) {
      case 0: newY = Math.min(y + 1, this.gridSize - 1); break;
      case 1: newY = Math.max(y - 1, 0); break;
      case 2: newX = Math.max(x - 1, 0); break;
      case 3: newX = Math.min(x + 1, this.gridSize - 1); break;
    }

    // Check for obstacles
    const hitObstacle = this.obstacles.some(([ox, oy]) => ox === newX && oy === newY);
    
    if (!hitObstacle) {
      this.agentPosition = [newX, newY];
    }

    // Calculate reward
    let reward = this.rewardStep;
    if (this.agentPosition[0] === this.goalPosition[0] && 
        this.agentPosition[1] === this.goalPosition[1]) {
      reward = this.rewardGoal;
    } else if (hitObstacle) {
      reward = this.rewardObstacle;
    }

    return {
      nextState: [...this.agentPosition],
      reward,
      info: { hitObstacle, goalReached: this.isTerminal(this.agentPosition) }
    };
  }

  isTerminal(state) {
    return state[0] === this.goalPosition[0] && state[1] === this.goalPosition[1];
  }

  render() {
    let grid = '';
    for (let y = this.gridSize - 1; y >= 0; y--) {
      for (let x = 0; x < this.gridSize; x++) {
        if (x === this.agentPosition[0] && y === this.agentPosition[1]) {
          grid += 'A ';
        } else if (x === this.goalPosition[0] && y === this.goalPosition[1]) {
          grid += 'G ';
        } else if (this.obstacles.some(([ox, oy]) => ox === x && oy === y)) {
          grid += 'X ';
        } else {
          grid += '. ';
        }
      }
      grid += '\n';
    }
    console.log(grid);
  }
}

export default RLEnvironment;
