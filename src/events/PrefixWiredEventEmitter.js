/**
 * Prefix Wired Asynchronous Event Emitter
 * Core event system for RL framework with prefix wiring support
 */
import EventEmitter from 'eventemitter3';

export class PrefixWiredEventEmitter extends EventEmitter {
  constructor() {
    super();
    this.prefixWires = new Map();
    this.eventQueue = [];
    this.isProcessing = false;
  }

  /**
   * Register a prefix handler that will be called before any event matching the prefix
   * @param {string} prefix - Event prefix to match (e.g., 'rl:', 'task:')
   * @param {Function} handler - Handler function to execute before matching events
   */
  addPrefixWire(prefix, handler, priority = 0) {
    if (!this.prefixWires.has(prefix)) {
      this.prefixWires.set(prefix, []);
    }
    this.prefixWires.get(prefix).push({ handler, priority });
    this.prefixWires.get(prefix).sort((a, b) => b.priority - a.priority);
    return this;
  }

  /**
   * Remove a prefix wire handler
   * @param {string} prefix 
   * @param {Function} handler 
   */
  removePrefixWire(prefix, handler) {
    if (this.prefixWires.has(prefix)) {
      const wires = this.prefixWires.get(prefix);
      const index = wires.findIndex(w => w.handler === handler);
      if (index > -1) {
        wires.splice(index, 1);
      }
    }
    return this;
  }

  /**
   * Emit an event with prefix wiring execution
   * @param {string} event - Event name
   * @param  {...any} args - Event arguments
   */
  async emit(event, ...args) {
    // Execute prefix wires first
    for (const [prefix, wires] of this.prefixWires) {
      if (event.startsWith(prefix)) {
        for (const wire of wires) {
          await Promise.resolve(wire.handler(event, ...args));
        }
      }
    }

    // Queue the event if already processing
    if (this.isProcessing) {
      this.eventQueue.push({ event, args });
      return;
    }

    this.isProcessing = true;
    try {
      super.emit(event, ...args);
      
      // Process queued events
      while (this.eventQueue.length > 0) {
        const { event: queuedEvent, args: queuedArgs } = this.eventQueue.shift();
        super.emit(queuedEvent, ...queuedArgs);
      }
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Emit event asynchronously without blocking
   * @param {string} event 
   * @param  {...any} args 
   */
  emitAsync(event, ...args) {
    setImmediate(() => this.emit(event, ...args));
    return this;
  }
}

export default PrefixWiredEventEmitter;
