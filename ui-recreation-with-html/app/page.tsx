import MagiDiagram from "@/components/magi-diagram"

/**
 * MAGI System Page - PDF Page 2 Layout
 *
 * 3 layers stacked via absolute positioning:
 *  Layer 1 (center): MagiDiagram SVG (cells, MAGI logo, connection lines)
 *  Layer 2 (left):   "提訴" header card + system summary text
 *  Layer 3 (right):  "決議" header card + status badges (審議中/可決/否決)
 *
 * Status badges match PDF page 3 design:
 *  Double-bordered rectangles (outer+inner border) on black background
 *  審議中 = gold/yellow borders + gold text
 *  可決   = green borders + green text
 *  否決   = red borders + red text
 */
export default function MagiPage() {
  const orange = "#e8a000"
  const green = "#00cc44"
  const dark = "#0d1210"
  const red = "#cc2200"

  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-[#0d1210] p-4">
      <div
        className="relative w-full"
        style={{ aspectRatio: "1460 / 820", maxWidth: "min(1460px, calc(100vh * 1460 / 820))" }}
      >
        {/* ============================================ */}
        {/* LAYER 1: Center MAGI Diagram SVG             */}
        {/* ============================================ */}
        <MagiDiagram />

        {/* ============================================ */}
        {/* LAYER 2: Left floating - "提訴" + summary    */}
        {/* Positioned at top-left, above the diagram    */}
        {/* ============================================ */}
        <div
          className="absolute z-10 pointer-events-none"
          style={{ top: "3%", left: "3%", width: "34%" }}
        >
          {/* Header card: green lines top & bottom, text centered */}
          <div
            className="relative flex items-center justify-center"
            style={{
              backgroundColor: dark,
              padding: "clamp(8px, 1.5vw, 22px) 0",
            }}
          >
            {/* Green lines - top */}
            <div className="absolute top-0 left-0 w-full flex flex-col" style={{ gap: "3px" }}>
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
            </div>
            {/* Green lines - bottom */}
            <div className="absolute bottom-0 left-0 w-full flex flex-col" style={{ gap: "3px" }}>
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
            </div>
            <span
              className="relative z-10 font-black"
              style={{
                color: orange,
                fontSize: "clamp(22px, 4.4vw, 64px)",
                letterSpacing: "0.5em",
              }}
            >
              {"提 訴"}
            </span>
          </div>

          {/* System info summary */}
          <div style={{ paddingLeft: "4%", paddingTop: "8%" }}>
            <p
              className="font-bold"
              style={{
                color: orange,
                fontSize: "clamp(14px, 2.2vw, 32px)",
                letterSpacing: "0.05em",
                lineHeight: 1.2,
              }}
            >
              CODE:127
            </p>
            <div
              className="flex flex-col font-bold"
              style={{
                color: orange,
                fontSize: "clamp(10px, 1.4vw, 20px)",
                letterSpacing: "0.04em",
                lineHeight: 1.5,
                marginTop: "3%",
              }}
            >
              <p>{"FILE\uFF1AMAGI_SYS"}</p>
              <p>{"EXTENSIO\uFF2E:4088"}</p>
              <p>EX_MODE:OFF</p>
              <p>PRIORITY:AAA</p>
            </div>
          </div>
        </div>

        {/* ============================================ */}
        {/* LAYER 3: Right floating - "決議" header      */}
        {/* Positioned at top-right, above the diagram   */}
        {/* ============================================ */}
        <div
          className="absolute z-10 pointer-events-none"
          style={{ top: "3%", right: "3%", width: "34%" }}
        >
          <div
            className="relative flex items-center justify-center"
            style={{
              backgroundColor: dark,
              padding: "clamp(8px, 1.5vw, 22px) 0",
            }}
          >
            <div className="absolute top-0 left-0 w-full flex flex-col" style={{ gap: "3px" }}>
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
            </div>
            <div className="absolute bottom-0 left-0 w-full flex flex-col" style={{ gap: "3px" }}>
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
              <div style={{ height: "3px", backgroundColor: green }} />
            </div>
            <span
              className="relative z-10 font-black"
              style={{
                color: orange,
                fontSize: "clamp(22px, 4.4vw, 64px)",
                letterSpacing: "0.5em",
              }}
            >
              {"決 議"}
            </span>
          </div>
        </div>

        {/* ============================================ */}
        {/* STATUS BADGES (PDF page 3 design)            */}
        {/* Double-bordered rectangles, black background  */}
        {/* ============================================ */}

        {/* 審議中 - inside BALTHASAR-2 */}
        <div
          className="absolute z-10 flex items-center justify-center"
          style={{
            top: "42%",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: dark,
            border: `3px solid ${orange}`,
            padding: "clamp(2px, 0.3vw, 4px)",
          }}
        >
          <div
            className="flex items-center justify-center"
            style={{
              border: `2px solid ${orange}`,
              padding: "clamp(4px, 0.5vw, 8px) clamp(10px, 1.6vw, 28px)",
            }}
          >
            <span
              className="font-black"
              style={{
                color: orange,
                fontSize: "clamp(12px, 2vw, 30px)",
                letterSpacing: "0.15em",
              }}
            >
              {"審議中"}
            </span>
          </div>
        </div>

        {/* 可決 - inside CASPER-3 */}
        <div
          className="absolute z-10 flex items-center justify-center"
          style={{
            top: "76%",
            left: "16%",
            transform: "translateY(-50%)",
            backgroundColor: dark,
            border: `3px solid ${green}`,
            padding: "clamp(2px, 0.3vw, 4px)",
          }}
        >
          <div
            className="flex items-center justify-center"
            style={{
              border: `2px solid ${green}`,
              padding: "clamp(3px, 0.4vw, 6px) clamp(8px, 1.4vw, 20px)",
            }}
          >
            <span
              className="font-black"
              style={{
                color: green,
                fontSize: "clamp(10px, 1.6vw, 24px)",
                letterSpacing: "0.2em",
              }}
            >
              {"可決"}
            </span>
          </div>
        </div>

        {/* 否決 - inside MELCHIOR-1 */}
        <div
          className="absolute z-10 flex items-center justify-center"
          style={{
            top: "76%",
            right: "10%",
            transform: "translateY(-50%)",
            backgroundColor: dark,
            border: `3px solid ${red}`,
            padding: "clamp(2px, 0.3vw, 4px)",
          }}
        >
          <div
            className="flex items-center justify-center"
            style={{
              border: `2px solid ${red}`,
              padding: "clamp(3px, 0.4vw, 6px) clamp(8px, 1.4vw, 20px)",
            }}
          >
            <span
              className="font-black"
              style={{
                color: red,
                fontSize: "clamp(10px, 1.6vw, 24px)",
                letterSpacing: "0.2em",
              }}
            >
              {"否決"}
            </span>
          </div>
        </div>
      </div>
    </main>
  )
}
