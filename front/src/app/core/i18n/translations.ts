export interface AppTranslations {
  // Header
  brandCaption: string;
  appsBadge: string;
  freefallBadge: string;
  simMode: string;
  evidenceMode: string;
  inferenceMode: string;
  simModeTitle: string;
  evidenceModeTitle: string;
  inferenceModeTitle: string;
  demoBtn: string;
  demoBtnTitle: string;
  themeToggleTitle: string;
  themeLightAria: string;
  themeDarkAria: string;
  datasetsLabel: string;
  langBtnTitle: string;

  // Viewport 3D
  chamberTitle: string;
  layerAll: string;
  layerFlame: string;
  layerTemp: string;
  layerRad: string;
  layerSoot: string;
  sFlameBadge: string;
  solidBadge: string;
  earthBadge: string;
  vacuumBadge: string;
  exploratoryBadge: string;
  zoomOutTitle: string;
  zoomInTitle: string;
  resetViewTitle: string;
  camOrbit: string;
  camTop: string;
  camSide: string;
  camOscilloscope: string;
  camSensors: string;
  interactionHint: string;
  chartTitle: string;
  chartElapsed: string;
  flameRadiusLabel: string;
  peakTempLabel: string;
  radFluxLabel: string;
  radLossLabel: string;
  extinctionLabel: string;
  footerNasaRef: string;
  sensorPopupTitle: string;
  rawSignalLabel: string;
  calibrationLockTag: string;
  psiSourceFile: string;
  radialDistance: string;

  // Scenario Controls
  consoleTitle: string;
  presetsTitle: string;
  presetSFlame: string;
  presetSaffire: string;
  presetBass: string;
  presetExploration: string;
  presetVacuum: string;
  unitsToggleTitle: string;
  subtabAll: string;
  subtabFluid: string;
  subtabAtmo: string;
  subtabSuppression: string;
  secFluidTitle: string;
  gravityLabel: string;
  gravityHint: string;
  quiescentIss: string;
  nominalIss: string;
  rcsManeuver: string;
  earthConvective: string;
  burnerLabel: string;
  porousSphere: string;
  solidSample: string;
  fuelLabel: string;
  flowVelocityLabel: string;
  flowStatic: string;
  flowBlowoff: string;
  flowDirectionLabel: string;
  concurrentFlow: string;
  opposedFlow: string;
  o2Label: string;
  o2Moc: string;
  o2Saffire: string;
  o2Enriched: string;
  nasaStd6001Unassessed: string;
  chamberPressureLabel: string;
  viewGauge: string;
  viewAbsolute: string;
  vacuumMark: string;
  orionMark: string;
  atmMark: string;
  flightNoteTag: string;
  flightNoteText: string;
  emergencyVentBtn: string;
  vacuumActiveTitle: string;
  vacuumActiveDesc: string;
  repressBtn: string;
  suppressorsTitle: string;
  injectN2: string;
  injectCO2: string;
  exportJson: string;

  // Bayesian & SCM Panel
  bayesianSubtab: string;
  scmSubtab: string;
  digitalTwinSubtab: string;
  bayesianHeader: string;
  selectMfcPattern: string;
  patternSoloMfc3: string;
  patternCoupled: string;
  patternPreflow: string;
  patternRamp: string;
  patternUnsupported: string;
  modelSelectLabel: string;
  probPmt3: string;
  probRad: string;
  probIgnition: string;
  unsupportedAlert: string;
  cptTableTitle: string;
  cptColCondition: string;
  provenanceLabel: string;
  inferenceTypeLabel: string;

  // Counterfactual & Digital Twin
  observedTab: string;
  hypotheticalTab: string;
  compareTab: string;
  observedHeader: string;
  hypotheticalHeader: string;
  compareHeader: string;
  mfc2Consign: string;
  mfc3Consign: string;
  causalBoundsNote: string;
  causalDisclaimer: string;
  discreteEventsLabel: string;
  eventNumber: string;
  calibrationLockActive: string;
  rayClusterBridge: string;
  rayZeroCopyStatus: string;
  taskLatency: string;
  workerStatus: string;

  // Evidence Card & Knowledge Triad
  evidenceCardDirect: string;
  evidenceCardAnalogous: string;
  limitsOfExtrap: string;
  counterfactualAnalysis: string;
  consultEvidenceBtn: string;
  evaluateCounterexampleBtn: string;
  suggestNextTestBtn: string;
  triadKnow: string;
  triadInfer: string;
  triadDontKnow: string;

  // Tour
  tourStep: string;
  tourOf: string;
  tourMode: string;
  tourPrev: string;
  tourNext: string;
  tourEnd: string;
}

export const TRANSLATIONS_EN: AppTranslations = {
  // Header
  brandCaption: 'Probabilistic & Causal Intelligence for Microgravity Combustion · NASA PSI',
  appsBadge: 'NASA Space Apps',
  freefallBadge: 'Flame in Freefall',
  simMode: 'SIMULATION',
  evidenceMode: 'NASA EVIDENCE',
  inferenceMode: 'INFERENCE',
  simModeTitle: '3D simulation and exploratory physical visualization',
  evidenceModeTitle: 'Empirical data and documented measurements from NASA PSI',
  inferenceModeTitle: 'Bayesian networks (BN-01/02/03) and SCM counterfactual engine',
  demoBtn: 'Jury Demo (90s)',
  demoBtnTitle: '90-second guided tour designed for the scientific evaluation jury',
  themeToggleTitle: 'Toggle theme',
  themeLightAria: 'Switch to light mode',
  themeDarkAria: 'Switch to dark mode',
  datasetsLabel: 'Datasets:',
  langBtnTitle: 'Switch application language',

  // Viewport 3D
  chamberTitle: 'Microgravity Combustion Chamber',
  layerAll: 'NASA Optics',
  layerFlame: 'q_chem',
  layerTemp: 'T(r) Field',
  layerRad: 'q_rad Loss',
  layerSoot: 'Soot Y_s',
  sFlameBadge: 's-Flame (ACME)',
  solidBadge: 'Solid Sample',
  earthBadge: '1.0 g (Earth Buoyant)',
  vacuumBadge: 'Space Vacuum (0 kPa)',
  exploratoryBadge: 'EXPLORATORY MODEL ↗',
  zoomOutTitle: 'Zoom out',
  zoomInTitle: 'Zoom in',
  resetViewTitle: 'Reset camera view',
  camOrbit: '3D Orbit',
  camTop: 'Top (90°)',
  camSide: 'Profile',
  camOscilloscope: 'Oscilloscope',
  camSensors: 'Sensors',
  interactionHint: 'Drag 360° · Scroll zoom',
  chartTitle: 'Live Dynamic Flight Telemetry',
  chartElapsed: 's elapsed',
  flameRadiusLabel: 'Flame Radius:',
  peakTempLabel: 'T_flame:',
  radFluxLabel: "q''_rad:",
  radLossLabel: 'Rad. Loss (X_rad):',
  extinctionLabel: 'Extinction Risk:',
  footerNasaRef: 'NASA experimental data C-1998-485 / BASS-II / FLEX / ACME',
  sensorPopupTitle: 'ACME Digital Twin Sensor Probe',
  rawSignalLabel: 'Raw Instrumental Signal:',
  calibrationLockTag: 'CALIBRATION LOCK ACTIVE',
  psiSourceFile: 'PSI-23 Source File:',
  radialDistance: 'Radial Distance:',

  // Scenario Controls
  consoleTitle: 'IGNIS-μ Console (NASA PSI)',
  presetsTitle: 'Presets:',
  presetSFlame: 's-Flame (ACME)',
  presetSaffire: 'Saffire VI',
  presetBass: 'BASS-II',
  presetExploration: 'Exploration',
  presetVacuum: 'Vacuum (0 kPa)',
  unitsToggleTitle: 'Toggle SI / NASA imperial units',
  subtabAll: 'View All',
  subtabFluid: 'Fluid & Gravity',
  subtabAtmo: 'Atmosphere & Pressure',
  subtabSuppression: 'Suppression & Safety',
  secFluidTitle: 'Fluid Dynamics & Effective Gravity',
  gravityLabel: 'Gravitational environment (g-Jitter / Convection)',
  gravityHint: 'Symmetric spherical diffusion (microgravity) vs elongated buoyant plume (NASA C-1998-485).',
  quiescentIss: 'ISS Quiescent',
  nominalIss: 'ISS Nominal',
  rcsManeuver: 'RCS Maneuver',
  earthConvective: 'Earth Buoyant',
  burnerLabel: 'Experimental apparatus (NASA ACME / Saffire)',
  porousSphere: 'Porous Sphere (s-Flame)',
  solidSample: 'Solid Sample',
  fuelLabel: 'Fuel material (NASA Flight Qualified)',
  flowVelocityLabel: 'Forced ventilation velocity',
  flowStatic: '0 (Static - Radiative Quench)',
  flowBlowoff: '35 cm/s (Blow-off Risk)',
  flowDirectionLabel: 'Oxidant flow direction',
  concurrentFlow: 'Concurrent (Wake preheating)',
  opposedFlow: 'Opposed (Frontal dissipation)',
  o2Label: 'O₂ Concentration (Molar)',
  o2Moc: '18% (MOC Limit)',
  o2Saffire: '30% (Saffire VI)',
  o2Enriched: '38% (Enriched)',
  nasaStd6001Unassessed: 'NASA-STD-6001 · COMPLIANCE NOT ASSESSED',
  chamberPressureLabel: 'Chamber / cabin pressure',
  viewGauge: 'View Gauge (ΔP)',
  viewAbsolute: 'View Absolute',
  vacuumMark: '0 kPa (Vacuum)',
  orionMark: '55 kPa (Orion/Saffire Cabin)',
  atmMark: '101.3 kPa (1 atm)',
  flightNoteTag: '[FLIGHT_NOTE]',
  flightNoteText: 'In microgravity (ISS-MSG), chamber maintains passive negative differential (ΔP ≈ -0.5 kPa) to prevent combustion toxins leaking to crew cabin.',
  emergencyVentBtn: 'Emergency Space Vacuum Purge (0.0 kPa · ΔP: -101.3 kPa · Quench)',
  vacuumActiveTitle: '[CHAMBER PURGED TO SPACE VACUUM]',
  vacuumActiveDesc: 'Outer vent valve open. Pressure = 0 kPa. Flame extinguished instantly by explosive decompression.',
  repressBtn: 'Restore Cabin Pressurization (55 kPa)',
  suppressorsTitle: 'Suppressant Injection:',
  injectN2: 'Inject N₂',
  injectCO2: 'Inject CO₂',
  exportJson: 'Export (JSON)',

  // Bayesian & SCM Panel
  bayesianSubtab: 'Live Bayesian (BN)',
  scmSubtab: 'Factual vs Counterfactual',
  digitalTwinSubtab: 'Digital Twin 20013D1',
  bayesianHeader: 'Live Bayesian Inference Engine',
  selectMfcPattern: 'Mass Flow Controller (MFC) Pattern:',
  patternSoloMfc3: 'Solo MFC3 positive',
  patternCoupled: 'MFC2 + MFC3 coupled',
  patternPreflow: 'Preflow low regime',
  patternRamp: 'High ramp excitation',
  patternUnsupported: 'Unsampled continuous state',
  modelSelectLabel: 'Structural Model:',
  probPmt3: 'Probability of High PMT3 (OH*):',
  probRad: 'Probability of High Radiometer Flux:',
  probIgnition: 'Posterior Ignition Probability:',
  unsupportedAlert: 'Prediction unavailable: continuous slider coordinates fall outside empirical sample support in training CPTs.',
  cptTableTitle: 'Active Conditional Probability Table (CPT)',
  cptColCondition: 'Parent Condition',
  provenanceLabel: 'Provenance:',
  inferenceTypeLabel: 'Inference Type:',

  // Counterfactual & Digital Twin
  observedTab: 'OBSERVED',
  hypotheticalTab: 'HYPOTHETICAL',
  compareTab: 'COMPARE',
  observedHeader: 'Empirical NASA 20013D1 Observation',
  hypotheticalHeader: 'Structural Intervention do(MFC)',
  compareHeader: 'SCM Model Comparison & Honest Bounds',
  mfc2Consign: 'MFC2 Inflow Setpoint:',
  mfc3Consign: 'MFC3 Inflow Setpoint:',
  causalBoundsNote: 'Identified coupling bounds over observational distributions under structural SCM assumptions.',
  causalDisclaimer: 'Causal effect not identified: interval reflects epistemic coupling bounds, not an experimentally demonstrated physical certainty.',
  discreteEventsLabel: 'Discrete MFC2/MFC3 Events in Volts [V] (20013D1_mfcSetpoints.csv):',
  eventNumber: 'Event',
  calibrationLockActive: 'CALIBRATION LOCK: Voltage [V] to Mass Flow [kg/s] not calibrated. Continuous interpolation disabled.',
  rayClusterBridge: 'Ray Zero-Copy Swarm Bridge',
  rayZeroCopyStatus: 'Ray Zero-Copy Shared Memory: READY (64 MB Ring Buffer)',
  taskLatency: 'Distributed LOJO Task Latency: 38ms',
  workerStatus: 'Worker VM3 (Spacecraft Flight Node): Synced with Supabase PSI-23',

  // Evidence Card & Knowledge Triad
  evidenceCardDirect: 'Direct Evidence:',
  evidenceCardAnalogous: 'Analogous Evidence:',
  limitsOfExtrap: 'Limits of Extrapolation',
  counterfactualAnalysis: 'Counterfactual Analysis:',
  consultEvidenceBtn: 'Inspect Experimental Evidence',
  evaluateCounterexampleBtn: 'Evaluate Counterexample',
  suggestNextTestBtn: 'Suggest Next Experiment',
  triadKnow: 'WHAT WE KNOW',
  triadInfer: 'WHAT WE INFER',
  triadDontKnow: "WHAT WE DON'T KNOW",

  // Tour
  tourStep: 'STEP',
  tourOf: 'OF',
  tourMode: 'Mode:',
  tourPrev: '← Previous',
  tourNext: 'Next Step →',
  tourEnd: 'Finish Demo',
};

export const TRANSLATIONS_ES: AppTranslations = {
  // Header
  brandCaption: 'Inteligencia Probabilística y Causal para Combustión en Microgravedad · NASA PSI',
  appsBadge: 'NASA Space Apps',
  freefallBadge: 'Flame in Freefall',
  simMode: 'SIMULACIÓN',
  evidenceMode: 'EVIDENCIA NASA',
  inferenceMode: 'INFERENCIA',
  simModeTitle: 'Simulación 3D y exploración física ilustrativa',
  evidenceModeTitle: 'Condiciones y mediciones empíricas documentadas en NASA PSI',
  inferenceModeTitle: 'Modelos bayesianos (BN-01/02/03) y comparador contrafactual SCM',
  demoBtn: 'Demo Jurado (90s)',
  demoBtnTitle: 'Recorrido guiado de 90 segundos para el jurado evaluador',
  themeToggleTitle: 'Cambiar tema',
  themeLightAria: 'Activar modo claro',
  themeDarkAria: 'Activar modo oscuro',
  datasetsLabel: 'Datasets:',
  langBtnTitle: 'Alternar idioma de la aplicación',

  // Viewport 3D
  chamberTitle: 'Cámara de Combustión en Microgravedad',
  layerAll: 'Óptica NASA',
  layerFlame: 'q_chem',
  layerTemp: 'Campo T(r)',
  layerRad: 'Pérdida q_rad',
  layerSoot: 'Hollín Y_s',
  sFlameBadge: 's-Flame (ACME)',
  solidBadge: 'Muestra Sólida',
  earthBadge: '1.0 g (Tierra Convectiva)',
  vacuumBadge: 'Purga a Vacío (0 kPa)',
  exploratoryBadge: 'MODELO ILUSTRATIVO ↗',
  zoomOutTitle: 'Alejar',
  zoomInTitle: 'Acercar',
  resetViewTitle: 'Restablecer vista',
  camOrbit: '3D Órbita',
  camTop: 'Cenital (90°)',
  camSide: 'Perfil',
  camOscilloscope: 'Osciloscopio',
  camSensors: 'Sensores',
  interactionHint: 'Arrastra 360° · Rueda zoom',
  chartTitle: 'Telemetría Dinámica de Vuelo (En Vivo)',
  chartElapsed: 's transcurridos',
  flameRadiusLabel: 'Radio Llama:',
  peakTempLabel: 'T_flame:',
  radFluxLabel: "q''_rad:",
  radLossLabel: 'Pérdida Rad. (X_rad):',
  extinctionLabel: 'Riesgo Extinción:',
  footerNasaRef: 'Datos experimentales NASA C-1998-485 / BASS-II / FLEX / ACME',
  sensorPopupTitle: 'Sonda Instrumental Gemelo Digital ACME',
  rawSignalLabel: 'Señal Instrumental Cruda:',
  calibrationLockTag: 'CANDADO DE CALIBRACIÓN ACTIVO',
  psiSourceFile: 'Archivo Fuente PSI-23:',
  radialDistance: 'Distancia Radial:',

  // Scenario Controls
  consoleTitle: 'Consola IGNIS-μ (NASA PSI)',
  presetsTitle: 'Preajustes:',
  presetSFlame: 's-Flame (ACME)',
  presetSaffire: 'Saffire VI',
  presetBass: 'BASS-II',
  presetExploration: 'Exploración',
  presetVacuum: 'Vacío (0 kPa)',
  unitsToggleTitle: 'Alternar unidades SI / NASA',
  subtabAll: 'Ver Todo',
  subtabFluid: 'Fluido & Gravedad',
  subtabAtmo: 'Atmósfera & Presión',
  subtabSuppression: 'Supresión & Seg.',
  secFluidTitle: 'Fluidodinámica & Gravedad Efectiva',
  gravityLabel: 'Entorno gravitatorio (g-Jitter / Convección)',
  gravityHint: 'Difusión esférica simétrica (microgravedad) vs penacho boyante alargado (NASA C-1998-485).',
  quiescentIss: 'ISS Quiesc.',
  nominalIss: 'ISS Nominal',
  rcsManeuver: 'Maniobra RCS',
  earthConvective: 'Tierra Boyante',
  burnerLabel: 'Aparato experimental (NASA ACME / Saffire)',
  porousSphere: 'Esfera Porosa (s-Flame)',
  solidSample: 'Muestra Sólida',
  fuelLabel: 'Material combustible (NASA Flight Qualified)',
  flowVelocityLabel: 'Velocidad de ventilación forzada',
  flowStatic: '0 (Estático - Apagado radiativo)',
  flowBlowoff: '35 cm/s (Riesgo blow-off)',
  flowDirectionLabel: 'Dirección del flujo de oxidante',
  concurrentFlow: 'Concurrente (Precalentamiento)',
  opposedFlow: 'Opuesto (Disipación frontal)',
  o2Label: 'Concentración de O₂ (Molar)',
  o2Moc: '18% (Límite MOC)',
  o2Saffire: '30% (Saffire VI)',
  o2Enriched: '38% (Enriquecido)',
  nasaStd6001Unassessed: 'NASA-STD-6001 · COMPLIANCE NOT ASSESSED',
  chamberPressureLabel: 'Presión de cámara / cabina',
  viewGauge: 'Ver Manométrica (ΔP)',
  viewAbsolute: 'Ver Absoluta',
  vacuumMark: '0 kPa (Vacío)',
  orionMark: '55 kPa (Cabina Orion/Saffire)',
  atmMark: '101.3 kPa (1 atm)',
  flightNoteTag: '[FLIGHT_NOTE]',
  flightNoteText: 'En microgravedad (ISS-MSG), la cámara opera con diferencial negativo pasivo (ΔP ≈ -0.5 kPa) para retener productos de combustión en caso de fuga.',
  emergencyVentBtn: 'Purga al Vacío Espacial (0.0 kPa · ΔP: -101.3 kPa · Extinción)',
  vacuumActiveTitle: '[CÁMARA PURGADA AL VACÍO ESPACIAL]',
  vacuumActiveDesc: 'Válvula exterior abierta. Presión = 0 kPa. Llama extinguida instantáneamente por descompresión explosiva.',
  repressBtn: 'Restablecer Presurización de Cabina (55 kPa)',
  suppressorsTitle: 'Inyección de Supresores:',
  injectN2: 'Inyectar N₂',
  injectCO2: 'Inyectar CO₂',
  exportJson: 'Exportar (JSON)',

  // Bayesian & SCM Panel
  bayesianSubtab: 'Live Bayesian (BN)',
  scmSubtab: 'Factual vs Contrafactual',
  digitalTwinSubtab: 'Gemelo Digital 20013D1',
  bayesianHeader: 'Motor de Inferencia Bayesiana en Vivo',
  selectMfcPattern: 'Patrón de Flujo Másico (MFC):',
  patternSoloMfc3: 'Solo MFC3 positivo',
  patternCoupled: 'MFC2 + MFC3 acoplados',
  patternPreflow: 'Régimen bajo pre-flujo',
  patternRamp: 'Excitación rampa alta',
  patternUnsupported: 'Estado continuo no muestreado',
  modelSelectLabel: 'Modelo Estructural:',
  probPmt3: 'Probabilidad de PMT3 Alto (OH*):',
  probRad: 'Probabilidad de Radiómetro Alto:',
  probIgnition: 'Probabilidad Posterior de Ignición:',
  unsupportedAlert: 'Predicción no disponible: los valores continuos seleccionados caen fuera del soporte muestral de las CPTs.',
  cptTableTitle: 'Tabla de Probabilidad Condicional Activa (CPT)',
  cptColCondition: 'Condición Padre',
  provenanceLabel: 'Procedencia:',
  inferenceTypeLabel: 'Tipo de Inferencia:',

  // Counterfactual & Digital Twin
  observedTab: 'OBSERVED',
  hypotheticalTab: 'HYPOTHETICAL',
  compareTab: 'COMPARE',
  observedHeader: 'Observación Empírica NASA 20013D1',
  hypotheticalHeader: 'Intervención Estructural do(MFC)',
  compareHeader: 'Comparación de Modelos SCM y Cotas Honestas',
  mfc2Consign: 'Consigna de Inyección MFC2:',
  mfc3Consign: 'Consigna de Inyección MFC3:',
  causalBoundsNote: 'Cotas de acoplamiento identificadas sobre distribuciones observacionales bajo supuestos estructurales del SCM.',
  causalDisclaimer: 'Efecto causal no identificado: el intervalo refleja cotas de acoplamiento epistémico y no una certeza física demostrada.',
  discreteEventsLabel: 'Eventos Discretos MFC2/MFC3 en Voltios [V] (20013D1_mfcSetpoints.csv):',
  eventNumber: 'Evento',
  calibrationLockActive: 'CANDADO ACTIVO: Calibración Voltios [V] a Flujo Másico [kg/s] no verificada. Interpolación continua deshabilitada.',
  rayClusterBridge: 'Puente Swarm Ray Zero-Copy',
  rayZeroCopyStatus: 'Memoria Compartida Ray Zero-Copy: ACTIVO (Ring Buffer de 64 MB)',
  taskLatency: 'Latencia Tareas Distribuidas LOJO: 38ms',
  workerStatus: 'Worker VM3 (Nodo de Vuelo Spacecraft): Sincronizado con Supabase PSI-23',

  // Evidence Card & Knowledge Triad
  evidenceCardDirect: 'Evidencia Directa:',
  evidenceCardAnalogous: 'Evidencia Análoga:',
  limitsOfExtrap: 'Límites de Extrapolación',
  counterfactualAnalysis: 'Análisis Contrafactual:',
  consultEvidenceBtn: 'Consultar Evidencia Experimental',
  evaluateCounterexampleBtn: 'Evaluar Contraejemplo Físico',
  suggestNextTestBtn: 'Sugerir Siguiente Ensayo',
  triadKnow: 'LO QUE SABEMOS',
  triadInfer: 'LO QUE INFERIMOS',
  triadDontKnow: 'LO QUE NO SABEMOS',

  // Tour
  tourStep: 'PASO',
  tourOf: 'DE',
  tourMode: 'Modo:',
  tourPrev: '← Anterior',
  tourNext: 'Siguiente Paso →',
  tourEnd: 'Finalizar Demo',
};
