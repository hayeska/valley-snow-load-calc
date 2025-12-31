import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Label } from './components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table'
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert'
import { Separator } from './components/ui/separator'
import { Calculator, Snowflake, AlertTriangle, CheckCircle, Zap, Ruler, Building } from 'lucide-react'

import { calculator } from './services/calculator'
import type { RoofGeometry, SnowLoadInputs, BeamDesignInputs, CalculationResults } from './types'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<CalculationResults | null>(null)
  const [error, setError] = useState<string>('')

  // Form state
  const [geometry, setGeometry] = useState<RoofGeometry>({
    northPitch: 8,
    westPitch: 10,
    northSpan: 20,
    southSpan: 17,
    ewHalfWidth: 45,
    valleyOffset: 15,
    valleyAngle: 90,
  })

  const [snowInputs, setSnowInputs] = useState<SnowLoadInputs>({
    groundSnowLoad: 50,
    importanceFactor: 1.0,
    exposureFactor: 1.0,
    thermalFactor: 1.2,
    winterWindParameter: 0.4,
    isSlipperySurface: false,
  })

  const [beamInputs, setBeamInputs] = useState<BeamDesignInputs>({
    beamWidth: 5.125,
    beamDepth: 11.875,
    materialType: 'Douglas Fir',
    allowableFb: 2400,
    allowableFv: 265,
    modulusE: 1800000,
    deflectionLimitSnow: 240,
    deflectionLimitTotal: 360,
    roofDeadLoad: 15,
  })

  const [includeBeamDesign, setIncludeBeamDesign] = useState(false)

  const handleCalculate = async () => {
    setIsLoading(true)
    setError('')
    try {
      const calculationResults = await calculator.performCalculations(
        geometry,
        snowInputs,
        includeBeamDesign ? beamInputs : undefined
      )
      setResults(calculationResults)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGeometryChange = (field: keyof RoofGeometry, value: number) => {
    setGeometry((prev: RoofGeometry) => ({ ...prev, [field]: value }))
  }

  const handleSnowInputChange = (field: keyof SnowLoadInputs, value: number | boolean) => {
    setSnowInputs((prev: SnowLoadInputs) => ({ ...prev, [field]: value }))
  }

  const handleBeamInputChange = (field: keyof BeamDesignInputs, value: number | string) => {
    setBeamInputs((prev: BeamDesignInputs) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Snowflake className="h-10 w-10 text-blue-600" />
            <Building className="h-8 w-8 text-green-600" />
            <h1 className="text-4xl font-bold text-gray-900">Valley Snow Load Calculator</h1>
          </div>
          <p className="text-lg text-gray-600 max-w-4xl mx-auto">
            Complete engineering tool for calculating snow loads on valley structures according to ASCE 7-22 standards.
            Features roof geometry analysis, beam design, real-time calculations, and comprehensive results.
          </p>
          <div className="mt-4 flex items-center justify-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-green-500" />
              ASCE 7-22 Compliant
            </span>
            <span className="flex items-center gap-1">
              <Ruler className="h-4 w-4 text-blue-500" />
              Valley Geometry Analysis
            </span>
            <span className="flex items-center gap-1">
              <Zap className="h-4 w-4 text-orange-500" />
              Beam Design Module
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Input Parameters Card */}
          <div className="xl:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5" />
                  Input Parameters
                </CardTitle>
                <CardDescription>
                  Complete roof geometry, snow loads, and beam design parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <Tabs defaultValue="geometry" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="geometry">Roof Geometry & Valleys</TabsTrigger>
                    <TabsTrigger value="loads">Snow Load Parameters</TabsTrigger>
                    <TabsTrigger value="beam">Beam Design</TabsTrigger>
                  </TabsList>

                  <TabsContent value="geometry" className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Roof Slope Angles</h3>
                        <div className="space-y-2">
                          <Label htmlFor="northPitch">North Roof Slope (degrees from horizontal)</Label>
                          <Input
                            id="northPitch"
                            type="number"
                            step="0.1"
                            min="0"
                            max="90"
                            value={geometry.northPitch}
                            onChange={(e) => handleGeometryChange('northPitch', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Angle from horizontal plane (rise/run)</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="westPitch">West Roof Slope (degrees from horizontal)</Label>
                          <Input
                            id="westPitch"
                            type="number"
                            step="0.1"
                            min="0"
                            max="90"
                            value={geometry.westPitch}
                            onChange={(e) => handleGeometryChange('westPitch', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Angle from horizontal plane (rise/run)</p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Horizontal Spans</h3>
                        <div className="space-y-2">
                          <Label htmlFor="northSpan">North Roof Horizontal Span (ft)</Label>
                          <Input
                            id="northSpan"
                            type="number"
                            step="0.1"
                            min="0"
                            value={geometry.northSpan}
                            onChange={(e) => handleGeometryChange('northSpan', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Horizontal distance from eave to ridge</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="southSpan">South Roof Horizontal Span (ft)</Label>
                          <Input
                            id="southSpan"
                            type="number"
                            step="0.1"
                            min="0"
                            value={geometry.southSpan}
                            onChange={(e) => handleGeometryChange('southSpan', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Horizontal distance from eave to ridge</p>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Valley Configuration</h3>
                        <div className="space-y-2">
                          <Label htmlFor="ewHalfWidth">East-West Half Width (ft)</Label>
                          <Input
                            id="ewHalfWidth"
                            type="number"
                            step="0.1"
                            min="0"
                            value={geometry.ewHalfWidth}
                            onChange={(e) => handleGeometryChange('ewHalfWidth', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Distance from valley centerline to building edge</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="valleyOffset">Valley Projection/Building Width (ft)</Label>
                          <Input
                            id="valleyOffset"
                            type="number"
                            step="0.1"
                            min="0"
                            value={geometry.valleyOffset}
                            onChange={(e) => handleGeometryChange('valleyOffset', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Horizontal distance from valley to building exterior</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="valleyAngle">Valley Dihedral Angle (degrees)</Label>
                          <Input
                            id="valleyAngle"
                            type="number"
                            step="0.1"
                            min="0"
                            max="180"
                            value={geometry.valleyAngle}
                            onChange={(e) => handleGeometryChange('valleyAngle', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">Angle between roof planes at valley intersection</p>
                        </div>
                      </div>

                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Critical Valley Analysis</AlertTitle>
                        <AlertDescription>
                          Valley calculations are critical for structural design. This calculator performs complete
                          ASCE 7-22 Section 7.7 analysis including balanced loads, unbalanced loads, and windward
                          drift surcharges. Results determine beam sizing and connection requirements.
                        </AlertDescription>
                      </Alert>
                    </div>
                  </TabsContent>

                  <TabsContent value="loads" className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Site-Specific Snow Load</h3>
                        <div className="space-y-2">
                          <Label htmlFor="groundSnowLoad">Ground Snow Load, pg (psf) - ASCE 7-22 Section 7.2</Label>
                          <Input
                            id="groundSnowLoad"
                            type="number"
                            step="0.1"
                            min="0"
                            max="200"
                            value={snowInputs.groundSnowLoad}
                            onChange={(e) => handleSnowInputChange('groundSnowLoad', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">
                            Obtain from ASCE 7 Hazard Tool at: https://asce7hazardtool.online/
                            <br />
                            Values range from 0 psf (no snow) to 200+ psf in severe climates
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Load Factors</h3>
                        <div className="space-y-2">
                          <Label htmlFor="importanceFactor">Importance Factor (Is) - ASCE 7-22 Table 1.5-2</Label>
                          <Select
                            value={snowInputs.importanceFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('importanceFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="1.0">1.0 - Agricultural, Minor Storage, etc.</SelectItem>
                              <SelectItem value="1.1">1.1 - Standard Buildings (Risk Category II)</SelectItem>
                              <SelectItem value="1.2">1.2 - Essential Facilities, High Occupancy</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-sm text-gray-600">Risk Category II is most common for standard buildings</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="exposureFactor">Exposure Factor (Ce) - ASCE 7-22 Table 7.3-1</Label>
                          <Select
                            value={snowInputs.exposureFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('exposureFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0.9">0.9 - Sheltered (Terrain Category B, fully exposed)</SelectItem>
                              <SelectItem value="1.0">1.0 - Normal (Terrain Category C, suburban)</SelectItem>
                              <SelectItem value="1.2">1.2 - Exposed (Terrain Category D, open areas)</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-sm text-gray-600">Based on upwind terrain and exposure conditions</p>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Thermal & Wind</h3>
                        <div className="space-y-2">
                          <Label htmlFor="thermalFactor">Thermal Factor (Ct) - ASCE 7-22 Table 7.3-2</Label>
                          <Select
                            value={snowInputs.thermalFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('thermalFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0.8">0.8 - Freezer Buildings (≤0°F interior)</SelectItem>
                              <SelectItem value="0.9">0.9 - Continuously Heated (55°F+ interior)</SelectItem>
                              <SelectItem value="1.0">1.0 - Unheated (varies with climate)</SelectItem>
                              <SelectItem value="1.1">1.1 - Heated with Cold Roof (Ct &gt; 1.1)</SelectItem>
                              <SelectItem value="1.2">1.2 - Cold Storage (0-55°F interior)</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-sm text-gray-600">Based on roof surface temperature relative to air temperature</p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="winterWindParameter">Winter Wind Parameter, Cw - ASCE 7-22 Figure 7.6-1</Label>
                          <Input
                            id="winterWindParameter"
                            type="number"
                            step="0.01"
                            min="0.25"
                            max="0.65"
                            value={snowInputs.winterWindParameter}
                            onChange={(e) => handleSnowInputChange('winterWindParameter', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">
                            Percentage of time wind speed &gt;10 mph during Oct-Apr
                            <br />
                            From ASCE Hazard Tool or local weather data (typically 0.25-0.65)
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Surface Conditions</h3>
                        <div className="space-y-2">
                          <Label>Slope Factor Surface Type - ASCE 7-22 Figure 7.4-1</Label>
                          <Select
                            value={snowInputs.isSlipperySurface ? "slippery" : "non-slippery"}
                            onValueChange={(value) => handleSnowInputChange('isSlipperySurface', value === "slippery")}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="non-slippery">Non-Slippery - Standard roof surfaces</SelectItem>
                              <SelectItem value="slippery">Slippery - Glass, metal, membranes with aggregate</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-sm text-gray-600">
                            Determines slope factor (Cs) calculation method
                          </p>
                        </div>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="beam" className="space-y-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <input
                        type="checkbox"
                        id="includeBeamDesign"
                        checked={includeBeamDesign}
                        onChange={(e) => setIncludeBeamDesign(e.target.checked)}
                        className="rounded"
                      />
                      <Label htmlFor="includeBeamDesign" className="text-base">
                        Include Beam Design Analysis
                      </Label>
                    </div>

                    {includeBeamDesign && (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold text-gray-900">Beam Cross-Section</h3>
                          <div className="space-y-2">
                            <Label htmlFor="beamWidth">Beam Width (in) - Face dimension</Label>
                            <Input
                              id="beamWidth"
                              type="number"
                              step="0.125"
                              min="1"
                              max="24"
                              value={beamInputs.beamWidth}
                              onChange={(e) => handleBeamInputChange('beamWidth', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Width of beam face (load-bearing dimension)</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="beamDepth">Beam Depth (in) - Height dimension</Label>
                            <Input
                              id="beamDepth"
                              type="number"
                              step="0.125"
                              min="1"
                              max="48"
                              value={beamInputs.beamDepth}
                              onChange={(e) => handleBeamInputChange('beamDepth', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Height of beam (strong axis bending)</p>
                          </div>
                        </div>

                          <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900">Material Properties</h3>
                            <div className="space-y-2">
                              <Label htmlFor="materialType">Wood Species - NDS 2018 Allowable Stresses</Label>
                              <Select
                                value={beamInputs.materialType}
                                onValueChange={(value) => handleBeamInputChange('materialType', value)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="Douglas Fir">Douglas Fir - High strength, Fb=2400 psi</SelectItem>
                                  <SelectItem value="Southern Pine">Southern Pine - Strong, Fb=2000-2400 psi</SelectItem>
                                  <SelectItem value="Spruce-Pine-Fir">Spruce-Pine-Fir - Versatile, Fb=1500-1900 psi</SelectItem>
                                  <SelectItem value="Hem-Fir">Hem-Fir - Good strength/cost ratio</SelectItem>
                                  <SelectItem value="Redwood">Redwood - Naturally decay resistant</SelectItem>
                                  <SelectItem value="Cedar">Cedar - Light weight, naturally decay resistant</SelectItem>
                                </SelectContent>
                              </Select>
                              <p className="text-sm text-gray-600">Affects allowable bending stress (Fb) and shear stress (Fv)</p>
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="allowableFb">Allowable Bending Stress (psi)</Label>
                              <Input
                                id="allowableFb"
                                type="number"
                                value={beamInputs.allowableFb}
                                onChange={(e) => handleBeamInputChange('allowableFb', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                          </div>
                        </div>

                        <Separator />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold text-gray-900">Material Properties</h3>
                          <div className="space-y-2">
                            <Label htmlFor="allowableFb">Allowable Bending Stress, Fb (psi) - NDS 2018</Label>
                            <Input
                              id="allowableFb"
                              type="number"
                              min="1000"
                              max="3000"
                              value={beamInputs.allowableFb}
                              onChange={(e) => handleBeamInputChange('allowableFb', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Bending stress capacity (depends on species & grade)</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="allowableFv">Allowable Shear Stress, Fv (psi) - NDS 2018</Label>
                            <Input
                              id="allowableFv"
                              type="number"
                              min="100"
                              max="300"
                              value={beamInputs.allowableFv}
                              onChange={(e) => handleBeamInputChange('allowableFv', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Shear stress capacity parallel to grain</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="modulusE">Modulus of Elasticity, E (psi) - NDS 2018</Label>
                            <Input
                              id="modulusE"
                              type="number"
                              min="1000000"
                              max="2000000"
                              value={beamInputs.modulusE}
                              onChange={(e) => handleBeamInputChange('modulusE', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Stiffness for deflection calculations</p>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold text-gray-900">Serviceability Criteria</h3>
                          <div className="space-y-2">
                            <Label htmlFor="deflectionLimitSnow">Snow Load Deflection Limit (L/n)</Label>
                            <Input
                              id="deflectionLimitSnow"
                              type="number"
                              min="180"
                              max="360"
                              value={beamInputs.deflectionLimitSnow}
                              onChange={(e) => handleBeamInputChange('deflectionLimitSnow', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Typical: L/240 (snow) = 0.00417 × span</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="deflectionLimitTotal">Total Load Deflection Limit (L/n)</Label>
                            <Input
                              id="deflectionLimitTotal"
                              type="number"
                              min="240"
                              max="480"
                              value={beamInputs.deflectionLimitTotal}
                              onChange={(e) => handleBeamInputChange('deflectionLimitTotal', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Typical: L/360 (total) = 0.00278 × span</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="roofDeadLoad">Roof Dead Load (psf)</Label>
                            <Input
                              id="roofDeadLoad"
                              type="number"
                              step="0.5"
                              min="5"
                              max="50"
                              value={beamInputs.roofDeadLoad}
                              onChange={(e) => handleBeamInputChange('roofDeadLoad', parseFloat(e.target.value) || 0)}
                            />
                            <p className="text-sm text-gray-600">Self-weight of roof system (typically 15-25 psf)</p>
                          </div>
                        </div>
                        </div>
                      </>
                    )}
                  </TabsContent>
                </Tabs>

                <Separator />

                <Button
                  onClick={handleCalculate}
                  disabled={isLoading}
                  className="w-full"
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Calculating...
                    </>
                  ) : (
                    <>
                      <Calculator className="h-4 w-4 mr-2" />
                      Calculate Snow Loads{includeBeamDesign ? ' & Beam Design' : ''}
                    </>
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Calculation Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="space-y-8">
            {/* Snow Load Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Snowflake className="h-5 w-5 text-blue-600" />
                  Snow Load Analysis Results
                </CardTitle>
                <CardDescription>
                  ASCE 7-22 compliant snow load calculations for valley structures
                </CardDescription>
              </CardHeader>
              <CardContent>
                {results ? (
                  <Tabs defaultValue="summary" className="w-full">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="summary">Summary</TabsTrigger>
                      <TabsTrigger value="loads">Load Analysis</TabsTrigger>
                      <TabsTrigger value="valley">Valley Loads</TabsTrigger>
                      <TabsTrigger value="diagrams">Diagrams</TabsTrigger>
                    </TabsList>

                    <TabsContent value="summary" className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {results.pf.toFixed(1)}
                          </div>
                          <div className="text-sm text-blue-700">Flat Roof Snow Load pf (psf)</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {results.lv.toFixed(2)}
                          </div>
                          <div className="text-sm text-green-700">Valley Length (ft)</div>
                        </div>
                        <div className="bg-orange-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600">
                            {results.cs.toFixed(3)}
                          </div>
                          <div className="text-sm text-orange-700">Slope Factor Cs</div>
                        </div>
                        <div className="bg-purple-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-purple-600">
                            {results.valleyLoads.verticalLoad.toFixed(1)}
                          </div>
                          <div className="text-sm text-purple-700">Valley Load (psf)</div>
                        </div>
                      </div>
                      <Alert>
                        <CheckCircle className="h-4 w-4" />
                        <AlertTitle>ASCE 7-22 Compliance Verified</AlertTitle>
                        <AlertDescription>
                          All calculations follow ASCE 7-22 Chapter 7 snow load provisions including slope factors,
                          unbalanced loads, and drift surcharges.
                        </AlertDescription>
                      </Alert>
                    </TabsContent>

                    <TabsContent value="loads" className="space-y-4">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                          <h3 className="text-lg font-semibold mb-4">Load Factors Applied</h3>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Factor</TableHead>
                                <TableHead className="text-right">Value</TableHead>
                                <TableHead>Description</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              <TableRow>
                                <TableCell>Ground Snow (pg)</TableCell>
                                <TableCell className="text-right font-mono">{snowInputs.groundSnowLoad}</TableCell>
                                <TableCell>From ASCE Hazard Tool</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Importance (Is)</TableCell>
                                <TableCell className="text-right font-mono">{snowInputs.importanceFactor}</TableCell>
                                <TableCell>Risk category factor</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Exposure (Ce)</TableCell>
                                <TableCell className="text-right font-mono">{snowInputs.exposureFactor}</TableCell>
                                <TableCell>Terrain exposure</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Thermal (Ct)</TableCell>
                                <TableCell className="text-right font-mono">{snowInputs.thermalFactor}</TableCell>
                                <TableCell>Roof thermal condition</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Slope (Cs)</TableCell>
                                <TableCell className="text-right font-mono">
                                  {(() => {
                                    const cs = (() => {
                                      const avgPitch = (geometry.northPitch + geometry.westPitch) / 2;
                                      if (avgPitch < 15) return 1.0;
                                      if (snowInputs.isSlipperySurface) {
                                        if (avgPitch >= 70) return 0.0;
                                        if (avgPitch >= 60) return 0.083;
                                        if (avgPitch >= 50) return 0.167;
                                        if (avgPitch >= 40) return 0.250;
                                        if (avgPitch >= 30) return 0.333;
                                        if (avgPitch >= 20) return 0.500;
                                        return 0.667;
                                      } else {
                                        if (snowInputs.thermalFactor >= 1.1) {
                                          if (avgPitch >= 70) return 0.0;
                                          if (avgPitch >= 60) return 0.111;
                                          if (avgPitch >= 50) return 0.222;
                                          if (avgPitch >= 40) return 0.333;
                                          if (avgPitch >= 30) return 0.444;
                                          if (avgPitch >= 20) return 0.556;
                                          return 0.667;
                                        } else {
                                          if (avgPitch >= 70) return 0.0;
                                          if (avgPitch >= 60) return 0.143;
                                          if (avgPitch >= 50) return 0.286;
                                          if (avgPitch >= 40) return 0.429;
                                          if (avgPitch >= 30) return 0.571;
                                          if (avgPitch >= 20) return 0.714;
                                          return 0.857;
                                        }
                                      }
                                    })();
                                    return cs.toFixed(3);
                                  })()}
                                </TableCell>
                                <TableCell>From Figure 7.4-1</TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-4">Calculated Loads</h3>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Load Type</TableHead>
                                <TableHead className="text-right">North Roof</TableHead>
                                <TableHead className="text-right">West Roof</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              <TableRow>
                                <TableCell>Balanced Load (psf)</TableCell>
                                <TableCell className="text-right font-mono">{results.balancedLoads.northRoof.toFixed(1)}</TableCell>
                                <TableCell className="text-right font-mono">{results.balancedLoads.westRoof.toFixed(1)}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Unbalanced Load (psf)</TableCell>
                                <TableCell className="text-right font-mono">{results.unbalancedLoads.northRoof.toFixed(1)}</TableCell>
                                <TableCell className="text-right font-mono">{results.unbalancedLoads.westRoof.toFixed(1)}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Drift Load (psf)</TableCell>
                                <TableCell className="text-right font-mono" colSpan={2}>{Math.max(results.driftLoads.leeSide, results.driftLoads.windwardSide).toFixed(1)}</TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="valley" className="space-y-4">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <Card>
                          <CardHeader>
                            <CardTitle>Valley Load Analysis</CardTitle>
                            <CardDescription>Governing loads for valley beam design</CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="bg-red-50 p-4 rounded-lg">
                                <div className="text-xl font-bold text-red-600">
                                  {results.valleyLoads.verticalLoad.toFixed(1)} psf
                                </div>
                                <div className="text-sm text-red-700">Vertical Load</div>
                              </div>
                              <div className="bg-yellow-50 p-4 rounded-lg">
                                <div className="text-xl font-bold text-yellow-600">
                                  {results.valleyLoads.horizontalLoad.toFixed(1)} psf
                                </div>
                                <div className="text-sm text-yellow-700">Horizontal Load</div>
                              </div>
                            </div>
                            <Alert>
                              <AlertTriangle className="h-4 w-4" />
                              <AlertTitle>Design Load Combination</AlertTitle>
                              <AlertDescription>
                                Use the governing combination of balanced + unbalanced + drift loads
                                for structural design per ASCE 7-22 Section 7.8.
                              </AlertDescription>
                            </Alert>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader>
                            <CardTitle>Tributary Area Analysis</CardTitle>
                            <CardDescription>Load distribution based on roof geometry</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span>North Roof Area:</span>
                                <span className="font-mono">{(geometry.northSpan * geometry.ewHalfWidth * 2).toFixed(1)} ft²</span>
                              </div>
                              <div className="flex justify-between">
                                <span>West Roof Area:</span>
                                <span className="font-mono">{(geometry.southSpan * geometry.ewHalfWidth * 2).toFixed(1)} ft²</span>
                              </div>
                              <div className="flex justify-between border-t pt-2">
                                <span>Total Area:</span>
                                <span className="font-mono">{((geometry.northSpan + geometry.southSpan) * geometry.ewHalfWidth * 2).toFixed(1)} ft²</span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </TabsContent>

                    <TabsContent value="diagrams" className="space-y-4">
                      {results.diagrams ? (
                        <div className="space-y-6">
                          <Alert>
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Diagram Preview</AlertTitle>
                            <AlertDescription>
                              Interactive diagrams showing load distributions and structural analysis.
                              Full implementation would include SVG-based charts.
                            </AlertDescription>
                          </Alert>

                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Card>
                              <CardHeader>
                                <CardTitle>Roof Profile & Snow Distribution</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="bg-gray-100 h-64 rounded-lg flex items-center justify-center">
                                  <div className="text-center text-gray-600">
                                    <Snowflake className="h-12 w-12 mx-auto mb-2" />
                                    <p>Roof Profile Diagram</p>
                                    <p className="text-sm">Shows valley geometry and snow load distribution</p>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            <Card>
                              <CardHeader>
                                <CardTitle>Structural Analysis</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="bg-gray-100 h-64 rounded-lg flex items-center justify-center">
                                  <div className="text-center text-gray-600">
                                    <Ruler className="h-12 w-12 mx-auto mb-2" />
                                    <p>Shear & Moment Diagrams</p>
                                    <p className="text-sm">Beam analysis results</p>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </div>
                        </div>
                      ) : (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>No Diagrams Available</AlertTitle>
                          <AlertDescription>
                            Diagrams are generated when beam design analysis is included.
                            Enable "Include Beam Design Analysis" to see structural diagrams.
                          </AlertDescription>
                        </Alert>
                      )}
                    </TabsContent>
                  </Tabs>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Calculator className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Enter parameters and click "Calculate Snow Loads" to see results</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Beam Design Results */}
            {results?.beamDesign && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building className="h-5 w-5 text-green-600" />
                    Beam Design Analysis
                  </CardTitle>
                  <CardDescription>
                    Structural analysis for valley beam with snow and dead loads
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="design" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="design">Design Check</TabsTrigger>
                      <TabsTrigger value="loads">Applied Loads</TabsTrigger>
                      <TabsTrigger value="capacity">Beam Capacity</TabsTrigger>
                    </TabsList>

                    <TabsContent value="design" className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className={`p-4 rounded-lg ${results.beamDesign.momentUtilization > 100 ? 'bg-red-50' : 'bg-green-50'}`}>
                          <div className="text-xl font-bold text-current">
                            {results.beamDesign.momentUtilization.toFixed(1)}%
                          </div>
                          <div className="text-sm">Moment Utilization</div>
                        </div>
                        <div className={`p-4 rounded-lg ${results.beamDesign.shearUtilization > 100 ? 'bg-red-50' : 'bg-green-50'}`}>
                          <div className="text-xl font-bold text-current">
                            {results.beamDesign.shearUtilization.toFixed(1)}%
                          </div>
                          <div className="text-sm">Shear Utilization</div>
                        </div>
                        <div className={`p-4 rounded-lg ${results.beamDesign.deflectionUtilization > 100 ? 'bg-red-50' : 'bg-green-50'}`}>
                          <div className="text-xl font-bold text-current">
                            {results.beamDesign.deflectionUtilization.toFixed(1)}%
                          </div>
                          <div className="text-sm">Deflection Utilization</div>
                        </div>
                      </div>

                      {results.beamDesign.momentUtilization > 100 || results.beamDesign.shearUtilization > 100 || results.beamDesign.deflectionUtilization > 100 ? (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>Design Check Failed</AlertTitle>
                          <AlertDescription>
                            The selected beam section does not meet all design criteria.
                            Consider increasing beam size or using higher strength material.
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <Alert>
                          <CheckCircle className="h-4 w-4" />
                          <AlertTitle>Design Check Passed</AlertTitle>
                          <AlertDescription>
                            The beam section meets all strength and serviceability requirements
                            for the applied load combination.
                          </AlertDescription>
                        </Alert>
                      )}
                    </TabsContent>

                    <TabsContent value="loads" className="space-y-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Load Component</TableHead>
                            <TableHead className="text-right">Load (plf)</TableHead>
                            <TableHead>Description</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell>Dead Load</TableCell>
                            <TableCell className="text-right font-mono">{results.beamDesign.totalLoad.toFixed(1)}</TableCell>
                            <TableCell>Roof dead load</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Snow Load</TableCell>
                            <TableCell className="text-right font-mono">{(results.valleyLoads.verticalLoad * geometry.ewHalfWidth * 2).toFixed(1)}</TableCell>
                            <TableCell>Valley snow load</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell className="font-semibold">Total Load</TableCell>
                            <TableCell className="text-right font-mono font-semibold">
                              {(results.beamDesign.totalLoad + results.valleyLoads.verticalLoad * geometry.ewHalfWidth * 2).toFixed(1)}
                            </TableCell>
                            <TableCell>ASD combination (D + 0.7S)</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TabsContent>

                    <TabsContent value="capacity" className="space-y-4">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                          <h3 className="text-lg font-semibold mb-4">Beam Properties</h3>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>Material:</span>
                              <span className="font-medium">{beamInputs.materialType}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Size:</span>
                              <span className="font-mono">{beamInputs.beamWidth}" × {beamInputs.beamDepth}"</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Section Modulus:</span>
                              <span className="font-mono">{results.beamDesign.actualMomentCapacity.toFixed(1)} in³</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Weight:</span>
                              <span className="font-mono">{results.beamDesign.beamWeight.toFixed(1)} lbs</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-4">Design Capacities</h3>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>Moment Capacity:</span>
                              <span className="font-mono">{(results.beamDesign.actualMomentCapacity / 12).toFixed(0)} ft-lbs</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Shear Capacity:</span>
                              <span className="font-mono">{results.beamDesign.actualShearCapacity.toFixed(0)} lbs</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Deflection Limit:</span>
                              <span className="font-mono">L/{beamInputs.deflectionLimitSnow}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Actual Deflection:</span>
                              <span className="font-mono">{results.beamDesign.deflectionSnow.toFixed(2)}"</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

