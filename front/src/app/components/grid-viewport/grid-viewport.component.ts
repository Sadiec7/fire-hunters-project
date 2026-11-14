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

      // Densidad y emisión óptica de la llama en microgravedad (NASA C-1998-485 / BASS-II / FLEX)
      vec4 sampleMicrogravityFlame(vec3 p) {
        if (u_isVenting > 0.5) {
          return vec4(0.0);
        }

        // Centro del domo esférico de difusión sobre la muestra sólida
        vec3 flameCenter = vec3(0.0, 0.06, 0.0);
        vec3 q = p - flameCenter;

        // Deformación por boyamiento gravitacional (1-g Terrestre vs 0-g Espacial - Foto 1 NASA)
        if (u_gravity > 0.05) {
          float buoyFactor = clamp(u_gravity, 0.0, 1.0);
          if (q.y > -0.05) {
            q.y *= (1.0 / (1.0 + buoyFactor * 1.55));
            q.xz *= (1.0 + max(0.0, q.y) * 1.25 * buoyFactor);
          }
        }

        // 1. Deformación convectiva por flujo forzado (NASA BASS-II)
        float flowMag = u_flowVelocity / 25.0;
        float flowDir = u_flowDirection;
        if (u_flowVelocity > 0.5) {
          float rYZ = length(q.yz);
          float wake = max(0.0, 1.0 - rYZ / 0.85);
          q.x -= flowDir * flowMag * 0.42 * wake;
          q.x *= 1.0 / (1.0 + flowMag * 0.35);
        }

        float r = length(q);

        // Radio físico de difusión esférica dependiente de concentración de O2
        float o2Ratio = clamp((u_oxygen - 18.0) / 20.0, 0.0, 1.0);
        float R = 0.48 + o2Ratio * 0.18;
        
        // Suave pulsación respiratoria natural de microgravedad
        float pulsation = sin(u_time * 2.2 + q.y * 2.5) * 0.012;
        R += pulsation;

        // 2. ENVOLTURA ESFÉRICA AZUL (Quimioluminiscencia CH* a 431 nm y C2* Swan bands)
        // Zona de reacción delgada donde se produce la máxima quimioluminiscencia
        float dShell = abs(r - R);
        float blueShell = exp(-dShell * dShell * 95.0);

        // Atenuación suave hacia la base donde toca la muestra de combustible
        float baseFade = smoothstep(-0.25, -0.05, q.y);
        blueShell *= baseFade;

        // 3. NÚCLEO VIOLETA / MAGENTA INTERIOR (Emisión de radicales - Foto 1 NASA)
        float coreDist = r / (R + 0.001);
        float violetCore = exp(-coreDist * coreDist * 4.5) * max(0.0, 1.0 - coreDist) * baseFade;

        // 4. INCANDESCENCIA DE HOLLÍN DORADO / ÁMBAR (FLEX / Saffire en O2 >= 22%)
        float amberSoot = 0.0;
        float whiteHot = 0.0;
        if (u_oxygen >= 22.0) {
          float sootFactor = clamp((u_oxygen - 21.0) / 10.0, 0.0, 1.0);
          vec3 sootPos = q - vec3(flowDir * flowMag * 0.08, -0.05, 0.0);
          float rSoot = length(sootPos);
          amberSoot = exp(-rSoot * rSoot * 16.0) * sootFactor * 2.4 * baseFade;
          whiteHot = amberSoot * amberSoot * 0.75;
        }

        // Síntesis espectral de colores de las fotografías de NASA
        vec3 colBlue   = vec3(0.05, 0.48, 1.0) * blueShell * 4.2;
        vec3 colViolet = vec3(0.74, 0.38, 0.96) * violetCore * 1.8;
        vec3 colAmber  = vec3(1.0, 0.64, 0.14) * amberSoot * 3.0;
        vec3 colWhite  = vec3(1.0, 0.98, 0.90) * whiteHot * 2.0;

        // En 1-g terrestre, el hollín sube acelerado por boyamiento generando la punta amarilla (Foto 1 NASA izquierda)
        if (u_gravity > 0.5) {
          float tipSoot = smoothstep(0.0, 0.38, q.y) * 1.9;
          colAmber += vec3(1.0, 0.72, 0.18) * tipSoot * 2.4;
          colWhite += vec3(1.0, 0.96, 0.88) * tipSoot * 1.3;
        }

        vec3 rgb = colBlue + colViolet + colAmber + colWhite;
        float alpha = clamp(blueShell * 1.45 + violetCore * 0.85 + amberSoot * 1.15, 0.0, 1.0);

        // Extinción si se supera el límite de disipación térmica
        if (u_extinctionProb > 0.5) {
          float dim = max(0.08, 1.0 - (u_extinctionProb - 0.5) / 0.5);
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

            // Cuadrícula limpia sin fwidth
            vec2 gridFract = abs(fract(hit.xz * 3.2) - 0.5);
            float gridLine = step(0.465, max(gridFract.x, gridFract.y));
            float gridFade = smoothstep(2.6, 0.2, distXZ);

            vec3 gridCol = (u_isDark > 0.5) ? vec3(0.12, 0.55, 1.0) : vec3(0.05, 0.42, 0.88);
            vec3 floorBase = (u_isDark > 0.5) ? vec3(0.04, 0.04, 0.05) : vec3(0.92, 0.93, 0.95);

            // Reflejo lumínico del fuego sobre el piso
            float glowFactor = smoothstep(1.4, 0.0, distXZ) * 0.4;
            vec3 flameReflection = vec3(0.08, 0.42, 1.0) * glowFactor + vec3(1.0, 0.55, 0.1) * glowFactor * 0.4;

            color = mix(floorBase, gridCol, gridLine * 0.25 * gridFade) + flameReflection;
          }
        }

        // 2. MUESTRA DE COMBUSTIBLE SÓLIDO (PMMA / SIBAL / Nomex / Delrin / Silicone)
        vec3 plateMin = vec3(-0.55, -0.22, -0.14);
        vec3 plateMax = vec3(0.55, -0.12, 0.14);
        vec2 boxT = intersectBox(ro, rd, plateMin, plateMax);

        float substrateHitT = -1.0;
        if (boxT.x > 0.0 && boxT.x < boxT.y) {
          if (tFloor < 0.0 || boxT.x < tFloor) {
            substrateHitT = boxT.x;
            vec3 hitP = ro + boxT.x * rd;
            vec3 normal = vec3(0.0, 1.0, 0.0);
            if (abs(hitP.x - plateMin.x) < 0.005) normal = vec3(-1.0, 0.0, 0.0);
            else if (abs(hitP.x - plateMax.x) < 0.005) normal = vec3(1.0, 0.0, 0.0);
            else if (abs(hitP.z - plateMin.z) < 0.005) normal = vec3(0.0, 0.0, -1.0);
            else if (abs(hitP.z - plateMax.z) < 0.005) normal = vec3(0.0, 0.0, 1.0);

            vec3 plateCol = (u_isDark > 0.5) ? vec3(0.18, 0.19, 0.21) : vec3(0.40, 0.42, 0.46);
            
            // Iluminación superior e incandescencia térmica de pirólisis en el centro
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

        // 3. RAYMARCHING VOLUMÉTRICO DE LA LLAMA 3D (NASA C-1998-485 / BASS-II)
        if (u_layer == 0.0 || u_layer == 1.0) {
          vec3 flameCenter = vec3(0.0, 0.06, 0.0);
          float o2Ratio = clamp((u_oxygen - 18.0) / 20.0, 0.0, 1.0);
          float boundRadius = 0.54 + o2Ratio * 0.22 + (u_flowVelocity / 25.0) * 0.35;
          vec2 tSphere = intersectSphere(ro, rd, flameCenter, boundRadius);

          if (tSphere.y > 0.0) {
            float tStart = max(0.05, tSphere.x);
            float tEnd = tSphere.y;
            
            // Detener el raymarching si el rayo choca con el piso o el sustrato antes
            if (tFloor > 0.0 && tFloor < tEnd) tEnd = tFloor;
            if (substrateHitT > 0.0 && substrateHitT < tEnd) tEnd = substrateHitT;

            if (tEnd > tStart) {
              const int STEPS = 34;
              float stepDist = (tEnd - tStart) / float(STEPS);
              vec3 accumColor = vec3(0.0);
              float accumAlpha = 0.0;
              float t = tStart + stepDist * 0.5;

              for (int i = 0; i < 34; i++) {
                vec3 p = ro + t * rd;
                vec4 samp = sampleMicrogravityFlame(p);

                if (samp.a > 0.001) {
                  float dens = samp.a * stepDist * 5.2;
                  accumColor += samp.rgb * dens * (1.0 - accumAlpha);
                  accumAlpha += dens;
                  if (accumAlpha >= 0.96) break;
                }
                t += stepDist;
              }

              // Fusión aditiva y volumétrica de la emisión lumínica (Efecto Limb Brightening)
              color = color * (1.0 - accumAlpha * 0.65) + accumColor;
            }
          }
        }

        // 4. MICRO-PARTÍCULAS DE HOLLÍN EN ÓRBITA 3D (NASA FLEX Photo 4)
        if (u_oxygen >= 23.0 && (u_layer == 0.0 || u_layer == 1.0)) {
          for (int k = 0; k < 20; k++) {
            float fk = float(k);
            float ang = u_time * 0.5 + fk * 0.314;
            float rad = 0.18 + sin(fk * 2.3) * 0.14;
            float py = 0.06 + cos(fk * 1.8 + u_time * 0.65) * 0.16;

            vec3 partPos = vec3(cos(ang) * rad, py, sin(ang) * rad);
            partPos.x += (u_flowDirection * (u_flowVelocity / 25.0) * 0.28) * sin(fk * 1.5);

            vec3 toP = partPos - ro;
            float proj = dot(toP, rd);
            if (proj > 0.0) {
              vec3 closeP = ro + proj * rd;
              float distP = length(closeP - partPos);
              float sparkGlow = smoothstep(0.035, 0.0, distP);
              if (sparkGlow > 0.0) {
                color += vec3(1.0, 0.68, 0.18) * sparkGlow * 2.2;
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
    else if (this.ignisService.activeLayer() === 'sensors') layerId = 2.0;
    else if (this.ignisService.activeLayer() === 'gases') layerId = 3.0;
    gl.uniform1f(this.uLayerLoc, layerId);

    gl.uniform1f(this.uGravityLoc, t.gravityG);
    gl.uniform1f(this.uIsVentingLoc, s.isVentingToSpace ? 1.0 : 0.0);

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

  public setLayer(layer: 'all' | 'flame' | 'sensors' | 'gases'): void {
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
