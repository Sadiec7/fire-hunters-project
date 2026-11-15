import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IgnisService } from '../../core/services/ignis.service';
import {
  BayesianNetworkModel,
  BurnerGeometryType,
  CounterfactualMode,
  EvidencePassportData,
  FlowDirectionType,
  GravityMode,
  MaterialType,
  MfcPatternState,
  ScientificRealityMode,
  ScmModelVariant,
} from '../../core/models/ignis.model';

@Component({
  selector: 'app-scenario-controls',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './scenario-controls.component.html',
  styleUrls: ['./scenario-controls.component.scss'],
})
export class ScenarioControlsComponent {
  public readonly ignisService = inject(IgnisService);

  public readonly materials: MaterialType[] = [
    'Etileno (C₂H₄)',
    'Metano (CH₄)',
    'PMMA',
    'SIBAL',
    'Nomex',
    'Delrin',
    'Silicone',
  ];

  public setScientificMode(mode: ScientificRealityMode): void {
    this.ignisService.setScientificMode(mode);
  }

  public setInferenceSubMode(subMode: 'bayesian' | 'counterfactual' | 'digital-twin'): void {
    this.ignisService.setInferenceSubMode(subMode);
  }

  public onMfcEventChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.setMfcEventIndex(val);
  }

  public getSelectedEvent() {
    const idx = this.ignisService.currentMfcEventIndex();
    return this.ignisService.discreteMfcEvents().find(e => e.eventIndex === idx) || this.ignisService.discreteMfcEvents()[0];
  }

  public setSimulationPanel(panel: 'all' | 'atmosphere' | 'fluid' | 'suppression'): void {
    this.ignisService.setSimulationPanel(panel);
  }

  public setMfcPattern(pattern: MfcPatternState): void {
    this.ignisService.setMfcPattern(pattern);
  }

  public setBayesianModel(model: BayesianNetworkModel): void {
    this.ignisService.setBayesianModel(model);
  }

  public setCounterfactualTab(tab: CounterfactualMode): void {
    this.ignisService.setCounterfactualTab(tab);
  }

  public setScmModel(m: ScmModelVariant): void {
    this.ignisService.setScmModel(m);
  }

  public onMfc2ScaleChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.mfc2Multiplier.set(val);
  }

  public onMfc3ScaleChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.mfc3Multiplier.set(val);
  }

  public openEvidencePassport(data: Partial<EvidencePassportData>): void {
    this.ignisService.openEvidencePassport(data);
  }

  public setMaterial(material: MaterialType): void {
    this.ignisService.updateMaterial(material);
    if (material === 'Etileno (C₂H₄)' || material === 'Metano (CH₄)') {
      this.ignisService.setBurnerGeometry('sflame-sphere');
    } else {
      this.ignisService.setBurnerGeometry('solid-flat');
    }
  }

  public setBurnerGeometry(geometry: BurnerGeometryType): void {
    this.ignisService.setBurnerGeometry(geometry);
  }

  public onOxygenChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.updateOxygen(val);
  }

  public onPressureChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.updatePressure(val);
  }

  public onFlowChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    this.ignisService.updateFlow(val);
  }

  public setFlowDirection(direction: FlowDirectionType): void {
    this.ignisService.updateDirection(direction);
  }

  public setGravityMode(mode: GravityMode): void {
    this.ignisService.setGravityMode(mode);
  }

  public togglePressureMode(): void {
    this.ignisService.togglePressureMode();
  }

  public toggleUnits(): void {
    this.ignisService.toggleUnits();
  }

  public triggerVacuumVenting(): void {
    this.ignisService.triggerVacuumVenting();
  }

  public restoreCabinAtmosphere(): void {
    this.ignisService.restoreCabinAtmosphere();
  }

  public injectSuppressant(gas: 'N2' | 'CO2'): void {
    this.ignisService.injectSuppressant(gas);
  }

  public exportTelemetry(): void {
    this.ignisService.exportTelemetryData();
  }

  // Preajustes rápidos emblemáticos de investigaciones NASA (s-Flame ACME / BASS-II / Saffire)
  public applyPreset(preset: 'sflame-acme' | 'saffire-vi' | 'bass-extinction' | 'exploration-atm' | 'vacuum-quench'): void {
    if (preset === 'sflame-acme') {
      this.ignisService.updateMaterial('Etileno (C₂H₄)');
      this.ignisService.setBurnerGeometry('sflame-sphere');
      this.ignisService.updateOxygen(30);
      this.ignisService.updatePressure(55);
      this.ignisService.updateFlow(12);
      this.ignisService.updateDirection('concurrent');
      this.ignisService.setGravityMode('micro-quiescent');
    } else if (preset === 'saffire-vi') {
      this.ignisService.updateMaterial('PMMA');
      this.ignisService.setBurnerGeometry('solid-flat');
      this.ignisService.updateOxygen(30);
      this.ignisService.updatePressure(55);
      this.ignisService.updateFlow(20);
      this.ignisService.updateDirection('concurrent');
      this.ignisService.setGravityMode('micro-quiescent');
    } else if (preset === 'bass-extinction') {
      this.ignisService.updateMaterial('PMMA');
      this.ignisService.setBurnerGeometry('solid-flat');
      this.ignisService.updateOxygen(19);
      this.ignisService.updatePressure(101.3);
      this.ignisService.updateFlow(4);
      this.ignisService.updateDirection('opposed');
      this.ignisService.setGravityMode('micro-quiescent');
    } else if (preset === 'exploration-atm') {
      this.ignisService.updateMaterial('SIBAL');
      this.ignisService.setBurnerGeometry('solid-flat');
      this.ignisService.updateOxygen(32);
      this.ignisService.updatePressure(56);
      this.ignisService.updateFlow(15);
      this.ignisService.updateDirection('concurrent');
      this.ignisService.setGravityMode('micro-active');
    } else if (preset === 'vacuum-quench') {
      this.triggerVacuumVenting();
    }
  }
}
