/**
 * Simple Policy Network for RL
 */
export class SimplePolicy {
  constructor(inputSize, outputSize, config = {}) {
    this.inputSize = inputSize;
    this.outputSize = outputSize;
    this.learningRate = config.learningRate || 0.01;
    
    // Initialize weights with small random values
    this.weights = [];
    this.biases = [];
    
    // Simple single-layer network
    for (let i = 0; i < outputSize; i++) {
      const layerWeights = [];
      for (let j = 0; j < inputSize; j++) {
        layerWeights.push((Math.random() - 0.5) * 0.1);
      }
      this.weights.push(layerWeights);
      this.biases.push(0);
    }
  }

  /**
   * Forward pass through the network
   * @param {Array} input - Input state vector
   * @returns {Array} Output probabilities
   */
  forward(input) {
    const outputs = [];
    
    for (let i = 0; i < this.outputSize; i++) {
      let sum = this.biases[i];
      for (let j = 0; j < this.inputSize; j++) {
        sum += input[j] * this.weights[i][j];
      }
      outputs.push(sum);
    }

    // Softmax activation
    return this.softmax(outputs);
  }

  /**
   * Softmax function
   * @param {Array} x 
   * @returns {Array}
   */
  softmax(x) {
    const maxVal = Math.max(...x);
    const exps = x.map(v => Math.exp(v - maxVal));
    const sumExps = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sumExps);
  }

  /**
   * Predict action from state
   * @param {Array} state 
   * @returns {number} Selected action
   */
  async predict(state) {
    const probs = this.forward(state);
    
    // Sample action based on probabilities
    const rand = Math.random();
    let cumSum = 0;
    for (let i = 0; i < probs.length; i++) {
      cumSum += probs[i];
      if (rand < cumSum) {
        return i;
      }
    }
    return probs.length - 1;
  }

  /**
   * Update policy using REINFORCE-style update
   * @param {Array} state 
   * @param {number} action 
   * @param {number} target - Target value (reward-to-go)
   * @param {number} learningRate 
   * @returns {number} Loss value
   */
  async update(state, action, target, learningRate = this.learningRate) {
    const probs = this.forward(state);
    
    // Calculate loss (negative log likelihood * target)
    const logProb = Math.log(Math.max(probs[action], 1e-10));
    const loss = -logProb * target;

    // Gradient update
    for (let i = 0; i < this.outputSize; i++) {
      for (let j = 0; j < this.inputSize; j++) {
        if (i === action) {
          // Increase probability of taken action
          this.weights[i][j] += learningRate * target * state[j] * (1 - probs[i]);
        } else {
          // Decrease probability of other actions
          this.weights[i][j] -= learningRate * target * state[j] * probs[i];
        }
      }
      
      // Update biases
      if (i === action) {
        this.biases[i] += learningRate * target * (1 - probs[i]);
      } else {
        this.biases[i] -= learningRate * target * probs[i];
      }
    }

    return loss;
  }

  /**
   * Get policy parameters
   * @returns {Object}
   */
  getParams() {
    return {
      weights: this.weights.map(w => [...w]),
      biases: [...this.biases]
    };
  }

  /**
   * Set policy parameters
   * @param {Object} params 
   */
  setParams(params) {
    this.weights = params.weights.map(w => [...w]);
    this.biases = [...params.biases];
  }

  toJSON() {
    return {
      inputSize: this.inputSize,
      outputSize: this.outputSize,
      learningRate: this.learningRate,
      weightsShape: [this.outputSize, this.inputSize]
    };
  }
}

/**
 * Simple Value Function Approximator
 */
export class SimpleValueFunction {
  constructor(inputSize, config = {}) {
    this.inputSize = inputSize;
    this.learningRate = config.learningRate || 0.01;
    
    // Initialize weights
    this.weights = [];
    for (let i = 0; i < inputSize; i++) {
      this.weights.push((Math.random() - 0.5) * 0.1);
    }
    this.bias = 0;
  }

  /**
   * Predict value of state
   * @param {Array} state 
   * @returns {number} Value estimate
   */
  async predict(state) {
    let value = this.bias;
    for (let i = 0; i < this.inputSize; i++) {
      value += state[i] * this.weights[i];
    }
    return value;
  }

  /**
   * Update value function using TD error
   * @param {Array} state 
   * @param {number} target 
   * @param {number} learningRate 
   * @returns {number} TD error
   */
  async update(state, target, learningRate = this.learningRate) {
    const prediction = await this.predict(state);
    const tdError = target - prediction;

    // Update weights
    for (let i = 0; i < this.inputSize; i++) {
      this.weights[i] += learningRate * tdError * state[i];
    }
    this.bias += learningRate * tdError;

    return Math.abs(tdError);
  }

  toJSON() {
    return {
      inputSize: this.inputSize,
      learningRate: this.learningRate
    };
  }
}

export default { SimplePolicy, SimpleValueFunction };
