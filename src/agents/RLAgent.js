/**
 * Reinforcement Learning Agent with Prefix Wired Async Support
 */
import PrefixWiredEventEmitter from '../events/PrefixWiredEventEmitter.js';

export class RLAgent extends PrefixWiredEventEmitter {
  constructor(config = {}) {
    super();
    this.id = config.id || `agent-${Date.now()}`;
    this.stateSpace = config.stateSpace || null;
    this.actionSpace = config.actionSpace || null;
    this.policy = config.policy || null;
    this.valueFunction = config.valueFunction || null;
    this.learningRate = config.learningRate || 0.01;
    this.discountFactor = config.discountFactor || 0.99;
    this.explorationRate = config.explorationRate || 0.1;
    this.experienceBuffer = [];
    this.maxBufferSize = config.maxBufferSize || 10000;
    this.trainingStep = 0;
    
    // Setup prefix wires for agent events
    this.addPrefixWire('agent:', async (event, data) => {
      await this.handleAgentEvent(event, data);
    });
  }

  async handleAgentEvent(event, data) {
    console.log(`[Agent Event] ${event}:`, data ? JSON.stringify(data) : '');
  }

  /**
   * Select action based on current policy with exploration
   * @param {Array} state - Current state vector
   * @returns {number} Selected action
   */
  async selectAction(state) {
    this.emitAsync('agent:action-select-start', { state, step: this.trainingStep });
    
    // Epsilon-greedy exploration
    if (Math.random() < this.explorationRate) {
      const randomAction = Math.floor(Math.random() * this.actionSpace);
      this.emitAsync('agent:action-selected', { action: randomAction, exploratory: true });
      return randomAction;
    }

    // Use policy to select action
    if (this.policy) {
      const action = await this.policy.predict(state);
      this.emitAsync('agent:action-selected', { action, exploratory: false });
      return action;
    }

    // Default: random action
    const defaultAction = Math.floor(Math.random() * this.actionSpace);
    this.emitAsync('agent:action-selected', { action: defaultAction, exploratory: true });
    return defaultAction;
  }

  /**
   * Store experience tuple
   * @param {Array} state 
   * @param {number} action 
   * @param {number} reward 
   * @param {Array} nextState 
   * @param {boolean} done 
   */
  storeExperience(state, action, reward, nextState, done) {
    const experience = { state, action, reward, nextState, done };
    this.experienceBuffer.push(experience);
    
    if (this.experienceBuffer.length > this.maxBufferSize) {
      this.experienceBuffer.shift();
    }
    
    this.emitAsync('agent:experience-stored', { 
      bufferSize: this.experienceBuffer.length,
      experience 
    });
  }

  /**
   * Sample batch from experience buffer
   * @param {number} batchSize 
   * @returns {Array} Batch of experiences
   */
  sampleBatch(batchSize = 32) {
    const batch = [];
    const bufferLength = this.experienceBuffer.length;
    
    for (let i = 0; i < batchSize && bufferLength > 0; i++) {
      const index = Math.floor(Math.random() * bufferLength);
      batch.push(this.experienceBuffer[index]);
    }
    
    return batch;
  }

  /**
   * Update agent based on batch of experiences
   * @param {Array} batch 
   */
  async update(batch) {
    this.emitAsync('agent:update-start', { batchSize: batch.length, step: this.trainingStep });
    
    if (!this.policy) {
      console.warn('No policy configured for training');
      return;
    }

    let totalLoss = 0;
    
    for (const exp of batch) {
      const { state, action, reward, nextState, done } = exp;
      
      // Calculate target value
      let target = reward;
      if (!done && this.valueFunction) {
        const nextValue = await this.valueFunction.predict(nextState);
        target += this.discountFactor * nextValue;
      }

      // Update policy
      const loss = await this.policy.update(state, action, target, this.learningRate);
      totalLoss += loss;
    }

    this.trainingStep++;
    const avgLoss = totalLoss / batch.length;
    
    this.emitAsync('agent:update-complete', { 
      step: this.trainingStep, 
      avgLoss,
      batchSize: batch.length 
    });
    
    return avgLoss;
  }

  /**
   * Train agent for one episode
   * @param {Environment} env 
   * @param {number} maxSteps 
   * @returns {Object} Episode statistics
   */
  async trainEpisode(env, maxSteps = 1000) {
    this.emitAsync('agent:episode-start', { episode: this.trainingStep });
    
    let state = await env.reset();
    let totalReward = 0;
    let steps = 0;
    let done = false;

    while (!done && steps < maxSteps) {
      const action = await this.selectAction(state);
      const { nextState, reward, terminated, truncated } = await env.step(action);
      done = terminated || truncated;
      
      this.storeExperience(state, action, reward, nextState, done);
      
      state = nextState;
      totalReward += reward;
      steps++;
    }

    // Update agent with episode experiences
    const batch = this.sampleBatch(Math.min(64, this.experienceBuffer.length));
    if (batch.length > 0) {
      await this.update(batch);
    }

    // Decay exploration rate
    this.explorationRate = Math.max(0.01, this.explorationRate * 0.995);

    this.emitAsync('agent:episode-complete', { 
      episode: this.trainingStep,
      totalReward, 
      steps,
      explorationRate: this.explorationRate 
    });

    return { totalReward, steps, done };
  }

  /**
   * Evaluate agent performance
   * @param {Environment} env 
   * @param {number} episodes 
   * @returns {Object} Evaluation statistics
   */
  async evaluate(env, episodes = 10) {
    this.emitAsync('agent:evaluation-start', { episodes });
    
    // Disable exploration during evaluation
    const originalExploration = this.explorationRate;
    this.explorationRate = 0;

    let totalRewards = [];
    let totalSteps = [];

    for (let i = 0; i < episodes; i++) {
      const result = await this.trainEpisode(env, 1000);
      totalRewards.push(result.totalReward);
      totalSteps.push(result.steps);
    }

    // Restore exploration rate
    this.explorationRate = originalExploration;

    const stats = {
      avgReward: totalRewards.reduce((a, b) => a + b, 0) / episodes,
      minReward: Math.min(...totalRewards),
      maxReward: Math.max(...totalRewards),
      avgSteps: totalSteps.reduce((a, b) => a + b, 0) / episodes,
      episodes
    };

    this.emitAsync('agent:evaluation-complete', stats);
    
    return stats;
  }

  toJSON() {
    return {
      id: this.id,
      stateSpace: this.stateSpace,
      actionSpace: this.actionSpace,
      learningRate: this.learningRate,
      discountFactor: this.discountFactor,
      explorationRate: this.explorationRate,
      trainingStep: this.trainingStep,
      bufferSize: this.experienceBuffer.length
    };
  }
}

export default RLAgent;
