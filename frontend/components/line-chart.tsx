interface Series {
  label: string;
  values: (number | null)[];
  /** `primary` follows the product accent; `muted` is the quiet reference line. */
  tone: 'primary' | 'muted';
  dashed?: boolean;
}

interface Props {
  /** One ISO date per point, shared by every series. */
  dates: string[];
  series: Series[];
  yMax: number;
  ariaLabel: string;
  formatDate: (iso: string) => string;
  /** Formats a value on the vertical axis in the reader's language. */
  formatTick?: (value: number) => string;
}

const WIDTH = 720;
const HEIGHT = 230;
const LEFT = 48;
const RIGHT = 12;
const TOP = 12;
const BOTTOM = 28;
const TICKS = 4;
const X_LABELS = 5;

// Steps whose quarter is a clean number, so the four grid lines read 0, 70, 140, 210, 280
// rather than rounded halves.
const NICE_STEPS = [1, 1.2, 1.6, 2, 2.4, 2.8, 3.2, 4, 5, 6, 8, 10];

function niceCeil(value: number): number {
  const power = 10 ** Math.floor(Math.log10(Math.max(value, 1e-9)));
  const fraction = value / power;
  return (NICE_STEPS.find((step) => step >= fraction - 1e-9) ?? 10) * power;
}

/**
 * Lines over time, drawn with theme tokens so they follow light and dark mode. A gap in the
 * data (a null) breaks the line instead of being drawn as zero. The table beside the chart
 * carries the same numbers.
 */
export function LineChart({
  dates,
  series,
  yMax,
  ariaLabel,
  formatDate,
  formatTick = (value) => String(Math.round(value * 10) / 10),
}: Props) {
  const top = niceCeil(yMax);
  const last = Math.max(dates.length - 1, 1);
  const x = (index: number) => LEFT + (index / last) * (WIDTH - LEFT - RIGHT);
  const y = (value: number) => TOP + (1 - Math.min(value, top) / top) * (HEIGHT - TOP - BOTTOM);

  const path = (values: (number | null)[]) => {
    let drawing = false;
    return values
      .map((value, index) => {
        if (value === null) {
          drawing = false;
          return '';
        }
        const command = drawing ? 'L' : 'M';
        drawing = true;
        return `${command}${x(index).toFixed(1)} ${y(value).toFixed(1)}`;
      })
      .join(' ');
  };

  const labelIndexes = Array.from({ length: X_LABELS }, (_, step) =>
    Math.round((step / (X_LABELS - 1)) * last),
  );

  return (
    <svg
      className="zira-chart"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={ariaLabel}
    >
      {Array.from({ length: TICKS + 1 }, (_, index) => {
        const value = (top / TICKS) * index;
        return (
          <g key={index}>
            <line className="zira-chart-grid" x1={LEFT} x2={WIDTH - RIGHT} y1={y(value)} y2={y(value)} />
            <text className="zira-chart-text" x={LEFT - 6} y={y(value) + 4} textAnchor="end">
              {formatTick(value)}
            </text>
          </g>
        );
      })}
      {labelIndexes.map((index) => (
        <text
          key={index}
          className="zira-chart-text"
          x={x(index)}
          y={HEIGHT - 8}
          textAnchor={index === 0 ? 'start' : index === last ? 'end' : 'middle'}
        >
          {formatDate(dates[index])}
        </text>
      ))}
      {series.map((line) => (
        <path
          key={line.label}
          className={[
            'zira-line',
            line.tone === 'muted' ? 'zira-line--muted' : '',
            line.dashed ? 'zira-line--dashed' : '',
          ]
            .filter(Boolean)
            .join(' ')}
          d={path(line.values)}
        >
          <title>{line.label}</title>
        </path>
      ))}
    </svg>
  );
}
