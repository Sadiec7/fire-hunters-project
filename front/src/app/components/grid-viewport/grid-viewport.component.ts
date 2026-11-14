import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';

@Component({
  selector: 'app-grid-viewport',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './grid-viewport.component.html',
  styleUrls: ['./grid-viewport.component.scss'],
})
export class GridViewportComponent {
  public readonly ignisService = inject(IgnisService);

  // Dimensiones dinámicas de la llama en microgravedad
  public readonly flameStyles = computed(() => {
    const s = this.ignisService.scenario();
    const t = this.ignisService.telemetry();

    // En microgravedad, a mayor oxígeno la llama es más brillante y compacta; con mayor flujo se elonga
    const scale = 0.8 + (s.oxygenFraction / 28) * 0.4;
    const elongation = s.flowVelocity > 10 ? 1 + (s.flowVelocity / 35) * 0.5 : 1;
    const isConcurrent = s.flowDirection === 'concurrent';

    return {
      transform: `scale(${scale}) scaleX(${isConcurrent ? elongation : 1 / elongation})`,
      opacity: t.flameExtinctionProb > 0.7 ? 0.25 : 1,
    };
  });

  public setLayer(layer: 'all' | 'flame' | 'sensors' | 'gases'): void {
    this.ignisService.setLayer(layer);
  }
}
