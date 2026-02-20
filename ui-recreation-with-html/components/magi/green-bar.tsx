export function GreenBar({ text, align = "left" }: { text: string; align?: "left" | "right" }) {
  return (
    <div className={`relative flex flex-col ${align === "right" ? "items-end" : "items-start"}`}>
      <div className={`relative z-10 px-4 pb-1 text-[clamp(2rem,5vw,4rem)] font-bold tracking-[0.3em] text-[#e8a000] ${align === "right" ? "text-right" : "text-left"}`}>
        {text}
      </div>
      <div className="w-full flex flex-col gap-[3px]">
        <div className="h-[4px] w-full bg-[#00cc44]" />
        <div className="h-[4px] w-full bg-[#00cc44]" />
        <div className="h-[4px] w-full bg-[#00cc44]" />
        <div className="h-[3px] w-full bg-[#0d1210]" />
        <div className="h-[4px] w-full bg-[#00cc44]" />
        <div className="h-[4px] w-full bg-[#00cc44]" />
        <div className="h-[4px] w-full bg-[#00cc44]" />
      </div>
    </div>
  )
}
