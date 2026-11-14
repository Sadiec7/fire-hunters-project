import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
})
export class HeaderComponent {
  public readonly ignisService = inject(IgnisService);
}
