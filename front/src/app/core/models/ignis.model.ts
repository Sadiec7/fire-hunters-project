export type MaterialType = 'Etileno (C₂H₄)' | 'Metano (CH₄)' | 'PMMA' | 'SIBAL' | 'Nomex' | 'Delrin' | 'Silicone';
export type BurnerGeometryType = 'sflame-sphere' | 'solid-flat';
export type VisualLayerType = 'all' | 'flame' | 'temperature' | 'radiation' | 'soot';
export type FlowDirectionType = 'concurrent' | 'opposed';
export type FireRiskLevel = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW' | 'EXTINCT';
export type GravityMode = 'micro-quiescent' | 'micro-active' | 'micro-rcs' | 'earth-1g';
export type PressureDisplayMode = 'absolute' | 'gauge';
export type UnitsSystem = 'si' | 'imperial';

// Modos de Realidad Científica (Scientific Reality Mode)
export type ScientificRealityMode = 'simulation' | 'evidence' | 'inference';

// Modelos y Estados para Live Bayesian Inference
export type BayesianNetworkModel = 'BN-01' | 'BN-02' | 'BN-03';
export type MfcPatternState = 'solo-mfc3' | 'mfc2-mfc3-coupled' | 'preflow-low' | 'ramp-high' | 'unsupported';

export interface BayesianInferenceResult {
  variableName: string;
  stateName: string;
  modelId: BayesianNetworkModel;
  modelDescription: string;
  probPmt3High: number | null;
  probRadiometerHigh: number | null;
  probIgnition: number | null;
  isSupported: boolean;
  unsupportedReason?: string;
  provenance: string;
  inferenceType: string;
  cptNodesSample: { condition: string; pPmt3: number; pRad: number }[];
}

// Factual vs. Counterfactual Explorer
export type CounterfactualMode = 'observed' | 'hypothetical' | 'compare';
export type ScmModelVariant = 'M1' | 'M2' | 'M3';

export interface SensorChannelReading {
  channelId: string;
  name: string;
  unit: string;
  observedValue: number;
  hypotheticalValue: number;
  delta: number;
  deltaPct: number;
  calibrationVerified: boolean;
}

export interface CounterfactualComparisonData {
  expId: string;
  scmModel: ScmModelVariant;
  scmModelName: string;
  interventionDesc: string;
  mfc2Multiplier: number;
  mfc3Multiplier: number;
  channels: SensorChannelReading[];
  couplingLowerPct: number;
  couplingUpperPct: number;
  couplingEquationLatex: string;
  causalEffectIdentified: boolean;
  disclaimer: string;
}

// NASA Evidence Passport
export interface EvidencePassportData {
  id: string;
  title: string;
  investigation: string;
  experimentId: string;
  observedVar: string;
  sourceFile: string;
  sha256: string;
  transformation: string;
  modelUsed: string;
  limitations: string;
  psiUrl: string;
  epistemicTag: 'OBSERVED' | 'INFERRED' | 'UNVERIFIED';
}

// Clasificación de Jornadas (What NASA Should Test Next / LOJO)
export interface JornadaRankingItem {
  jornadaId: number;
  name: string;
  isMostInfluential: boolean;
  trialsCount: number;
  baselineRmse: number;
  withoutJornadaRmse: number;
  deltaRmseLojo: number;
  ateShiftPct: number;
  rationale: string;
  suggestedConditions: string;
}

// Ficha de Propuesta de Investigación (Generated Experiment Brief)
export interface ExperimentBrief {
  briefId: string;
  title: string;
  targetJornada: number;
  scientificHypothesis: string;
  proposedConditions: {
    flowVelocity: string;
    oxygenFraction: string;
    pressure: string;
    burnerGeometry: string;
    fuel: string;
  };
  targetSensors: string[];
  existingEvidencePsi: string;
  epistemicLimitations: string;
  systemDisclaimer: string;
  generatedDate: string;
}

// Mission Control 90s Guided Demo Step
export interface MissionControlStep {
  stepIndex: number;
  timeRange: string;
  title: string;
  instruction: string;
  mode: ScientificRealityMode;
  featureKey: string;
}

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
  nasaStd6001Status: 'COMPLIANCE NOT ASSESSED' | 'PASSED' | 'MARGINAL' | 'FAILED'; // Estado formal NASA-STD-6001 Test 1 (requiere cámara vertical de vuelo)
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
