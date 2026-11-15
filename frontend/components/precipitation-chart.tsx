import type { YearStat } from '@/lib/types';

interface Props {
  years: YearStat[];
  ariaLabel: string;
  /** Formats a value in mm for the hover text. */
  format: (value: number) => string;
}

const BAR = 20;
const PITCH = 30;
const LEFT = 48;
const TOP = 12;
const PLOT_HEIGHT = 190;
const BOTTOM = 28;
const TICKS = 4;
// With many years only some labels are drawn, so they stay readable when the chart shrinks.
const LABEL_EVERY = 5;
const MANY_YEARS = 12;

function niceCeil(value: number): number {
  const power = 10 ** Math.floor(Math.log10(value));
  const fraction = value / power;
  const step = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  return step * power;
}

/**
 * Total precipitation for each year. Drawn with the product accent and the muted text
 * token, so it follows light and dark mode. The yearly table beside it carries the same
 * numbers for anyone who cannot read a chart.
 */
export function PrecipitationChart({ years, ariaLabel, format }: Props) {
  const values = years.map((year) => year.precipitation_mm ?? 0);
  const top = niceCeil(Math.max(...values, 1));
  const width = LEFT + years.length * PITCH;
  const height = TOP + PLOT_HEIGHT + BOTTOM;
  const y = (value: number) => TOP + PLOT_HEIGHT - (value / top) * PLOT_HEIGHT;

  return (
    <svg
      className="zira-chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
    >
      {Array.from({ length: TICKS + 1 }, (_, index) => {
        const value = (top / TICKS) * index;
        return (
          <g key={index}>
            <line className="zira-chart-grid" x1={LEFT} x2={width} y1={y(value)} y2={y(value)} />
            <text className="zira-chart-text" x={LEFT - 6} y={y(value) + 4} textAnchor="end">
              {Math.round(value)}
            </text>
          </g>
        );
      })}
      {years.map((year, index) => {
        const value = year.precipitation_mm ?? 0;
        const x = LEFT + index * PITCH + (PITCH - BAR) / 2;
        const showLabel =
          years.length <= MANY_YEARS || index % LABEL_EVERY === 0 || index === years.length - 1;
        return (
          <g key={year.year}>
            <rect className="zira-chart-bar" x={x} y={y(value)} width={BAR} height={TOP + PLOT_HEIGHT - y(value)}>
              <title>{`${year.year}: ${format(value)} mm`}</title>
            </rect>
            {showLabel && (
              <text
                className="zira-chart-text"
                x={x + BAR / 2}
                y={TOP + PLOT_HEIGHT + 18}
                textAnchor="middle"
              >
                {year.year}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
