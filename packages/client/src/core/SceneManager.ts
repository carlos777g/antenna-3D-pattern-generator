import * as THREE from "three";

/**
 * SceneManager
 * Responsabilidad única: configurar y mantener los 4 pilares de Three.js
 *   - Scene
 *   - Camera
 *   - Renderer
 *   - Animation Loop
 *
 * NO sabe nada de React. Recibe un <canvas> nativo y parámetros planos.
 */
export class SceneManager {
  constructor(canvas) {
    this.canvas = canvas;

    // 1. SCENE
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f0f1a);

    // 2. CAMERA
    this.camera = new THREE.PerspectiveCamera(
      60,
      canvas.clientWidth / canvas.clientHeight,
      0.1,
      100
    );
    this.camera.position.set(0, 0, 3);

    // 3. RENDERER
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);

    // Luces
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(5, 5, 5);
    this.scene.add(dirLight);

    // Helper de ejes (X=rojo, Y=verde, Z=azul)
    this.scene.add(new THREE.AxesHelper(2));

    // Mesh activo (puede ser reemplazado por GeometryBuilder)
    this.mesh = null;

    // 4. ANIMATION LOOP
    this.animId = null;

    // Orbit manual
    this._initOrbit();
  }

  // ------------------------------------------------------------------
  // Agrega o reemplaza el mesh en la escena.
  // GeometryBuilder llama esto con el mesh ya construido.
  // ------------------------------------------------------------------
  setMesh(mesh) {
    if (this.mesh) {
      this.scene.remove(this.mesh);
      this.mesh.geometry.dispose();
      this.mesh.material.dispose();
    }
    this.mesh = mesh;
    this.scene.add(this.mesh);
  }

  // ------------------------------------------------------------------
  // Loop de animación
  // ------------------------------------------------------------------
  startLoop() {
    const animate = () => {
      this.animId = requestAnimationFrame(animate);
      this._updateOrbit();
      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  stopLoop() {
    cancelAnimationFrame(this.animId);
  }

  // ------------------------------------------------------------------
  // Redimensionar cuando cambia el contenedor
  // ------------------------------------------------------------------
  resize(w, h) {
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  // ------------------------------------------------------------------
  // Orbit: drag → rotar, scroll → zoom
  // ------------------------------------------------------------------
  _initOrbit() {
    this._orbit = { active: false, x: 0, y: 0, rotX: 0 };

    this.canvas.addEventListener("mousedown", (e) => {
      this._orbit.active = true;
      this._orbit.x = e.clientX;
      this._orbit.y = e.clientY;
    });
    this.canvas.addEventListener("mouseup", () => {
      this._orbit.active = false;
    });
    this.canvas.addEventListener("mousemove", (e) => {
      if (!this._orbit.active) return;
      this._orbit.rotX += (e.clientY - this._orbit.y) * 0.005;
      this._orbit.x = e.clientX;
      this._orbit.y = e.clientY;
    });
    this.canvas.addEventListener("wheel", (e) => {
      this.camera.position.z = Math.max(
        1,
        Math.min(10, this.camera.position.z + e.deltaY * 0.005)
      );
    });
  }

  _updateOrbit() {
    if (!this.mesh) return;
    this.mesh.rotation.x = this._orbit.rotX;
    this.mesh.rotation.y += 0.004; // rotación automática suave
  }
}