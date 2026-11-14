export type MaterialType = 'PMMA' | 'SIBAL' | 'Nomex' | 'Delrin' | 'Silicone';
export type FlowDirectionType = 'concurrent' | 'opposed';
export type FireRiskLevel = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW' | 'EXTINCT';

export interface PhysicalScenario {
  material: MaterialType;
  oxygenFraction: number;      // 18% - 40%
  pressureKpa: number;         // 40 kPa - 105 kPa
  flowVelocity: number;        // 0 cm/s - 35 cm/s
  flowDirection: FlowDirectionType;
  suppressant: string;
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

export interface SensorTelemetry {
  thermocoupleTempC: number;
  radiometerFluxKwM2: number;
  coPpm: number;
  co2Percent: number;
  flameSpreadVelocityCmS: number;
  flameExtinctionProb: number;
}
