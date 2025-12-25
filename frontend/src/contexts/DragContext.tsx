/** 拖拽 Context - 用于传递拖拽状态和数据 */

'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface DragContextType {
  draggedElementIds: string[] | null;
  setDraggedElementIds: (ids: string[] | null) => void;
  isDraggingElement: boolean;
  setIsDraggingElement: (isDragging: boolean) => void;
}

const DragContext = createContext<DragContextType>({
  draggedElementIds: null,
  setDraggedElementIds: () => {},
  isDraggingElement: false,
  setIsDraggingElement: () => {},
});

export function DragProvider({ children }: { children: ReactNode }) {
  const [draggedElementIds, setDraggedElementIds] = useState<string[] | null>(null);
  const [isDraggingElement, setIsDraggingElement] = useState(false);

  return (
    <DragContext.Provider
      value={{
        draggedElementIds,
        setDraggedElementIds,
        isDraggingElement,
        setIsDraggingElement,
      }}
    >
      {children}
    </DragContext.Provider>
  );
}

export function useDrag() {
  return useContext(DragContext);
}

