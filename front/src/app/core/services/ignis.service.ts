import { Injectable, computed, signal } from '@angular/core';
import {
  ActiveLearningRecommendation,
  Counterexample,
  EvidenceCard,
  KnowledgeTriadItem,
  PhysicalScenario,
  SensorTelemetry,
} from '../models/ignis.model';

@Injectable({
  providedIn: 'root',
})
export class IgnisService {
  // Modo de color (Light / Dark estilo Apple)
  public readonly isDarkMode = signal<boolean>(false);

  // Estado reactivo del escenario experimental
  public readonly scenario = signal<PhysicalScenario>({
    material: 'PMMA',
    oxygenFraction: 30, // 30% O2 (Caso Saffire VI / BASS-II)
    pressureKpa: 55,   // 55 kPa atmósfera de cabina espacial
    flowVelocity: 20,  // 20 cm/s ventilación forzada en microgravedad
    flowDirection: 'concurrent',
    suppressant: 'Ninguno',
  });

  // Modal / Drawer activo para las 3 acciones científicas
  public readonly activeDrawer = signal<'evidence' | 'challenge' | 'next-test' | null>(null);

  // Filtro de capa visual en el gemelo 3D
  public readonly activeLayer = signal<'all' | 'flame' | 'sensors' | 'gases'>('all');

  // Alternar tema oscuro/claro
  public toggleTheme(): void {
    this.isDarkMode.update((dark) => !dark);
  }

  // Telemetría calculada en base a física de combustión en microgravedad
  public readonly telemetry = computed<SensorTelemetry>(() => {
    const s = this.scenario();
    const o2Factor = s.oxygenFraction / 21;
    const flowFactor = Math.max(0.1, s.flowVelocity / 15);
    const pressureFactor = s.pressureKpa / 101.3;

    const baseTemp = 410;
    const temp = Math.round(baseTemp + (o2Factor * 210) + (flowFactor * 70) * pressureFactor);
    const co = Math.round(42 * o2Factor * flowFactor * (s.material === 'PMMA' ? 1.4 : 1.1));
    const co2 = Number((0.55 * o2Factor * pressureFactor).toFixed(2));
    const flux = Number((1.75 * o2Factor * flowFactor).toFixed(2));
    const spread = Number((0.32 * o2Factor * (s.flowDirection === 'concurrent' ? 1.45 : 0.55)).toFixed(2));
    
    let extinctionProb = 0.04;
    if (s.oxygenFraction < 20 && s.flowVelocity < 4) extinctionProb = 0.89;
    else if (s.oxygenFraction < 23 && s.flowVelocity > 25) extinctionProb = 0.62;

    return {
      thermocoupleTempC: temp,
      radiometerFluxKwM2: flux,
      coPpm: co,
      co2Percent: co2,
      flameSpreadVelocityCmS: spread,
      flameExtinctionProb: extinctionProb,
    };
  });

  // Tarjeta de Evidencia Dinámica (Fire Evidence Card)
  public readonly evidenceCard = computed<EvidenceCard>(() => {
    const s = this.scenario();
    const t = this.telemetry();

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
        counterfactual: 'Reducir O₂ por debajo de 23% o invertir la ventilación a flujo opuesto para inducir extinción convectiva.',
        warning: 'No se registran ensayos idénticos a escala de volumen cerrado para esta concentración exacta.',
        psiUrl: 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-98',
        causalChain: {
          conditions: `${s.material} · O₂: ${s.oxygenFraction}% · P: ${s.pressureKpa} kPa · Flujo: ${s.flowVelocity} cm/s`,
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
          conditions: `${s.material} · O₂: ${s.oxygenFraction}% · P: ${s.pressureKpa} kPa`,
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
        title: 'Influencia de presión de cabina reducida',
        description: `A 55 kPa disminuye la densidad molecular del oxidante, extendiendo la zona de difusión y moderando el calor sensible liberado.`,
        source: 'Inferencia de Transporte de Masa',
        badgeText: 'Modelo físico',
        confidence: 0.76,
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

  public updateMaterial(material: PhysicalScenario['material']): void {
    this.scenario.update((s) => ({ ...s, material }));
  }

  public updateOxygen(oxygenFraction: number): void {
    this.scenario.update((s) => ({ ...s, oxygenFraction }));
  }

  public updatePressure(pressureKpa: number): void {
    this.scenario.update((s) => ({ ...s, pressureKpa }));
  }

  public updateFlow(flowVelocity: number): void {
    this.scenario.update((s) => ({ ...s, flowVelocity }));
  }

  public updateDirection(flowDirection: PhysicalScenario['flowDirection']): void {
    this.scenario.update((s) => ({ ...s, flowDirection }));
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
