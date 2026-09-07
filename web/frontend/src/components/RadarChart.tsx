import { PolarAngleAxis, PolarGrid, Radar, RadarChart as RechartsRadarChart, ResponsiveContainer } from "recharts";

export interface RadarDatum {
  label: string;
  value: number; // normalized 0-1
}

export function RadarChart({ data, height = 140 }: { data: RadarDatum[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={data} outerRadius="68%">
        <PolarGrid stroke="var(--border)" />
        <PolarAngleAxis dataKey="label" tick={{ fill: "var(--muted)", fontSize: 9 }} />
        <Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.35} isAnimationActive={false} />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
