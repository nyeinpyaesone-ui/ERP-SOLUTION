/**
 * Task Module - Handles unfinished tasks with backfill support
 */
import PrefixWiredEventEmitter from '../events/PrefixWiredEventEmitter.js';

export class Task {
  constructor(id, type, payload = {}) {
    this.id = id;
    this.type = type;
    this.payload = payload;
    this.status = 'pending'; // pending, running, completed, failed, backfilled
    this.createdAt = Date.now();
    this.startedAt = null;
    this.completedAt = null;
    this.result = null;
    this.error = null;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  async execute(context) {
    this.status = 'running';
    this.startedAt = Date.now();
    
    try {
      const result = await this.payload.execute?.(context, this);
      this.status = 'completed';
      this.completedAt = Date.now();
      this.result = result;
      return result;
    } catch (error) {
      this.error = error.message;
      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        this.status = 'pending';
        throw error;
      }
      this.status = 'failed';
      this.completedAt = Date.now();
      throw error;
    }
  }

  toJSON() {
    return {
      id: this.id,
      type: this.type,
      status: this.status,
      createdAt: this.createdAt,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
      result: this.result,
      error: this.error,
      retryCount: this.retryCount
    };
  }
}

export class TaskManager extends PrefixWiredEventEmitter {
  constructor() {
    super();
    this.tasks = new Map();
    this.taskQueue = [];
    this.activeTasks = new Set();
    this.maxConcurrent = 5;
    this.isRunning = false;
    
    // Setup prefix wires for task events
    this.addPrefixWire('task:', async (event, taskId, data) => {
      await this.handleTaskEvent(event, taskId, data);
    });
  }

  async handleTaskEvent(event, taskId, data) {
    // Log and track all task events
    console.log(`[Task Event] ${event}: ${taskId}`, data ? JSON.stringify(data) : '');
  }

  createTask(id, type, payload) {
    const task = new Task(id, type, payload);
    this.tasks.set(id, task);
    this.emitAsync('task:created', id, { type, payload });
    return task;
  }

  getTask(id) {
    return this.tasks.get(id);
  }

  getAllTasks() {
    return Array.from(this.tasks.values());
  }

  getUnfinishedTasks() {
    return this.getAllTasks().filter(t => 
      t.status === 'pending' || t.status === 'running' || t.status === 'failed'
    );
  }

  async queueTask(taskId) {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error(`Task ${taskId} not found`);
    }
    
    if (task.status !== 'pending' && task.status !== 'failed') {
      return;
    }

    this.taskQueue.push(taskId);
    this.emitAsync('task:queued', taskId);
    
    if (!this.isRunning) {
      this.processQueue();
    }
  }

  async processQueue() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    
    while (this.taskQueue.length > 0) {
      // Wait if we're at max concurrent tasks
      while (this.activeTasks.size >= this.maxConcurrent) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const taskId = this.taskQueue.shift();
      const task = this.tasks.get(taskId);
      
      if (task && (task.status === 'pending' || task.status === 'failed')) {
        this.activeTasks.add(taskId);
        this.emitAsync('task:started', taskId);
        
        // Execute task asynchronously
        this.executeTask(task).finally(() => {
          this.activeTasks.delete(taskId);
        });
      }
    }
    
    this.isRunning = false;
  }

  async executeTask(task) {
    try {
      const context = { taskManager: this };
      const result = await task.execute(context);
      this.emitAsync('task:completed', task.id, { result });
      return result;
    } catch (error) {
      if (task.status === 'failed') {
        this.emitAsync('task:failed', task.id, { error: task.error });
        
        // Auto-queue for backfill if retries exhausted
        if (task.retryCount >= task.maxRetries) {
          this.emitAsync('task:needs-backfill', task.id);
        }
      } else {
        // Retry
        this.taskQueue.unshift(task.id);
      }
      throw error;
    }
  }

  /**
   * Backfill unfinished or failed tasks
   */
  async backfillUnfinishedTasks() {
    const unfinished = this.getUnfinishedTasks();
    console.log(`[Backfill] Found ${unfinished.length} unfinished tasks`);
    
    for (const task of unfinished) {
      if (task.status === 'failed' || task.status === 'running') {
        task.status = 'pending';
        task.retryCount = 0;
        task.error = null;
        task.startedAt = null;
        this.emitAsync('task:backfilled', task.id);
      }
      await this.queueTask(task.id);
    }
    
    return unfinished.length;
  }

  clearCompleted() {
    for (const [id, task] of this.tasks) {
      if (task.status === 'completed') {
        this.tasks.delete(id);
        this.emitAsync('task:cleared', id);
      }
    }
  }

  getStatus() {
    const all = this.getAllTasks();
    return {
      total: all.length,
      pending: all.filter(t => t.status === 'pending').length,
      running: this.activeTasks.size,
      completed: all.filter(t => t.status === 'completed').length,
      failed: all.filter(t => t.status === 'failed').length,
      backfilled: all.filter(t => t.status === 'backfilled').length
    };
  }
}

export default TaskManager;
