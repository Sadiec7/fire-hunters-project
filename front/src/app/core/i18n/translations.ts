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
  netThermalBalanceLabel: string;
  radFluxLabel: string;
  radLossLabel: string;
  extinctionLabel: string;
  untestedLabel: string;
  modelM1: string;
  modelM2: string;
  modelM3: string;
  colObserved: string;
  colHypotheticalScm: string;
  colDiffDelta: string;
  viewWhyBtn: string;
  genBriefBtn: string;
  closePassportBtn: string;
  openPsiRecordBtn: string;
  loadParamsBtn: string;
  refutabilityTitle: string;
  refutabilityDesc: string;
  counterexampleDetected: string;
  predForScenario: string;
  sustainedSpread: string;
  actualOutcome: string;
  whyDiffOccurred: string;
  examineBassBtn: string;
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
  secAtmoTitle: string;
  secSuppressionTitle: string;
  gravityLabel: string;
  gravityHint: string;
  quiescentIss: string;
  nominalIss: string;
  rcsManeuver: string;
  earthConvective: string;
  burnerLabel: string;
  porousSphere: string;
  solidSample: string;
  burnerSFlameOption: string;
  burnerSolidOption: string;
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
  o2Hint: string;
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
  modelBn01: string;
  modelBn02: string;
  modelBn03: string;
  probPmt3: string;
  probRad: string;
  probIgnition: string;
  unsupportedAlert: string;
  cptTableTitle: string;
  cptColCondition: string;
  provenanceLabel: string;
  inferenceTypeLabel: string;
  colInfo: string;
  colResult: string;
  colVarSelected: string;
  colStateSelected: string;
  colModel: string;
  colInferenceTypeVal: string;

  // Counterfactual & Digital Twin
  observedTab: string;
  hypotheticalTab: string;
  compareTab: string;
  observedHeader: string;
  hypotheticalHeader: string;
  compareHeader: string;
  treatmentRegistered: string;
  instrumentalChannel: string;
  observedRawVal: string;
  colUnit: string;
  calibrationStatus: string;
  calibrationLockChip: string;
  hypoIntervention: string;
  selectedScmModelLabel: string;
  mfc2Consign: string;
  mfc3Consign: string;
  projectedUnderDo: string;
  modelComparisonLabel: string;
  honestBoundsLabel: string;
  causalBoundsNote: string;
  causalDisclaimer: string;
  discreteEventsLabel: string;
  eventNumber: string;
  calibrationLockActive: string;
  rayClusterBridge: string;
  rayZeroCopyStatus: string;
  taskLatency: string;
  workerStatus: string;
  sensorMatrixHeader: string;
  physicsAuditHeader: string;

  // NASA Evidence Catalog (View C)
  evidenceCatalogTitle: string;
  evidenceCatalogDesc: string;
  trial42Events: string;
  trial20013d1Desc: string;
  trialFileLabel: string;
  session20176: string;
  trial16Trials: string;
  trialMaxCausal: string;
  trial20176Desc: string;
  trialAteShift: string;
  trialSolidComb: string;
  trialSaffireDesc: string;
  trialSamplesLabel: string;
  trialFlowLabel: string;

  // Evidence Card & Knowledge Triad
  evidenceCardStatus: string;
  evidenceCardConfidence: string;
  evidenceCardHeatRelease: string;
  evidenceCardCO: string;
  evidenceCardCO2: string;
  pipelineTitle: string;
  pipelineSub: string;
  step01Input: string;
  step02Mech: string;
  step03Obs: string;
  step04Outcome: string;
  evidenceCardDirect: string;
  evidenceCardAnalogous: string;
  limitsOfExtrap: string;
  counterfactualAnalysis: string;
  runCounterfactualBtn: string;
  consultEvidenceBtn: string;
  evaluateCounterexampleBtn: string;
  suggestNextTestBtn: string;
  triadHeadlineTitle: string;
  triadHeadlineSub: string;
  triadKnow: string;
  triadInfer: string;
  triadDontKnow: string;

  // Action Drawers
  drawerTraceabilityTitle: string;
  drawerChallengeTitle: string;
  drawerNextTestTitle: string;
  drawerEvidenceIntro: string;
  drawerPassportTitle: string;
  drawerPassportSub: string;
  passportIdLabel: string;
  passportInvestLabel: string;
  passportObsVarLabel: string;
  passportSourceLabel: string;
  passportTransformLabel: string;
  passportModelLabel: string;
  passportLimitsLabel: string;

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
  flameRadiusLabel: 'Flame Radius r_f',
  peakTempLabel: 'T_max',
  netThermalBalanceLabel: 'Net Balance',
  radFluxLabel: "q''_rad:",
  radLossLabel: 'Rad. Loss (X_rad):',
  extinctionLabel: 'Extinction',
  untestedLabel: 'UNTESTED',
  modelM1: 'M1 (Linear Coupling)',
  modelM2: 'M2 (Thermophoretic Saturation)',
  modelM3: 'M3 (Radiative Feedback)',
  colObserved: 'Observed',
  colHypotheticalScm: 'Hypothetical (SCM)',
  colDiffDelta: 'Difference Δ',
  viewWhyBtn: 'Why this experiment?',
  genBriefBtn: 'Generate Research Brief',
  closePassportBtn: 'Close Passport',
  openPsiRecordBtn: 'Consult Official NASA PSI Record',
  loadParamsBtn: 'Load parameters into simulation',
  refutabilityTitle: 'Scientific refutability criterion:',
  refutabilityDesc: 'The system queries the historical repository for the nearest trial where apparent identical conditions yielded an opposite outcome.',
  counterexampleDetected: 'Counterexample detected',
  predForScenario: 'Prediction for your scenario:',
  sustainedSpread: 'Sustained spread',
  actualOutcome: 'Actual outcome of this trial:',
  whyDiffOccurred: 'Why did the physical difference occur?',
  examineBassBtn: 'Examine in BASS-II (PSI-25)',
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
  secAtmoTitle: 'Fuel, Oxidizer & Pressure',
  secSuppressionTitle: 'Suppressant Injection & Telemetry',
  gravityLabel: 'Gravitational environment (g-Jitter / Convection)',
  gravityHint: 'Symmetric spherical diffusion (microgravity) vs elongated buoyant plume (NASA C-1998-485).',
  quiescentIss: 'ISS Quiescent',
  nominalIss: 'ISS Nominal',
  rcsManeuver: 'RCS Maneuver',
  earthConvective: 'Earth Buoyant',
  burnerLabel: 'Experimental apparatus (NASA ACME / Saffire)',
  porousSphere: 'Porous Sphere (s-Flame)',
  solidSample: 'Solid Sample',
  burnerSFlameOption: 's-Flame Spherical Burner (ACME)',
  burnerSolidOption: 'Solid Sample (BASS / Saffire)',
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
  o2Hint: 'NASA Criterion: Flammability depends on oxygen partial pressure P_O₂ (oxidizer molar density).',
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
  bayesianSubtab: 'Bayesian (BN)',
  scmSubtab: 'SCM Causal',
  digitalTwinSubtab: 'Digital Twin',
  bayesianHeader: 'Live Bayesian Inference Engine',
  selectMfcPattern: 'Mass Flow Controller (MFC) Pattern:',
  patternSoloMfc3: 'Solo MFC3 positive',
  patternCoupled: 'MFC2 + MFC3 coupled',
  patternPreflow: 'Preflow low regime',
  patternRamp: 'High ramp excitation',
  patternUnsupported: 'Unsampled continuous state',
  modelSelectLabel: 'Structural Model:',
  modelBn01: 'BN-01 (Injection & Chemilum.)',
  modelBn02: 'BN-02 (Cool Flame)',
  modelBn03: 'BN-03 (E-Field)',
  probPmt3: 'Probability of High PMT3 (OH*):',
  probRad: 'Probability of High Radiometer Flux:',
  probIgnition: 'Posterior Ignition Probability:',
  unsupportedAlert: 'Prediction unavailable: continuous slider coordinates fall outside empirical sample support in training CPTs.',
  cptTableTitle: 'Active Conditional Probability Table (CPT)',
  cptColCondition: 'Parent Condition',
  provenanceLabel: 'Provenance:',
  inferenceTypeLabel: 'Inference Type:',
  colInfo: 'Information',
  colResult: 'Result',
  colVarSelected: 'Selected Variable',
  colStateSelected: 'Selected State',
  colModel: 'Model',
  colInferenceTypeVal: 'Conditional, observational',

  // Counterfactual & Digital Twin
  observedTab: 'OBSERVED',
  hypotheticalTab: 'HYPOTHETICAL',
  compareTab: 'COMPARE',
  observedHeader: 'Empirical NASA 20013D1 Observation',
  hypotheticalHeader: 'Structural Intervention do(MFC)',
  compareHeader: 'SCM Model Comparison & Honest Bounds',
  treatmentRegistered: 'Registered Instrumental Treatment:',
  instrumentalChannel: 'Instrumental Channel',
  observedRawVal: 'Observed Raw Value',
  colUnit: 'Unit',
  calibrationStatus: 'Calibration Status',
  calibrationLockChip: 'Calibration Lock',
  hypoIntervention: 'Hypothetical Structural Intervention:',
  selectedScmModelLabel: 'Selected SCM Model:',
  mfc2Consign: 'do(MFC2) Scaling:',
  mfc3Consign: 'do(MFC3) Scaling:',
  projectedUnderDo: 'Projected Values under do(MFC):',
  modelComparisonLabel: 'Structural Comparison of Models M1, M2 & M3:',
  honestBoundsLabel: 'Honest Coupling Bounds:',
  causalBoundsNote: 'Identified coupling bounds over observational distributions under structural SCM assumptions.',
  causalDisclaimer: 'Causal effect not identified: interval reflects epistemic coupling bounds, not an experimentally demonstrated physical certainty.',
  discreteEventsLabel: 'Discrete MFC2/MFC3 Events in Volts [V] (20013D1_mfcSetpoints.csv):',
  eventNumber: 'Event',
  calibrationLockActive: 'CALIBRATION LOCK: Voltage [V] to Mass Flow [kg/s] not calibrated. Continuous interpolation disabled.',
  rayClusterBridge: 'Ray Zero-Copy Swarm Bridge',
  rayZeroCopyStatus: 'Ray Zero-Copy Shared Memory: READY (64 MB Ring Buffer)',
  taskLatency: 'Distributed LOJO Task Latency: 38ms',
  workerStatus: 'Worker VM3 (Spacecraft Flight Node): Synced with Supabase PSI-23',
  sensorMatrixHeader: 'NASA PSI-23 Instrumental Sensors (acme_geometry_manifest.json)',
  physicsAuditHeader: 'Burke-Schumann Thermodynamic & RTE Radiation Audit (ia/solver_3d.py)',

  // NASA Evidence Catalog (View C)
  evidenceCatalogTitle: 'Microgravity Combustion Experimental Trials Catalog',
  evidenceCatalogDesc: 'Raw, unmodified open data from NASA Physical Sciences Informatics. 282 s-Flame trials across 18 operational ISS sessions.',
  trial42Events: '42 Reconstructed Events',
  trial20013d1Desc: 'Stepped voltage setpoints for MFC2 and MFC3 with 6-channel acquisition in stable microgravity.',
  trialFileLabel: 'File:',
  session20176: 'Session 20176',
  trial16Trials: '16 Trials',
  trialMaxCausal: 'Highest Causal Influence',
  trial20176Desc: 'Asymmetric injection in ultralow flow; its exclusion increases validation RMSE by 194%.',
  trialAteShift: 'ATE Shift:',
  trialSolidComb: 'Solid Combustion',
  trialSaffireDesc: 'Large-scale flight tests on unmanned Cygnus spacecraft prior to atmospheric reentry.',
  trialSamplesLabel: 'Samples: PMMA and SIBAL',
  trialFlowLabel: 'Forced flow: 20 cm/s',

  // Evidence Card & Knowledge Triad
  evidenceCardStatus: 'STATUS:',
  evidenceCardConfidence: 'BAYESIAN CONFIDENCE:',
  evidenceCardHeatRelease: 'HEAT RELEASE (HRR)',
  evidenceCardCO: 'CARBON MONOXIDE (CO)',
  evidenceCardCO2: 'CARBON DIOXIDE (CO₂)',
  pipelineTitle: 'MECHANISTIC INFERENCE PIPELINE (INTERACTIVE)',
  pipelineSub: 'Click on a stage to display thermal balance equations',
  step01Input: 'INPUT',
  step02Mech: 'MECHANISM',
  step03Obs: 'OBSERVATION',
  step04Outcome: 'OUTCOME',
  evidenceCardDirect: 'Direct Evidence:',
  evidenceCardAnalogous: 'Analogous Evidence:',
  limitsOfExtrap: 'Limits of Extrapolation',
  counterfactualAnalysis: 'Counterfactual Analysis:',
  runCounterfactualBtn: 'EXECUTE COUNTERFACTUAL IN SIMULATION',
  consultEvidenceBtn: 'Inspect Experimental Evidence',
  evaluateCounterexampleBtn: 'Evaluate Counterexample',
  suggestNextTestBtn: 'Suggest Next Experiment',
  triadHeadlineTitle: 'Scientific Certainty Triad',
  triadHeadlineSub: 'Strict differentiation between direct measurements and theoretical models',
  triadKnow: 'WHAT WE KNOW (EMPIRICAL)',
  triadInfer: 'WHAT WE INFER (CAUSAL)',
  triadDontKnow: "WHAT WE DON'T KNOW (FRONTIER)",

  // Action Drawers
  drawerTraceabilityTitle: 'Experimental Traceability · NASA PSI',
  drawerChallengeTitle: 'Physical Counterexample Engine · Refutability',
  drawerNextTestTitle: 'Next Experimental Trial · Active Learning',
  drawerEvidenceIntro: 'Each deduction in IGNIS-μ is mapped against physical measurements from the NASA Physical Sciences Informatics (PSI) repository. Verifiable open data:',
  drawerPassportTitle: 'EVIDENCE PASSPORT · NASA PSI',
  drawerPassportSub: 'Provenance, Cryptography & Scientific Integrity of Deduction',
  passportIdLabel: 'Master Identifier:',
  passportInvestLabel: 'PSI Investigation:',
  passportObsVarLabel: 'Observed Variable:',
  passportSourceLabel: 'Source File:',
  passportTransformLabel: 'Transformation Applied:',
  passportModelLabel: 'Model Used:',
  passportLimitsLabel: 'Epistemic Limitations:',

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
  flameRadiusLabel: 'Radio Llama r_f',
  peakTempLabel: 'T_max',
  netThermalBalanceLabel: 'Balance Neto',
  radFluxLabel: "q''_rad:",
  radLossLabel: 'Pérdida Rad. (X_rad):',
  extinctionLabel: 'Extinción',
  untestedLabel: 'NO_ENSAYADO',
  modelM1: 'M1 (Acoplamiento Lineal)',
  modelM2: 'M2 (Saturación Termoforética)',
  modelM3: 'M3 (Retroalimentación Radiativa)',
  colObserved: 'Observado',
  colHypotheticalScm: 'Hipotético (SCM)',
  colDiffDelta: 'Diferencia Δ',
  viewWhyBtn: '¿Por qué este experimento?',
  genBriefBtn: 'Generar Ficha Experimental',
  closePassportBtn: 'Cerrar Pasaporte',
  openPsiRecordBtn: 'Consultar Registro Oficial en NASA PSI',
  loadParamsBtn: 'Cargar parámetros en la simulación',
  refutabilityTitle: 'Criterio de refutabilidad científica:',
  refutabilityDesc: 'El sistema busca el ensayo más cercano en el archivo histórico donde las mismas condiciones aparentes produjeron un resultado opuesto.',
  counterexampleDetected: 'Contraejemplo detectado',
  predForScenario: 'Predicción para tu escenario:',
  sustainedSpread: 'Propagación sostenida',
  actualOutcome: 'Resultado real de este ensayo:',
  whyDiffOccurred: '¿Por qué ocurrió la diferencia física?',
  examineBassBtn: 'Examinar en BASS-II (PSI-25)',
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
  secAtmoTitle: 'Combustible, Oxidante y Presión',
  secSuppressionTitle: 'Inyección de Supresores y Telemetría',
  gravityLabel: 'Entorno gravitatorio (g-Jitter / Convección)',
  gravityHint: 'Difusión esférica simétrica (microgravedad) vs penacho boyante alargado (NASA C-1998-485).',
  quiescentIss: 'ISS Quiesc.',
  nominalIss: 'ISS Nominal',
  rcsManeuver: 'Maniobra RCS',
  earthConvective: 'Tierra Boyante',
  burnerLabel: 'Aparato experimental (NASA ACME / Saffire)',
  porousSphere: 'Esfera Porosa (s-Flame)',
  solidSample: 'Muestra Sólida',
  burnerSFlameOption: 'Quemador Esférico s-Flame (ACME)',
  burnerSolidOption: 'Muestra Sólida (BASS / Saffire)',
  fuelLabel: 'Material de ensayo (NASA PSI Flight Qualified)',
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
  o2Hint: 'Criterio NASA: La inflamabilidad depende de la presión parcial P_O₂ (densidad molar de oxidante).',
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
  bayesianSubtab: 'Bayesiano (BN)',
  scmSubtab: 'SCM Causal',
  digitalTwinSubtab: 'Gemelo Digital',
  bayesianHeader: 'Motor de Inferencia Bayesiana en Vivo',
  selectMfcPattern: 'Patrón de Flujo Másico (MFC):',
  patternSoloMfc3: 'Solo MFC3 positivo',
  patternCoupled: 'MFC2 + MFC3 acoplados',
  patternPreflow: 'Régimen bajo pre-flujo',
  patternRamp: 'Excitación rampa alta',
  patternUnsupported: 'Estado continuo no muestreado',
  modelSelectLabel: 'Modelo Estructural:',
  modelBn01: 'BN-01 (Inyección & Quimiolum.)',
  modelBn02: 'BN-02 (Llama Fría)',
  modelBn03: 'BN-03 (Campo E-Field)',
  probPmt3: 'Probabilidad de PMT3 Alto (OH*):',
  probRad: 'Probabilidad de Radiómetro Alto:',
  probIgnition: 'Probabilidad Posterior de Ignición:',
  unsupportedAlert: 'Predicción no disponible: los valores continuos seleccionados caen fuera del soporte muestral de las CPTs.',
  cptTableTitle: 'Tabla de Probabilidad Condicional Activa (CPT)',
  cptColCondition: 'Condición Padre',
  provenanceLabel: 'Procedencia:',
  inferenceTypeLabel: 'Tipo de Inferencia:',
  colInfo: 'Información',
  colResult: 'Resultado',
  colVarSelected: 'Variable seleccionada',
  colStateSelected: 'Estado seleccionado',
  colModel: 'Modelo',
  colInferenceTypeVal: 'Condicional, observacional',

  // Counterfactual & Digital Twin
  observedTab: 'OBSERVED',
  hypotheticalTab: 'HYPOTHETICAL',
  compareTab: 'COMPARE',
  observedHeader: 'Observación Empírica NASA 20013D1',
  hypotheticalHeader: 'Intervención Estructural do(MFC)',
  compareHeader: 'Comparación de Modelos SCM y Cotas Honestas',
  treatmentRegistered: 'Tratamiento Instrumental Registrado:',
  instrumentalChannel: 'Canal Instrumental',
  observedRawVal: 'Valor Crudo Observado',
  colUnit: 'Unidad',
  calibrationStatus: 'Estado de Calibración',
  calibrationLockChip: 'Bloqueo de Calibración',
  hypoIntervention: 'Intervención Estructural Hipotética:',
  selectedScmModelLabel: 'Modelo SCM Seleccionado:',
  mfc2Consign: 'Escalamiento do(MFC2):',
  mfc3Consign: 'Escalamiento do(MFC3):',
  projectedUnderDo: 'Valores Proyectados bajo do(MFC):',
  modelComparisonLabel: 'Comparación Estructural de Modelos M1, M2 y M3:',
  honestBoundsLabel: 'Cotas de Acoplamiento Honestadas:',
  causalBoundsNote: 'Cotas de acoplamiento identificadas sobre distribuciones observacionales bajo supuestos estructurales del SCM.',
  causalDisclaimer: 'Efecto causal no identificado: el intervalo refleja cotas de acoplamiento epistémico y no una certeza física demostrada.',
  discreteEventsLabel: 'Eventos Discretos MFC2/MFC3 en Voltios [V] (20013D1_mfcSetpoints.csv):',
  eventNumber: 'Evento',
  calibrationLockActive: 'CANDADO ACTIVO: Calibración Voltios [V] a Flujo Másico [kg/s] no verificada. Interpolación continua deshabilitada.',
  rayClusterBridge: 'Puente Swarm Ray Zero-Copy',
  rayZeroCopyStatus: 'Memoria Compartida Ray Zero-Copy: ACTIVO (Ring Buffer de 64 MB)',
  taskLatency: 'Latencia Tareas Distribuidas LOJO: 38ms',
  workerStatus: 'Worker VM3 (Nodo de Vuelo Spacecraft): Sincronizado con Supabase PSI-23',
  sensorMatrixHeader: 'Sensores Instrumentales NASA PSI-23 (acme_geometry_manifest.json)',
  physicsAuditHeader: 'Auditoría Termodinámica Burke-Schumann y Radiación RTE (ia/solver_3d.py)',

  // NASA Evidence Catalog (View C)
  evidenceCatalogTitle: 'Catálogo de Ensayos Experimentales de Combustión en Microgravedad',
  evidenceCatalogDesc: 'Datos abiertos no modificados provenientes del NASA Physical Sciences Informatics. 282 ensayos de s-Flame en 18 jornadas operativas en la ISS.',
  trial42Events: '42 Eventos Reconstruidos',
  trial20013d1Desc: 'Consignas escalonadas de voltajes MFC2 y MFC3 con adquisición de 6 canales en microgravedad estable.',
  trialFileLabel: 'Archivo:',
  session20176: 'Jornada 20176',
  trial16Trials: '16 Ensayos',
  trialMaxCausal: 'Máxima Influencia Causal',
  trial20176Desc: 'Inyección asimétrica en flujo ultrabajo; su exclusión incrementa el RMSE de validación en 194%.',
  trialAteShift: 'Shift de ATE:',
  trialSolidComb: 'Combustión Sólida',
  trialSaffireDesc: 'Ensayos a gran escala en nave no tripulada Cygnus previa a la reentrada atmosférica.',
  trialSamplesLabel: 'Muestras: PMMA y SIBAL',
  trialFlowLabel: 'Flujo forzado: 20 cm/s',

  // Evidence Card & Knowledge Triad
  evidenceCardStatus: 'ESTADO:',
  evidenceCardConfidence: 'CONFIANZA BAYESIANA:',
  evidenceCardHeatRelease: 'CALOR LIBERADO (HRR)',
  evidenceCardCO: 'MONÓXIDO (CO)',
  evidenceCardCO2: 'DIÓXIDO (CO₂)',
  pipelineTitle: 'PIPELINE DE INFERENCIA MECANICISTA (INTERACTIVO)',
  pipelineSub: 'Haz clic en una etapa para desplegar ecuaciones de balance térmico',
  step01Input: 'ENTRADA',
  step02Mech: 'MECANISMO',
  step03Obs: 'OBSERVACIÓN',
  step04Outcome: 'RESULTADO',
  evidenceCardDirect: 'Evidencia Directa:',
  evidenceCardAnalogous: 'Evidencia Análoga:',
  limitsOfExtrap: 'Límites de Extrapolación',
  counterfactualAnalysis: 'Análisis Contrafactual:',
  runCounterfactualBtn: 'EJECUTAR CONTRAFACTUAL EN LA SIMULACIÓN',
  consultEvidenceBtn: 'Consultar Evidencia Experimental',
  evaluateCounterexampleBtn: 'Evaluar Contraejemplo Físico',
  suggestNextTestBtn: 'Sugerir Siguiente Ensayo',
  triadHeadlineTitle: 'Triada de Certeza Científica',
  triadHeadlineSub: 'Diferenciación estricta entre mediciones directas y modelos teóricos',
  triadKnow: 'LO QUE SABEMOS (EMPÍRICO)',
  triadInfer: 'LO QUE INFERIMOS (CAUSAL)',
  triadDontKnow: 'LO QUE NO SABEMOS (FRONTERA)',

  // Action Drawers
  drawerTraceabilityTitle: 'Trazabilidad Experimental · NASA PSI',
  drawerChallengeTitle: 'Motor de Contraejemplos · Refutabilidad',
  drawerNextTestTitle: 'Siguiente Ensayo Experimental · Active Learning',
  drawerEvidenceIntro: 'Cada deducción de IGNIS-μ se mapea contra mediciones del repositorio NASA Physical Sciences Informatics (PSI). Datos abiertos verificables:',
  drawerPassportTitle: 'EVIDENCE PASSPORT · NASA PSI',
  drawerPassportSub: 'Procedencia, Criptografía e Integridad Científica de la Deducción',
  passportIdLabel: 'Identificador Maestro:',
  passportInvestLabel: 'Investigación PSI:',
  passportObsVarLabel: 'Variable Observada:',
  passportSourceLabel: 'Archivo Fuente:',
  passportTransformLabel: 'Transformación Aplicada:',
  passportModelLabel: 'Modelo Utilizado:',
  passportLimitsLabel: 'Limitaciones Epistémicas:',

  // Tour
  tourStep: 'PASO',
  tourOf: 'DE',
  tourMode: 'Modo:',
  tourPrev: '← Anterior',
  tourNext: 'Siguiente Paso →',
  tourEnd: 'Finalizar Demo',
};
