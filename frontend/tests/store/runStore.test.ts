import { describe, it, expect, beforeEach } from 'vitest';
import { useRunStore } from '../../src/store/runStore';

// We need to reset the store before each test
const initialState = useRunStore.getState();

describe('runStore message logic', () => {
  beforeEach(() => {
    useRunStore.setState(initialState, true); // true = replace state
  });

  it('should append tokens to an existing message from the same node', () => {
    // Initial state
    useRunStore.getState().addMessage({
      role: 'ai',
      content: 'Hello',
      nodeId: 'node-1',
    });

    useRunStore.getState().appendToken(' World', 'node-1');

    const messages = useRunStore.getState().messages;
    expect(messages).toHaveLength(1);
    expect(messages[0].content).toBe('Hello World');
  });

  it('should NOT append tokens to a completed message', () => {
    // 1. Create message
    useRunStore.getState().addMessage({
      role: 'ai',
      content: 'Step 1',
      nodeId: 'node-1',
    });

    // 2. Mark as complete
    useRunStore.getState().completeNodeMessage('node-1');

    const msgsAfterComplete = useRunStore.getState().messages;
    expect(msgsAfterComplete[0].isComplete).toBe(true);

    // 3. Append token for same node (should start new message)
    useRunStore.getState().appendToken('Step 2', 'node-1');

    const finalMessages = useRunStore.getState().messages;
    expect(finalMessages).toHaveLength(2);
    expect(finalMessages[0].content).toBe('Step 1');
    expect(finalMessages[0].isComplete).toBe(true);
    expect(finalMessages[1].content).toBe('Step 2');
    expect(finalMessages[1].role).toBe('ai');
  });

  it('should handle interleaved messages from different nodes', () => {
    // Node A starts
    useRunStore.getState().addMessage({ role: 'ai', content: 'A1', nodeId: 'node-A' });

    // Node B starts
    useRunStore.getState().addMessage({ role: 'ai', content: 'B1', nodeId: 'node-B' });

    // Append to A
    useRunStore.getState().appendToken('A', 'node-A');

    // Append to B
    useRunStore.getState().appendToken('B', 'node-B');

    const messages = useRunStore.getState().messages;
    expect(messages).toHaveLength(2);
    expect(messages[0].content).toBe('A1A');
    expect(messages[1].content).toBe('B1B');
  });

  it('should start new message if last message is from different node but current node completed its previous message', () => {
    // 1. Node A runs and completes
    useRunStore.getState().addMessage({ role: 'ai', content: 'A1', nodeId: 'node-A' });
    useRunStore.getState().completeNodeMessage('node-A');

    // 2. Node B runs
    useRunStore.getState().addMessage({ role: 'ai', content: 'B1', nodeId: 'node-B' });

    // 3. Node A runs AGAIN (e.g. loop)
    useRunStore.getState().appendToken('A2', 'node-A');

    const messages = useRunStore.getState().messages;
    expect(messages).toHaveLength(3);
    expect(messages[0].content).toBe('A1');
    expect(messages[0].isComplete).toBe(true);
    expect(messages[1].content).toBe('B1');
    expect(messages[2].content).toBe('A2');
  });
});
