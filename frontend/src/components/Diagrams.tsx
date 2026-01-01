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
    const scale = 3; // pixels per foot - adjusted for plan view
    const centerX = width / 2;
    const centerY = height / 2;

    // Building dimensions based on geometry
    const buildingWidth = geometry.ewHalfWidth * 2 * scale; // Total width
    const buildingHeight = geometry.northSpan * scale * 2; // Total height

    // Building outline coordinates (centered)
    const buildingLeft = centerX - buildingWidth / 2;
    const buildingRight = centerX + buildingWidth / 2;
    const buildingTop = centerY - buildingHeight / 2;
    const buildingBottom = centerY + buildingHeight / 2;

    // Ridge lines
    const ewRidgeY = centerY; // Horizontal E-W ridge through center
    const nsRidgeX = centerX; // Vertical N-S ridge through center

    // Valley lines - converging to low point
    // Valley offset creates the convergence point
    const valleyOffset = geometry.valleyOffset * scale;
    const valleyLowX = centerX + valleyOffset;
    const valleyLowY = centerY;


    return (
      <Group>
        {/* Title */}
        <Text
          x={20}
          y={20}
          text="Roof Plan View with Valley Geometry"
          fontSize={16}
          fontStyle="bold"
          fill="#1f2937"
        />

        {/* Building Outline - Rectangular */}
        <Rect
          x={buildingLeft}
          y={buildingTop}
          width={buildingWidth}
          height={buildingHeight}
          stroke="#000000"
          strokeWidth={2}
          fill="transparent"
        />

        {/* E-W Ridge (horizontal solid line across center) */}
        <Line
          points={[buildingLeft, ewRidgeY, buildingRight, ewRidgeY]}
          stroke="#000000"
          strokeWidth={2}
        />

        {/* N-S Ridge (vertical solid line from E-W ridge midpoint south only) */}
        <Line
          points={[nsRidgeX, ewRidgeY, nsRidgeX, buildingBottom]}
          stroke="#000000"
          strokeWidth={2}
        />

        {/* Valley Lines (dashed red lines along valley direction) */}
        {/* Valley line extending from ridge intersection */}
        <Line
          points={[
            valleyLowX, ewRidgeY,
            valleyLowX, buildingBottom
          ]}
          stroke="#ef4444"
          strokeWidth={2}
          dash={[8, 4]}
        />

        {/* Valley low point marker */}
        <Circle
          x={valleyLowX}
          y={valleyLowY}
          radius={4}
          fill="#ef4444"
        />

        {/* Labels and Dimensions */}

        {/* North span 16.0 ft above top */}
        <Text
          x={centerX - 30}
          y={buildingTop - 25}
          text={`North span ${geometry.northSpan.toFixed(1)} ft`}
          fontSize={11}
          fill="#000000"
        />

        {/* South span 16.0 ft below bottom */}
        <Text
          x={centerX - 30}
          y={buildingBottom + 10}
          text={`South span ${geometry.southSpan.toFixed(1)} ft`}
          fontSize={11}
          fill="#000000"
        />

        {/* lu_west 42.2 ft on left and right */}
        <Text
          x={buildingLeft - 50}
          y={centerY - 10}
          text={`lu_west ${geometry.ewHalfWidth.toFixed(1)} ft`}
          fontSize={11}
          fill="#000000"
        />
        <Text
          x={buildingRight + 10}
          y={centerY - 10}
          text={`lu_west ${geometry.ewHalfWidth.toFixed(1)} ft`}
          fontSize={11}
          fill="#000000"
        />

        {/* Valley offset ±16.0 ft with bidirectional arrow */}
        <Arrow
          points={[centerX - valleyOffset, ewRidgeY + 30, centerX + valleyOffset, ewRidgeY + 30]}
          pointerLength={8}
          pointerWidth={8}
          fill="#000000"
          stroke="#000000"
          strokeWidth={1}
        />
        <Arrow
          points={[centerX + valleyOffset, ewRidgeY + 30, centerX - valleyOffset, ewRidgeY + 30]}
          pointerLength={8}
          pointerWidth={8}
          fill="#000000"
          stroke="#000000"
          strokeWidth={1}
        />
        <Text
          x={centerX - 25}
          y={ewRidgeY + 35}
          text={`Valley offset ±${geometry.valleyOffset.toFixed(1)} ft`}
          fontSize={11}
          fill="#000000"
        />

        {/* lv = 22.6 ft along valley line */}
        <Text
          x={valleyLowX + 10}
          y={valleyLowY + 5}
          text={`lv = ${results.lv.toFixed(1)} ft`}
          fontSize={11}
          fill="#ef4444"
          fontStyle="bold"
        />

        {/* Compass "N ↑" in top-right */}
        <Text
          x={width - 60}
          y={40}
          text="N ↑"
          fontSize={14}
          fill="#000000"
          fontStyle="bold"
        />

        {/* Legend in corner */}
        <Group x={20} y={height - 120}>
          <Text x={0} y={0} text="Legend:" fontSize={12} fontStyle="bold" fill="#000000" />

          <Line x={0} y={15} points={[0, 0, 20, 0]} stroke="#000000" strokeWidth={2} />
          <Text x={25} y={10} text="Building Outline (black solid)" fontSize={10} fill="#000000" />

          <Line x={0} y={30} points={[0, 0, 20, 0]} stroke="#000000" strokeWidth={2} />
          <Text x={25} y={25} text="E-W Ridge (black solid)" fontSize={10} fill="#000000" />

          <Line x={0} y={45} points={[0, 0, 20, 0]} stroke="#000000" strokeWidth={2} />
          <Text x={25} y={40} text="N-S Ridge (black solid)" fontSize={10} fill="#000000" />

          <Line x={0} y={60} points={[0, 0, 20, 0]} stroke="#ef4444" strokeWidth={2} dash={[4, 2]} />
          <Text x={25} y={55} text="Valley Line (red dashed)" fontSize={10} fill="#000000" />
        </Group>
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
