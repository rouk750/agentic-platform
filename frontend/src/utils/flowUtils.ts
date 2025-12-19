
// Helper functions for cleaning graph data before comparison/saving

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const cleanNode = (node: any) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { selected, dragging, resizing, positionAbsolute, measured, width, height, ...rest } = node;
    return rest;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const cleanEdge = (edge: any) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { selected, animated, style, ...rest } = edge;
    return rest;
};
