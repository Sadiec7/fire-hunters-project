import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';
import { KnowledgeTriadItem } from '../../core/models/ignis.model';

@Component({
  selector: 'app-knowledge-triad',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './knowledge-triad.component.html',
  styleUrls: ['./knowledge-triad.component.scss'],
})
export class KnowledgeTriadComponent {
  public readonly ignisService = inject(IgnisService);

  public readonly knowItems = computed<KnowledgeTriadItem[]>(() =>
    this.ignisService.knowledgeTriad().filter((item) => item.category === 'KNOW')
  );

  public readonly inferItems = computed<KnowledgeTriadItem[]>(() =>
    this.ignisService.knowledgeTriad().filter((item) => item.category === 'INFER')
  );

  public readonly dontKnowItems = computed<KnowledgeTriadItem[]>(() =>
    this.ignisService.knowledgeTriad().filter((item) => item.category === 'DONT_KNOW')
  );
}
