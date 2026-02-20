export function SystemInfo() {
  return (
    <div className="flex flex-col gap-1 px-4 pt-2">
      <div className="text-[clamp(1.2rem,3vw,2.2rem)] font-bold tracking-wide text-[#e8a000]">
        {"CODE:127"}
      </div>
      <div className="flex flex-col gap-0 text-[clamp(0.7rem,1.8vw,1.2rem)] font-bold tracking-wide text-[#e8a000]">
        <span>{"FILE：MAGI_SYS"}</span>
        <span>{"EXTENSION:4088"}</span>
        <span>{"EX_MODE:OFF"}</span>
        <span>{"PRIORITY:AAA"}</span>
      </div>
    </div>
  )
}
