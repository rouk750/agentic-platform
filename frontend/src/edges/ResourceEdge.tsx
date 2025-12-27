import { BaseEdge, EdgeProps, getSmoothStepPath } from '@xyflow/react';

export default function ResourceEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
}: EdgeProps) {
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeDasharray: '5,5', // Dotted line style
          stroke: style.stroke || '#8b5cf6', // Default violet color for resources
          strokeWidth: 2,
        }}
      />
      <title>Resource Link: Implicit Access</title>
    </>
  );
}
