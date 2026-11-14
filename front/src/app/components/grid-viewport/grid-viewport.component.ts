import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { IgnisService } from '../../core/services/ignis.service';
import { VisualLayerType } from '../../core/models/ignis.model';

interface ScreenSensor {
  id: string;
  name: string;
  value: string;
  x: number;
  y: number;
  visible: boolean;
  isWarning?: boolean;
}

@Component({
  selector: 'app-grid-viewport',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './grid-viewport.component.html',
  styleUrls: ['./grid-viewport.component.scss'],
})
export class GridViewportComponent implements AfterViewInit, OnDestroy {
  public readonly ignisService = inject(IgnisService);

  @ViewChild('webglCanvas', { static: false })
  private webglCanvasRef!: ElementRef<HTMLCanvasElement>;

  @ViewChild('arenaContainer', { static: false })
  private arenaContainerRef!: ElementRef<HTMLDivElement>;

  // Cámara 3D Orbital (Rotación en espacio 3D y Zoom)
  public readonly rotX = signal<number>(20);   // Inclinación vertical (elevación)
  public readonly rotY = signal<number>(-20);  // Giro horizontal (azimut 360°)
  public readonly zoom = signal<number>(1.0);  // Nivel de zoom (0.6x a 2.2x)

  // Sensores proyectados en coordenadas de pantalla
  public readonly projectedSensors = signal<ScreenSensor[]>([]);

  // Estado de interacción de arrastre
  private isDragging = false;
  private lastPointerX = 0;
  private lastPointerY = 0;

  // WebGL context y variables
  private gl: WebGLRenderingContext | null = null;
  private program: WebGLProgram | null = null;
  private animationFrameId: number | null = null;
  private startTime = Date.now();
  private resizeObserver: ResizeObserver | null = null;

  // Ubicaciones de Uniforms
  private uResolutionLoc: WebGLUniformLocation | null = null;
  private uTimeLoc: WebGLUniformLocation | null = null;
  private uRotXLoc: WebGLUniformLocation | null = null;
  private uRotYLoc: WebGLUniformLocation | null = null;
  private uZoomLoc: WebGLUniformLocation | null = null;
  private uOxygenLoc: WebGLUniformLocation | null = null;
  private uFlowVelocityLoc: WebGLUniformLocation | null = null;
  private uFlowDirectionLoc: WebGLUniformLocation | null = null;
  private uExtinctionProbLoc: WebGLUniformLocation | null = null;
  private uIsDarkLoc: WebGLUniformLocation | null = null;
  private uLayerLoc: WebGLUniformLocation | null = null;
  private uGravityLoc: WebGLUniformLocation | null = null;
  private uIsVentingLoc: WebGLUniformLocation | null = null;
  private uBurnerTypeLoc: WebGLUniformLocation | null = null;
  private uPressureLoc: WebGLUniformLocation | null = null;
  private uMaxTempLoc: WebGLUniformLocation | null = null;
  private uIsSootyLoc: WebGLUniformLocation | null = null;
  private uFlameRadiusLoc: WebGLUniformLocation | null = null;

  // Visualización del osciloscopio de telemetría en vivo
  public readonly showLiveChart = signal<boolean>(false);

  public toggleLiveChart(): void {
    this.showLiveChart.update((v) => !v);
  }

  public ngAfterViewInit(): void {
    setTimeout(() => {
      this.initWebGL();
      this.setupResizeObserver();
      this.startRenderLoop();
    }, 60);
  }

  public ngOnDestroy(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }

  private setupResizeObserver(): void {
    const container = this.arenaContainerRef?.nativeElement;
    if (!container || typeof ResizeObserver === 'undefined') return;

    this.resizeObserver = new ResizeObserver(() => {
      this.resizeCanvas();
    });
    this.resizeObserver.observe(container);
  }

  private resizeCanvas(): void {
    const canvas = this.webglCanvasRef?.nativeElement;
    const container = this.arenaContainerRef?.nativeElement;
    if (!canvas || !container) return;

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
      if (this.gl) {
        this.gl.viewport(0, 0, width, height);
      }
    }
  }

  // =========================================================================
  // MOTOR WEBGL 3D VOLUMÉTRICO (100% ESTÁNDAR GLSL ES 1.00 - CERO ERRORES)
  // =========================================================================

  private initWebGL(): void {
    const canvas = this.webglCanvasRef?.nativeElement;
    if (!canvas) return;

    this.resizeCanvas();

    this.gl = canvas.getContext('webgl', {
      alpha: true,
      antialias: true,
      depth: false,
      preserveDrawingBuffer: false,
    });

    if (!this.gl) {
      console.warn('WebGL no disponible en este entorno');
      return;
    }

    const gl = this.gl;

    const vsSource = `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    const fsSource = `
      precision highp float;

      uniform vec2 u_resolution;
      uniform float u_time;
      uniform float u_rotX;
      uniform float u_rotY;
      uniform float u_zoom;
      uniform float u_oxygen;
      uniform float u_flowVelocity;
      uniform float u_flowDirection;
      uniform float u_extinctionProb;
      uniform float u_isDark;
      uniform float u_layer;
      uniform float u_gravity;
      uniform float u_isVenting;
      uniform float u_burnerType;
      uniform float u_pressure;
      uniform float u_maxTemp;
      uniform float u_isSooty;
      uniform float u_flameRadius;

      // =========================================================================
      // MODELO FÍSICO Y MATEMÁTICO s-Flame (NASA ACME - CIR ISS)
      // Navier-Stokes bajo Mach, Arrhenius, Transferencia Radiativa RTE y Difusión
      // =========================================================================
      vec4 sampleAcmeFlame(vec3 p) {
        if (u_isVenting > 0.5) {
          return vec4(0.0);
        }

        vec3 flameCenter = (u_burnerType < 0.5) ? vec3(0.0, 0.0, 0.0) : vec3(0.0, 0.06, 0.0);
        vec3 q = p - flameCenter;

        // 1. Deformación boyante residual (Ecuación de momentum con término (rho - rho_inf)*g, Sección 3.2, 7.5)
        if (u_gravity > 0.02) {
          float buoy = clamp(u_gravity, 0.0, 1.0);
          if (q.y > -0.05) {
            q.y *= (1.0 / (1.0 + buoy * 1.85));
            q.xz *= (1.0 + max(0.0, q.y) * 1.35 * buoy);
          }
        }

        // 2. Deformación convectiva tridimensional por flujo forzado (Sección 1)
        float flowFactor = u_flowVelocity / 25.0;
        float flowDir = u_flowDirection;
        if (u_flowVelocity > 0.5) {
          float rYZ = length(q.yz);
          float wake = max(0.0, 1.0 - rYZ / 0.85);
          q.x -= flowDir * flowFactor * 0.38 * wake;
          q.x *= 1.0 / (1.0 + flowFactor * 0.28);
        }

        float r = length(q);
        float rs = (u_burnerType < 0.5) ? 0.16 : 0.08;

        // No combustión dentro del núcleo sólido del quemador poroso
        if (r < rs * 0.95) return vec4(0.0);

        // Radio estequiométrico de llama rf (Solución convectivo-difusiva analítica, Sección 3.3, 7.2)
        float R = u_flameRadius;
        if (R < 0.18) R = 0.44;
        float pulsation = sin(u_time * 2.4 + q.y * 2.8) * 0.008;
        R += pulsation;

        // Espesor característico de la zona de reacción (Función de la presión, Sección 4.1, 4.4)
        float delta = 0.044 / sqrt(max(0.15, u_pressure / 55.0));
        float df = abs(r - R);

        // Tasa de reacción química de Arrhenius w_chem (Sección 4.4, 9.1)
        float wChem = exp(- (df * df) / (delta * delta * 1.85)) * (u_pressure / 55.0) * (u_oxygen / 21.0);

        if (u_burnerType >= 0.5) {
          wChem *= smoothstep(-0.24, -0.05, q.y);
        }

        // Campo térmico T(r) en Kelvin (Sección 3.4, 9.2)
        float tRel = exp(- (df * df) / (delta * delta * 4.2));
        float T_local = 300.0 + (u_maxTemp - 300.0) * tRel;

        // Divergencia del flujo radiativo q_rad (Sección 5, 9.4)
        float qRad = pow(T_local / 1850.0, 4.0) * exp(-df * 2.4) * (u_pressure / 55.0);

        // Emisión quimioluminiscente de radicales excitados CH* (431 nm) y C2* Swan bands (516 nm)
        vec3 colBlue = vec3(0.05, 0.48, 1.0) * wChem * 4.2;
        float rCore = clamp((r - rs) / max(0.001, R - rs), 0.0, 1.0);
        float violet = exp(-rCore * rCore * 4.2) * (1.0 - rCore);
        vec3 colViolet = vec3(0.74, 0.35, 0.95) * violet * 1.7;

        // Concha esférica de partículas de hollín (Sección 6: llamas sooty de etileno)
        float soot = 0.0;
        if (u_isSooty > 0.5 && u_oxygen >= 20.0) {
          float rSoot = rs + (R - rs) * 0.74;
          float dSoot = abs(r - rSoot);
          float sootFactor = clamp((u_oxygen - 19.0) / 10.0, 0.0, 1.0);
          soot = exp(- (dSoot * dSoot) / 0.0032) * sootFactor * 2.6;
        }
        vec3 colSoot = vec3(1.0, 0.62, 0.14) * soot * 3.0;

        if (u_gravity > 0.4) {
          float tipSoot = smoothstep(0.05, 0.45, q.y) * 2.2;
          colSoot += vec3(1.0, 0.85, 0.22) * tipSoot * 2.4;
        }

        // Determinación de color y opacidad según la capa física activa (Sección 9)
        vec3 rgb = vec3(0.0);
        float alpha = 0.0;

        if (u_layer < 0.5) {
          // CAPA 0: Óptica Real NASA (Foto s-Flame CIR / BASS)
          rgb = colBlue + colViolet + colSoot;
          alpha = clamp(wChem * 1.55 + violet * 0.85 + soot * 1.25, 0.0, 1.0);
        } else if (u_layer < 1.5) {
          // CAPA 1: Tasa de Reacción de Arrhenius y Liberación Química q_chem (Sección 4.4, 9.1)
          rgb = mix(vec3(0.02, 0.22, 0.85), vec3(0.15, 0.98, 1.0), smoothstep(0.1, 0.9, wChem)) * wChem * 4.5;
          alpha = clamp(wChem * 1.8, 0.0, 1.0);
        } else if (u_layer < 2.5) {
          // CAPA 2: Campo Térmico Tridimensional T(r) en Kelvin (Sección 3.4, 9.2)
          float tNorm = clamp((T_local - 300.0) / 1850.0, 0.0, 1.0);
          vec3 colTemp = mix(vec3(0.04, 0.08, 0.45), vec3(0.1, 0.75, 0.35), smoothstep(0.05, 0.35, tNorm));
          colTemp = mix(colTemp, vec3(1.0, 0.65, 0.05), smoothstep(0.35, 0.7, tNorm));
          colTemp = mix(colTemp, vec3(1.0, 0.98, 0.92), smoothstep(0.7, 1.0, tNorm));
          rgb = colTemp * (0.4 + tNorm * 3.2);
          alpha = clamp(tNorm * 1.2, 0.0, 1.0);
        } else if (u_layer < 3.5) {
          // CAPA 3: Divergencia del Flujo Radiativo q_rad (Sección 5, 9.4)
          rgb = vec3(0.96, 0.18, 0.72) * qRad * 4.5;
          alpha = clamp(qRad * 1.9, 0.0, 1.0);
        } else {
          // CAPA 4: Concha y Densidad de Partículas de Hollín Y_s (Sección 6)
          rgb = vec3(1.0, 0.65, 0.15) * soot * 4.0;
          alpha = clamp(soot * 1.6, 0.0, 1.0);
        }

        // Extinción física por pérdida radiativa (Criterio 9.5 de ACME: q_chem < q_rad)
        if (u_extinctionProb > 0.5) {
          float dim = max(0.05, 1.0 - (u_extinctionProb - 0.5) / 0.5);
          rgb *= dim;
          alpha *= dim;
        }

        return vec4(rgb, alpha);
      }

      // Intersección analítica con esfera contenedora
      vec2 intersectSphere(vec3 ro, vec3 rd, vec3 center, float radius) {
        vec3 oc = ro - center;
        float b = dot(oc, rd);
        float c = dot(oc, oc) - radius * radius;
        float h = b * b - c;
        if (h < 0.0) return vec2(-1.0, -1.0);
        float sqrtH = sqrt(h);
        return vec2(-b - sqrtH, -b + sqrtH);
      }

      // Intersección con cilindro vertical (tallo del quemador de s-Flame)
      vec2 intersectVerticalCylinder(vec3 ro, vec3 rd, vec2 centerXZ, float radius, float yMin, float yMax) {
        vec2 oc = ro.xz - centerXZ;
        float a = dot(rd.xz, rd.xz);
        float b = dot(oc, rd.xz);
        float c = dot(oc, oc) - radius * radius;
        float h = b * b - a * c;
        if (h < 0.0 || a < 0.0001) return vec2(-1.0, -1.0);
        float sqrtH = sqrt(h);
        float t1 = (-b - sqrtH) / a;
        float t2 = (-b + sqrtH) / a;
        float y1 = ro.y + t1 * rd.y;
        if (t1 > 0.0 && y1 >= yMin && y1 <= yMax) return vec2(t1, t2);
        return vec2(-1.0, -1.0);
      }

      // Intersección analítica con paralelepípedo de muestra sólida (100% compatible GLSL ES 1.00)
      vec2 intersectBox(vec3 ro, vec3 rd, vec3 bmin, vec3 bmax) {
        vec3 invD = vec3(1.0) / (rd + sign(rd) * 0.00001);
        vec3 t0 = (bmin - ro) * invD;
        vec3 t1 = (bmax - ro) * invD;
        vec3 tmin = min(t0, t1);
        vec3 tmax = max(t0, t1);
        float nearT = max(max(tmin.x, tmin.y), tmin.z);
        float farT = min(min(tmax.x, tmax.y), tmax.z);
        return vec2(nearT, farT);
      }

      void main() {
        vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / min(u_resolution.x, u_resolution.y);

        // Cámara 3D Orbital con protección total anti-bloqueo cenital
        float camDist = 3.2 / u_zoom;
        float rx = u_rotX;
        float ry = u_rotY;

        float cx = cos(rx), sx = sin(rx);
        float cy = cos(ry), sy = sin(ry);

        vec3 ro = vec3(sy * cx, sx, cy * cx) * camDist;
        vec3 target = vec3(0.0, 0.05, 0.0);

        vec3 fwd = normalize(target - ro);
        vec3 worldUp = vec3(0.0, 1.0, 0.0);
        if (abs(fwd.y) > 0.98) {
          worldUp = vec3(0.0, 0.0, -1.0);
        }
        vec3 rgt = normalize(cross(fwd, worldUp));
        vec3 up = cross(rgt, fwd);

        vec3 rd = normalize(uv.x * rgt + uv.y * up + 1.85 * fwd);

        // Fondo Apple (Modo Oscuro OLED o Modo Claro Apple)
        vec3 bgColor = (u_isDark > 0.5) ? vec3(0.03, 0.03, 0.04) : vec3(0.95, 0.96, 0.97);
        vec3 color = bgColor;

        // 1. PISO CON CUADRÍCULA EN PERSPECTIVA 3D (Y = -0.45)
        float floorY = -0.45;
        float tFloor = -1.0;
        if (rd.y < -0.001) {
          tFloor = (floorY - ro.y) / rd.y;
          if (tFloor > 0.0) {
            vec3 hit = ro + tFloor * rd;
            float distXZ = length(hit.xz);

            vec2 gridFract = abs(fract(hit.xz * 3.2) - 0.5);
            float gridLine = step(0.465, max(gridFract.x, gridFract.y));
            float gridFade = smoothstep(2.6, 0.2, distXZ);

            vec3 gridCol = (u_isDark > 0.5) ? vec3(0.12, 0.55, 1.0) : vec3(0.05, 0.42, 0.88);
            vec3 floorBase = (u_isDark > 0.5) ? vec3(0.04, 0.04, 0.05) : vec3(0.92, 0.93, 0.95);

            float glowFactor = smoothstep(1.4, 0.0, distXZ) * 0.4;
            vec3 flameReflection = vec3(0.08, 0.42, 1.0) * glowFactor + vec3(1.0, 0.55, 0.1) * glowFactor * 0.4;

            color = mix(floorBase, gridCol, gridLine * 0.25 * gridFade) + flameReflection;
          }
        }

        // 2. APARATO EXPERIMENTAL: QUEMADOR ESFÉRICO POROSO s-Flame (ACME) vs MUESTRA PLANA SÓLIDA
        float apparatusHitT = -1.0;

        if (u_burnerType < 0.5) {
          // A) QUEMADOR ESFÉRICO POROSO s-Flame (ACME NASA CIR)
          // Radio rs = 0.16 (6.35 mm scale), centrado en (0.0, 0.0, 0.0)
          vec2 sphereBurnerT = intersectSphere(ro, rd, vec3(0.0, 0.0, 0.0), 0.16);
          vec2 stemT = intersectVerticalCylinder(ro, rd, vec2(0.0), 0.038, -0.45, -0.14);

          if (sphereBurnerT.x > 0.0) {
            apparatusHitT = sphereBurnerT.x;
            vec3 hitP = ro + sphereBurnerT.x * rd;
            vec3 norm = normalize(hitP);

            // Textura porosa de bronce sinterizado con relieve de inyección
            float pore = sin(hitP.x * 90.0) * sin(hitP.y * 90.0) * sin(hitP.z * 90.0);
            vec3 bronzeBase = (u_isDark > 0.5) ? vec3(0.46, 0.38, 0.26) : vec3(0.55, 0.46, 0.32);
            vec3 bronzePore = (u_isDark > 0.5) ? vec3(0.20, 0.15, 0.10) : vec3(0.28, 0.22, 0.16);
            vec3 burnerCol = mix(bronzeBase, bronzePore, step(0.18, pore));

            float diff = max(0.22, dot(norm, normalize(vec3(0.4, 0.85, 0.5))));
            burnerCol *= diff;
            burnerCol += vec3(1.0, 0.42, 0.08) * 0.32 * (u_maxTemp / 2000.0);
            color = mix(color, burnerCol, 0.95);
          } else if (stemT.x > 0.0 && (tFloor < 0.0 || stemT.x < tFloor)) {
            // Tallo vertical de soporte de acero inoxidable
            apparatusHitT = stemT.x;
            vec3 hitP = ro + stemT.x * rd;
            vec3 norm = normalize(vec3(hitP.x, 0.0, hitP.z));
            float diff = max(0.2, dot(norm, normalize(vec3(0.5, 0.4, 0.8))));
            vec3 stemCol = ((u_isDark > 0.5) ? vec3(0.32, 0.34, 0.38) : vec3(0.58, 0.60, 0.64)) * diff;
            color = mix(color, stemCol, 0.92);
          }
        } else {
          // B) MUESTRA PLANA SÓLIDA (BASS-II / Saffire)
          vec3 plateMin = vec3(-0.55, -0.22, -0.14);
          vec3 plateMax = vec3(0.55, -0.12, 0.14);
          vec2 boxT = intersectBox(ro, rd, plateMin, plateMax);

          if (boxT.x > 0.0 && boxT.x < boxT.y) {
            if (tFloor < 0.0 || boxT.x < tFloor) {
              apparatusHitT = boxT.x;
              vec3 hitP = ro + boxT.x * rd;
              vec3 normal = vec3(0.0, 1.0, 0.0);
              if (abs(hitP.x - plateMin.x) < 0.005) normal = vec3(-1.0, 0.0, 0.0);
              else if (abs(hitP.x - plateMax.x) < 0.005) normal = vec3(1.0, 0.0, 0.0);
              else if (abs(hitP.z - plateMin.z) < 0.005) normal = vec3(0.0, 0.0, -1.0);
              else if (abs(hitP.z - plateMax.z) < 0.005) normal = vec3(0.0, 0.0, 1.0);

              vec3 plateCol = (u_isDark > 0.5) ? vec3(0.18, 0.19, 0.21) : vec3(0.40, 0.42, 0.46);
              if (normal.y > 0.5) {
                float pyrolDist = length(hitP.xz);
                float pyrolGlow = smoothstep(0.32, 0.0, pyrolDist);
                vec3 pyrolColor = vec3(1.0, 0.45, 0.08) * pyrolGlow * 1.2;
                vec3 blueEdgeRefl = vec3(0.1, 0.5, 1.0) * smoothstep(0.55, 0.2, pyrolDist) * 0.4;
                plateCol += pyrolColor + blueEdgeRefl;
              }
              color = mix(color, plateCol, 0.94);
            }
          }
        }

        // 3. RAYMARCHING VOLUMÉTRICO s-Flame ACME (Ecuaciones de Conservación y Radiación)
        vec3 flameCenter = (u_burnerType < 0.5) ? vec3(0.0, 0.0, 0.0) : vec3(0.0, 0.06, 0.0);
        float boundRadius = max(0.52, u_flameRadius * 1.55 + (u_flowVelocity / 25.0) * 0.35);
        vec2 tSphere = intersectSphere(ro, rd, flameCenter, boundRadius);

        if (tSphere.y > 0.0) {
          float tStart = max(0.05, tSphere.x);
          float tEnd = tSphere.y;

          if (tFloor > 0.0 && tFloor < tEnd) tEnd = tFloor;
          if (apparatusHitT > 0.0 && apparatusHitT < tEnd) tEnd = apparatusHitT;

          if (tEnd > tStart) {
            const int STEPS = 36;
            float stepDist = (tEnd - tStart) / float(STEPS);
            vec3 accumColor = vec3(0.0);
            float accumAlpha = 0.0;
            float t = tStart + stepDist * 0.5;

            for (int i = 0; i < 36; i++) {
              vec3 p = ro + t * rd;
              vec4 samp = sampleAcmeFlame(p);

              if (samp.a > 0.001) {
                float dens = samp.a * stepDist * 5.4;
                accumColor += samp.rgb * dens * (1.0 - accumAlpha);
                accumAlpha += dens;
                if (accumAlpha >= 0.96) break;
              }
              t += stepDist;
            }

            color = color * (1.0 - accumAlpha * 0.65) + accumColor;
          }
        }

        // 4. MICRO-PARTÍCULAS DE HOLLÍN EN ÓRBITA ESFÉRICA (NASA s-Flame / FLEX Photo 4)
        if (u_isSooty > 0.5 && u_oxygen >= 20.0 && (u_layer < 0.5 || u_layer > 3.5)) {
          for (int k = 0; k < 22; k++) {
            float fk = float(k);
            float ang = u_time * 0.45 + fk * 0.285;
            float rad = u_flameRadius * 0.76 + sin(fk * 2.3) * 0.04;
            float py = sin(fk * 1.8 + u_time * 0.6) * (u_flameRadius * 0.7);

            vec3 partPos = vec3(cos(ang) * rad, py, sin(ang) * rad);
            partPos.x += (u_flowDirection * (u_flowVelocity / 25.0) * 0.25) * sin(fk * 1.5);
            if (u_gravity > 0.4) {
              partPos.y += sin(fk * 3.1) * 0.25 + 0.12;
            }

            vec3 toP = partPos - ro;
            float proj = dot(toP, rd);
            if (proj > 0.0) {
              vec3 closeP = ro + proj * rd;
              float distP = length(closeP - partPos);
              float sparkGlow = smoothstep(0.03, 0.0, distP);
              if (sparkGlow > 0.0) {
                color += vec3(1.0, 0.70, 0.18) * sparkGlow * 2.4;
              }
            }
          }
        }

        gl_FragColor = vec4(color, 1.0);
      }
    `;

    const vs = this.compileShader(gl, gl.VERTEX_SHADER, vsSource);
    const fs = this.compileShader(gl, gl.FRAGMENT_SHADER, fsSource);
    if (!vs || !fs) {
      console.error('No se pudo inicializar los shaders WebGL');
      return;
    }

    this.program = gl.createProgram();
    if (!this.program) return;

    gl.attachShader(this.program, vs);
    gl.attachShader(this.program, fs);
    gl.linkProgram(this.program);

    if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
      console.error('Error al enlazar programa WebGL:', gl.getProgramInfoLog(this.program));
      return;
    }

    gl.useProgram(this.program);

    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0,
      ]),
      gl.STATIC_DRAW
    );

    const posAttrib = gl.getAttribLocation(this.program, 'a_position');
    gl.enableVertexAttribArray(posAttrib);
    gl.vertexAttribPointer(posAttrib, 2, gl.FLOAT, false, 0, 0);

    // Guardar ubicaciones de Uniforms
    this.uResolutionLoc = gl.getUniformLocation(this.program, 'u_resolution');
    this.uTimeLoc = gl.getUniformLocation(this.program, 'u_time');
    this.uRotXLoc = gl.getUniformLocation(this.program, 'u_rotX');
    this.uRotYLoc = gl.getUniformLocation(this.program, 'u_rotY');
    this.uZoomLoc = gl.getUniformLocation(this.program, 'u_zoom');
    this.uOxygenLoc = gl.getUniformLocation(this.program, 'u_oxygen');
    this.uFlowVelocityLoc = gl.getUniformLocation(this.program, 'u_flowVelocity');
    this.uFlowDirectionLoc = gl.getUniformLocation(this.program, 'u_flowDirection');
    this.uExtinctionProbLoc = gl.getUniformLocation(this.program, 'u_extinctionProb');
    this.uIsDarkLoc = gl.getUniformLocation(this.program, 'u_isDark');
    this.uLayerLoc = gl.getUniformLocation(this.program, 'u_layer');
    this.uGravityLoc = gl.getUniformLocation(this.program, 'u_gravity');
    this.uIsVentingLoc = gl.getUniformLocation(this.program, 'u_isVenting');
    this.uBurnerTypeLoc = gl.getUniformLocation(this.program, 'u_burnerType');
    this.uPressureLoc = gl.getUniformLocation(this.program, 'u_pressure');
    this.uMaxTempLoc = gl.getUniformLocation(this.program, 'u_maxTemp');
    this.uIsSootyLoc = gl.getUniformLocation(this.program, 'u_isSooty');
    this.uFlameRadiusLoc = gl.getUniformLocation(this.program, 'u_flameRadius');
  }

  private compileShader(gl: WebGLRenderingContext, type: number, source: string): WebGLShader | null {
    const shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('Error de compilación en Shader:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  }

  private startRenderLoop(): void {
    const render = () => {
      this.renderFrame();
      this.updateProjectedSensors();
      this.animationFrameId = requestAnimationFrame(render);
    };
    render();
  }

  private renderFrame(): void {
    const gl = this.gl;
    const canvas = this.webglCanvasRef?.nativeElement;
    if (!gl || !this.program || !canvas) return;

    gl.useProgram(this.program);

    const s = this.ignisService.scenario();
    const t = this.ignisService.telemetry();
    const elapsedTime = (Date.now() - this.startTime) * 0.001;

    gl.uniform2f(this.uResolutionLoc, canvas.width, canvas.height);
    gl.uniform1f(this.uTimeLoc, elapsedTime);
    gl.uniform1f(this.uRotXLoc, (this.rotX() * Math.PI) / 180);
    gl.uniform1f(this.uRotYLoc, (this.rotY() * Math.PI) / 180);
    gl.uniform1f(this.uZoomLoc, this.zoom());
    gl.uniform1f(this.uOxygenLoc, s.oxygenFraction);
    gl.uniform1f(this.uFlowVelocityLoc, s.flowVelocity);
    gl.uniform1f(this.uFlowDirectionLoc, s.flowDirection === 'concurrent' ? 1.0 : -1.0);
    gl.uniform1f(this.uExtinctionProbLoc, t.flameExtinctionProb);
    gl.uniform1f(this.uIsDarkLoc, this.ignisService.isDarkMode() ? 1.0 : 0.0);

    let layerId = 0.0;
    if (this.ignisService.activeLayer() === 'flame') layerId = 1.0;
    else if (this.ignisService.activeLayer() === 'temperature') layerId = 2.0;
    else if (this.ignisService.activeLayer() === 'radiation') layerId = 3.0;
    else if (this.ignisService.activeLayer() === 'soot') layerId = 4.0;
    gl.uniform1f(this.uLayerLoc, layerId);

    gl.uniform1f(this.uGravityLoc, t.gravityG);
    gl.uniform1f(this.uIsVentingLoc, s.isVentingToSpace ? 1.0 : 0.0);
    gl.uniform1f(this.uBurnerTypeLoc, s.burnerGeometry === 'sflame-sphere' ? 0.0 : 1.0);
    gl.uniform1f(this.uPressureLoc, s.pressureKpa);
    gl.uniform1f(this.uMaxTempLoc, t.maxFlameTempK);
    gl.uniform1f(this.uIsSootyLoc, s.material === 'Metano (CH₄)' ? 0.0 : 1.0);
    const normRf = (t.flameRadiusMm / 6.35) * 0.16;
    gl.uniform1f(this.uFlameRadiusLoc, normRf);

    gl.drawArrays(gl.TRIANGLES, 0, 6);
  }

  // =========================================================================
  // PROYECCIÓN 3D -> 2D LIMPIA DE SENSORES (SIN AMONTONAMIENTO)
  // =========================================================================

  private updateProjectedSensors(): void {
    const canvas = this.webglCanvasRef?.nativeElement;
    if (!canvas) return;

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (width === 0 || height === 0) return;

    const t = this.ignisService.telemetry();

    // Sensores colocados estratégicamente fuera de la envolvente de la llama
    const sensorDefs = [
      {
        id: 'tc',
        name: 'Termopar TC-01',
        value: `${t.thermocoupleTempC} °C`,
        pos3D: [-0.85, 0.42, 0.2],
        isWarning: false,
      },
      {
        id: 'rad',
        name: 'Radiómetro RAD-04',
        value: `${t.radiometerFluxKwM2} kW/m²`,
        pos3D: [0.85, 0.42, -0.2],
        isWarning: false,
      },
      {
        id: 'gas',
        name: 'Sensor CO / CO₂',
        value: `${t.coPpm} ppm · ${t.co2Percent}%`,
        pos3D: [0.85, -0.15, 0.35],
        isWarning: t.coPpm > 45,
      },
    ];

    const rx = (this.rotX() * Math.PI) / 180;
    const ry = (this.rotY() * Math.PI) / 180;
    const camDist = 3.2 / this.zoom();

    const cx = Math.cos(rx), sx = Math.sin(rx);
    const cy = Math.cos(ry), sy = Math.sin(ry);

    const ro = [sy * cx * camDist, sx * camDist, cy * cx * camDist];
    const target = [0.0, 0.05, 0.0];

    const forward = this.normalize3([target[0] - ro[0], target[1] - ro[1], target[2] - ro[2]]);
    const worldUp = Math.abs(forward[1]) > 0.98 ? [0.0, 0.0, -1.0] : [0.0, 1.0, 0.0];
    const right = this.normalize3(this.cross3(forward, worldUp));
    const up = this.cross3(right, forward);

    const projected: ScreenSensor[] = [];

    for (const s of sensorDefs) {
      const p = s.pos3D;
      const v = [p[0] - ro[0], p[1] - ro[1], p[2] - ro[2]];

      const zCam = this.dot3(v, forward);
      if (zCam > 0.3) {
        const xCam = this.dot3(v, right);
        const yCam = this.dot3(v, up);

        const aspect = Math.min(width, height);
        const focal = 1.85;

        const screenX = width / 2 + (xCam / zCam) * focal * aspect;
        const screenY = height / 2 - (yCam / zCam) * focal * aspect;

        projected.push({
          id: s.id,
          name: s.name,
          value: s.value,
          x: Math.round(screenX),
          y: Math.round(screenY),
          visible: screenX > 50 && screenX < width - 50 && screenY > 50 && screenY < height - 50,
          isWarning: s.isWarning,
        });
      }
    }

    this.projectedSensors.set(projected);
  }

  // =========================================================================
  // INTERACCIÓN: ROTACIÓN ORBITAL 3D Y ZOOM FLUIDOS
  // =========================================================================

  public onPointerDown(event: MouseEvent | TouchEvent): void {
    this.isDragging = true;
    const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
    const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY;
    this.lastPointerX = clientX;
    this.lastPointerY = clientY;
  }

  @HostListener('window:pointermove', ['$event'])
  @HostListener('window:touchmove', ['$event'])
  public onPointerMove(event: MouseEvent | TouchEvent): void {
    if (!this.isDragging) return;

    const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
    const clientY = 'touches' in event ? event.touches[0].clientY : event.clientY;

    const deltaX = clientX - this.lastPointerX;
    const deltaY = clientY - this.lastPointerY;

    this.lastPointerX = clientX;
    this.lastPointerY = clientY;

    const newRotY = (this.rotY() + deltaX * 0.45) % 360;
    const newRotX = Math.max(-10, Math.min(75, this.rotX() - deltaY * 0.35));

    this.rotY.set(Math.round(newRotY * 10) / 10);
    this.rotX.set(Math.round(newRotX * 10) / 10);
  }

  @HostListener('window:pointerup')
  @HostListener('window:touchend')
  public onPointerUp(): void {
    this.isDragging = false;
  }

  public onWheelZoom(event: WheelEvent): void {
    event.preventDefault();
    const zoomDelta = -event.deltaY * 0.0014;
    const newZoom = Math.max(0.6, Math.min(2.2, this.zoom() + zoomDelta));
    this.zoom.set(Math.round(newZoom * 100) / 100);
  }

  public zoomIn(): void {
    this.zoom.update((z) => Math.min(2.2, Math.round((z + 0.15) * 100) / 100));
  }

  public zoomOut(): void {
    this.zoom.update((z) => Math.max(0.6, Math.round((z - 0.15) * 100) / 100));
  }

  public resetCamera(): void {
    this.rotX.set(20);
    this.rotY.set(-20);
    this.zoom.set(1.0);
  }

  public setCameraView(view: 'isometric' | 'top' | 'side'): void {
    if (view === 'isometric') {
      this.rotX.set(20);
      this.rotY.set(-20);
    } else if (view === 'top') {
      this.rotX.set(75);
      this.rotY.set(0);
    } else if (view === 'side') {
      this.rotX.set(6);
      this.rotY.set(90);
    }
  }

  public setLayer(layer: VisualLayerType): void {
    this.ignisService.setLayer(layer);
  }

  private dot3(a: number[], b: number[]): number {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  }

  private cross3(a: number[], b: number[]): number[] {
    return [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0],
    ];
  }

  private normalize3(v: number[]): number[] {
    const len = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (len === 0) return [0, 0, 0];
    return [v[0] / len, v[1] / len, v[2] / len];
  }
}
