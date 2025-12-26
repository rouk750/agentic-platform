import type { Message } from '../types/execution';

/**
 * Finds the index of the message to append a token to.
 * Searches backwards for a message with the same nodeId.
 * Stops searching if a 'user' message is encountered (new turn boundary).
 */
export const findTargetMessageIndex = (messages: Message[], nodeId: string | undefined): number => {
  // If no nodeId, default to the very last message (legacy/optimistic behavior)
  // Caller handles the check for role='ai' on the absolute last message if needed,
  // but here we are looking for a *specific* target.
  if (!nodeId) return -1;

  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];

    // Stop at user input - we never merge across turns
    if (msg.role === 'user') return -1;

    // Skip traces or other utility messages if necessary,
    // though typically we only care about interleaving AI messages.

    if (msg.role === 'ai' && msg.nodeId === nodeId) {
      // if the message is already completed (e.g. from previous loop iteration),
      // we should not append to it.
      if (msg.isComplete) return -1;
      return i;
    }
  }

  return -1;
};

/**
 * Determines if a new token should be appended to the last message or start a new one.
 * Robust logic to handle missing nodeIds and interleaved streams.
 * @deprecated Use findTargetMessageIndex pattern instead for parallel streams
 */
export const shouldAppendToken = (
  lastMsg: Message | undefined,
  nodeId: string | undefined
): boolean => {
  const isAiMsg = lastMsg && lastMsg.role === 'ai';
  if (!isAiMsg) return false;

  // 1. If we don't have a nodeId for the new token, assume it belongs to current bubble
  if (!nodeId) return true;

  // 2. If last message has no nodeId, assume it's ours (optimistic merge)
  if (!lastMsg.nodeId) return true;

  // 3. If both have IDs, they must match
  return lastMsg.nodeId === nodeId;
};

/**
 * Groups a linear list of messages into columns based on their source Node ID.
 * Used for Split View in parallel execution.
 */
export const groupMessagesByNode = (messages: Message[]): Record<string, Message[]> => {
  const groups: Record<string, Message[]> = {};

  messages.forEach((msg) => {
    // If message has no nodeId (e.g. user input), we might want to show it in ALL columns
    // or a specific "main" column. For now, let's group by nodeId if present.
    // If not present (User/System), maybe put in a "Common" or "System" group?
    // Or for Split View, we might replicate User messages to all streams for context.

    const key = msg.nodeId || 'system'; // 'system' or 'user' messages often lack nodeId

    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(msg);
  });

  return groups;
};

/**
 * Detects if the current execution state involves parallel streams.
 * A heuristic: if we have multiple active nodes OR messages from multiple AI nodes in the recent history.
 */
export const detectParallelism = (activeNodeIds: string[], _messages: Message[]): boolean => {
  // 1. If multiple nodes are currently active, it's parallel.
  if (activeNodeIds.length > 1) return true;

  // 2. Scan recent messages (e.g. last 10) to see if we have interleaved non-sequential nodeIds.
  // Simplifying: just check if active nodes > 1 for now, as that's the live state.
  // The user wants to see streams simultaneously.
  return activeNodeIds.length > 1;
};

// --- Hybrid Layout Types & Logic ---

export type LinearBlock = { type: 'linear'; messages: Message[] };
export type ParallelBlock = { type: 'parallel'; groups: Record<string, Message[]> };
export type LayoutBlock = LinearBlock | ParallelBlock;

/**
 * Groups messages into Linear and Parallel blocks for the Hybrid View.
 * Algorithm:
 * 1. Accumulate consecutive AI messages into a buffer.
 * 2. When a delimiter (User input, System start) is found, flush the buffer.
 * 3. Flush analysis: If buffer contains multiple unique nodeIds, it's a ParallelBlock. Otherwise LinearBlock.
 */
export const groupMessagesForLayout = (messages: Message[]): LayoutBlock[] => {
  const blocks: LayoutBlock[] = [];
  let aiBuffer: Message[] = [];

  const flushBuffer = () => {
    if (aiBuffer.length === 0) return;

    // Analyze buffer
    const nodeIds = new Set(aiBuffer.map((m) => m.nodeId).filter(Boolean));

    if (nodeIds.size > 1) {
      // Parallel Block
      blocks.push({
        type: 'parallel',
        groups: groupMessagesByNode(aiBuffer),
      });
    } else {
      // Linear Block
      blocks.push({
        type: 'linear',
        messages: [...aiBuffer],
      });
    }
    aiBuffer = [];
  };

  messages.forEach((msg) => {
    if (msg.role === 'ai') {
      aiBuffer.push(msg);
    } else {
      // User or System message acts as a delimiter
      flushBuffer();

      // Add the delimiter as a linear block
      blocks.push({
        type: 'linear',
        messages: [msg],
      });
    }
  });

  // Flush any remaining messages at the end
  flushBuffer();

  // Optimization: Merge consecutive linear blocks?
  // Not strictly necessary if renderer handles it, but cleaner.
  // For now, simple list is fine.

  return blocks;
};
