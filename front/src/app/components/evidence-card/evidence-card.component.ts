import { Component, inject } from '@angular/core';
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

  public openDrawer(type: 'evidence' | 'challenge' | 'next-test'): void {
    this.ignisService.openDrawer(type);
  }
}
