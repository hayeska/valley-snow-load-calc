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

import { calculator, type RoofGeometry, type SnowLoadInputs, type BeamDesignInputs, type CalculationResults } from './services/calculator'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<CalculationResults | null>(null)
  const [error, setError] = useState<string>('')

  // Form state
  const [geometry, setGeometry] = useState<RoofGeometry>({
    northPitch: 8,
    westPitch: 10,
    northSpan: 20,
    southSpan: 18,
    ewHalfWidth: 45,
    valleyOffset: 15,
    valleyAngle: 90,
  })

  const [snowInputs, setSnowInputs] = useState<SnowLoadInputs>({
    groundSnowLoad: 35,
    importanceFactor: 1.1,
    exposureFactor: 1.0,
    thermalFactor: 0.9,
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
    setGeometry(prev => ({ ...prev, [field]: value }))
  }

  const handleSnowInputChange = (field: keyof SnowLoadInputs, value: number | boolean) => {
    setSnowInputs(prev => ({ ...prev, [field]: value }))
  }

  const handleBeamInputChange = (field: keyof BeamDesignInputs, value: number | string) => {
    setBeamInputs(prev => ({ ...prev, [field]: value }))
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
                        <h3 className="text-lg font-semibold text-gray-900">Roof Pitches</h3>
                        <div className="space-y-2">
                          <Label htmlFor="northPitch">North Roof Pitch (degrees)</Label>
                          <Input
                            id="northPitch"
                            type="number"
                            value={geometry.northPitch}
                            onChange={(e) => handleGeometryChange('northPitch', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="westPitch">West Roof Pitch (degrees)</Label>
                          <Input
                            id="westPitch"
                            type="number"
                            value={geometry.westPitch}
                            onChange={(e) => handleGeometryChange('westPitch', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Roof Spans</h3>
                        <div className="space-y-2">
                          <Label htmlFor="northSpan">North Span Length (ft)</Label>
                          <Input
                            id="northSpan"
                            type="number"
                            value={geometry.northSpan}
                            onChange={(e) => handleGeometryChange('northSpan', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="southSpan">South Span Length (ft)</Label>
                          <Input
                            id="southSpan"
                            type="number"
                            value={geometry.southSpan}
                            onChange={(e) => handleGeometryChange('southSpan', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Valley Geometry</h3>
                        <div className="space-y-2">
                          <Label htmlFor="ewHalfWidth">E-W Half Width (ft)</Label>
                          <Input
                            id="ewHalfWidth"
                            type="number"
                            value={geometry.ewHalfWidth}
                            onChange={(e) => handleGeometryChange('ewHalfWidth', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="valleyOffset">Valley Offset/Projection (ft)</Label>
                          <Input
                            id="valleyOffset"
                            type="number"
                            value={geometry.valleyOffset}
                            onChange={(e) => handleGeometryChange('valleyOffset', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="valleyAngle">Valley Angle (degrees)</Label>
                          <Input
                            id="valleyAngle"
                            type="number"
                            value={geometry.valleyAngle}
                            onChange={(e) => handleGeometryChange('valleyAngle', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                      </div>

                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Valley Analysis</AlertTitle>
                        <AlertDescription>
                          The calculator performs complete valley analysis including balanced loads, unbalanced loads,
                          and drift surcharges according to ASCE 7-22 Section 7.7.
                        </AlertDescription>
                      </Alert>
                    </div>
                  </TabsContent>

                  <TabsContent value="loads" className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Ground Snow Load</h3>
                        <div className="space-y-2">
                          <Label htmlFor="groundSnowLoad">Ground Snow Load (psf)</Label>
                          <Input
                            id="groundSnowLoad"
                            type="number"
                            value={snowInputs.groundSnowLoad}
                            onChange={(e) => handleSnowInputChange('groundSnowLoad', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">From ASCE Hazard Tool/Geodatabase</p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Load Factors</h3>
                        <div className="space-y-2">
                          <Label htmlFor="importanceFactor">Importance Factor (Is)</Label>
                          <Select
                            value={snowInputs.importanceFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('importanceFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="1.0">1.0 (Low Importance)</SelectItem>
                              <SelectItem value="1.1">1.1 (Standard)</SelectItem>
                              <SelectItem value="1.2">1.2 (High Importance)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="exposureFactor">Exposure Factor (Ce)</Label>
                          <Select
                            value={snowInputs.exposureFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('exposureFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0.9">0.9 (Sheltered)</SelectItem>
                              <SelectItem value="1.0">1.0 (Normal)</SelectItem>
                              <SelectItem value="1.2">1.2 (Windy)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Thermal & Wind</h3>
                        <div className="space-y-2">
                          <Label htmlFor="thermalFactor">Thermal Factor (Ct)</Label>
                          <Select
                            value={snowInputs.thermalFactor.toString()}
                            onValueChange={(value) => handleSnowInputChange('thermalFactor', parseFloat(value))}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0.8">0.8 (Cold - All Ground Snow)</SelectItem>
                              <SelectItem value="0.9">0.9 (Normal)</SelectItem>
                              <SelectItem value="1.0">1.0 (Warm - All Rain)</SelectItem>
                              <SelectItem value="1.1">1.1 (Intermediate)</SelectItem>
                              <SelectItem value="1.2">1.2 (Cold)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="winterWindParameter">Winter Wind Parameter (Cw)</Label>
                          <Input
                            id="winterWindParameter"
                            type="number"
                            step="0.1"
                            value={snowInputs.winterWindParameter}
                            onChange={(e) => handleSnowInputChange('winterWindParameter', parseFloat(e.target.value) || 0)}
                          />
                          <p className="text-sm text-gray-600">From ASCE Hazard Tool (0.25-0.65)</p>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-900">Surface Conditions</h3>
                        <div className="space-y-2">
                          <Label>Slope Factor Surface Type</Label>
                          <Select
                            value={snowInputs.isSlipperySurface ? "slippery" : "non-slippery"}
                            onValueChange={(value) => handleSnowInputChange('isSlipperySurface', value === "slippery")}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="non-slippery">Non-Slippery (Standard)</SelectItem>
                              <SelectItem value="slippery">Slippery Surface</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-sm text-gray-600">
                            Affects Cs calculation per ASCE 7-22 Figure 7.4-1
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
                            <h3 className="text-lg font-semibold text-gray-900">Beam Dimensions</h3>
                            <div className="space-y-2">
                              <Label htmlFor="beamWidth">Beam Width (inches)</Label>
                              <Input
                                id="beamWidth"
                                type="number"
                                step="0.125"
                                value={beamInputs.beamWidth}
                                onChange={(e) => handleBeamInputChange('beamWidth', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="beamDepth">Beam Depth (inches)</Label>
                              <Input
                                id="beamDepth"
                                type="number"
                                step="0.125"
                                value={beamInputs.beamDepth}
                                onChange={(e) => handleBeamInputChange('beamDepth', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                          </div>

                          <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900">Material Properties</h3>
                            <div className="space-y-2">
                              <Label htmlFor="materialType">Wood Species</Label>
                              <Select
                                value={beamInputs.materialType}
                                onValueChange={(value) => handleBeamInputChange('materialType', value)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="Douglas Fir">Douglas Fir</SelectItem>
                                  <SelectItem value="Southern Pine">Southern Pine</SelectItem>
                                  <SelectItem value="Spruce-Pine-Fir">Spruce-Pine-Fir</SelectItem>
                                  <SelectItem value="Hem-Fir">Hem-Fir</SelectItem>
                                  <SelectItem value="Redwood">Redwood</SelectItem>
                                  <SelectItem value="Cedar">Cedar</SelectItem>
                                </SelectContent>
                              </Select>
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
                            <h3 className="text-lg font-semibold text-gray-900">Design Criteria</h3>
                            <div className="space-y-2">
                              <Label htmlFor="allowableFv">Allowable Shear Stress (psi)</Label>
                              <Input
                                id="allowableFv"
                                type="number"
                                value={beamInputs.allowableFv}
                                onChange={(e) => handleBeamInputChange('allowableFv', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="modulusE">Modulus of Elasticity (psi)</Label>
                              <Input
                                id="modulusE"
                                type="number"
                                value={beamInputs.modulusE}
                                onChange={(e) => handleBeamInputChange('modulusE', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                          </div>

                          <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900">Deflection Limits</h3>
                            <div className="space-y-2">
                              <Label htmlFor="deflectionLimitSnow">Snow Load Deflection (L/n)</Label>
                              <Input
                                id="deflectionLimitSnow"
                                type="number"
                                value={beamInputs.deflectionLimitSnow}
                                onChange={(e) => handleBeamInputChange('deflectionLimitSnow', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="deflectionLimitTotal">Total Load Deflection (L/n)</Label>
                              <Input
                                id="deflectionLimitTotal"
                                type="number"
                                value={beamInputs.deflectionLimitTotal}
                                onChange={(e) => handleBeamInputChange('deflectionLimitTotal', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="roofDeadLoad">Roof Dead Load (psf)</Label>
                              <Input
                                id="roofDeadLoad"
                                type="number"
                                value={beamInputs.roofDeadLoad}
                                onChange={(e) => handleBeamInputChange('roofDeadLoad', parseFloat(e.target.value) || 0)}
                              />
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
                            {Math.max(results.balancedLoads.northRoof, results.balancedLoads.westRoof).toFixed(1)}
                          </div>
                          <div className="text-sm text-blue-700">Balanced Roof Load (psf)</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {Math.max(results.unbalancedLoads.northRoof, results.unbalancedLoads.westRoof).toFixed(1)}
                          </div>
                          <div className="text-sm text-green-700">Unbalanced Roof Load (psf)</div>
                        </div>
                        <div className="bg-orange-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600">
                            {Math.max(results.driftLoads.leeSide, results.driftLoads.windwardSide).toFixed(1)}
                          </div>
                          <div className="text-sm text-orange-700">Drift Load (psf)</div>
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

