import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

/**
 * SceneManager
 * Single responsibility: set up and maintain the four Three.js pillars
 *   - Scene
 *   - Camera
 *   - Renderer
 *   - Animation loop
 *
 * It knows nothing about React. It takes a native <canvas> and flat
 * parameters.
 */
export class SceneManager {
  private canvas: HTMLCanvasElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  private frame: THREE.Group;
  private patternMesh: THREE.Mesh | null;
  private controls: OrbitControls;
  private animId: number | null;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;

    // 1. SCENE
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f0f1a);

    // 2. CAMERA
    this.camera = new THREE.PerspectiveCamera(
      60,
      canvas.clientWidth / canvas.clientHeight,
      0.1,
      100,
    );
    this.camera.position.set(0, 0, 3);

    // 3. RENDERER
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      // Required so the PNG export can read the canvas outside the frame in
      // which it was drawn.
      preserveDrawingBuffer: true,
    });
    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);

    // Lights
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(5, 5, 5);
    this.scene.add(dirLight);

    // Axes helper (X = red, Y = green, Z = blue)
    this.scene.add(new THREE.AxesHelper(2));

    // The renderer is Y-up; the contract is the physical antenna frame, which
    // is Z-up. Rotating -90 degrees about X maps (x, y, z) to (x, z, -y), so
    // antenna +Z appears as renderer +Y. Applying it here, on a container,
    // keeps the vertex data in antenna coordinates for export and comparison.
    this.frame = new THREE.Group();
    this.frame.rotation.x = -Math.PI / 2;
    this.scene.add(this.frame);

    this.patternMesh = null;

    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    // Keyboard support is required by RNF-05 (multiple input devices).
    this.controls.listenToKeyEvents(window);

    // 4. ANIMATION LOOP
    this.animId = null;
  }

  /**
   * Installs a pattern geometry, replacing and disposing any previous one.
   * The geometry is expected in the Z-up antenna frame; the container
   * handles the renderer's Y-up convention.
   */
  setPatternGeometry(geometry: THREE.BufferGeometry): void {
    if (this.patternMesh) {
      this.frame.remove(this.patternMesh);
      this.patternMesh.geometry.dispose();
      (this.patternMesh.material as THREE.Material).dispose();
    }

    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      shininess: 40,
    });

    this.patternMesh = new THREE.Mesh(geometry, material);
    this.frame.add(this.patternMesh);
  }

  dispose(): void {
    this.stopLoop();
    this.controls.dispose();
    if (this.patternMesh) {
      this.patternMesh.geometry.dispose();
      (this.patternMesh.material as THREE.Material).dispose();
    }
    this.renderer.dispose();
  }

  startLoop(): void {
    const animate = () => {
      this.animId = requestAnimationFrame(animate);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  stopLoop(): void {
    if (this.animId !== null) {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
  }

  /**
   * Captures the current view as a PNG data URL.
   *
   * The renderer is created with preserveDrawingBuffer so the buffer is
   * still readable outside the frame that drew it; without it this returns
   * a blank image.
   */
  captureSnapshot(): string {
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL("image/png");
  }

  /** Resizes when the container changes. */
  resize(w: number, h: number): void {
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }
}
