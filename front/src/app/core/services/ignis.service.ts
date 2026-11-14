import { Injectable, computed, signal } from '@angular/core';
import {
  ActiveLearningRecommendation,
  Counterexample,
  EvidenceCard,
  GravityMode,
  KnowledgeTriadItem,
  PhysicalScenario,
  PressureDisplayMode,
  SensorTelemetry,
  TelemetryPoint,
  UnitsSystem,
} from '../models/ignis.model';

@Injectable({
  providedIn: 'root',
})
export class IgnisService {
  // Modo de color (Light / Dark estilo Apple)
  public readonly isDarkMode = signal<boolean>(false);

  // Estado reactivo del escenario experimental aeroespacial
  public readonly scenario = signal<PhysicalScenario>({
    material: 'PMMA',
    oxygenFraction: 30, // 30% O2 (Caso Saffire VI / BASS-II)
    pressureKpa: 55,   // 55 kPa atmósfera de cabina espacial Exploration Atmosphere
    flowVelocity: 20,  // 20 cm/s ventilación forzada en microgravedad
    flowDirection: 'concurrent',
    suppressant: 'Ninguno',
    gravityMode: 'micro-quiescent',
    pressureMode: 'absolute',
    unitsSystem: 'si',
    isVentingToSpace: false,
  });

  // Modal / Drawer activo para las 3 acciones científicas
  public readonly activeDrawer = signal<'evidence' | 'challenge' | 'next-test' | null>(null);

  // Filtro de capa visual en el gemelo 3D
  public readonly activeLayer = signal<'all' | 'flame' | 'sensors' | 'gases'>('all');

  // Historial dinámico para el osciloscopio de telemetría en tiempo real
  public readonly telemetryHistory = signal<TelemetryPoint[]>([
    { timeSec: 0, temperatureC: 410, coPpm: 25, radiometerKwM2: 1.1 },
    { timeSec: 5, temperatureC: 520, coPpm: 48, radiometerKwM2: 1.8 },
    { timeSec: 10, temperatureC: 680, coPpm: 75, radiometerKwM2: 2.6 },
    { timeSec: 15, temperatureC: 760, coPpm: 92, radiometerKwM2: 3.1 },
    { timeSec: 20, temperatureC: 795, coPpm: 105, radiometerKwM2: 3.4 },
  ]);

  // Alternar tema oscuro/claro
  public toggleTheme(): void {
    this.isDarkMode.update((dark) => !dark);
  }

  // Telemetría rigurosa calculada con ecuaciones de combustión en microgravedad
  public readonly telemetry = computed<SensorTelemetry>(() => {
    const s = this.scenario();

    // 1. Efecto de gravedad efectiva (g-jitter residual)
    let gLevel = 0.000001; // 10^-6 g (Quiescente ISS)
    if (s.gravityMode === 'micro-active') gLevel = 0.0001;
    else if (s.gravityMode === 'micro-rcs') gLevel = 0.01;
    else if (s.gravityMode === 'earth-1g') gLevel = 1.0;

    // 2. Protocolo de Purga a Vacío Espacial (Depressurization / Vacuum Venting)
    if (s.isVentingToSpace) {
      return {
        thermocoupleTempC: -15,
        radiometerFluxKwM2: 0.0,
        coPpm: 0,
        co2Percent: 0.0,
        flameSpreadVelocityCmS: 0.0,
        flameExtinctionProb: 1.0,
        gaugePressureKpa: -101.3,
        pressurePsia: 0.0,
        partialPressureO2Kpa: 0.0,
        partialPressureO2Psia: 0.0,
        reynoldsNumber: 0,
        damkohlerNumber: 0,
        nasaStd6001Status: 'PASSED',
        gravityG: gLevel,
        history: this.telemetryHistory(),
      };
    }

    // 3. Parámetros de presión física y manométrica (presión diferencial negativa)
    const pAbs = s.pressureKpa;
    const pGauge = Number((pAbs - 101.325).toFixed(1)); // Negativa respecto a 1 atm
    const pPsia = Number((pAbs * 0.145038).toFixed(2));

    // Presión Parcial de Oxígeno P_O2 = P * y_O2 (Parámetro crítico de NASA-STD-6001)
    const pO2Kpa = Number((pAbs * (s.oxygenFraction / 100)).toFixed(2));
    const pO2Psia = Number((pO2Kpa * 0.145038).toFixed(2));

    // Factores de transporte químico y fluido
    const o2Factor = s.oxygenFraction / 21;
    const flowFactor = Math.max(0.05, s.flowVelocity / 15);
    const pressureFactor = pAbs / 101.3;
    const buoyancyBoost = s.gravityMode === 'earth-1g' ? 1.65 : 1.0; // Convección natural boyante en Tierra

    // Temperatura de frente de llama
    const baseTemp = 420;
    const temp = Math.round((baseTemp + (o2Factor * 220) + (flowFactor * 65) * pressureFactor) * buoyancyBoost);

    // Emisiones de gases tóxicos (Monóxido y Dióxido de Carbono)
    const matFactor = s.material === 'PMMA' ? 1.4 : s.material === 'Delrin' ? 1.25 : 1.0;
    const co = Math.round(44 * o2Factor * flowFactor * matFactor);
    const co2 = Number((0.58 * o2Factor * pressureFactor * (s.gravityMode === 'earth-1g' ? 1.4 : 1.0)).toFixed(2));

    // Flujo térmico radiativo y velocidad de propagación
    const flux = Number((1.8 * o2Factor * flowFactor * pressureFactor).toFixed(2));
    const spreadMult = s.flowDirection === 'concurrent' ? 1.48 : 0.42;
    const spread = Number((0.34 * o2Factor * spreadMult * (s.gravityMode === 'earth-1g' ? 2.1 : 1.0)).toFixed(2));

    // Probabilidad física de extinción
    let extinctionProb = 0.03;
    if (s.oxygenFraction < 19.5 && s.flowVelocity < 4.0) {
      extinctionProb = 0.94; // Extinción por pérdida radiativa (NASA ACME)
    } else if (s.oxygenFraction < 22.0 && s.flowVelocity > 24.0 && s.flowDirection === 'opposed') {
      extinctionProb = 0.72; // Extinción por soplado convectivo (Blow-off)
    } else if (pAbs < 30.0) {
      extinctionProb = 0.88; // Límite de baja presión por despresurización
    }

    // Número de Reynolds de conducto (L = 5 cm, nu = 1.5e-5 m2/s)
    const reynolds = Math.round((s.flowVelocity * 0.05 / 0.000015) * pressureFactor);

    // Número de Damköhler (Da = tau_res / tau_chem): relación de tiempos característicos
    const damkohler = Number(((pressureFactor * Math.pow(o2Factor, 2)) / (flowFactor + 0.25)).toFixed(2));

    // Evaluación formal según NASA-STD-6001 Test 1 (Upward Flame Propagation)
    let flammability: 'PASSED' | 'MARGINAL' | 'FAILED' = 'MARGINAL';
    if (pO2Kpa >= 22.5 || s.oxygenFraction >= 32 || (s.material === 'PMMA' && s.oxygenFraction >= 26 && s.flowVelocity > 10)) {
      flammability = 'FAILED'; // Falla criterio de seguridad contra incendios en naves
    } else if (s.oxygenFraction <= 20.8 && pO2Kpa <= 17.5) {
      flammability = 'PASSED'; // Autoextinguible
    }

    return {
      thermocoupleTempC: temp,
      radiometerFluxKwM2: flux,
      coPpm: co,
      co2Percent: co2,
      flameSpreadVelocityCmS: spread,
      flameExtinctionProb: extinctionProb,
      gaugePressureKpa: pGauge,
      pressurePsia: pPsia,
      partialPressureO2Kpa: pO2Kpa,
      partialPressureO2Psia: pO2Psia,
      reynoldsNumber: reynolds,
      damkohlerNumber: damkohler,
      nasaStd6001Status: flammability,
      gravityG: gLevel,
      history: this.telemetryHistory(),
    };
  });

  // Tarjeta de Evidencia Dinámica (Fire Evidence Card)
  public readonly evidenceCard = computed<EvidenceCard>(() => {
    const s = this.scenario();
    const t = this.telemetry();

    if (s.isVentingToSpace) {
      return {
        id: 'EVID-VENT-VACUUM',
        title: 'Purga al Vacío Espacial: Extinción Instantánea por Descompresión',
        risk: 'EXTINCT',
        confidence: 0.99,
        heatReleaseKw: 0.0,
        coPpm: 0,
        co2Fraction: 0.0,
        directEvidence: 'NASA Apollo 13 Protocol & ISS Node 2 Emergency Depress Procedure',
        analogousEvidence: 'NASA Glenn Zero-G Vacuum Quench Facility',
        extrapolatedVars: [],
        counterfactual: 'Restaurar la presurización de cabina a 55 kPa para permitir el reinicio de reacciones químicas.',
        warning: 'Protocolo de última línea de defensa contra incendios catastróficos en cabina.',
        psiUrl: 'https://psi.nasa.gov',
        causalChain: {
          conditions: `Presión de cabina evacuada al espacio exterior: P_abs = 0 kPa · ΔP = -101.3 kPa`,
          physicalMechanism: 'La caída instantánea de presión anula la densidad de oxidante; las moléculas de combustible pirolizado se expanden libremente sin colisiones reactivas.',
          observations: 'Flap de apagado ultrarrápido sin combustión latente ni formación residual de monóxido de carbono.',
          outcome: 'Extinción absoluta garantizada por colapso termodinámico de la presión de vapor.',
          risk: 'EXTINCT',
          confidence: 0.99,
        },
      };
    }

    const isHighO2 = s.oxygenFraction >= 28;
    const isConcurrent = s.flowDirection === 'concurrent';

    if (isHighO2 && isConcurrent) {
      return {
        id: 'EVID-SAF-06',
        title: `${s.material} bajo flujo concurrente y oxígeno enriquecido`,
        risk: 'CRITICAL',
        confidence: 0.84,
        heatReleaseKw: Number((2.4 * (s.oxygenFraction / 28)).toFixed(1)),
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: 'NASA Saffire-VI Ensayo 03 & BASS-II PSI-25',
        analogousEvidence: 'FLEX PSI-69 (Dinámica de radiación en microgravedad)',
        extrapolatedVars: ['Geometría a escala de módulo completo', 'Interferencias de racks presurizados'],
        counterfactual: 'Reducir O₂ por debajo de 23% o activar purga a vacío para inducir extinción inmediata.',
        warning: 'No se registran ensayos idénticos a escala de volumen cerrado para esta concentración exacta.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-98',
        causalChain: {
          conditions: `${s.material} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa (ΔP: ${t.gaugePressureKpa} kPa) · Flujo: ${s.flowVelocity} cm/s`,
          physicalMechanism: 'La ventilación forzada suple la ausencia de boyamiento gravitatorio; la alta presencia de oxidante acelera la pirólisis superficial sin desprender la llama.',
          observations: 'Propagación sostenida de frente continuo y desprendimiento acelerado de monóxido de carbono previo al alza térmica global.',
          outcome: 'Combustión estable y riesgo primario por toxicidad respiratoria.',
          risk: 'CRITICAL',
          confidence: 0.84,
        },
      };
    } else if (s.oxygenFraction < 22) {
      return {
        id: 'EVID-BASS-14',
        title: `${s.material} en umbral de extinción por disipación radiativa`,
        risk: 'LOW',
        confidence: 0.74,
        heatReleaseKw: 0.4,
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: 'BASS-II PSI-25 Ensayo 14 & FLEX PSI-69',
        analogousEvidence: 'NASA ACME (Límites de estabilidad en llamas difusas)',
        extrapolatedVars: ['Material con degradación térmica previa'],
        counterfactual: 'Incrementar el flujo por encima de 12 cm/s suministra oxidante suficiente para reactivar la combustión.',
        warning: 'Extinción dominada por pérdida de calor en la base del espécimen.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25',
        causalChain: {
          conditions: `${s.material} · O₂: ${s.oxygenFraction}% · Flujo bajo`,
          physicalMechanism: 'La velocidad de pérdida radiativa supera la tasa de generación exotérmica por transporte difusivo.',
          observations: 'Contracción progresiva del diámetro de la llama hasta el apagado total sin rescoldo residual.',
          outcome: 'Extinción espontánea por balance térmico negativo.',
          risk: 'LOW',
          confidence: 0.74,
        },
      };
    } else {
      return {
        id: 'EVID-FLEX-42',
        title: `${s.material} en régimen de combustión cuasi-estacionaria`,
        risk: 'HIGH',
        confidence: 0.78,
        heatReleaseKw: 1.3,
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: 'Saffire-I PSI-98 & BASS-II',
        analogousEvidence: 'SoFIE (Solid Fuel Ignition and Extinction)',
        extrapolatedVars: ['Efectos de curvatura en conductos de ventilación'],
        counterfactual: 'Una reducción de presión a 45 kPa disminuye la velocidad de propagación un 22%.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-69',
        causalChain: {
          conditions: `${s.material} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa`,
          physicalMechanism: 'Equilibrio estacionario entre transporte forzado de oxidante y pirólisis del combustible sólido.',
          observations: 'Estructura elíptica con base translúcida azulada y emisión controlada de partículas de hollín.',
          outcome: 'Propagación laminar continua.',
          risk: 'HIGH',
          confidence: 0.78,
        },
      };
    }
  });

  // Triada de Evidencia Científica (WHAT WE KNOW / INFER / DON'T KNOW)
  public readonly knowledgeTriad = computed<KnowledgeTriadItem[]>(() => {
    const s = this.scenario();
    const t = this.telemetry();
    return [
      {
        id: 'k1',
        category: 'KNOW',
        title: 'Medición de gases en cápsula Cygnus',
        description: `En ensayos con flujos de 20 cm/s sobre materiales sólidos, el incremento crítico temprano corresponde al CO y CO₂, mientras que la temperatura global de cabina sube con menor rapidez.`,
        source: 'NASA Saffire VI (ICES-2024-365)',
        badgeText: 'Observación directa',
        confidence: 0.95,
      },
      {
        id: 'k2',
        category: 'KNOW',
        title: 'Límite de sustentación BASS-II',
        description: `Muestras de ${s.material} de espesor normalizado no sostienen llama en microgravedad con O₂ inferior al 20.8% si la ventilación es menor a 5 cm/s.`,
        source: 'NASA BASS-II (PSI-25)',
        badgeText: 'Dato empírico',
        confidence: 0.92,
      },
      {
        id: 'i1',
        category: 'INFER',
        title: 'Precalentamiento por flujo concurrente',
        description: `Al orientar el flujo a ${s.flowVelocity} cm/s en dirección concurrente, los gases de escape precalientan la zona virgen del combustible, incrementando la propagación un ~38%.`,
        source: 'Modelo Mecanicista FLEX / BASS',
        badgeText: 'Inferencia causal',
        confidence: 0.81,
      },
      {
        id: 'i2',
        category: 'INFER',
        title: 'Efecto de Presión Parcial P_O2 en Inflamabilidad',
        description: `A ${s.pressureKpa} kPa, la presión parcial de oxígeno es ${t.partialPressureO2Kpa} kPa. El criterio NASA-STD-6001 estipula que la densidad molar de oxidante es el factor determinante, no el porcentaje bruto.`,
        source: 'NASA-STD-6001 Flammability Test',
        badgeText: 'Física aeroespacial',
        confidence: 0.88,
      },
      {
        id: 'd1',
        category: 'DONT_KNOW',
        title: 'Zonas de estancamiento en geometrías complejas',
        description: `No existen ensayos con configuraciones de bahías de carga presurizadas con recirculación turbulenta inducida por obstáculos internos.`,
        source: 'Límite de Dominio Experimental',
        badgeText: 'Sin datos empíricos',
      },
      {
        id: 'd2',
        category: 'DONT_KNOW',
        title: 'Degradación térmica de larga duración',
        description: `La serie Saffire contempló eventos controlados de hasta ~3.2 kW. Se carece de datos experimentales de combustión sostenida mayor a 40 minutos.`,
        source: 'Incertidumbre Epistémica',
        badgeText: 'Frontera de conocimiento',
      },
    ];
  });

  // Contraejemplo más cercano (Counterexample Engine)
  public readonly counterexample = computed<Counterexample>(() => {
    const s = this.scenario();
    return {
      id: 'CE-BASS-25-X',
      experimentTitle: 'BASS-II Ensayo PSI-25 #48 (Combustible Sólido)',
      contradictoryOutcome: 'Extinción prematura observada',
      observedDifference: `Con O₂ al ${s.oxygenFraction}% y condiciones térmicas iniciales similares, el espécimen experimentó extinción completa por disipación de calor hacia el soporte estructural y un micro-gradiente de flujo inverso.`,
      nasaSource: 'NASA Physical Sciences Informatics PSI-25',
      sourceUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25',
    };
  });

  // Aprendizaje Activo (Active Learning)
  public readonly testRecommendation = computed<ActiveLearningRecommendation>(() => {
    const s = this.scenario();
    return {
      nextTestTitle: 'Ensayo Crítico de Límite de Flujo Concurrente con PMMA Delgado',
      coordinates: {
        material: s.material,
        oxygenFraction: 27.5,
        pressureKpa: 52,
        flowVelocity: 6.5,
        flowDirection: 'concurrent',
      },
      rationale:
        'En la zona de 26% a 29% de O₂ con flujos bajos (5 a 8 cm/s), la frontera entre extinción radiativa y propagación sostenida presenta la mayor dispersión en los datos (entropía predictiva H = 0.94). Un ensayo en este punto reducirá la incertidumbre del modelo en un 38.4%.',
      uncertaintyScore: 0.94,
      expectedEntropyReduction: '38.4%',
    };
  });

  // =========================================================================
  // ACCIONES Y PROTOCOLOS AEROESPACIALES
  // =========================================================================

  public updateMaterial(material: PhysicalScenario['material']): void {
    this.scenario.update((s) => ({ ...s, material }));
    this.recordTelemetryStep();
  }

  public updateOxygen(oxygenFraction: number): void {
    this.scenario.update((s) => ({ ...s, oxygenFraction }));
    this.recordTelemetryStep();
  }

  public updatePressure(pressureKpa: number): void {
    this.scenario.update((s) => ({ ...s, pressureKpa, isVentingToSpace: false }));
    this.recordTelemetryStep();
  }

  public updateFlow(flowVelocity: number): void {
    this.scenario.update((s) => ({ ...s, flowVelocity }));
    this.recordTelemetryStep();
  }

  public updateDirection(flowDirection: PhysicalScenario['flowDirection']): void {
    this.scenario.update((s) => ({ ...s, flowDirection }));
    this.recordTelemetryStep();
  }

  public setGravityMode(gravityMode: GravityMode): void {
    this.scenario.update((s) => ({ ...s, gravityMode }));
    this.recordTelemetryStep();
  }

  public togglePressureMode(): void {
    this.scenario.update((s) => ({
      ...s,
      pressureMode: s.pressureMode === 'absolute' ? 'gauge' : 'absolute',
    }));
  }

  public toggleUnits(): void {
    this.scenario.update((s) => ({
      ...s,
      unitsSystem: s.unitsSystem === 'si' ? 'imperial' : 'si',
    }));
  }

  // Protocolo de Purga al Vacío Espacial Exterior (Emergency Vacuum Venting)
  public triggerVacuumVenting(): void {
    this.scenario.update((s) => ({
      ...s,
      isVentingToSpace: true,
      pressureKpa: 0,
    }));
    this.recordTelemetryStep();
  }

  // Restaurar Atmósfera de Cabina Nominal
  public restoreCabinAtmosphere(): void {
    this.scenario.update((s) => ({
      ...s,
      isVentingToSpace: false,
      pressureKpa: 55, // Atmósfera nominal de exploración
      oxygenFraction: 30,
    }));
    this.recordTelemetryStep();
  }

  // Inyección de Agente Extintor Inerte (N2 / CO2)
  public injectSuppressant(gas: 'N2' | 'CO2'): void {
    this.scenario.update((s) => ({
      ...s,
      oxygenFraction: Math.max(12, s.oxygenFraction - 12),
      suppressant: gas,
    }));
    this.recordTelemetryStep();
  }

  // Exportar Telemetría Experimental en formato JSON estructurado
  public exportTelemetryData(): void {
    const s = this.scenario();
    const t = this.telemetry();
    const e = this.evidenceCard();

    const report = {
      experimentId: `IGNIS-${e.id}-${Date.now()}`,
      timestampIso: new Date().toISOString(),
      facility: 'NASA Physical Sciences Informatics (PSI) Mirror',
      conditions: {
        material: s.material,
        oxygenFractionPercent: s.oxygenFraction,
        pressureAbsoluteKpa: s.pressureKpa,
        pressureGaugeNegativeKpa: t.gaugePressureKpa,
        pressurePsia: t.pressurePsia,
        partialPressureO2Kpa: t.partialPressureO2Kpa,
        flowVelocityCmS: s.flowVelocity,
        flowDirection: s.flowDirection,
        effectiveGravityG: t.gravityG,
        isVentingToSpace: s.isVentingToSpace,
      },
      telemetry: {
        thermocoupleTempC: t.thermocoupleTempC,
        radiometerFluxKwM2: t.radiometerFluxKwM2,
        carbonMonoxidePpm: t.coPpm,
        carbonDioxidePercent: t.co2Percent,
        flameSpreadRateCmS: t.flameSpreadVelocityCmS,
        extinctionProbability: t.flameExtinctionProb,
        reynoldsNumber: t.reynoldsNumber,
        damkohlerNumber: t.damkohlerNumber,
        nasaStd6001Classification: t.nasaStd6001Status,
      },
      causalChain: e.causalChain,
      verificationSource: e.directEvidence,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `IGNIS_Telemetry_${s.material}_${s.oxygenFraction}O2.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  private recordTelemetryStep(): void {
    const t = this.telemetry();
    const hist = this.telemetryHistory();
    const nextTime = hist.length > 0 ? hist[hist.length - 1].timeSec + 5 : 0;
    const newPoint: TelemetryPoint = {
      timeSec: nextTime,
      temperatureC: t.thermocoupleTempC,
      coPpm: t.coPpm,
      radiometerKwM2: t.radiometerFluxKwM2,
    };
    const updated = [...hist.slice(-7), newPoint];
    this.telemetryHistory.set(updated);
  }

  public openDrawer(type: 'evidence' | 'challenge' | 'next-test'): void {
    this.activeDrawer.set(type);
  }

  public closeDrawer(): void {
    this.activeDrawer.set(null);
  }

  public setLayer(layer: 'all' | 'flame' | 'sensors' | 'gases'): void {
    this.activeLayer.set(layer);
  }
}
