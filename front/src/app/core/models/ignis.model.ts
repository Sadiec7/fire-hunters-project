export type MaterialType = 'Etileno (C₂H₄)' | 'Metano (CH₄)' | 'PMMA' | 'SIBAL' | 'Nomex' | 'Delrin' | 'Silicone';
export type BurnerGeometryType = 'sflame-sphere' | 'solid-flat';
export type VisualLayerType = 'all' | 'flame' | 'temperature' | 'radiation' | 'soot';
export type FlowDirectionType = 'concurrent' | 'opposed';
export type FireRiskLevel = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW' | 'EXTINCT';
export type GravityMode = 'micro-quiescent' | 'micro-active' | 'micro-rcs' | 'earth-1g';
export type PressureDisplayMode = 'absolute' | 'gauge';
export type UnitsSystem = 'si' | 'imperial';

export interface PhysicalScenario {
  material: MaterialType;
  burnerGeometry: BurnerGeometryType; // Quemador esférico poroso (s-Flame ACME) vs muestra plana
  oxygenFraction: number;      // 18% - 40% molar
  pressureKpa: number;         // 0 kPa (vacío) a 105 kPa (1 atm)
  flowVelocity: number;        // 0 cm/s - 35 cm/s
  flowDirection: FlowDirectionType;
  suppressant: string;
  gravityMode: GravityMode;    // Entorno de aceleración
  pressureMode: PressureDisplayMode; // Absoluta vs Manométrica Negativa
  unitsSystem: UnitsSystem;    // SI vs Imperial NASA
  isVentingToSpace: boolean;   // Protocolo de purga al vacío espacial exterior
}

export interface CausalChain {
  conditions: string;
  physicalMechanism: string;
  observations: string;
  outcome: string;
  risk: FireRiskLevel;
  confidence: number;
}

export interface EvidenceCard {
  id: string;
  title: string;
  risk: FireRiskLevel;
  confidence: number;
  causalChain: CausalChain;
  directEvidence: string;
  analogousEvidence: string;
  extrapolatedVars: string[];
  counterfactual: string;
  warning?: string;
  psiUrl: string;
  heatReleaseKw: number;
  coPpm: number;
  co2Fraction: number;
}

export interface KnowledgeTriadItem {
  id: string;
  category: 'KNOW' | 'INFER' | 'DONT_KNOW';
  title: string;
  description: string;
  source: string;
  badgeText: string;
  confidence?: number;
}

export interface Counterexample {
  id: string;
  experimentTitle: string;
  contradictoryOutcome: string;
  observedDifference: string;
  nasaSource: string;
  sourceUrl: string;
}

export interface ActiveLearningRecommendation {
  nextTestTitle: string;
  coordinates: {
    material: MaterialType;
    oxygenFraction: number;
    pressureKpa: number;
    flowVelocity: number;
    flowDirection: FlowDirectionType;
  };
  rationale: string;
  uncertaintyScore: number;
  expectedEntropyReduction: string;
}

export interface TelemetryPoint {
  timeSec: number;
  temperatureC: number;
  coPpm: number;
  radiometerKwM2: number;
}

export interface SensorTelemetry {
  thermocoupleTempC: number;
  radiometerFluxKwM2: number;
  coPpm: number;
  co2Percent: number;
  flameSpreadVelocityCmS: number;
  flameExtinctionProb: number;
  // Parámetros aeroespaciales avanzados
  gaugePressureKpa: number;       // Presión manométrica (negativa respecto a 1 atm o cabina)
  pressurePsia: number;           // Presión en psia (estándar NASA)
  partialPressureO2Kpa: number;   // Presión parcial P_O2 = P * y_O2 (parámetro de inflamabilidad NASA-STD-6001)
  partialPressureO2Psia: number;  // P_O2 en psia
  reynoldsNumber: number;         // Re = u * L / nu (transporte laminar en microgravedad)
  damkohlerNumber: number;        // Da = tau_flow / tau_chem (régimen de combustión vs apagado)
  nasaStd6001Status: 'PASSED' | 'MARGINAL' | 'FAILED'; // Criterio de inflamabilidad NASA-STD-6001 Test 1
  gravityG: number;               // Nivel de gravedad efectivo en g (1e-6 a 1.0)
  // Variables Físicas de s-Flame (NASA ACME)
  flameRadiusMm: number;          // Radio de llama esférica r_f (mm) según difusión-convección
  burnerRadiusMm: number;         // Radio del quemador poroso esférico r_s = 6.35 mm
  maxFlameTempK: number;          // Temperatura pico de llama en Kelvin (Sección 9.2)
  heatReleaseChemKw: number;      // Tasa de liberación de calor exotérmico q_chem (kW) (Sección 9.3)
  radiativeLossKw: number;        // Pérdida volumétrica radiativa q_rad (kW) (Sección 9.4)
  netThermalBalanceKw: number;    // Balance térmico neto q_net = q_chem - q_rad (Sección 9.5)
  history: TelemetryPoint[];      // Registro temporal para telemetría interactiva en vivo
}
