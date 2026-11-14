import { Component, HostBinding, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from './components/header/header.component';
import { GridViewportComponent } from './components/grid-viewport/grid-viewport.component';
import { ScenarioControlsComponent } from './components/scenario-controls/scenario-controls.component';
import { EvidenceCardComponent } from './components/evidence-card/evidence-card.component';
import { KnowledgeTriadComponent } from './components/knowledge-triad/knowledge-triad.component';
import { ActionDrawerComponent } from './components/action-drawer/action-drawer.component';
import { IgnisService } from './core/services/ignis.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    GridViewportComponent,
    ScenarioControlsComponent,
    EvidenceCardComponent,
    KnowledgeTriadComponent,
    ActionDrawerComponent,
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.scss'],
})
export class App {
  public readonly ignisService = inject(IgnisService);

  // Clase dinámica para el modo oscuro en el host
  @HostBinding('class.dark-theme')
  get isDark(): boolean {
    return this.ignisService.isDarkMode();
  }

  // Coordenadas del cursor para el sutil reflejo de luz interactivo
  public mouseX = signal<number>(50);
  public mouseY = signal<number>(30);

  @HostListener('mousemove', ['$event'])
  public onMouseMove(event: MouseEvent): void {
    const x = Math.round((event.clientX / window.innerWidth) * 100);
    const y = Math.round((event.clientY / window.innerHeight) * 100);
    this.mouseX.set(x);
    this.mouseY.set(y);
  }
}
