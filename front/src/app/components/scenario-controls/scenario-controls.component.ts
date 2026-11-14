import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IgnisService } from '../../core/services/ignis.service';
import { FlowDirectionType, GravityMode, MaterialType } from '../../core/models/ignis.model';

@Component({
  selector: 'app-scenario-controls',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './scenario-controls.component.html',
  styleUrls: ['./scenario-controls.component.scss'],
})
export class ScenarioControlsComponent {
  public readonly ignisService = inject(IgnisService);

  public readonly materials: MaterialType[] = ['PMMA', 'SIBAL', 'Nomex', 'Delrin', 'Silicone'];

  public setMaterial(material: MaterialType): void {
    this.ignisService.updateMaterial(material);
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

  // Preajustes rápidos emblemáticos de investigaciones NASA
  public applyPreset(preset: 'saffire-vi' | 'bass-extinction' | 'exploration-atm' | 'vacuum-quench'): void {
    if (preset === 'saffire-vi') {
      this.ignisService.updateMaterial('PMMA');
      this.ignisService.updateOxygen(30);
      this.ignisService.updatePressure(55);
      this.ignisService.updateFlow(20);
      this.ignisService.updateDirection('concurrent');
      this.ignisService.setGravityMode('micro-quiescent');
    } else if (preset === 'bass-extinction') {
      this.ignisService.updateMaterial('PMMA');
      this.ignisService.updateOxygen(19);
      this.ignisService.updatePressure(101.3);
      this.ignisService.updateFlow(4);
      this.ignisService.updateDirection('opposed');
      this.ignisService.setGravityMode('micro-quiescent');
    } else if (preset === 'exploration-atm') {
      this.ignisService.updateMaterial('SIBAL');
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
