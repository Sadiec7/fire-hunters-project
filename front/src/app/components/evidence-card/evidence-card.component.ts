import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';

@Component({
  selector: 'app-evidence-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './evidence-card.component.html',
  styleUrls: ['./evidence-card.component.scss'],
})
export class EvidenceCardComponent {
  public readonly ignisService = inject(IgnisService);

  public readonly activeCausalStep = signal<number | null>(null);

  public selectCausalStep(step: number): void {
    if (this.activeCausalStep() === step) {
      this.activeCausalStep.set(null);
    } else {
      this.activeCausalStep.set(step);
    }
  }

  public openDrawer(type: 'evidence' | 'challenge' | 'next-test'): void {
    this.ignisService.openDrawer(type);
  }

  // Ejecuta la condición contrafactual de NASA directamente en la simulación
  public applyCounterfactual(): void {
    const s = this.ignisService.scenario();
    if (s.oxygenFraction >= 25) {
      this.ignisService.updateOxygen(21);
      this.ignisService.updateDirection('opposed');
    } else {
      this.ignisService.updateOxygen(30);
      this.ignisService.updateFlow(18);
      this.ignisService.updateDirection('concurrent');
    }
  }

  public exportData(): void {
    this.ignisService.exportTelemetryData();
  }
}
