import { useState, useEffect, useRef } from "react";

// ─── Paleta y estilos base ────────────────────────────────────────────────────
const C = {
  bg:      "#0d0f14",
  surface: "#141720",
  border:  "#1e2330",
  accent:  "#4fffb0",
  warn:    "#ffb347",
  danger:  "#ff5f6d",
  text:    "#e8eaf0",
  muted:   "#6b7280",
};

// ─── Arquetipos (mirror del Python, para preview sin backend) ─────────────────
const ARCHETYPES = [
  {
    key: "polarizacion_extrema",
    nombre_ui: "Polarización Extrema",
    descripcion_ui: "Dos bandos irreconciliables. El centro es tierra de nadie.",
    icono: "⚡",
    tag: "Conflicto",
    tagColor: C.danger,
    lambda_social: 0.4,
    temperature: 0.03,
    attractors: [-0.85, 0.85],
    repellers: [0.0],
  },
  {
    key: "consenso_moderado",
    nombre_ui: "Búsqueda de Consenso",
    descripcion_ui: "La sociedad tiende a acuerdos. El centro atrae a todos.",
    icono: "🤝",
    tag: "Estabilidad",
    tagColor: C.accent,
    lambda_social: 0.6,
    temperature: 0.02,
    attractors: [0.0],
    repellers: [],
  },
  {
    key: "fragmentacion_3_grupos",
    nombre_ui: "Tres Facciones",
    descripcion_ui: "La sociedad se divide en tres grupos que coexisten sin fusionarse.",
    icono: "🔺",
    tag: "Fragmentación",
    tagColor: C.warn,
    lambda_social: 0.5,
    temperature: 0.04,
    attractors: [-0.7, 0.0, 0.7],
    repellers: [],
  },
  {
    key: "caos_social",
    nombre_ui: "Caos Social",
    descripcion_ui: "Sin estructura clara. Cada agente actúa por impulso propio.",
    icono: "🌀",
    tag: "Caos",
    tagColor: "#a855f7",
    lambda_social: 0.3,
    temperature: 0.15,
    attractors: [],
    repellers: [],
  },
  {
    key: "consenso_forzado",
    nombre_ui: "Uniformidad Forzada",
    descripcion_ui: "Presión institucional fuerte hacia una sola posición.",
    icono: "📢",
    tag: "Control",
    tagColor: "#60a5fa",
    lambda_social: 0.2,
    temperature: 0.01,
    attractors: [0.3],
    repellers: [-0.5],
  },
  {
    key: "radicalizacion_progresiva",
    nombre_ui: "Radicalización Progresiva",
    descripcion_ui: "Los agentes empiezan en el centro pero son jalados hacia los extremos.",
    icono: "📉",
    tag: "Riesgo",
    tagColor: C.danger,
    lambda_social: 0.35,
    temperature: 0.02,
    attractors: [-0.9, 0.9],
    repellers: [0.0],
  },
];

// ─── Glossary bilingüe para tooltips ─────────────────────────────────────────
const GLOSSARY = {
  "Energía Global": "La 'presión' del escenario sobre todos los agentes. Como la cultura, la propaganda o las instituciones.",
  "Cohesión de Red": "Qué tanto pesan las opiniones de tus contactos directos sobre la tuya.",
  "Temperatura Social": "El nivel de caos o imprevisibilidad del sistema. Alta temp = decisiones más erráticas.",
  "Polarización": "Qué tan dividida está la sociedad. Alta = grupos muy separados.",
  "Tensión Total": "Energía acumulada del sistema. Si sube, el conflicto está creciendo.",
  "Disonancia de Red": "Qué tan diferente piensas respecto a tus vecinos directos. Alta = burbujas más fuertes.",
};

// ─── Simulación simplificada en JS (para preview) ────────────────────────────
function runSimulation(archetype, nAgents, steps) {
  const opinions = Array.from({ length: nAgents }, () => (Math.random() * 2 - 1));
  const history  = [opinions.slice()];

  for (let t = 0; t < steps; t++) {
    const newOps = opinions.map((x, i) => {
      // Fuerza global: suma de atractores
      let gGlobal = 0;
      for (const c of archetype.attractors) gGlobal += 2 * 1.5 * (x - c);
      for (const r of archetype.repellers)  gGlobal -= 1.5 * (-(x - r) / 0.09) * Math.exp(-Math.pow(x - r, 2) / 0.18);

      // Fuerza local (vecinos aleatorios simplificado)
      const neighbor = opinions[(i + 1) % nAgents];
      const gLocal   = (x - neighbor);

      const score    = (1 - archetype.lambda_social) * gGlobal + archetype.lambda_social * gLocal;
      const noise    = (Math.random() - 0.5) * 2 * Math.sqrt(2 * 0.01 * archetype.temperature);
      const next     = x - 0.01 * score + noise;
      return Math.max(-1, Math.min(1, next));
    });
    opinions.splice(0, opinions.length, ...newOps);
    if (t % 10 === 0) history.push(opinions.slice());
  }
  return history;
}

function metrics(opinions) {
  const mean = opinions.reduce((a, b) => a + b, 0) / opinions.length;
  const std  = Math.sqrt(opinions.reduce((a, b) => a + (b - mean) ** 2, 0) / opinions.length);
  return {
    polarizacion:  std.toFixed(3),
    posicion_media: mean.toFixed(3),
    tension: (opinions.reduce((a, b) => a + Math.abs(b), 0) / opinions.length).toFixed(3),
  };
}

// ─── Componente de Tooltip ────────────────────────────────────────────────────
function Tooltip({ term, children }) {
  const [show, setShow] = useState(false);
  return (
    <span style={{ position: "relative", display: "inline-block" }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{ borderBottom: `1px dashed ${C.muted}`, cursor: "help" }}
      >
        {children}
      </span>
      {show && (
        <div style={{
          position: "absolute", bottom: "120%", left: "50%",
          transform: "translateX(-50%)",
          background: "#1e2330", border: `1px solid ${C.border}`,
          borderRadius: 8, padding: "8px 12px", width: 220,
          fontSize: 12, color: C.text, zIndex: 100,
          boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
        }}>
          {GLOSSARY[term] || ""}
        </div>
      )}
    </span>
  );
}

// ─── Mini gráfico de distribución ────────────────────────────────────────────
function OpinionHistogram({ opinions }) {
  const bins = 20;
  const counts = new Array(bins).fill(0);
  for (const op of opinions) {
    const idx = Math.min(bins - 1, Math.floor((op + 1) / 2 * bins));
    counts[idx]++;
  }
  const max = Math.max(...counts, 1);

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 60, width: "100%" }}>
      {counts.map((c, i) => {
        const pos = (i / bins) * 2 - 1;
        const color = pos < -0.3 ? "#ff5f6d" : pos > 0.3 ? "#60a5fa" : C.accent;
        return (
          <div key={i} style={{
            flex: 1, height: `${(c / max) * 100}%`,
            background: color, opacity: 0.8, borderRadius: "2px 2px 0 0",
            transition: "height 0.3s ease",
          }} />
        );
      })}
    </div>
  );
}

// ─── Tarjeta de Métrica ───────────────────────────────────────────────────────
function MetricCard({ label, value, color, tooltip }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 10, padding: "12px 16px", flex: 1,
    }}>
      <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>
        {tooltip ? <Tooltip term={tooltip}>{label}</Tooltip> : label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color || C.text, fontFamily: "monospace" }}>
        {value}
      </div>
    </div>
  );
}

// ─── Componente Principal ─────────────────────────────────────────────────────
export default function BeyondSightUI() {
  const [selected, setSelected]   = useState(null);
  const [nAgents, setNAgents]     = useState(50);
  const [steps, setSteps]         = useState(200);
  const [simData, setSimData]     = useState(null);
  const [running, setRunning]     = useState(false);
  const [frame, setFrame]         = useState(0);
  const [lambdaOverride, setLambdaOverride] = useState(null);
  const [tempOverride, setTempOverride]     = useState(null);
  const intervalRef = useRef(null);

  // Limpiar al cambiar escenario
  useEffect(() => {
    setSimData(null);
    setFrame(0);
    setLambdaOverride(null);
    setTempOverride(null);
    if (intervalRef.current) clearInterval(intervalRef.current);
    setRunning(false);
  }, [selected]);

  function handleRun() {
    if (!selected) return;
    const arch = {
      ...selected,
      lambda_social: lambdaOverride ?? selected.lambda_social,
      temperature:   tempOverride   ?? selected.temperature,
    };
    const data = runSimulation(arch, nAgents, steps);
    setSimData(data);
    setFrame(0);
    setRunning(true);

    let f = 0;
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      f++;
      if (f >= data.length) { clearInterval(intervalRef.current); setRunning(false); f = data.length - 1; }
      setFrame(f);
    }, 80);
  }

  const currentOpinions = simData ? simData[Math.min(frame, simData.length - 1)] : [];
  const m = currentOpinions.length > 0 ? metrics(currentOpinions) : null;

  return (
    <div style={{
      background: C.bg, minHeight: "100vh", color: C.text,
      fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
      padding: "24px", boxSizing: "border-box",
    }}>

      {/* Encabezado */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: C.accent, letterSpacing: 3, marginBottom: 6 }}>
          BEYONDSIGHT · SIMULADOR DE DINÁMICAS SOCIALES
        </div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: C.text }}>
          Arquitecto Social
        </h1>
        <p style={{ margin: "6px 0 0", fontSize: 13, color: C.muted }}>
          Selecciona un escenario y observa cómo evoluciona la opinión pública.
        </p>
      </div>

      {/* Grid de Arquetipos */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: C.muted, letterSpacing: 2, marginBottom: 12 }}>
          ESCENARIOS DISPONIBLES
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
          {ARCHETYPES.map(arch => (
            <div
              key={arch.key}
              onClick={() => setSelected(arch)}
              style={{
                background: selected?.key === arch.key ? "#1a2035" : C.surface,
                border: `1px solid ${selected?.key === arch.key ? C.accent : C.border}`,
                borderRadius: 10, padding: "14px", cursor: "pointer",
                transition: "all 0.2s",
                boxShadow: selected?.key === arch.key ? `0 0 12px ${C.accent}22` : "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <span style={{ fontSize: 22 }}>{arch.icono}</span>
                <span style={{
                  fontSize: 10, padding: "2px 8px", borderRadius: 20,
                  background: arch.tagColor + "22", color: arch.tagColor, fontWeight: 600,
                }}>
                  {arch.tag}
                </span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, marginTop: 8, color: C.text }}>{arch.nombre_ui}</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4, lineHeight: 1.4 }}>{arch.descripcion_ui}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Panel de Control (visible si hay selección) */}
      {selected && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: 20, marginBottom: 20,
        }}>
          <div style={{ fontSize: 11, color: C.muted, letterSpacing: 2, marginBottom: 16 }}>
            AJUSTES DE SIMULACIÓN — {selected.nombre_ui}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

            {/* Agentes */}
            <div>
              <label style={{ fontSize: 12, color: C.muted }}>
                Agentes en la simulación: <span style={{ color: C.text }}>{nAgents}</span>
              </label>
              <input type="range" min={10} max={200} value={nAgents}
                onChange={e => setNAgents(+e.target.value)}
                style={{ width: "100%", accentColor: C.accent, marginTop: 6 }} />
              <div style={{ fontSize: 11, color: C.muted }}>
                ↳ Cuántas personas simulamos en la red.
              </div>
            </div>

            {/* Pasos */}
            <div>
              <label style={{ fontSize: 12, color: C.muted }}>
                Duración (pasos de tiempo): <span style={{ color: C.text }}>{steps}</span>
              </label>
              <input type="range" min={50} max={500} step={50} value={steps}
                onChange={e => setSteps(+e.target.value)}
                style={{ width: "100%", accentColor: C.accent, marginTop: 6 }} />
              <div style={{ fontSize: 11, color: C.muted }}>
                ↳ Cuántos ciclos de interacción simulamos.
              </div>
            </div>

            {/* Lambda social */}
            <div>
              <label style={{ fontSize: 12, color: C.muted }}>
                <Tooltip term="Cohesión de Red">Cohesión de Red (λ)</Tooltip>:&nbsp;
                <span style={{ color: C.accent }}>{(lambdaOverride ?? selected.lambda_social).toFixed(2)}</span>
              </label>
              <input type="range" min={0} max={1} step={0.05}
                value={lambdaOverride ?? selected.lambda_social}
                onChange={e => setLambdaOverride(+e.target.value)}
                style={{ width: "100%", accentColor: C.warn, marginTop: 6 }} />
              <div style={{ fontSize: 11, color: C.muted }}>
                ↳ 0 = la propaganda domina · 1 = solo importan tus amigos
              </div>
            </div>

            {/* Temperatura */}
            <div>
              <label style={{ fontSize: 12, color: C.muted }}>
                <Tooltip term="Temperatura Social">Temperatura Social (T)</Tooltip>:&nbsp;
                <span style={{ color: C.warn }}>{(tempOverride ?? selected.temperature).toFixed(3)}</span>
              </label>
              <input type="range" min={0.005} max={0.2} step={0.005}
                value={tempOverride ?? selected.temperature}
                onChange={e => setTempOverride(+e.target.value)}
                style={{ width: "100%", accentColor: "#a855f7", marginTop: 6 }} />
              <div style={{ fontSize: 11, color: C.muted }}>
                ↳ Baja = conducta predecible · Alta = caos e impulsividad
              </div>
            </div>
          </div>

          <button
            onClick={handleRun}
            disabled={running}
            style={{
              background: running ? C.surface : C.accent,
              color: running ? C.muted : C.bg,
              border: `1px solid ${running ? C.border : C.accent}`,
              borderRadius: 8, padding: "10px 24px",
              fontSize: 13, fontWeight: 700, cursor: running ? "not-allowed" : "pointer",
              fontFamily: "inherit", transition: "all 0.2s",
            }}
          >
            {running ? "⏳ Simulando..." : "▶ Ejecutar Simulación"}
          </button>
        </div>
      )}

      {/* Resultados */}
      {simData && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Métricas */}
          <div>
            <div style={{ fontSize: 11, color: C.muted, letterSpacing: 2, marginBottom: 10 }}>
              ESTADO ACTUAL DEL SISTEMA — paso {frame * 10}/{steps}
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <MetricCard
                label="Polarización"
                tooltip="Polarización"
                value={m?.polarizacion}
                color={+m?.polarizacion > 0.4 ? C.danger : C.accent}
              />
              <MetricCard
                label="Posición Media"
                value={m?.posicion_media}
                color={Math.abs(+m?.posicion_media) > 0.3 ? C.warn : C.accent}
              />
              <MetricCard
                label="Tensión Total"
                tooltip="Tensión Total"
                value={m?.tension}
                color={+m?.tension > 0.5 ? C.danger : C.text}
              />
            </div>
          </div>

          {/* Histograma */}
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 12, padding: 20,
          }}>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 12 }}>
              DISTRIBUCIÓN DE OPINIONES — Rojo: izquierda · Verde: centro · Azul: derecha
            </div>
            <OpinionHistogram opinions={currentOpinions} />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 10, color: C.muted }}>
              <span>-1 (Radical)</span>
              <span>0 (Neutral)</span>
              <span>+1 (Radical)</span>
            </div>
          </div>

          {/* Leyenda de conceptos */}
          <div style={{
            background: "#0f1218", border: `1px solid ${C.border}`,
            borderRadius: 10, padding: 16,
          }}>
            <div style={{ fontSize: 11, color: C.muted, letterSpacing: 2, marginBottom: 10 }}>
              GLOSARIO RÁPIDO
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {Object.entries(GLOSSARY).slice(0, 4).map(([term, def]) => (
                <div key={term} style={{ fontSize: 11 }}>
                  <span style={{ color: C.accent }}>{term}:</span>
                  <span style={{ color: C.muted }}> {def}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
