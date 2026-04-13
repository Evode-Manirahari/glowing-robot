import { useState, useEffect, useRef } from "react";
import type { ReplayFrame } from "../lib/api";

interface Props {
  frames: ReplayFrame[];
  waypoints: { x: number; y: number }[];
  obstacles: { x: number; y: number; radius: number }[];
  collisionTimes?: number[];
}

const W = 600;
const H = 400;
const PAD = 40;

function toCanvas(
  x: number,
  y: number,
  minX: number,
  maxX: number,
  minY: number,
  maxY: number,
): [number, number] {
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  const cx = PAD + ((x - minX) / rangeX) * (W - PAD * 2);
  const cy = H - PAD - ((y - minY) / rangeY) * (H - PAD * 2);
  return [cx, cy];
}

export default function ReplayViewer({ frames, waypoints, obstacles, collisionTimes = [] }: Props) {
  const [playing, setPlaying] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const allX = [...frames.map(f => f.x), ...waypoints.map(w => w.x), ...obstacles.map(o => o.x)];
  const allY = [...frames.map(f => f.y), ...waypoints.map(w => w.y), ...obstacles.map(o => o.y)];
  const minX = Math.min(...allX) - 0.5;
  const maxX = Math.max(...allX) + 0.5;
  const minY = Math.min(...allY) - 0.5;
  const maxY = Math.max(...allY) + 0.5;

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setCurrentIdx(i => {
          if (i >= frames.length - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        });
      }, 60);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, frames.length]);

  const collisionSet = new Set(collisionTimes.map(t => Math.round(t * 10)));
  const currentFrame = frames[currentIdx];

  function pathD() {
    return frames.slice(0, currentIdx + 1).map((f, i) => {
      const [cx, cy] = toCanvas(f.x, f.y, minX, maxX, minY, maxY);
      return `${i === 0 ? "M" : "L"} ${cx} ${cy}`;
    }).join(" ");
  }

  return (
    <div>
      <svg width={W} height={H} style={{ border: "1px solid #e5e7eb", borderRadius: 8, background: "#f9fafb", display: "block" }}>
        {/* Grid */}
        {[...Array(5)].map((_, i) => (
          <line key={i} x1={PAD + i * (W - PAD * 2) / 4} y1={PAD} x2={PAD + i * (W - PAD * 2) / 4} y2={H - PAD} stroke="#e5e7eb" strokeWidth={1} />
        ))}

        {/* Obstacles */}
        {obstacles.map((obs, i) => {
          const [cx, cy] = toCanvas(obs.x, obs.y, minX, maxX, minY, maxY);
          const rangeX = maxX - minX || 1;
          const r = (obs.radius / rangeX) * (W - PAD * 2);
          return <circle key={i} cx={cx} cy={cy} r={r} fill="#fee2e2" stroke="#ef4444" strokeWidth={1.5} />;
        })}

        {/* Waypoints */}
        {waypoints.map((wp, i) => {
          const [cx, cy] = toCanvas(wp.x, wp.y, minX, maxX, minY, maxY);
          return (
            <g key={i}>
              <circle cx={cx} cy={cy} r={6} fill="#dbeafe" stroke="#3b82f6" strokeWidth={1.5} />
              <text x={cx + 8} y={cy + 4} fontSize={10} fill="#3b82f6">WP{i + 1}</text>
            </g>
          );
        })}

        {/* Trajectory path */}
        {frames.length > 1 && (
          <path d={pathD()} fill="none" stroke="#6366f1" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* Collision dots */}
        {frames.slice(0, currentIdx + 1).filter(f => collisionSet.has(Math.round(f.t * 10))).map((f, i) => {
          const [cx, cy] = toCanvas(f.x, f.y, minX, maxX, minY, maxY);
          return <circle key={i} cx={cx} cy={cy} r={7} fill="#ef4444" opacity={0.8} />;
        })}

        {/* Robot */}
        {currentFrame && (() => {
          const [cx, cy] = toCanvas(currentFrame.x, currentFrame.y, minX, maxX, minY, maxY);
          const isCollision = collisionSet.has(Math.round(currentFrame.t * 10));
          return (
            <circle cx={cx} cy={cy} r={10} fill={isCollision ? "#dc2626" : "#111"} stroke="#fff" strokeWidth={2} />
          );
        })()}

        {/* Start / End labels */}
        {frames[0] && (() => {
          const [cx, cy] = toCanvas(frames[0].x, frames[0].y, minX, maxX, minY, maxY);
          return <text x={cx + 12} y={cy - 8} fontSize={10} fill="#6b7280">Start</text>;
        })()}
      </svg>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
        <button
          onClick={() => { setCurrentIdx(0); setPlaying(true); }}
          disabled={playing}
          style={{ background: "#111", color: "#fff", padding: "6px 16px", borderRadius: 6, border: "none", cursor: playing ? "not-allowed" : "pointer", fontSize: 13 }}
        >
          {playing ? "Playing..." : "Play"}
        </button>
        <button
          onClick={() => setPlaying(false)}
          disabled={!playing}
          style={{ padding: "6px 16px", borderRadius: 6, border: "1px solid #d1d5db", cursor: "pointer", fontSize: 13 }}
        >
          Pause
        </button>
        <input
          type="range"
          min={0}
          max={frames.length - 1}
          value={currentIdx}
          onChange={e => { setPlaying(false); setCurrentIdx(Number(e.target.value)); }}
          style={{ flex: 1 }}
        />
        <span style={{ fontSize: 12, color: "#6b7280", minWidth: 60 }}>
          t = {currentFrame?.t.toFixed(2)}s
        </span>
      </div>

      <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12, color: "#6b7280" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#111", display: "inline-block" }} /> Robot</span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444", display: "inline-block" }} /> Collision</span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#fee2e2", border: "1px solid #ef4444", display: "inline-block" }} /> Obstacle</span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#dbeafe", border: "1px solid #3b82f6", display: "inline-block" }} /> Waypoint</span>
      </div>
    </div>
  );
}
