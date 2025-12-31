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
import { Calculator, Snowflake, AlertTriangle, CheckCircle } from 'lucide-react'

import { calculator, type RoofGeometry, type CalculationInputs, type CalculationResults } from './services/calculator'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<CalculationResults | null>(null)
  const [error, setError] = useState<string>('')

  // Form state
  const [geometry, setGeometry] = useState<RoofGeometry>({
    roofPitchN: 8,
    roofPitchW: 10,
    northSpan: 20,
    southSpan: 18,
    ewHalfWidth: 45,
    valleyOffset: 15,
    valleyAngle: 90,
  })

  const [inputs, setInputs] = useState<CalculationInputs>({
    groundSnowLoad: 35,
    importanceFactor: 1.1,
    exposureFactor: 1.0,
    thermalFactor: 0.9,
    winterWindParameter: 0.4,
  })

  const handleCalculate = async () => {
    setIsLoading(true)
    setError('')
    try {
      const calculationResults = await calculator.performCalculations(geometry, inputs)
      setResults(calculationResults)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof RoofGeometry | keyof CalculationInputs, value: number) => {
    if (field in geometry) {
      setGeometry(prev => ({ ...prev, [field]: value }))
    } else {
      setInputs(prev => ({ ...prev, [field]: value }))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Snowflake className="h-10 w-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">Valley Snow Load Calculator</h1>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Professional engineering tool for calculating snow loads on valley structures according to ASCE 7-22 standards.
            Features real-time calculations, comprehensive results, and mobile-friendly design.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Parameters Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Input Parameters
              </CardTitle>
              <CardDescription>
                Enter roof geometry and snow load parameters for calculation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Tabs defaultValue="geometry" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="geometry">Roof Geometry</TabsTrigger>
                  <TabsTrigger value="loads">Snow Loads</TabsTrigger>
                </TabsList>

                <TabsContent value="geometry" className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="roofPitchN">North Roof Pitch (degrees)</Label>
                      <Input
                        id="roofPitchN"
                        type="number"
                        value={geometry.roofPitchN}
                        onChange={(e) => handleInputChange('roofPitchN', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="roofPitchW">West Roof Pitch (degrees)</Label>
                      <Input
                        id="roofPitchW"
                        type="number"
                        value={geometry.roofPitchW}
                        onChange={(e) => handleInputChange('roofPitchW', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="northSpan">North Span (ft)</Label>
                      <Input
                        id="northSpan"
                        type="number"
                        value={geometry.northSpan}
                        onChange={(e) => handleInputChange('northSpan', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="southSpan">South Span (ft)</Label>
                      <Input
                        id="southSpan"
                        type="number"
                        value={geometry.southSpan}
                        onChange={(e) => handleInputChange('southSpan', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="ewHalfWidth">E-W Half Width (ft)</Label>
                      <Input
                        id="ewHalfWidth"
                        type="number"
                        value={geometry.ewHalfWidth}
                        onChange={(e) => handleInputChange('ewHalfWidth', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="valleyOffset">Valley Offset (ft)</Label>
                      <Input
                        id="valleyOffset"
                        type="number"
                        value={geometry.valleyOffset}
                        onChange={(e) => handleInputChange('valleyOffset', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="loads" className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="groundSnowLoad">Ground Snow Load (psf)</Label>
                      <Input
                        id="groundSnowLoad"
                        type="number"
                        value={inputs.groundSnowLoad}
                        onChange={(e) => handleInputChange('groundSnowLoad', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="importanceFactor">Importance Factor</Label>
                      <Select value={inputs.importanceFactor.toString()} onValueChange={(value) => handleInputChange('importanceFactor', parseFloat(value))}>
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
                      <Label htmlFor="exposureFactor">Exposure Factor</Label>
                      <Select value={inputs.exposureFactor.toString()} onValueChange={(value) => handleInputChange('exposureFactor', parseFloat(value))}>
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
                    <div className="space-y-2">
                      <Label htmlFor="thermalFactor">Thermal Factor</Label>
                      <Select value={inputs.thermalFactor.toString()} onValueChange={(value) => handleInputChange('thermalFactor', parseFloat(value))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0.8">0.8 (Cold)</SelectItem>
                          <SelectItem value="0.9">0.9 (Normal)</SelectItem>
                          <SelectItem value="1.0">1.0 (Warm)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="winterWindParameter">Winter Wind Parameter</Label>
                      <Input
                        id="winterWindParameter"
                        type="number"
                        step="0.1"
                        value={inputs.winterWindParameter}
                        onChange={(e) => handleInputChange('winterWindParameter', parseFloat(e.target.value) || 0)}
                      />
                    </div>
                  </div>
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
                    Calculate Snow Loads
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

          {/* Results Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Calculation Results
              </CardTitle>
              <CardDescription>
                Snow load calculations and design values
              </CardDescription>
            </CardHeader>
            <CardContent>
              {results ? (
                <Tabs defaultValue="summary" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="summary">Summary</TabsTrigger>
                    <TabsTrigger value="loads">Load Details</TabsTrigger>
                    <TabsTrigger value="design">Design Values</TabsTrigger>
                  </TabsList>

                  <TabsContent value="summary" className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {results.summary.maxValleyLoad.toFixed(1)} psf
                        </div>
                        <div className="text-sm text-blue-700">Maximum Valley Load</div>
                      </div>
                      <div className="bg-green-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {results.loads.uniformLoad.toFixed(1)} psf
                        </div>
                        <div className="text-sm text-green-700">Uniform Roof Load</div>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="loads" className="space-y-4">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Load Component</TableHead>
                          <TableHead className="text-right">Value (psf)</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell>Uniform Roof Load</TableCell>
                          <TableCell className="text-right font-mono">{results.loads.uniformLoad.toFixed(1)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Drift Load</TableCell>
                          <TableCell className="text-right font-mono">{results.loads.driftLoad.toFixed(1)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-semibold">Total Load</TableCell>
                          <TableCell className="text-right font-mono font-semibold">{results.loads.totalLoad.toFixed(1)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>North Rafter Load</TableCell>
                          <TableCell className="text-right font-mono">{results.loads.northLoad.toFixed(1)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>West Rafter Load</TableCell>
                          <TableCell className="text-right font-mono">{results.loads.westLoad.toFixed(1)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TabsContent>

                  <TabsContent value="design" className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="bg-orange-50 p-4 rounded-lg">
                        <div className="text-lg font-bold text-orange-600">
                          {results.summary.unbalancedLoad.toFixed(1)} psf
                        </div>
                        <div className="text-sm text-orange-700">Unbalanced Load</div>
                      </div>
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <div className="text-lg font-bold text-purple-600">
                          {results.summary.balancedLoad.toFixed(1)} psf
                        </div>
                        <div className="text-sm text-purple-700">Balanced Load</div>
                      </div>
                    </div>
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle>Design Considerations</AlertTitle>
                      <AlertDescription>
                        Maximum valley load of {results.summary.maxValleyLoad.toFixed(1)} psf should be used for beam design.
                        Consider unbalanced loading conditions for structural analysis.
                      </AlertDescription>
                    </Alert>
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
        </div>
      </div>
    </div>
  )
}

export default App
