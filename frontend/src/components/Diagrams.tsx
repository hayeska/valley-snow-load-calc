import React, { useRef, useState } from 'react';
import { Stage, Layer, Line, Rect, Text, Group, Arrow, Circle } from 'react-konva';
import type { RoofGeometry, CalculationResults } from '../types';

interface DiagramsProps {
  geometry: RoofGeometry;
  results: CalculationResults;
  width?: number;
  height?: number;
}

interface DiagramControls {
  zoom: number;
  panX: number;
  panY: number;
}

export const Diagrams: React.FC<DiagramsProps> = ({
  geometry,
  results,
  width = 800,
  height = 600
}) => {
  const [controls, setControls] = useState<DiagramControls>({
    zoom: 1,
    panX: 0,
    panY: 0
  });
  const [selectedDiagram, setSelectedDiagram] = useState<'roof' | 'loads' | 'beam'>('roof');
  const stageRef = useRef<any>(null);

  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const oldScale = controls.zoom;
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;

    setControls(prev => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(5, newScale))
    }));
  };

  const RoofCrossSectionDiagram: React.FC = () => {
    const scale = 4; // pixels per foot
    const centerX = width / 2;
    const centerY = height / 2;

    // Calculate roof geometry points
    const ridgeX = centerX;
    const valleyX = centerX + geometry.valleyOffset * scale;
    const ridgeY = centerY - 50;

    // North roof points
    const northEaveX = ridgeX - geometry.northSpan * scale;
    const northEaveY = ridgeY + (geometry.northSpan * scale) * Math.tan((geometry.northPitch * Math.PI) / 180);

    // West roof points
    const westEaveX = valleyX + geometry.southSpan * scale;
    const westEaveY = ridgeY + (geometry.southSpan * scale) * Math.tan((geometry.westPitch * Math.PI) / 180);

    // Valley point (intersection)
    const valleyY = Math.max(northEaveY, westEaveY);

    return (
      <Group>
        {/* Title */}
        <Text
          x={20}
          y={20}
          text="Roof Cross-Section & Valley Geometry"
          fontSize={16}
          fontStyle="bold"
          fill="#1f2937"
        />

        {/* Grid lines */}
        <Line
          points={[0, ridgeY, width, ridgeY]}
          stroke="#e5e7eb"
          strokeWidth={1}
          dash={[5, 5]}
        />

        {/* North Roof Plane */}
        <Line
          points={[northEaveX, northEaveY, ridgeX, ridgeY]}
          stroke="#3b82f6"
          strokeWidth={3}
        />
        <Text
          x={northEaveX - 60}
          y={northEaveY + 10}
          text={`North Roof (${geometry.northPitch}°)`}
          fontSize={12}
          fill="#3b82f6"
        />

        {/* West Roof Plane */}
        <Line
          points={[ridgeX, ridgeY, westEaveX, westEaveY]}
          stroke="#10b981"
          strokeWidth={3}
        />
        <Text
          x={westEaveX + 10}
          y={westEaveY - 20}
          text={`West Roof (${geometry.westPitch}°)`}
          fontSize={12}
          fill="#10b981"
        />

        {/* Valley line (perpendicular to ridge) */}
        <Line
          points={[ridgeX, ridgeY, valleyX, valleyY]}
          stroke="#ef4444"
          strokeWidth={2}
          dash={[10, 5]}
        />

        {/* Valley point */}
        <Circle
          x={valleyX}
          y={valleyY}
          radius={6}
          fill="#ef4444"
        />
        <Text
          x={valleyX + 10}
          y={valleyY - 25}
          text="Valley"
          fontSize={12}
          fontStyle="bold"
          fill="#ef4444"
        />

        {/* Dimensions */}
        {/* North span */}
        <Arrow
          points={[northEaveX, northEaveY + 30, ridgeX, northEaveY + 30]}
          pointerLength={10}
          pointerWidth={10}
          fill="#6b7280"
          stroke="#6b7280"
          strokeWidth={2}
        />
        <Text
          x={(northEaveX + ridgeX) / 2 - 20}
          y={northEaveY + 35}
          text={`${geometry.northSpan}'`}
          fontSize={11}
          fill="#6b7280"
        />

        {/* West span */}
        <Arrow
          points={[ridgeX, ridgeY - 30, westEaveX, ridgeY - 30]}
          pointerLength={10}
          pointerWidth={10}
          fill="#6b7280"
          stroke="#6b7280"
          strokeWidth={2}
        />
        <Text
          x={(ridgeX + westEaveX) / 2 - 15}
          y={ridgeY - 45}
          text={`${geometry.southSpan}'`}
          fontSize={11}
          fill="#6b7280"
        />

        {/* Valley offset */}
        <Arrow
          points={[ridgeX, ridgeY + 20, valleyX, ridgeY + 20]}
          pointerLength={10}
          pointerWidth={10}
          fill="#6b7280"
          stroke="#6b7280"
          strokeWidth={2}
        />
        <Text
          x={(ridgeX + valleyX) / 2 - 20}
          y={ridgeY + 25}
          text={`${geometry.valleyOffset}' offset`}
          fontSize={11}
          fill="#6b7280"
        />

        {/* Valley length */}
        <Text
          x={valleyX - 30}
          y={valleyY + 20}
          text={`Valley Length: ${results.lv.toFixed(2)}'`}
          fontSize={12}
          fontStyle="bold"
          fill="#1f2937"
        />
      </Group>
    );
  };

  const SnowLoadDiagram: React.FC = () => {
    const scale = 4;
    const centerX = width / 2;
    const centerY = height / 2;

    // Calculate roof geometry points (same as above)
    const ridgeX = centerX;
    const valleyX = centerX + geometry.valleyOffset * scale;
    const ridgeY = centerY - 50;

    const northEaveX = ridgeX - geometry.northSpan * scale;
    const northEaveY = ridgeY + (geometry.northSpan * scale) * Math.tan((geometry.northPitch * Math.PI) / 180);

    const westEaveX = valleyX + geometry.southSpan * scale;
    const westEaveY = ridgeY + (geometry.southSpan * scale) * Math.tan((geometry.westPitch * Math.PI) / 180);

    return (
      <Group>
        {/* Title */}
        <Text
          x={20}
          y={20}
          text="Snow Load Distribution (psf)"
          fontSize={16}
          fontStyle="bold"
          fill="#1f2937"
        />

        {/* Roof outline */}
        <Line
          points={[northEaveX, northEaveY, ridgeX, ridgeY, westEaveX, westEaveY]}
          stroke="#6b7280"
          strokeWidth={2}
        />

        {/* Balanced snow load on North roof */}
        <Rect
          x={northEaveX}
          y={ridgeY - 40}
          width={geometry.northSpan * scale}
          height={20}
          fill="#3b82f6"
          opacity={0.7}
        />
        <Text
          x={northEaveX + 20}
          y={ridgeY - 35}
          text={`${results.balancedLoads.northRoof.toFixed(1)} psf`}
          fontSize={11}
          fill="white"
          fontStyle="bold"
        />

        {/* Balanced snow load on West roof */}
        <Rect
          x={ridgeX}
          y={ridgeY - 40}
          width={geometry.southSpan * scale}
          height={20}
          fill="#10b981"
          opacity={0.7}
        />
        <Text
          x={ridgeX + 20}
          y={ridgeY - 35}
          text={`${results.balancedLoads.westRoof.toFixed(1)} psf`}
          fontSize={11}
          fill="white"
          fontStyle="bold"
        />

        {/* Drift load at valley */}
        {results.driftLoads.leeSide > 0 && (
          <Group>
            <Rect
              x={valleyX - 20}
              y={ridgeY - 60}
              width={40}
              height={20}
              fill="#ef4444"
              opacity={0.8}
            />
            <Text
              x={valleyX - 15}
              y={ridgeY - 55}
              text={`${results.driftLoads.leeSide.toFixed(1)} psf`}
              fontSize={10}
              fill="white"
              fontStyle="bold"
            />
          </Group>
        )}

        {/* Valley load indicator */}
        <Circle
          x={valleyX}
          y={ridgeY - 80}
          radius={8}
          fill="#8b5cf6"
        />
        <Text
          x={valleyX + 15}
          y={ridgeY - 85}
          text={`Valley: ${results.valleyLoads.verticalLoad.toFixed(1)} psf`}
          fontSize={12}
          fontStyle="bold"
          fill="#8b5cf6"
        />

        {/* Legend */}
        <Group x={20} y={height - 100}>
          <Rect x={0} y={0} width={15} height={15} fill="#3b82f6" />
          <Text x={20} y={0} text="Balanced Load" fontSize={12} />

          <Rect x={0} y={20} width={15} height={15} fill="#ef4444" />
          <Text x={20} y={20} text="Drift Load" fontSize={12} />

          <Circle x={7} y={42} radius={7} fill="#8b5cf6" />
          <Text x={20} y={35} text="Valley Load" fontSize={12} />
        </Group>
      </Group>
    );
  };

  const BeamDiagram: React.FC = () => {
    const beamLength = results.lv * 4; // Scale for display
    const beamX = (width - beamLength) / 2;
    const beamY = height / 2;

    return (
      <Group>
        {/* Title */}
        <Text
          x={20}
          y={20}
          text="Valley Beam Analysis"
          fontSize={16}
          fontStyle="bold"
          fill="#1f2937"
        />

        {/* Beam */}
        <Line
          points={[beamX, beamY, beamX + beamLength, beamY]}
          stroke="#8b5cf6"
          strokeWidth={8}
          lineCap="round"
        />

        {/* Supports */}
        <Line
          points={[beamX, beamY, beamX, beamY + 30]}
          stroke="#374151"
          strokeWidth={4}
        />
        <Line
          points={[beamX + beamLength, beamY, beamX + beamLength, beamY + 30]}
          stroke="#374151"
          strokeWidth={4}
        />

        {/* Valley load arrow */}
        <Arrow
          points={[beamX + beamLength / 2, beamY - 50, beamX + beamLength / 2, beamY]}
          pointerLength={15}
          pointerWidth={15}
          fill="#ef4444"
          stroke="#ef4444"
          strokeWidth={2}
        />
        <Text
          x={beamX + beamLength / 2 - 30}
          y={beamY - 80}
          text={`${results.valleyLoads.verticalLoad.toFixed(1)} plf`}
          fontSize={12}
          fill="#ef4444"
          fontStyle="bold"
        />

        {/* Dimensions */}
        <Arrow
          points={[beamX, beamY + 50, beamX + beamLength, beamY + 50]}
          pointerLength={10}
          pointerWidth={10}
          fill="#6b7280"
          stroke="#6b7280"
          strokeWidth={2}
        />
        <Text
          x={beamX + beamLength / 2 - 25}
          y={beamY + 55}
          text={`${results.lv.toFixed(2)}' span`}
          fontSize={11}
          fill="#6b7280"
        />

        <Text
          x={beamX + beamLength / 2 - 40}
          y={beamY + 80}
          text="(Simply supported beam analysis)"
          fontSize={10}
          fill="#9ca3af"
        />
      </Group>
    );
  };

  return (
    <div className="space-y-4">
      {/* Diagram Controls */}
      <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedDiagram('roof')}
            className={`px-4 py-2 rounded ${
              selectedDiagram === 'roof'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border'
            }`}
          >
            Roof Geometry
          </button>
          <button
            onClick={() => setSelectedDiagram('loads')}
            className={`px-4 py-2 rounded ${
              selectedDiagram === 'loads'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border'
            }`}
          >
            Snow Loads
          </button>
          <button
            onClick={() => setSelectedDiagram('beam')}
            className={`px-4 py-2 rounded ${
              selectedDiagram === 'beam'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border'
            }`}
          >
            Beam Analysis
          </button>
        </div>

        <div className="flex gap-2 items-center ml-auto">
          <button
            onClick={() => setControls(prev => ({ ...prev, zoom: prev.zoom * 1.2 }))}
            className="px-3 py-1 bg-white border rounded text-sm"
          >
            Zoom +
          </button>
          <span className="text-sm text-gray-600">
            {Math.round(controls.zoom * 100)}%
          </span>
          <button
            onClick={() => setControls(prev => ({ ...prev, zoom: prev.zoom / 1.2 }))}
            className="px-3 py-1 bg-white border rounded text-sm"
          >
            Zoom -
          </button>
        </div>
      </div>

      {/* Diagram Canvas */}
      <div className="border rounded-lg overflow-hidden bg-white">
        <Stage
          ref={stageRef}
          width={width}
          height={height}
          scaleX={controls.zoom}
          scaleY={controls.zoom}
          x={controls.panX}
          y={controls.panY}
          onWheel={handleWheel}
          draggable
          onDragEnd={(e) => {
            setControls(prev => ({
              ...prev,
              panX: e.target.x(),
              panY: e.target.y()
            }));
          }}
        >
          <Layer>
            {selectedDiagram === 'roof' && <RoofCrossSectionDiagram />}
            {selectedDiagram === 'loads' && <SnowLoadDiagram />}
            {selectedDiagram === 'beam' && <BeamDiagram />}
          </Layer>
        </Stage>
      </div>

      {/* Instructions */}
      <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
        <p><strong>Controls:</strong> Drag to pan • Mouse wheel to zoom • Click diagram tabs to switch views</p>
      </div>
    </div>
  );
};
