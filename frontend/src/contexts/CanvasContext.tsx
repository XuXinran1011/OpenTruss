/** Canvas Context - 用于共享 Canvas ref */

'use client';

import { createContext, useContext, ReactNode } from 'react';
import { CanvasHandle } from '@/components/canvas/Canvas';

interface CanvasContextType {
  canvasRef: React.RefObject<CanvasHandle> | null;
}

const CanvasContext = createContext<CanvasContextType>({ canvasRef: null });

export function CanvasProvider({
  canvasRef,
  children,
}: {
  canvasRef: React.RefObject<CanvasHandle>;
  children: ReactNode;
}) {
  return (
    <CanvasContext.Provider value={{ canvasRef }}>
      {children}
    </CanvasContext.Provider>
  );
}

export function useCanvas() {
  return useContext(CanvasContext);
}

