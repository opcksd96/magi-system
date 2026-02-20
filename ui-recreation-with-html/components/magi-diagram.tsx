/**
 * MAGI System Diagram - Center Layer (SVG)
 *
 * Coordinate system: 1460 x 820 viewBox
 *
 * All cells are inset from the edges to ensure dark background
 * is visible around all sides (matching reference design).
 *
 * BALTHASAR-2 (top center):
 *   Rectangular with bottom-left and bottom-right corners cut.
 *   Starts below the header area (~y=120), centered horizontally.
 *
 * CASPER-3 (bottom-left):
 *   Rectangular with only top-right corner cut diagonally.
 *
 * MELCHIOR-1 (bottom-right):
 *   Rectangular with only top-left corner cut diagonally.
 *
 * All cells have dark margin around them (not bleeding to edges).
 * Connection lines run along the gap boundaries between cells
 * with diamond connectors at arm junctions.
 * Horizontal orange bar connects CASPER-MELCHIOR through MAGI hub.
 */
export default function MagiDiagram() {
  const cyan = "#00e5ff"
  const dark = "#0d1210"
  const border = "#9a6b20"
  const orange = "#e8a000"
  const bw = 3

  /*
   * Geometry with proper margins:
   *
   * Left margin:   60px
   * Right margin:  60px
   * Top margin:    120px (space for headers)
   * Bottom margin: 50px
   *
   * BALTHASAR-2 (top center):
   *   TL: (430, 120)  TR: (1030, 120)
   *   Vertical sides down to y=360 then diagonal cuts
   *   BL cut: (430, 360) -> (650, 490)
   *   BR cut: (810, 490) -> (1030, 360)
   *
   * CASPER-3 (bottom-left):
   *   TL: (60, 445)   TR-cut-start: (540, 445)
   *   TR-cut-end: (625, 555)
   *   BR: (625, 770)  BL: (60, 770)
   *
   * MELCHIOR-1 (bottom-right):
   *   TL-cut-end: (835, 555)  TL-cut-start: (920, 445)
   *   TR: (1400, 445)
   *   BR: (1400, 770) BL: (835, 770)
   */

  // Cell polygons
  const balt = "430,120 1030,120 1030,360 810,490 650,490 430,360"
  const casp = "60,445 540,445 625,555 625,770 60,770"
  const melc = "835,555 920,445 1400,445 1400,770 835,770"

  // Diamond connector positions (at midpoint of each arm)
  const dLeftCx = (650 + 625) / 2   // 637.5
  const dLeftCy = (490 + 555) / 2   // 522.5
  const dRightCx = (810 + 835) / 2  // 822.5
  const dRightCy = (490 + 555) / 2  // 522.5
  const dSize = 18

  // Orange bar Y position (between MAGI text and bottom of hub)
  const barY = 680

  return (
    <svg
      viewBox="0 0 1460 820"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="absolute inset-0 h-full w-full"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* ============================================ */}
      {/* BALTHASAR-2 (top center)                     */}
      {/* BL & BR corners cut diagonally               */}
      {/* ============================================ */}
      <polygon
        points={balt}
        fill={cyan}
        stroke={border}
        strokeWidth={bw}
        strokeLinejoin="miter"
      />
      <text
        x="730" y="230"
        textAnchor="middle"
        dominantBaseline="middle"
        fill={dark}
        fontSize="42"
        fontWeight="bold"
        fontFamily="sans-serif"
        letterSpacing="3"
      >
        {"BALTHASAR\u20142"}
      </text>

      {/* ============================================ */}
      {/* CASPER-3 (bottom-left)                       */}
      {/* Only TR corner cut diagonally                */}
      {/* ============================================ */}
      <polygon
        points={casp}
        fill={cyan}
        stroke={border}
        strokeWidth={bw}
        strokeLinejoin="miter"
      />
      <text
        x="320" y="610"
        textAnchor="middle"
        dominantBaseline="middle"
        fill={dark}
        fontSize="38"
        fontWeight="bold"
        fontFamily="sans-serif"
        letterSpacing="3"
      >
        {"CASPER\u20143"}
      </text>

      {/* ============================================ */}
      {/* MELCHIOR-1 (bottom-right)                    */}
      {/* Only TL corner cut diagonally                */}
      {/* ============================================ */}
      <polygon
        points={melc}
        fill={cyan}
        stroke={border}
        strokeWidth={bw}
        strokeLinejoin="miter"
      />
      <text
        x="1140" y="610"
        textAnchor="middle"
        dominantBaseline="middle"
        fill={dark}
        fontSize="38"
        fontWeight="bold"
        fontFamily="sans-serif"
        letterSpacing="3"
      >
        {"MELCHIOR\u20141"}
      </text>

      {/* ============================================ */}
      {/* ORANGE NETWORK CONNECTION LINES              */}
      {/* Run along the gap boundaries between cells   */}
      {/* ============================================ */}

      {/* Left arm: BALTHASAR BL corner -> CASPER TR corner */}
      <line
        x1="650" y1="490" x2="625" y2="555"
        stroke={orange} strokeWidth="4"
      />
      {/* Right arm: BALTHASAR BR corner -> MELCHIOR TL corner */}
      <line
        x1="810" y1="490" x2="835" y2="555"
        stroke={orange} strokeWidth="4"
      />

      {/* Horizontal bar: CASPER right edge -> MELCHIOR left edge */}
      <rect
        x="625" y={barY} width={835 - 625} height="12"
        fill={orange} rx="1"
      />

      {/* ============================================ */}
      {/* CONNECTOR DIAMONDS at arm junctions          */}
      {/* ============================================ */}
      <rect
        x={dLeftCx - dSize / 2}
        y={dLeftCy - dSize / 2}
        width={dSize} height={dSize}
        fill={orange} stroke={dark} strokeWidth="2"
        transform={`rotate(45, ${dLeftCx}, ${dLeftCy})`}
      />
      <rect
        x={dRightCx - dSize / 2}
        y={dRightCy - dSize / 2}
        width={dSize} height={dSize}
        fill={orange} stroke={dark} strokeWidth="2"
        transform={`rotate(45, ${dRightCx}, ${dRightCy})`}
      />

      {/* ============================================ */}
      {/* MAGI LABEL                                   */}
      {/* Centered in the hub between bottom panels,   */}
      {/* above the orange horizontal bar              */}
      {/* ============================================ */}
      <text
        x="730" y="645"
        textAnchor="middle"
        dominantBaseline="middle"
        fill={orange}
        fontSize="48"
        fontWeight="bold"
        fontFamily="'Georgia', 'Times New Roman', serif"
        letterSpacing="6"
      >
        MAGI
      </text>
    </svg>
  )
}
