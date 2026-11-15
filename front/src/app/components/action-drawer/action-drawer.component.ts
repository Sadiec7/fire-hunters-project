import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';
import { EvidencePassportData, JornadaRankingItem } from '../../core/models/ignis.model';

@Component({
  selector: 'app-action-drawer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './action-drawer.component.html',
  styleUrls: ['./action-drawer.component.scss'],
})
export class ActionDrawerComponent {
  public readonly ignisService = inject(IgnisService);

  public close(): void {
    this.ignisService.closeDrawer();
  }

  public closePassport(): void {
    this.ignisService.closeEvidencePassport();
  }

  public closeWhy(): void {
    this.ignisService.closeWhyJornada();
  }

  public closeBrief(): void {
    this.ignisService.closeBrief();
  }

  public openWhy(jornada: JornadaRankingItem): void {
    this.ignisService.openWhyJornada(jornada);
  }

  public generateBrief(jornadaId: number): void {
    this.ignisService.generateExperimentBrief(jornadaId);
  }

  public openPassport(data: Partial<EvidencePassportData>): void {
    this.ignisService.openEvidencePassport(data);
  }

  public applyRecommendedTest(): void {
    const rec = this.ignisService.testRecommendation().coordinates;
    this.ignisService.updateMaterial(rec.material);
    this.ignisService.updateOxygen(rec.oxygenFraction);
    this.ignisService.updatePressure(rec.pressureKpa);
    this.ignisService.updateFlow(rec.flowVelocity);
    this.ignisService.updateDirection(rec.flowDirection);
    this.close();
  }
}
