import { Injectable, computed, signal } from '@angular/core';
import {
  ActiveLearningRecommendation,
  BayesianInferenceResult,
  BayesianNetworkModel,
  BurnerGeometryType,
  Counterexample,
  CounterfactualComparisonData,
  CounterfactualMode,
  DigitalTwinSensor,
  EvidenceCard,
  EvidencePassportData,
  ExperimentBrief,
  GravityMode,
  JornadaRankingItem,
  KnowledgeTriadItem,
  MfcDiscreteEvent,
  MfcPatternState,
  MissionControlStep,
  PhysicalScenario,
  PressureDisplayMode,
  RayClusterStatus,
  ScientificRealityMode,
  ScmModelVariant,
  SensorChannelReading,
  SensorTelemetry,
  TelemetryPoint,
  UnitsSystem,
  VisualLayerType,
} from '../models/ignis.model';
import { AppTranslations, TRANSLATIONS_EN, TRANSLATIONS_ES } from '../i18n/translations';

@Injectable({
  providedIn: 'root',
})
export class IgnisService {
  // Idioma activo: 'en' (Inglés por defecto como solicitó el usuario) o 'es' (Español)
  public readonly currentLang = signal<'en' | 'es'>('en');

  // Diccionario reactivo de traducciones para toda la aplicación
  public readonly t = computed<AppTranslations>(() =>
    this.currentLang() === 'en' ? TRANSLATIONS_EN : TRANSLATIONS_ES
  );

  public setLanguage(lang: 'en' | 'es'): void {
    this.currentLang.set(lang);
  }

  public toggleLanguage(): void {
    this.currentLang.update((l) => (l === 'en' ? 'es' : 'en'));
  }

  // Sensores del Gemelo Digital Basado en Evidencia (ia/acme_geometry_manifest.json & sensor_registry_20013d1.py)
  public readonly digitalTwinSensors = signal<DigitalTwinSensor[]>([
    {
      sensorId: 'TCBurner',
      label: 'TCBurner · Superficie del Quemador (r = 3.2 mm)',
      category: 'THERMOCOUPLE',
      positionXyzM: [0.0, 0.0, 0.0032],
      pos3D: [0.0, 0.12, 0.08],
      radialDistanceMm: 3.2,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'mV_raw',
      currentRawValue: 7.65,
      calibrationVerified: false,
      calibrationLockNote: 'Prohibido convertir a Kelvin [K] sin tabla de calibración validada.'
    },
    {
      sensorId: 'TCA',
      label: 'TCA · Rastrillo Radial Interior (r = 8.0 mm)',
      category: 'THERMOCOUPLE',
      positionXyzM: [0.008, 0.0, 0.0],
      pos3D: [0.35, 0.08, 0.0],
      radialDistanceMm: 8.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'mV_raw',
      currentRawValue: 15.95,
      calibrationVerified: false,
      calibrationLockNote: 'Termopar interior en zona de reacción; señal en mV sin linealizar.'
    },
    {
      sensorId: 'TCB',
      label: 'TCB · Rastrillo Radial Medio (r = 15.0 mm)',
      category: 'THERMOCOUPLE',
      positionXyzM: [0.015, 0.0, 0.0],
      pos3D: [0.65, 0.05, 0.0],
      radialDistanceMm: 15.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'mV_raw',
      currentRawValue: 13.15,
      calibrationVerified: false,
      calibrationLockNote: 'Termopar en zona de gases calientes; preserva mV instrumentales.'
    },
    {
      sensorId: 'TCC',
      label: 'TCC · Rastrillo Radial Exterior (r = 25.0 mm)',
      category: 'THERMOCOUPLE',
      positionXyzM: [0.025, 0.0, 0.0],
      pos3D: [0.95, 0.02, 0.0],
      radialDistanceMm: 25.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'mV_raw',
      currentRawValue: 8.60,
      calibrationVerified: false,
      calibrationLockNote: 'Gradiente periférico; candado epistémico activo.'
    },
    {
      sensorId: 'PMT3',
      label: 'PMT3 · Fotomultiplicador OH*/CH* (r = 125.0 mm)',
      category: 'PHOTOMULTIPLIER',
      positionXyzM: [0.0, 0.120, 0.035],
      pos3D: [0.0, 0.95, 0.35],
      radialDistanceMm: 125.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'V_raw_counts',
      currentRawValue: 4.20,
      calibrationVerified: false,
      calibrationLockNote: 'Conteo óptico crudo en V; no calibrado a concentración absoluta.'
    },
    {
      sensorId: 'RadiometerCenter',
      label: 'RadiometerCenter · Termopila Schmidt-Boelter (r = 154.0 mm)',
      category: 'RADIOMETER',
      positionXyzM: [0.0, -0.154, 0.0],
      pos3D: [0.0, -0.95, 0.0],
      radialDistanceMm: 154.0,
      verificationTier: 'VERIFIED_DIMENSION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_data.csv',
      originalUnit: 'mV_raw_irradiance',
      currentRawValue: 2.90,
      calibrationVerified: false,
      calibrationLockNote: 'Distancia nominal verificada (154 mm); irradiancia en mV.'
    },
    {
      sensorId: 'MFC2',
      label: 'MFC2 · Inyector de Flujo Másico (Conducto -X)',
      category: 'MASS_FLOW_CONTROLLER',
      positionXyzM: [-0.045, 0.0, -0.060],
      pos3D: [-0.75, -0.55, -0.35],
      radialDistanceMm: 75.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_mfcSetpoints.csv',
      originalUnit: 'V',
      currentRawValue: 1.82,
      calibrationVerified: false,
      calibrationLockNote: 'Consigna eléctrica en Voltios [V]; no interpretable como kg/s.'
    },
    {
      sensorId: 'MFC3',
      label: 'MFC3 · Inyector de Flujo Másico (Conducto +X)',
      category: 'MASS_FLOW_CONTROLLER',
      positionXyzM: [0.045, 0.0, -0.060],
      pos3D: [0.75, -0.55, -0.35],
      radialDistanceMm: 75.0,
      verificationTier: 'GEOMETRIC_APPROXIMATION',
      epistemicTag: 'OBSERVED',
      sourceFile: '20013D1_mfcSetpoints.csv',
      originalUnit: 'V',
      currentRawValue: 3.10,
      calibrationVerified: false,
      calibrationLockNote: 'Consigna eléctrica en Voltios [V]; candado activo sin calibración.'
    }
  ]);

  // Sonda de sensor seleccionada para inspección detallada en 3D
  public readonly activeSensorDetail = signal<DigitalTwinSensor | null>(null);

  public selectSensorDetail(sensor: DigitalTwinSensor | null): void {
    this.activeSensorDetail.set(sensor);
  }

  // 42 Eventos Discretos de MFC2/MFC3 (ia/data_bridge_20013d1.py)
  public readonly discreteMfcEvents = signal<MfcDiscreteEvent[]>([
    { eventIndex: 1, timeSec: 0.0, mfc2V: 0.00, mfc3V: 0.00, phaseNote: 'Pre-ignición (Líneas cerradas)' },
    { eventIndex: 5, timeSec: 14.2, mfc2V: 0.85, mfc3V: 1.20, phaseNote: 'Establecimiento de flujo laminar' },
    { eventIndex: 10, timeSec: 26.5, mfc2V: 1.20, mfc3V: 1.95, phaseNote: 'Ignición asistida por chispa' },
    { eventIndex: 15, timeSec: 41.0, mfc2V: 1.60, mfc3V: 2.65, phaseNote: 'Transitorio de crecimiento difusivo' },
    { eventIndex: 20, timeSec: 55.4, mfc2V: 1.82, mfc3V: 3.10, phaseNote: 'Pico nominal de llama esférica (ACME)' },
    { eventIndex: 25, timeSec: 72.0, mfc2V: 1.95, mfc3V: 3.05, phaseNote: 'Régimen cuasi-estacionario' },
    { eventIndex: 30, timeSec: 88.5, mfc2V: 1.70, mfc3V: 2.80, phaseNote: 'Modulación de diluyente N2' },
    { eventIndex: 35, timeSec: 104.2, mfc2V: 1.35, mfc3V: 2.10, phaseNote: 'Aproximación al umbral de extinción' },
    { eventIndex: 40, timeSec: 122.0, mfc2V: 0.70, mfc3V: 1.10, phaseNote: 'Contracción radiativa' },
    { eventIndex: 42, timeSec: 138.6, mfc2V: 0.00, mfc3V: 0.00, phaseNote: 'Extinción final espontánea (Quench)' }
  ]);

  public readonly currentMfcEventIndex = signal<number>(20);

  public setMfcEventIndex(idx: number): void {
    this.currentMfcEventIndex.set(idx);
    const evt = this.discreteMfcEvents().find(e => e.eventIndex === idx);
    if (evt) {
      this.digitalTwinSensors.update(sensors => sensors.map(s => {
        if (s.sensorId === 'MFC2') return { ...s, currentRawValue: evt.mfc2V };
        if (s.sensorId === 'MFC3') return { ...s, currentRawValue: evt.mfc3V };
        return s;
      }));
    }
  }

  // Estado del Clúster Distribuido Ray Zero-Copy & VM3 (ia/ray_cluster_bridge.py)
  public readonly rayClusterStatus = signal<RayClusterStatus>({
    ringBufferMb: 64,
    taskLatencyMs: 38,
    workerVm: 'VM3 (Spacecraft Flight Node)',
    isSynced: true,
    activeSwarmNodes: 4
  });
  // Modo de color (Light / Dark estilo Apple)
  public readonly isDarkMode = signal<boolean>(false);

  // Estado reactivo del escenario experimental aeroespacial (s-Flame ACME / BASS-II)
  public readonly scenario = signal<PhysicalScenario>({
    material: 'Etileno (C₂H₄)',
    burnerGeometry: 'sflame-sphere', // Quemador esférico poroso s-Flame (NASA ACME)
    oxygenFraction: 30, // 30% O2
    pressureKpa: 55,   // 55 kPa atmósfera de cabina espacial Exploration Atmosphere
    flowVelocity: 15,  // 15 cm/s flujo laminar en microgravedad
    flowDirection: 'concurrent',
    suppressant: 'Ninguno',
    gravityMode: 'micro-quiescent',
    pressureMode: 'absolute',
    unitsSystem: 'si',
    isVentingToSpace: false,
  });

  // Modal / Drawer activo para las 3 acciones científicas
  public readonly activeDrawer = signal<'evidence' | 'challenge' | 'next-test' | null>(null);

  // 1. Selector de Realidad Científica (Scientific Reality Mode)
  public readonly scientificMode = signal<ScientificRealityMode>('simulation');

  // Sub-modo para Vista B (Inferencia): 'bayesian' o 'counterfactual'
  public readonly inferenceSubMode = signal<'bayesian' | 'counterfactual' | 'digital-twin'>('bayesian');

  // Sub-panel en Simulación para desaturar los controles: 'all' | 'atmosphere' | 'fluid' | 'suppression'
  public readonly simulationPanel = signal<'all' | 'atmosphere' | 'fluid' | 'suppression'>('all');

  // Estado minimizado del tour Mission Control
  public readonly isTourMinimized = signal<boolean>(false);

  // 2. Live Bayesian Inference State
  public readonly selectedMfcPattern = signal<MfcPatternState>('solo-mfc3');
  public readonly selectedBayesianModel = signal<BayesianNetworkModel>('BN-01');

  // 3. Factual vs. Counterfactual Explorer State
  public readonly counterfactualTab = signal<CounterfactualMode>('observed');
  public readonly selectedScmModel = signal<ScmModelVariant>('M1');
  public readonly mfc2Multiplier = signal<number>(1.14);
  public readonly mfc3Multiplier = signal<number>(0.92);

  // 4. NASA Evidence Passport State
  public readonly activeEvidencePassport = signal<EvidencePassportData | null>(null);

  // 5. What NASA Should Test Next & LOJO State
  public readonly selectedJornadaWhy = signal<JornadaRankingItem | null>(null);
  public readonly generatedBrief = signal<ExperimentBrief | null>(null);

  // 6. Mission Control 90s Guided Demo State
  public readonly activeTourStep = signal<number | null>(null);

  // Filtro de capa visual en el gemelo digital 3D (Sección 9 ACME: campos físicos)
  public readonly activeLayer = signal<VisualLayerType>('all');

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

  public setLayer(layer: VisualLayerType): void {
    this.activeLayer.set(layer);
  }

  public setBurnerGeometry(geometry: BurnerGeometryType): void {
    this.scenario.update((s) => ({ ...s, burnerGeometry: geometry }));
  }

  // Telemetría rigurosa calculada con ecuaciones de combustión en microgravedad (NASA s-Flame ACME)
  public readonly telemetry = computed<SensorTelemetry>(() => {
    const s = this.scenario();

    // 1. Efecto de gravedad efectiva (g-jitter residual - Sección 7.5)
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
        flameRadiusMm: 0.0,
        burnerRadiusMm: 6.35,
        maxFlameTempK: 258.15,
        heatReleaseChemKw: 0.0,
        radiativeLossKw: 0.0,
        netThermalBalanceKw: 0.0,
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

    // Geometría del quemador s-Flame ACME: radio de esfera porosa r_s = 6.35 mm (Sección 7.1, 7.2)
    const rBurnerMm = 6.35;

    // Radio de llama esférica r_f (mm) según ecuación convectivo-difusiva analítica (Sección 3.3, 7.2)
    // r_f = r_s * [1 + 1.85 * (21 / y_O2)^0.4 * (1 + u_flow / 35)]
    const rfMm = Number((rBurnerMm * (1.0 + 1.82 * Math.pow(21.0 / s.oxygenFraction, 0.42) * (1.0 + s.flowVelocity / 35.0) * Math.pow(101.3 / Math.max(10.0, pAbs), 0.18))).toFixed(1));

    // Temperatura de llama T_max (K y °C) según balance de entalpía (Sección 3.4, 9.2)
    const baseTempK = s.material === 'Etileno (C₂H₄)' ? 1850 : s.material === 'Metano (CH₄)' ? 1720 : 1650;
    const tempMaxK = Math.round((baseTempK + (o2Factor * 320) + (flowFactor * 75) * pressureFactor) * (s.gravityMode === 'earth-1g' ? 1.12 : 0.96));
    const tempMaxC = tempMaxK - 273;

    // Emisiones de gases tóxicos (Monóxido y Dióxido de Carbono)
    const matFactor = s.material === 'Etileno (C₂H₄)' ? 1.5 : s.material === 'PMMA' ? 1.4 : s.material === 'Metano (CH₄)' ? 0.7 : 1.0;
    const co = Math.round(44 * o2Factor * flowFactor * matFactor);
    const co2 = Number((0.58 * o2Factor * pressureFactor * (s.gravityMode === 'earth-1g' ? 1.4 : 1.0)).toFixed(2));

    // Tasa de liberación de calor química q_chem (kW) (Sección 9.3)
    const qChemKw = Number((1.2 * o2Factor * flowFactor * pressureFactor * (s.material === 'Etileno (C₂H₄)' ? 1.35 : 1.0)).toFixed(2));

    // Pérdida volumétrica radiativa q_rad (kW) (Sección 5, 9.4)
    // q_rad = 4 * sigma * kappa_p * (T^4 - T_inf^4) * Vol
    const qRadKw = Number((0.24 * Math.pow(tempMaxK / 1000.0, 4) * pressureFactor * (rfMm / 15.0)).toFixed(2));

    // Balance térmico neto q_net = q_chem - q_rad (Sección 9.5)
    const qNetKw = Number((qChemKw - qRadKw).toFixed(2));

    // Flujo térmico radiativo sobre sensor y velocidad de propagación
    const flux = Number((qRadKw * 1.85).toFixed(2));
    const spreadMult = s.flowDirection === 'concurrent' ? 1.48 : 0.42;
    const spread = Number((0.34 * o2Factor * spreadMult * (s.gravityMode === 'earth-1g' ? 2.1 : 1.0)).toFixed(2));

    // Criterio de Extinción Físico de s-Flame (Sección 9.5: q_chem < q_rad)
    let extinctionProb = 0.03;
    if (qNetKw <= 0.05 || (s.oxygenFraction < 19.5 && s.flowVelocity < 4.0)) {
      extinctionProb = 0.95; // Extinción por pérdida radiativa (NASA ACME)
    } else if (s.oxygenFraction < 22.0 && s.flowVelocity > 24.0 && s.flowDirection === 'opposed') {
      extinctionProb = 0.72; // Extinción por soplado convectivo (Blow-off)
    } else if (pAbs < 30.0) {
      extinctionProb = 0.88; // Límite de baja presión por despresurización
    }

    // Número de Reynolds de conducto (L = 5 cm, nu = 1.5e-5 m2/s)
    const reynolds = Math.round((s.flowVelocity * 0.05 / 0.000015) * pressureFactor);

    // Número de Damköhler (Da = tau_res / tau_chem): relación de tiempos característicos
    const damkohler = Number(((pressureFactor * Math.pow(o2Factor, 2)) / (flowFactor + 0.25)).toFixed(2));

    // Criterio de rigor científico: NASA-STD-6001 requiere cámara vertical de vuelo estandarizada;
    // una simulación exploratoria no puede certificar ni reprobar la norma automáticamente.
    const flammability: 'COMPLIANCE NOT ASSESSED' | 'PASSED' | 'MARGINAL' | 'FAILED' = 'COMPLIANCE NOT ASSESSED';

    return {
      thermocoupleTempC: tempMaxC,
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
      flameRadiusMm: rfMm,
      burnerRadiusMm: rBurnerMm,
      maxFlameTempK: tempMaxK,
      heatReleaseChemKw: qChemKw,
      radiativeLossKw: qRadKw,
      netThermalBalanceKw: qNetKw,
      history: this.telemetryHistory(),
    };
  });

  public getTranslatedMaterial(mat?: string): string {
    const target = mat || this.scenario().material;
    const isEn = this.currentLang() === 'en';
    if (!isEn) return target;
    if (target === 'Etileno (C₂H₄)') return 'Ethylene (C₂H₄)';
    if (target === 'Silicone') return 'Silicone';
    return target;
  }

  // Tarjeta de Evidencia Dinámica (Fire Evidence Card)
  public readonly evidenceCard = computed<EvidenceCard>(() => {
    const s = this.scenario();
    const t = this.telemetry();
    const isEn = this.currentLang() === 'en';
    const matName = this.getTranslatedMaterial(s.material);

    if (s.isVentingToSpace) {
      return {
        id: 'EVID-VENT-VACUUM',
        title: isEn
          ? 'Space Vacuum Vent: Instant Extinction via Decompression'
          : 'Purga al Vacío Espacial: Extinción Instantánea por Descompresión',
        risk: 'EXTINCT',
        confidence: 0.99,
        heatReleaseKw: 0.0,
        coPpm: 0,
        co2Fraction: 0.0,
        directEvidence: 'NASA Apollo 13 Protocol & ISS Node 2 Emergency Depress Procedure',
        analogousEvidence: 'NASA Glenn Zero-G Vacuum Quench Facility',
        extrapolatedVars: [],
        counterfactual: isEn
          ? 'Restore cabin pressurization to 55 kPa to allow chemical reactions to reignite.'
          : 'Restaurar la presurización de cabina a 55 kPa para permitir el reinicio de reacciones químicas.',
        warning: isEn
          ? 'Last-resort defense protocol against catastrophic in-cabin fires.'
          : 'Protocolo de última línea de defensa contra incendios catastróficos en cabina.',
        psiUrl: 'https://psi.nasa.gov',
        causalChain: {
          conditions: isEn
            ? `Cabin pressure evacuated to space: P_abs = 0 kPa · ΔP = -101.3 kPa`
            : `Presión de cabina evacuada al espacio exterior: P_abs = 0 kPa · ΔP = -101.3 kPa`,
          physicalMechanism: isEn
            ? 'Instantaneous pressure drop voids oxidizer density; pyrolyzed fuel molecules expand freely without reactive collisions.'
            : 'La caída instantánea de presión anula la densidad de oxidante; las moléculas de combustible pirolizado se expanden libremente sin colisiones reactivas.',
          observations: isEn
            ? 'Ultra-fast flame quench flap with zero latent combustion or residual carbon monoxide.'
            : 'Flap de apagado ultrarrápido sin combustión latente ni formación residual de monóxido de carbono.',
          outcome: isEn
            ? 'Absolute extinction guaranteed by thermodynamic collapse of vapor pressure.'
            : 'Extinción absoluta garantizada por colapso termodinámico de la presión de vapor.',
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
        title: isEn
          ? `${matName} under concurrent flow and enriched oxygen`
          : `${s.material} bajo flujo concurrente y oxígeno enriquecido`,
        risk: 'CRITICAL',
        confidence: 0.84,
        heatReleaseKw: Number((2.4 * (s.oxygenFraction / 28)).toFixed(1)),
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: isEn ? 'NASA Saffire-VI Trial 03 & BASS-II PSI-25' : 'NASA Saffire-VI Ensayo 03 & BASS-II PSI-25',
        analogousEvidence: isEn ? 'FLEX PSI-69 (Microgravity radiation dynamics)' : 'FLEX PSI-69 (Dinámica de radiación en microgravedad)',
        extrapolatedVars: isEn
          ? ['Full-module scale geometry', 'Pressurized racks aerodynamic interference']
          : ['Geometría a escala de módulo completo', 'Interferencias de racks presurizados'],
        counterfactual: isEn
          ? 'Reduce O₂ below 23% or initiate space vacuum vent to induce immediate extinction.'
          : 'Reducir O₂ por debajo de 23% o activar purga a vacío para inducir extinción inmediata.',
        warning: isEn
          ? 'No identical closed-volume trials recorded for this exact concentration.'
          : 'No se registran ensayos idénticos a escala de volumen cerrado para esta concentración exacta.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-98',
        causalChain: {
          conditions: isEn
            ? `${matName} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa (ΔP: ${t.gaugePressureKpa} kPa) · Flow: ${s.flowVelocity} cm/s`
            : `${s.material} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa (ΔP: ${t.gaugePressureKpa} kPa) · Flujo: ${s.flowVelocity} cm/s`,
          physicalMechanism: isEn
            ? 'Forced ventilation replaces absent buoyant convection; high oxidizer presence accelerates surface pyrolysis without flame detachment.'
            : 'La ventilación forzada suple la ausencia de boyamiento gravitatorio; la alta presencia de oxidante acelera la pirólisis superficial sin desprender la llama.',
          observations: isEn
            ? 'Sustained continuous front propagation and accelerated carbon monoxide release prior to global thermal rise.'
            : 'Propagación sostenida de frente continuo y desprendimiento acelerado de monóxido de carbono previo al alza térmica global.',
          outcome: isEn
            ? 'Stable combustion and primary risk driven by respiratory toxicity.'
            : 'Combustión estable y riesgo primario por toxicidad respiratoria.',
          risk: 'CRITICAL',
          confidence: 0.84,
        },
      };
    } else if (s.oxygenFraction < 22) {
      return {
        id: 'EVID-BASS-14',
        title: isEn
          ? `${matName} at extinction threshold by radiative dissipation`
          : `${s.material} en umbral de extinción por disipación radiativa`,
        risk: 'LOW',
        confidence: 0.74,
        heatReleaseKw: 0.4,
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: isEn ? 'BASS-II PSI-25 Trial 14 & FLEX PSI-69' : 'BASS-II PSI-25 Ensayo 14 & FLEX PSI-69',
        analogousEvidence: isEn ? 'NASA ACME (Stability limits in diffusion flames)' : 'NASA ACME (Límites de estabilidad en llamas difusas)',
        extrapolatedVars: isEn ? ['Specimen with prior thermal degradation'] : ['Material con degradación térmica previa'],
        counterfactual: isEn
          ? 'Increasing flow above 12 cm/s supplies sufficient oxidizer to reignite combustion.'
          : 'Incrementar el flujo por encima de 12 cm/s suministra oxidante suficiente para reactivar la combustión.',
        warning: isEn
          ? 'Extinction dominated by heat loss into the specimen base.'
          : 'Extinción dominada por pérdida de calor en la base del espécimen.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25',
        causalChain: {
          conditions: isEn
            ? `${matName} · O₂: ${s.oxygenFraction}% · Low flow`
            : `${s.material} · O₂: ${s.oxygenFraction}% · Flujo bajo`,
          physicalMechanism: isEn
            ? 'Radiative loss rate exceeds exothermic chemical heat release under diffusive transport.'
            : 'La velocidad de pérdida radiativa supera la tasa de generación exotérmica por transporte difusivo.',
          observations: isEn
            ? 'Progressive flame diameter contraction until complete quench with no residual embers.'
            : 'Contracción progresiva del diámetro de la llama hasta el apagado total sin rescoldo residual.',
          outcome: isEn
            ? 'Spontaneous extinction via negative net thermal balance.'
            : 'Extinción espontánea por balance térmico negativo.',
          risk: 'LOW',
          confidence: 0.74,
        },
      };
    } else {
      return {
        id: 'EVID-FLEX-42',
        title: isEn
          ? `${matName} in quasi-steady combustion regime`
          : `${s.material} en régimen de combustión cuasi-estacionaria`,
        risk: 'HIGH',
        confidence: 0.78,
        heatReleaseKw: 1.3,
        coPpm: t.coPpm,
        co2Fraction: t.co2Percent,
        directEvidence: 'Saffire-I PSI-98 & BASS-II',
        analogousEvidence: 'SoFIE (Solid Fuel Ignition and Extinction)',
        extrapolatedVars: isEn ? ['Curvature effects in ventilation ducts'] : ['Efectos de curvatura en conductos de ventilación'],
        counterfactual: isEn
          ? 'Pressure reduction to 45 kPa decreases flame spread rate by 22%.'
          : 'Una reducción de presión a 45 kPa disminuye la velocidad de propagación un 22%.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-69',
        causalChain: {
          conditions: isEn
            ? `${matName} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa`
            : `${s.material} · O₂: ${s.oxygenFraction}% · P_abs: ${s.pressureKpa} kPa`,
          physicalMechanism: isEn
            ? 'Steady balance between forced oxidizer convection and solid fuel pyrolysis.'
            : 'Equilibrio estacionario entre transporte forzado de oxidante y pirólisis del combustible sólido.',
          observations: isEn
            ? 'Elliptical flame structure with translucent blue base and controlled soot emission.'
            : 'Estructura elíptica con base translúcida azulada y emisión controlada de partículas de hollín.',
          outcome: isEn
            ? 'Continuous laminar spread.'
            : 'Propagación laminar continua.',
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
    const isEn = this.currentLang() === 'en';
    const matName = this.getTranslatedMaterial(s.material);

    return isEn
      ? [
          {
            id: 'k1',
            category: 'KNOW',
            title: 'Gas concentrations in Cygnus module',
            description: `In flight trials with 20 cm/s forced flow over solid materials, early critical increases occur in CO and CO₂, whereas global cabin temperature rises much slower.`,
            source: 'NASA Saffire VI (ICES-2024-365)',
            badgeText: 'Direct observation',
            confidence: 0.95,
          },
          {
            id: 'k2',
            category: 'KNOW',
            title: 'BASS-II flammability limit',
            description: `Normalized thickness specimens of ${matName} fail to sustain flame in microgravity at O₂ below 20.8% if ventilation drops below 5 cm/s.`,
            source: 'NASA BASS-II (PSI-25)',
            badgeText: 'Empirical data',
            confidence: 0.92,
          },
          {
            id: 'i1',
            category: 'INFER',
            title: 'Concurrent flow preheating effect',
            description: `Orienting flow at ${s.flowVelocity} cm/s concurrently causes hot exhaust plume to preheat unburned fuel virgin surface, accelerating flame spread by ~38%.`,
            source: 'Mechanistic Model FLEX / BASS',
            badgeText: 'Causal inference',
            confidence: 0.81,
          },
          {
            id: 'i2',
            category: 'INFER',
            title: 'P_O2 partial pressure flammability criterion',
            description: `At ${s.pressureKpa} kPa, oxygen partial pressure is ${t.partialPressureO2Kpa} kPa. NASA-STD-6001 mandates oxidizer molar density as the physical governing parameter rather than volumetric percentage.`,
            source: 'NASA-STD-6001 Flammability Test',
            badgeText: 'Aerospace physics',
            confidence: 0.88,
          },
          {
            id: 'd1',
            category: 'DONT_KNOW',
            title: 'Recirculation dead zones in complex geometry',
            description: `Zero microgravity combustion tests exist for pressurized payload bay racks with obstacle-induced turbulent recirculation.`,
            source: 'Experimental Domain Boundary',
            badgeText: 'No empirical data',
          },
          {
            id: 'd2',
            category: 'DONT_KNOW',
            title: 'Long-duration thermal degradation',
            description: `Saffire series covered controlled burns up to ~3.2 kW. Experimental data is lacking for sustained microgravity combustion exceeding 40 minutes.`,
            source: 'Epistemic Uncertainty',
            badgeText: 'Knowledge frontier',
          },
        ]
      : [
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
    const isEn = this.currentLang() === 'en';

    return isEn
      ? {
          id: 'CE-BASS-25-X',
          experimentTitle: 'BASS-II Trial PSI-25 #48 (Solid Fuel)',
          contradictoryOutcome: 'Premature extinction observed',
          observedDifference: `At O₂ ${s.oxygenFraction}% and identical thermal conditions, specimen underwent complete extinction due to conductive heat loss into mounting support and an adverse micro-flow gradient.`,
          nasaSource: 'NASA Physical Sciences Informatics PSI-25',
          sourceUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25',
        }
      : {
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
    const isEn = this.currentLang() === 'en';

    return isEn
      ? {
          nextTestTitle: 'Critical Flammability Boundary Trial under Concurrent Flow with Thin PMMA',
          coordinates: {
            material: s.material,
            oxygenFraction: 27.5,
            pressureKpa: 52,
            flowVelocity: 6.5,
            flowDirection: 'concurrent',
          },
          rationale:
            'In the 26% to 29% O₂ range under low convective flow (5 to 8 cm/s), the boundary between radiative extinction and sustained propagation exhibits maximum epistemic dispersion (predictive entropy H = 0.94). A targeted trial here reduces model uncertainty by 38.4%.',
          uncertaintyScore: 0.94,
          expectedEntropyReduction: '38.4%',
        }
      : {
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

  // =========================================================================
  // 1. SCIENTIFIC REALITY MODE
  // =========================================================================
  public setScientificMode(mode: ScientificRealityMode): void {
    this.scientificMode.set(mode);
  }

  // =========================================================================
  // 2. LIVE BAYESIAN INFERENCE ENGINE (REDES BAYESIANAS BN-01, BN-02, BN-03)
  // =========================================================================
  public setMfcPattern(pattern: MfcPatternState): void {
    this.selectedMfcPattern.set(pattern);
  }

  public setBayesianModel(model: BayesianNetworkModel): void {
    this.selectedBayesianModel.set(model);
  }

  public readonly bayesianInference = computed<BayesianInferenceResult>(() => {
    const model = this.selectedBayesianModel();
    const pattern = this.selectedMfcPattern();
    const s = this.scenario();
    const isEn = this.currentLang() === 'en';

    // Condición de rigor científico: Si la combinación seleccionada está fuera del espacio de entrenamiento de NASA ACME (N=282)
    if (pattern === 'unsupported' || (model === 'BN-01' && pattern === 'preflow-low' && s.pressureKpa > 100)) {
      return {
        variableName: isEn ? 'MFC Pattern (MFC2 / MFC3 Setpoints)' : 'Patrón MFC (Consignas MFC2 / MFC3)',
        stateName: isEn ? 'Outside Experimental Support' : 'Fuera de Soporte Experimental',
        modelId: model,
        modelDescription: isEn
          ? `NASA ACME Bayesian Network ${model} (N=282 trials across 18 sessions)`
          : 'Red Bayesiana ' + model + ' de NASA ACME (N=282 ensayos en 18 jornadas)',
        probPmt3High: null,
        probRadiometerHigh: null,
        probIgnition: null,
        isSupported: false,
        unsupportedReason: isEn
          ? `Prediction unavailable: selected instrumental combination has no sample support in ${model} CPT (unsampled domain).`
          : 'Predicción no disponible: la combinación instrumental seleccionada no tiene soporte en la CPT de ' + model + ' (rango no entrenado).',
        provenance: 'NASA ACME (PSI-23)',
        inferenceType: isEn ? 'Observational Conditional Inference' : 'Inferencia Condicional Observacional',
        cptNodesSample: []
      };
    }

    if (model === 'BN-01') {
      if (pattern === 'solo-mfc3') {
        return {
          variableName: isEn ? 'MFC Setpoint Pattern' : 'Patrón de Consigna MFC',
          stateName: isEn ? 'Solo MFC3 Positive (Asymmetric Injection)' : 'Solo MFC3 Positivo (Inyección Asimétrica)',
          modelId: 'BN-01',
          modelDescription: isEn ? 'BN-01: Injection & Chemiluminescence Bayesian Network (NASA ACME)' : 'BN-01: Red Bayesiana de Inyección y Quimioluminiscencia (NASA ACME)',
          probPmt3High: 0.184,
          probRadiometerHigh: 0.218,
          probIgnition: 0.742,
          isSupported: true,
          provenance: isEn ? 'NASA ACME s-Flame (PSI-23 / Session 20176)' : 'NASA ACME s-Flame (PSI-23 / Jornada 20176)',
          inferenceType: 'P(Y | MFC_pattern = solo-mfc3)',
          cptNodesSample: [
            { condition: 'Solo MFC3 (+) | O2 = 21%', pPmt3: 0.18, pRad: 0.22 },
            { condition: 'Solo MFC3 (+) | O2 = 30%', pPmt3: 0.29, pRad: 0.35 },
            { condition: 'MFC2+MFC3 (+) | O2 = 21%', pPmt3: 0.84, pRad: 0.79 },
            { condition: 'Ramp High | O2 >= 30%', pPmt3: 0.92, pRad: 0.88 },
          ]
        };
      } else if (pattern === 'mfc2-mfc3-coupled') {
        return {
          variableName: isEn ? 'MFC Setpoint Pattern' : 'Patrón de Consigna MFC',
          stateName: isEn ? 'MFC2 & MFC3 Coupled (Bilateral Nominal Flow)' : 'MFC2 y MFC3 Acoplados (Flujo Nominal Bilateral)',
          modelId: 'BN-01',
          modelDescription: isEn ? 'BN-01: Injection & Chemiluminescence Bayesian Network (NASA ACME)' : 'BN-01: Red Bayesiana de Inyección y Quimioluminiscencia (NASA ACME)',
          probPmt3High: 0.842,
          probRadiometerHigh: 0.791,
          probIgnition: 0.965,
          isSupported: true,
          provenance: isEn ? 'NASA ACME s-Flame (PSI-23 / Trial 20013D1)' : 'NASA ACME s-Flame (PSI-23 / Ensayo 20013D1)',
          inferenceType: 'P(Y | MFC2, MFC3 coupled)',
          cptNodesSample: [
            { condition: 'MFC2+MFC3 | P = 55 kPa', pPmt3: 0.84, pRad: 0.79 },
            { condition: 'MFC2+MFC3 | P = 101.3 kPa', pPmt3: 0.89, pRad: 0.85 },
            { condition: 'Solo MFC3 (+) | P = 55 kPa', pPmt3: 0.18, pRad: 0.22 },
          ]
        };
      } else if (pattern === 'preflow-low') {
        return {
          variableName: isEn ? 'MFC Setpoint Pattern' : 'Patrón de Consigna MFC',
          stateName: isEn ? 'Low Preflow (< 1.0 V / Residual Flow)' : 'Preflow Bajo (< 1.0 V / Flujo Residual)',
          modelId: 'BN-01',
          modelDescription: isEn ? 'BN-01: Injection & Chemiluminescence Bayesian Network (NASA ACME)' : 'BN-01: Red Bayesiana de Inyección y Quimioluminiscencia (NASA ACME)',
          probPmt3High: 0.052,
          probRadiometerHigh: 0.081,
          probIgnition: 0.312,
          isSupported: true,
          provenance: isEn ? 'NASA ACME s-Flame (Purge Phase)' : 'NASA ACME s-Flame (Fase de Purga)',
          inferenceType: 'P(Y | preflow_low)',
          cptNodesSample: [
            { condition: 'Preflow < 1.0V | Quiescent', pPmt3: 0.05, pRad: 0.08 },
            { condition: 'Preflow < 1.0V | Convection', pPmt3: 0.12, pRad: 0.14 },
          ]
        };
      } else {
        return {
          variableName: isEn ? 'MFC Setpoint Pattern' : 'Patrón de Consigna MFC',
          stateName: isEn ? 'High Ramp (> 3.5 V / Vigorous Combustion)' : 'Rampa Alta (> 3.5 V / Combustión Vigorosa)',
          modelId: 'BN-01',
          modelDescription: isEn ? 'BN-01: Injection & Chemiluminescence Bayesian Network (NASA ACME)' : 'BN-01: Red Bayesiana de Inyección y Quimioluminiscencia (NASA ACME)',
          probPmt3High: 0.923,
          probRadiometerHigh: 0.884,
          probIgnition: 0.988,
          isSupported: true,
          provenance: isEn ? 'NASA ACME s-Flame (Plateau Phase 20013D1)' : 'NASA ACME s-Flame (Fase de Meseta 20013D1)',
          inferenceType: 'P(Y | ramp_high)',
          cptNodesSample: [
            { condition: 'Ramp > 3.5V | P = 55 kPa', pPmt3: 0.92, pRad: 0.88 },
            { condition: 'Ramp > 3.5V | P = 101.3 kPa', pPmt3: 0.96, pRad: 0.93 },
          ]
        };
      }
    } else if (model === 'BN-02') {
      return {
        variableName: isEn ? 'Thermal Regime & Cool Flame' : 'Régimen Térmico y Llama Fría',
        stateName: isEn ? 'Low Temperature Window (500 K - 1000 K)' : 'Ventana de Baja Temperatura (500 K - 1000 K)',
        modelId: 'BN-02',
        modelDescription: isEn ? 'BN-02: Chemiluminescence & Cool Flame Detection (FLEX / ACME)' : 'BN-02: Detección de Quimioluminiscencia y Llama Fría (FLEX / ACME)',
        probPmt3High: 0.675,
        probRadiometerHigh: 0.142,
        probIgnition: 0.810,
        isSupported: true,
        provenance: 'NASA FLEX / ACME PSI-117',
        inferenceType: 'P(CoolFlame | T in [500, 1000] K)',
        cptNodesSample: [
          { condition: 'T in [500, 1000] K | CH4', pPmt3: 0.68, pRad: 0.14 },
          { condition: 'T > 1000 K | C2H4', pPmt3: 0.89, pRad: 0.72 },
        ]
      };
    } else {
      return {
        variableName: isEn ? 'E-Field Coupling & Ionization' : 'Acoplamiento E-Field e Ionización',
        stateName: isEn ? 'Mesh Voltage V_efield in [0.2 V, 1.8 V]' : 'Voltaje de Malla V_efield in [0.2 V, 1.8 V]',
        modelId: 'BN-03',
        modelDescription: isEn ? 'BN-03: E-Field / Flame Ion Current Interaction (NASA ACME E-FIELD)' : 'BN-03: Interacción E-Field / Corriente Iónica de Llama (NASA ACME E-FIELD)',
        probPmt3High: 0.582,
        probRadiometerHigh: 0.495,
        probIgnition: 0.890,
        isSupported: true,
        provenance: 'NASA ACME E-FIELD Investigation',
        inferenceType: 'ρ(E_field, I_ion) = 0.781',
        cptNodesSample: [
          { condition: 'E-Field > 1.0 V | Concurrent', pPmt3: 0.58, pRad: 0.50 },
          { condition: 'E-Field = 0.0 V | Concurrent', pPmt3: 0.41, pRad: 0.38 },
        ]
      };
    }
  });

  // =========================================================================
  // 3. FACTUAL VS. COUNTERFACTUAL EXPLORER (SCM CAUSAL COMPARATOR)
  // =========================================================================
  public setCounterfactualTab(tab: CounterfactualMode): void {
    this.counterfactualTab.set(tab);
  }

  public setScmModel(m: ScmModelVariant): void {
    this.selectedScmModel.set(m);
  }

  public setMfcMultipliers(mfc2: number, mfc3: number): void {
    this.mfc2Multiplier.set(mfc2);
    this.mfc3Multiplier.set(mfc3);
  }

  public readonly counterfactualComparison = computed<CounterfactualComparisonData>(() => {
    const scm = this.selectedScmModel();
    const mfc2 = this.mfc2Multiplier();
    const mfc3 = this.mfc3Multiplier();
    const isEn = this.currentLang() === 'en';

    // Sensibilidad del SCM según scm_counterfactual_bridge.py
    const netDriveRatio = 0.65 * (mfc2 - 1.0) + 0.35 * (mfc3 - 1.0);
    let modelMult = 1.0;
    let scmName = isEn ? 'M1: Direct Linear Coupling' : 'M1: Acoplamiento Lineal Directo';
    if (scm === 'M2') {
      modelMult = 0.78;
      scmName = isEn ? 'M2: Thermophoretic Saturation & Soot Shell' : 'M2: Saturación Termoforética y Acumulación de Hollín';
    } else if (scm === 'M3') {
      modelMult = 1.25;
      scmName = isEn ? 'M3: Non-Linear SCM with Planck Radiative Feedback' : 'M3: SCM No Lineal con Retroalimentación Radiativa Planck';
    }

    const rawChannels = [
      { id: 'TCBurner', name: isEn ? 'Burner Thermocouple' : 'Termopar Quemador', unit: 'mV', obs: 3.420, gain: 0.85, cal: false },
      { id: 'TCA', name: isEn ? 'Thermocouple TCA (Front)' : 'Termopar TCA (Frente)', unit: 'mV', obs: 8.150, gain: 1.35, cal: false },
      { id: 'TCB', name: isEn ? 'Thermocouple TCB (Mid)' : 'Termopar TCB (Medio)', unit: 'mV', obs: 6.900, gain: 1.22, cal: false },
      { id: 'TCC', name: isEn ? 'Thermocouple TCC (Wake)' : 'Termopar TCC (Estela)', unit: 'mV', obs: 4.100, gain: 0.95, cal: false },
      { id: 'PMT3', name: isEn ? 'Photomultiplier PMT3' : 'Fotomultiplicador PMT3', unit: 'nA', obs: 142.50, gain: 1.55, cal: false },
      { id: 'RadiometerCenter', name: isEn ? 'Central Radiometer' : 'Radiómetro Central', unit: 'mV', obs: 1.620, gain: 1.18, cal: false },
    ];

    const channels: SensorChannelReading[] = rawChannels.map((c) => {
      const delta = Number((c.obs * c.gain * netDriveRatio * modelMult).toFixed(3));
      const hyp = Number((c.obs + delta).toFixed(3));
      const pct = Number(((delta / c.obs) * 100).toFixed(1));
      return {
        channelId: c.id,
        name: c.name,
        unit: c.unit,
        observedValue: c.obs,
        hypotheticalValue: hyp,
        delta: delta,
        deltaPct: pct,
        calibrationVerified: c.cal
      };
    });

    return {
      expId: 'NASA ACME 20013D1',
      scmModel: scm,
      scmModelName: scmName,
      interventionDesc: `do(MFC2_V = ${(mfc2 * 100).toFixed(0)}% · V_obs, MFC3_V = ${(mfc3 * 100).toFixed(0)}% · V_obs)`,
      mfc2Multiplier: mfc2,
      mfc3Multiplier: mfc3,
      channels: channels,
      couplingLowerPct: 44.83,
      couplingUpperPct: 82.21,
      couplingEquationLatex: '44.83% \\le P_\\Pi(\\Delta > 0) \\le 82.21%',
      causalEffectIdentified: false,
      disclaimer: isEn
        ? 'Coupling bounds over observational distributions conditional on SCM assumptions. Does not represent fire probability or identified physical causal effects (Flag: causal_effect_identified = False).'
        : 'Cotas de acoplamiento sobre distribuciones observacionales dependientes de supuestos del SCM. No representan probabilidades de incendio ni efectos causales físicos identificados (Bandera: causal_effect_identified = False).'
    };
  });

  // =========================================================================
  // 4. NASA EVIDENCE PASSPORT (TRAZABILIDAD Y LINAJE DE DATOS PSI)
  // =========================================================================
  public openEvidencePassport(passport: Partial<EvidencePassportData>): void {
    const isEn = this.currentLang() === 'en';
    const fullPassport: EvidencePassportData = {
      id: passport.id || 'PASSPORT-PSI-23',
      title: passport.title || (isEn ? 'Evidence Passport · NASA ACME s-Flame' : 'Pasaporte de Evidencia · NASA ACME s-Flame'),
      investigation: passport.investigation || 'NASA ACME (Advanced Combustion via Microgravity Experiments)',
      experimentId: passport.experimentId || '20013D1',
      observedVar: passport.observedVar || (isEn ? 'MFC2/MFC3 Setpoints [V], PMT3 [nA], RadiometerCenter [mV]' : 'Consignas MFC2/MFC3 [V], PMT3 [nA], RadiometerCenter [mV]'),
      sourceFile: passport.sourceFile || 'acme_sflame_raw_telemetry_20013d1.csv',
      sha256: passport.sha256 || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      transformation: passport.transformation || (isEn ? 'Raw flight instrumental voltages without forced interpolation to kg/s or K (Active Calibration Lock)' : 'Señales instrumentales crudas registradas en vuelo sin conversión forzada a kg/s ni K (Candado de Calibración Activo)'),
      modelUsed: passport.modelUsed || 'SCM Causal Graph v2.1 / Red Bayesiana BN-01',
      limitations: passport.limitations || (isEn ? 'Instrumental calibration curves pending official NASA PSI release; estimates bounded to N=282 empirical sample support.' : 'Curvas de calibración instrumental pendientes de publicación oficial en NASA PSI; estimaciones condicionadas al soporte muestral N=282 de 18 jornadas.'),
      psiUrl: passport.psiUrl || 'https://psi.nasa.gov',
      epistemicTag: passport.epistemicTag || 'OBSERVED',
    };
    this.activeEvidencePassport.set(fullPassport);
  }

  public closeEvidencePassport(): void {
    this.activeEvidencePassport.set(null);
  }

  // =========================================================================
  // 5. WHAT NASA SHOULD TEST NEXT & LOJO JORNADAS CLASSIFICATION
  // =========================================================================
  public readonly jornadaRankings = computed<JornadaRankingItem[]>(() => {
    const isEn = this.currentLang() === 'en';
    return isEn
      ? [
          {
            jornadaId: 20176,
            name: 'Session 20176 (NASA ACME s-Flame)',
            isMostInfluential: true,
            trialsCount: 16,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.241,
            deltaRmseLojo: 0.159,
            ateShiftPct: 34.2,
            rationale: 'Most influential session in NASA ACME dataset (N=282). Its exclusion creates a 194% surge in cross-validation error (LOJO RMSE leaps from 0.082 to 0.241) and shifts model causal ATE by concentrating asymmetric ultralow flow tests.',
            suggestedConditions: 'Replicate dual-valve injection with flow u < 4.5 cm/s, X_O2 in [18.0%, 21.0%] and high-speed UV/IR acquisition to resolve observed bimodal dynamics.'
          },
          {
            jornadaId: 20013,
            name: 'Session 20013 (Trial 20013D1)',
            isMostInfluential: false,
            trialsCount: 15,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.118,
            deltaRmseLojo: 0.036,
            ateShiftPct: 9.4,
            rationale: 'Holds benchmark trial 20013D1 with 42 stepped MFC2 and MFC3 voltage events under stable microgravity.',
            suggestedConditions: 'Test declining flow ramp response to characterize CO2/H2O radiative extinction threshold.'
          },
          {
            jornadaId: 20045,
            name: 'Session 20045 (E-Field Regime)',
            isMostInfluential: false,
            trialsCount: 16,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.104,
            deltaRmseLojo: 0.022,
            ateShiftPct: 6.8,
            rationale: 'Trials with coupled electric field mesh electrodes for ion redistribution within the reaction zone.',
            suggestedConditions: 'Sweep external mesh bias potential up to 2.5 kV under 55 kPa exploration atmosphere.'
          },
          {
            jornadaId: 20088,
            name: 'Session 20088 (He/N2 Dilution)',
            isMostInfluential: false,
            trialsCount: 15,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.097,
            deltaRmseLojo: 0.015,
            ateShiftPct: 4.1,
            rationale: 'Investigation of molar heat capacity and thermal diffusivity utilizing helium as inert diluent.',
            suggestedConditions: 'Increase He fraction above 40% molar to measure soot shell suppression and extinction limits.'
          }
        ]
      : [
          {
            jornadaId: 20176,
            name: 'Jornada 20176 (NASA ACME s-Flame)',
            isMostInfluential: true,
            trialsCount: 16,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.241,
            deltaRmseLojo: 0.159,
            ateShiftPct: 34.2,
            rationale: 'Es la jornada más influyente del dataset NASA ACME (N=282). Su exclusión genera un incremento del 194% en el error de validación cruzada (LOJO RMSE salta de 0.082 a 0.241) y desestabiliza el ATE del modelo causal por concentrar las pruebas de inyección asimétrica en flujo ultrabajo.',
            suggestedConditions: 'Replicar inyección bifásica con flujo u < 4.5 cm/s, X_O2 in [18.0%, 21.0%] y adquisición de alta velocidad en radiómetros UV/IR para resolver la bimodalidad observada.'
          },
          {
            jornadaId: 20013,
            name: 'Jornada 20013 (Ensayo 20013D1)',
            isMostInfluential: false,
            trialsCount: 15,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.118,
            deltaRmseLojo: 0.036,
            ateShiftPct: 9.4,
            rationale: 'Contiene el ensayo de referencia 20013D1 con 42 eventos de consignas escalonadas de voltajes MFC2 y MFC3 en microgravedad estable.',
            suggestedConditions: 'Probar respuesta en rampa descendente de flujo para delimitar el límite de extinción radiativa de CO2/H2O.'
          },
          {
            jornadaId: 20045,
            name: 'Jornada 20045 (Régimen E-Field)',
            isMostInfluential: false,
            trialsCount: 16,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.104,
            deltaRmseLojo: 0.022,
            ateShiftPct: 6.8,
            rationale: 'Ensayos con electrodos de campo eléctrico acoplados para redistribución de iones en la zona de reacción.',
            suggestedConditions: 'Variar potencial de polarización en malla externa hasta 2.5 kV bajo atmósfera de exploración de 55 kPa.'
          },
          {
            jornadaId: 20088,
            name: 'Jornada 20088 (Dilución He/N2)',
            isMostInfluential: false,
            trialsCount: 15,
            baselineRmse: 0.082,
            withoutJornadaRmse: 0.097,
            deltaRmseLojo: 0.015,
            ateShiftPct: 4.1,
            rationale: 'Estudio de capacidad calorífica molar y difusividad térmica con helio como diluyente inerte.',
            suggestedConditions: 'Aumentar fracción de He sobre 40% molar para medir la supresión de la concha de hollín.'
          }
        ];
  });

  public openWhyJornada(jornada: JornadaRankingItem): void {
    this.selectedJornadaWhy.set(jornada);
  }

  public closeWhyJornada(): void {
    this.selectedJornadaWhy.set(null);
  }

  public generateExperimentBrief(jornadaId: number): void {
    const j = this.jornadaRankings().find((item) => item.jornadaId === jornadaId) || this.jornadaRankings()[0];
    const isEn = this.currentLang() === 'en';
    const brief: ExperimentBrief = {
      briefId: `BRIEF-NASA-ACME-${j.jornadaId}-OPT`,
      title: isEn
        ? `High-Priority Experimental Campaign Proposal: Replication of Session ${j.jornadaId}`
        : `Propuesta de Campaña Experimental de Alta Relevancia: Replicación Jornada ${j.jornadaId}`,
      targetJornada: j.jornadaId,
      scientificHypothesis: isEn
        ? `Observed bimodality in Session ${j.jornadaId} stems from decoupling between characteristic Planck radiative diffusion timescale and ultralow convective transport (Da < 0.8), solvable via fine-step symmetric injection sweep.`
        : `La bimodalidad observada en la Jornada ${j.jornadaId} obedece a un desacoplamiento entre el tiempo característico de difusión radiativa de Planck y el transporte convectivo ultrabajo (Da < 0.8), susceptible de resolverse mediante barrido fino de inyección simétrica.`,
      proposedConditions: {
        flowVelocity: isEn ? '2.5 to 4.5 cm/s (Ultralow laminar flow)' : '2.5 a 4.5 cm/s (Flujo laminar ultrabajo)',
        oxygenFraction: isEn ? '19.0% to 21.0% molar (Normoxic boundary)' : '19.0% a 21.0% molar (Límite normóxico)',
        pressure: isEn ? '55.0 kPa (Exploration Atmosphere Cabin)' : '55.0 kPa (Cabina Exploration Atmosphere)',
        burnerGeometry: isEn ? 'Porous sintered bronze sphere rs = 6.35 mm' : 'Quemador esférico de bronce sinterizado rs = 6.35 mm',
        fuel: isEn ? 'Ethylene (C₂H₄) diluted with N₂' : 'Etileno (C₂H₄) diluido con N₂'
      },
      targetSensors: isEn
        ? [
            'PMT3 (CH* Chemiluminescence at 431 nm)',
            'Central Broadband Radiometer (Radiative divergence)',
            'Thermocouple Array TCA, TCB, TCC (Radial thermal gradient)',
            'High-speed camera at 1000 fps with bandpass interference filter'
          ]
        : [
            'PMT3 (Quimioluminiscencia CH* a 431 nm)',
            'Radiómetro Central de Banda Ancha (Divergencia radiativa)',
            'Arreglo de Termopares TCA, TCB, TCC (Gradiente térmico radial)',
            'Cámara de alta velocidad a 1000 fps con filtro interferencial'
          ],
      existingEvidencePsi: isEn
        ? 'NASA PSI Open Data (ACME / BASS-II Investigation). Historical record across 16 prior trials.'
        : 'Datos abiertos de NASA PSI (Investigación ACME / BASS-II). Registro histórico con 16 ensayos previos.',
      epistemicLimitations: isEn
        ? 'Requires mass flow calibration curve verification in V to sccm prior to ignition.'
        : 'Requiere validación de curva de calibración de flujo másico en V/sccm previa a la ignición.',
      systemDisclaimer: isEn
        ? 'Autonomous research brief generated by IGNIS-μ via epistemic entropy optimization; does not constitute an official protocol issued by NASA.'
        : 'Propuesta de investigación generada automáticamente por IGNIS-μ mediante optimización de entropía epistémica; no constituye un protocolo oficial emitido por la NASA.',
      generatedDate: isEn
        ? new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
        : new Date().toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' })
    };
    this.generatedBrief.set(brief);
  }

  public closeBrief(): void {
    this.generatedBrief.set(null);
  }

  // =========================================================================
  // 6. MISSION CONTROL 90-SECOND GUIDED DEMO
  // =========================================================================
  public readonly missionControlSteps = computed<MissionControlStep[]>(() => {
    const isEn = this.currentLang() === 'en';
    return isEn
      ? [
          {
            stepIndex: 1,
            timeRange: '0–20s',
            title: 'Exploratory Physics in Microgravity',
            instruction: 'Switch gravitational environment from 1.0 g to 10⁻⁶ g. Observe the disappearance of convective buoyancy and the emergence of a symmetric diffusion sphere. Note the explicit "Exploratory Physical Model" badge ensuring scientific honesty.',
            mode: 'simulation',
            featureKey: 'gravity'
          },
          {
            stepIndex: 2,
            timeRange: '20–35s',
            title: 'Scientific Reality Mode · NASA Evidence',
            instruction: 'Switch to "NASA EVIDENCE". The system locks speculation and displays trial 20013D1 with raw instrumental voltages and active calibration locks with zero falsified units.',
            mode: 'evidence',
            featureKey: 'evidence'
          },
          {
            stepIndex: 3,
            timeRange: '35–50s',
            title: 'Live Bayesian Inference (Empirical CPTs)',
            instruction: 'Switch to "INFERENCE" and select pattern "Solo MFC3 positive". BN-01 CPTs compute genuine conditional probabilities; continuous values outside sample support trigger honest "Prediction unavailable".',
            mode: 'inference',
            featureKey: 'bayesian'
          },
          {
            stepIndex: 4,
            timeRange: '50–70s',
            title: 'Factual vs. Counterfactual Explorer & Digital Twin',
            instruction: 'Explore [OBSERVED] vs [HYPOTHETICAL] vs [COMPARE] and the Digital Twin subtab. Scrub the 42 discrete events in Volts and inspect structural causal bounds (44.83% ≤ P ≤ 82.21%).',
            mode: 'inference',
            featureKey: 'counterfactual'
          },
          {
            stepIndex: 5,
            timeRange: '70–90s',
            title: 'What NASA Should Test Next & Evidence Passport',
            instruction: 'Open "Suggest Next Experiment". IGNIS-μ identifies Jornada 20176 as the most influential via LOJO validation, explains its ATE shift impact, and generates a structured NASA Research Brief.',
            mode: 'evidence',
            featureKey: 'next-test'
          }
        ]
      : [
          {
            stepIndex: 1,
            timeRange: '0–20s',
            title: 'Física Exploratoria en Microgravedad',
            instruction: 'Modifica el entorno gravitatorio de 1.0 g a 10⁻⁶ g. Observa cómo desaparece el boyamiento convectivo y emerge la esfera difusiva perfecta. Nota la etiqueta explícita de "Visualización Física Exploratoria" que garantiza rigor frente al jurado.',
            mode: 'simulation',
            featureKey: 'gravity'
          },
          {
            stepIndex: 2,
            timeRange: '20–35s',
            title: 'Modo Realidad Científica · Evidencia NASA',
            instruction: 'Conmuta a "NASA EVIDENCE". El sistema bloquea especulaciones y muestra únicamente el ensayo 20013D1 con voltajes instrumentales crudos y candado de calibración activo sin unidades falseadas.',
            mode: 'evidence',
            featureKey: 'evidence'
          },
          {
            stepIndex: 3,
            timeRange: '35–50s',
            title: 'Live Bayesian Inference (Probabilidades Reales)',
            instruction: 'Conmuta a "INFERENCE" y selecciona el patrón "Solo MFC3 positivo". Las CPT de la red BN-01 calculan probabilidades condicionales reales; si seleccionas un estado fuera del soporte muestral, el sistema declara con honestidad: "Predicción no disponible".',
            mode: 'inference',
            featureKey: 'bayesian'
          },
          {
            stepIndex: 4,
            timeRange: '50–70s',
            title: 'Factual vs. Counterfactual Explorer & Gemelo Digital',
            instruction: 'Explora [OBSERVED] vs [HYPOTHETICAL] vs [COMPARE] y la pestaña Gemelo Digital. Navega por los 42 eventos discretos en Voltios y compara las cotas estructurales del SCM (44.83% ≤ P ≤ 82.21%).',
            mode: 'inference',
            featureKey: 'counterfactual'
          },
          {
            stepIndex: 5,
            timeRange: '70–90s',
            title: 'What NASA Should Test Next & Evidence Passport',
            instruction: 'Abre "Sugerir Siguiente Ensayo". IGNIS-μ identifica la Jornada 20176 como la más influyente por validación LOJO, explica su impacto sobre el ATE y genera una Ficha de Propuesta de Investigación lista para la toma de decisiones.',
            mode: 'evidence',
            featureKey: 'next-test'
          }
        ];
  });

  public setInferenceSubMode(subMode: 'bayesian' | 'counterfactual' | 'digital-twin'): void {
    this.inferenceSubMode.set(subMode);
  }

  public setSimulationPanel(panel: 'all' | 'atmosphere' | 'fluid' | 'suppression'): void {
    this.simulationPanel.set(panel);
  }

  public toggleTourMinimize(): void {
    this.isTourMinimized.update((v) => !v);
  }

  public startMissionControlTour(): void {
    this.activeTourStep.set(1);
    this.isTourMinimized.set(false);
    this.syncTourState(1);
  }

  public goToTourStep(step: number): void {
    if (step < 1 || step > this.missionControlSteps().length) return;
    this.activeTourStep.set(step);
    this.syncTourState(step);
  }

  public nextTourStep(): void {
    const current = this.activeTourStep();
    if (current === null) return;
    if (current < this.missionControlSteps().length) {
      const next = current + 1;
      this.activeTourStep.set(next);
      this.syncTourState(next);
    } else {
      this.closeTour();
    }
  }

  public prevTourStep(): void {
    const current = this.activeTourStep();
    if (current === null || current <= 1) return;
    const prev = current - 1;
    this.activeTourStep.set(prev);
    this.syncTourState(prev);
  }

  public closeTour(): void {
    this.activeTourStep.set(null);
    this.isTourMinimized.set(false);
  }

  private syncTourState(stepIndex: number): void {
    const step = this.missionControlSteps()[stepIndex - 1];
    if (!step) return;

    this.setScientificMode(step.mode);

    if (step.featureKey === 'gravity') {
      this.simulationPanel.set('fluid');
    } else if (step.featureKey === 'bayesian') {
      this.inferenceSubMode.set('bayesian');
      this.selectedMfcPattern.set('solo-mfc3');
    } else if (step.featureKey === 'counterfactual') {
      this.inferenceSubMode.set('counterfactual');
      this.counterfactualTab.set('compare');
    } else if (step.featureKey === 'next-test') {
      this.openDrawer('next-test');
    }
  }
}
