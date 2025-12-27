/** 3D 预览组件
 * 
 * 使用 React Three Fiber 实现真正的 3D 渲染
 * 支持程序化渲染代理几何（不依赖 IFC）
 */

'use client';

import { useMemo, useRef, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid } from '@react-three/drei';
import { ElementDetail } from '@/services/elements';
import { geometryTo3d, Point3D, calculate3dBoundingBox } from '@/utils/geometry3d';
import { Group } from 'three';

interface Preview3DProps {
  elements: ElementDetail[];
  selectedElementIds?: string[];
  onElementClick?: (elementId: string) => void;
  onClose?: () => void;
  height?: number;
  width?: number;
}

/**
 * 渲染单个元素
 */
function ElementMesh({ 
  element, 
  isSelected, 
  onClick 
}: { 
  element: ElementDetail; 
  isSelected: boolean;
  onClick?: () => void;
}) {
  const meshRef = useRef<Group>(null);
  
  // 将几何坐标转换为 3D 点
  const points3d = useMemo(() => {
    return geometryTo3d(
      element.geometry,
      element.base_offset ?? 0,
      element.height ?? 0
    );
  }, [element.geometry, element.base_offset, element.height]);
  
  // 根据元素类型渲染不同的几何体
  const geometry = useMemo(() => {
    if (points3d.length < 2) return null;
    
    const elementType = element.speckle_type;
    const height = element.height ?? 0;
    const baseOffset = element.base_offset ?? 0;
    
    if (elementType === 'Wall' || elementType === 'Column') {
      // Wall/Column: 从轮廓路径和 height（拉伸距离）渲染 Box
      if (element.geometry.type === 'Polyline' && points3d.length >= 2) {
        // 计算轮廓的中心点和尺寸
        const bbox = calculate3dBoundingBox(points3d);
        const width = Math.max(bbox.maxX - bbox.minX, 0.1);
        const depth = Math.max(bbox.maxY - bbox.minY, 0.1);
        const heightValue = height > 0 ? height : 0.1;
        
        return {
          type: 'box' as const,
          width,
          height: heightValue,
          depth,
          position: [
            (bbox.minX + bbox.maxX) / 2,
            (bbox.minY + bbox.maxY) / 2,
            baseOffset + heightValue / 2
          ] as [number, number, number]
        };
      }
    } else if (elementType === 'Beam') {
      // Beam: 从 3D 起点/终点和 height（横截面深度）渲染 Box
      if (points3d.length >= 2) {
        const start = points3d[0];
        const end = points3d[points3d.length - 1];
        const length = Math.sqrt(
          Math.pow(end.x - start.x, 2) + 
          Math.pow(end.y - start.y, 2) + 
          Math.pow(end.z - start.z, 2)
        );
        const heightValue = height > 0 ? height : 0.3;
        const width = heightValue; // 假设横截面为正方形
        
        // 计算中心点和旋转
        const centerX = (start.x + end.x) / 2;
        const centerY = (start.y + end.y) / 2;
        const centerZ = (start.z + end.z) / 2;
        
        return {
          type: 'box' as const,
          width: heightValue,
          height: heightValue,
          depth: length,
          position: [centerX, centerY, centerZ] as [number, number, number],
          rotation: calculateRotation(start, end)
        };
      }
    } else if (elementType === 'Pipe') {
      // Pipe: 从 3D 中心线路径和直径渲染 Cylinder
      if (points3d.length >= 2) {
        const diameter = (element as any).diameter ?? 0.1;
        const radius = diameter / 2;
        
        // 创建沿路径的多个圆柱体
        const segments: Array<{
          type: 'cylinder';
          radius: number;
          height: number;
          position: [number, number, number];
          rotation: [number, number, number];
        }> = [];
        
        for (let i = 0; i < points3d.length - 1; i++) {
          const start = points3d[i];
          const end = points3d[i + 1];
          const length = Math.sqrt(
            Math.pow(end.x - start.x, 2) + 
            Math.pow(end.y - start.y, 2) + 
            Math.pow(end.z - start.z, 2)
          );
          
          const centerX = (start.x + end.x) / 2;
          const centerY = (start.y + end.y) / 2;
          const centerZ = (start.z + end.z) / 2;
          
          segments.push({
            type: 'cylinder',
            radius,
            height: length,
            position: [centerX, centerY, centerZ],
            rotation: calculateRotation(start, end)
          });
        }
        
        return { type: 'segments' as const, segments };
      }
    } else if (elementType === 'Floor' || elementType === 'Ceiling') {
      // Floor/Ceiling: 从轮廓和厚度渲染 Box（简化处理）
      if (element.geometry.type === 'Polyline' && points3d.length >= 3) {
        const thickness = height > 0 ? height : 0.2;
        const bbox = calculate3dBoundingBox(points3d);
        const width = Math.max(bbox.maxX - bbox.minX, 0.1);
        const depth = Math.max(bbox.maxY - bbox.minY, 0.1);
        const avgZ = points3d.reduce((sum, p) => sum + p.z, 0) / points3d.length;
        
        return {
          type: 'box' as const,
          width,
          height: thickness,
          depth,
          position: [
            (bbox.minX + bbox.maxX) / 2,
            (bbox.minY + bbox.maxY) / 2,
            avgZ + thickness / 2
          ] as [number, number, number]
        };
      }
    }
    
    // 默认：渲染为线框
    return {
      type: 'line' as const,
      points: points3d
    };
  }, [points3d, element]);
  
  if (!geometry) return null;
  
  const color = isSelected ? '#EA580C' : '#3F3F46';
  
  return (
    <group ref={meshRef} onClick={onClick}>
      {geometry.type === 'box' && (
        <mesh position={geometry.position} rotation={geometry.rotation}>
          <boxGeometry args={[geometry.width, geometry.height, geometry.depth]} />
          <meshStandardMaterial color={color} opacity={0.7} transparent />
        </mesh>
      )}
      {geometry.type === 'segments' && (
        <group>
          {geometry.segments.map((seg, i) => (
            <mesh key={i} position={seg.position} rotation={seg.rotation}>
              <cylinderGeometry args={[seg.radius, seg.radius, seg.height, 32]} />
              <meshStandardMaterial color={color} opacity={0.7} transparent />
            </mesh>
          ))}
        </group>
      )}
      {geometry.type === 'line' && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={geometry.points.length}
              array={new Float32Array(geometry.points.flatMap(p => [p.x, p.y, p.z]))}
              itemSize={3}
              usage="static"
            />
          </bufferGeometry>
          <lineBasicMaterial color={color} />
        </line>
      )}
    </group>
  );
}

/**
 * 计算从起点到终点的旋转角度
 */
function calculateRotation(start: Point3D, end: Point3D): [number, number, number] {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const dz = end.z - start.z;
  
  // 计算绕 Z 轴的旋转（水平方向）
  const yaw = Math.atan2(dy, dx);
  
  // 计算绕 Y 轴的旋转（垂直方向）
  const pitch = Math.atan2(dz, Math.sqrt(dx * dx + dy * dy));
  
  return [0, yaw, pitch];
}

/**
 * 场景内容
 */
function SceneContent({ 
  elements, 
  selectedElementIds = [],
  onElementClick 
}: { 
  elements: ElementDetail[];
  selectedElementIds: string[];
  onElementClick?: (elementId: string) => void;
}) {
  const { camera } = useThree();
  
  // 计算所有元素的边界框，用于自动调整相机
  const bbox = useMemo(() => {
    const allPoints: Point3D[] = [];
    elements.forEach(element => {
      const points3d = geometryTo3d(
        element.geometry,
        element.base_offset ?? 0,
        element.height ?? 0
      );
      allPoints.push(...points3d);
    });
    
    if (allPoints.length === 0) {
      return {
        minX: -10, minY: -10, minZ: 0,
        maxX: 10, maxY: 10, maxZ: 10
      };
    }
    
    return calculate3dBoundingBox(allPoints);
  }, [elements]);
  
  // 自动调整相机位置
  useEffect(() => {
    const centerX = (bbox.minX + bbox.maxX) / 2;
    const centerY = (bbox.minY + bbox.maxY) / 2;
    const centerZ = (bbox.minZ + bbox.maxZ) / 2;
    
    const sizeX = bbox.maxX - bbox.minX;
    const sizeY = bbox.maxY - bbox.minY;
    const sizeZ = bbox.maxZ - bbox.minZ;
    const maxSize = Math.max(sizeX, sizeY, sizeZ, 10);
    
    // 将相机放置在斜上方，距离根据边界框大小调整
    const distance = maxSize * 2;
    camera.position.set(
      centerX + distance * 0.7,
      centerY + distance * 0.7,
      centerZ + distance * 0.5
    );
    camera.lookAt(centerX, centerY, centerZ);
  }, [bbox, camera]);
  
  return (
    <>
      {/* 网格 */}
      <Grid args={[100, 100]} cellColor="#6b7280" sectionColor="#9ca3af" />
      
      {/* 坐标轴 */}
      <axesHelper args={[10]} />
      
      {/* 渲染所有元素 */}
      {elements.map(element => (
        <ElementMesh
          key={element.id}
          element={element}
          isSelected={selectedElementIds.includes(element.id)}
          onClick={() => onElementClick?.(element.id)}
        />
      ))}
      
      {/* 相机控制 */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={1}
        maxDistance={1000}
      />
    </>
  );
}

/**
 * 主组件
 */
export function Preview3D({
  elements,
  selectedElementIds = [],
  onElementClick,
  onClose,
  height,
  width,
}: Preview3DProps) {
  // 如果未指定尺寸，使用父容器
  const containerStyle = height && width 
    ? { width, height }
    : { width: '100%', height: '100%' };
  
  return (
    <div className="w-full h-full relative">
      {/* 3D 画布 */}
      <Canvas>
        <PerspectiveCamera makeDefault position={[10, 10, 10]} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <SceneContent
          elements={elements}
          selectedElementIds={selectedElementIds}
          onElementClick={onElementClick}
        />
      </Canvas>
      
      {/* 控制提示（悬浮在画布上） */}
      <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
        拖拽旋转 · 滚轮缩放 · 右键平移
      </div>
    </div>
  );
}
