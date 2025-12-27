/** 拖拽 Context - 用于传递拖拽状态和数据 */

'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface DragContextType {
  draggedElementIds: string[] | null;
  setDraggedElementIds: (ids: string[] | null) => void;
  isDraggingElement: boolean;
  setIsDraggingElement: (isDragging: boolean) => void;
  dragPosition: { x: number; y: number } | null;
  setDragPosition: (position: { x: number; y: number } | null) => void;
  dragPreviewElement: HTMLElement | null;
  setDragPreviewElement: (element: HTMLElement | null) => void;
}

const DragContext = createContext<DragContextType>({
  draggedElementIds: null,
  setDraggedElementIds: () => {},
  isDraggingElement: false,
  setIsDraggingElement: () => {},
  dragPosition: null,
  setDragPosition: () => {},
  dragPreviewElement: null,
  setDragPreviewElement: () => {},
});

export function DragProvider({ children }: { children: ReactNode }) {
  const [draggedElementIds, setDraggedElementIds] = useState<string[] | null>(null);
  const [isDraggingElement, setIsDraggingElement] = useState(false);
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);
  const [dragPreviewElement, setDragPreviewElement] = useState<HTMLElement | null>(null);

  return (
    <DragContext.Provider
      value={{
        draggedElementIds,
        setDraggedElementIds,
        isDraggingElement,
        setIsDraggingElement,
        dragPosition,
        setDragPosition,
        dragPreviewElement,
        setDragPreviewElement,
      }}
    >
      {children}
    </DragContext.Provider>
  );
}

export function useDrag() {
  return useContext(DragContext);
}

