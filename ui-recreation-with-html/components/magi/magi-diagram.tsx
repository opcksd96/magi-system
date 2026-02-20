export function MagiDiagram() {
  return (
    <div className="relative w-full" style={{ aspectRatio: "1456 / 600" }}>
      <svg
        viewBox="0 0 1456 600"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0 h-full w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* BALTHASAR-2 top center - trapezoid wider at top */}
        <path
          d="M420,0 L1020,0 L960,340 L480,340 Z"
          fill="#00e5ff"
          stroke="#9a6b20"
          strokeWidth="4"
        />
        {/* BALTHASAR-2 label */}
        <text
          x="720"
          y="180"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#0d1210"
          fontSize="48"
          fontWeight="bold"
          fontFamily="sans-serif"
          letterSpacing="2"
        >
          {"BALTHASAR\u20142"}
        </text>

        {/* CASPER-3 bottom left - pentagon-like shape */}
        <path
          d="M60,350 L470,350 L490,340 L480,340 L420,600 L60,600 Z"
          fill="#00e5ff"
          stroke="#9a6b20"
          strokeWidth="4"
        />
        {/* CASPER-3 label */}
        <text
          x="270"
          y="490"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#0d1210"
          fontSize="42"
          fontWeight="bold"
          fontFamily="sans-serif"
          letterSpacing="2"
        >
          {"CASPER\u20143"}
        </text>

        {/* MELCHIOR-1 bottom right */}
        <path
          d="M970,350 L980,340 L960,340 L1020,600 L1400,600 L1400,350 Z"
          fill="#00e5ff"
          stroke="#9a6b20"
          strokeWidth="4"
        />
        {/* MELCHIOR-1 label */}
        <text
          x="1190"
          y="490"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#0d1210"
          fontSize="42"
          fontWeight="bold"
          fontFamily="sans-serif"
          letterSpacing="2"
        >
          {"MELCHIOR\u20141"}
        </text>

        {/* Center connector black area */}
        <path
          d="M480,340 L490,340 L540,600 L420,600 Z"
          fill="#0d1210"
        />
        <path
          d="M960,340 L970,340 L1020,600 L940,600 Z"
          fill="#0d1210"
        />
        {/* Bottom center connector */}
        <path
          d="M420,600 L540,600 L540,420 L940,420 L940,600 L1020,600 L960,340 L480,340 Z"
          fill="#0d1210"
        />

        {/* Orange connector diamonds - left */}
        <rect
          x="475"
          y="330"
          width="40"
          height="40"
          fill="#e8a000"
          transform="rotate(45, 495, 350)"
        />
        {/* Orange connector diamonds - right */}
        <rect
          x="945"
          y="330"
          width="40"
          height="40"
          fill="#e8a000"
          transform="rotate(45, 965, 350)"
        />

        {/* MAGI center label area */}
        <rect
          x="580"
          y="430"
          width="300"
          height="80"
          fill="#0d1210"
        />
        <text
          x="730"
          y="475"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#e8a000"
          fontSize="60"
          fontWeight="bold"
          fontFamily="serif"
          letterSpacing="4"
        >
          MAGI
        </text>

        {/* Orange bar below MAGI */}
        <rect
          x="620"
          y="510"
          width="220"
          height="16"
          fill="#e8a000"
        />

      </svg>
    </div>
  )
}
