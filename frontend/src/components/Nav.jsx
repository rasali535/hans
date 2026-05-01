import { NavLink, useLocation } from "react-router-dom";
import { Cpu } from "lucide-react";

const items = [
  { to: "/", label: "Home", key: "home" },
  { to: "/console", label: "Console", key: "console" },
  { to: "/feed", label: "Feed", key: "feed" },
  { to: "/blueprint", label: "Blueprint", key: "blueprint" },
  { to: "/journal", label: "Journal", key: "journal" },
];

export default function Nav() {
  const { pathname } = useLocation();
  return (
    <nav
      className="sticky top-0 z-40 w-full bg-[#0A0A0A]/90 backdrop-blur-md border-b border-white/10"
      data-testid="top-nav"
    >
      <div className="mx-auto max-w-[1400px] px-6 h-14 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-3" data-testid="nav-logo">
          <div className="w-6 h-6 border border-[#ED1C24] flex items-center justify-center">
            <div className="w-1.5 h-1.5 bg-[#ED1C24]" />
          </div>
          <span className="font-display font-black tracking-tighter text-lg">FORGESIGHT</span>
          <span className="fs-label hidden md:inline">v0.1 · hackathon build</span>
        </NavLink>

        <div className="hidden md:flex items-center gap-1 border border-white/10 p-1">
          {items.map((it) => {
            const active = pathname === it.to;
            return (
              <NavLink
                key={it.key}
                to={it.to}
                data-testid={`nav-${it.key}`}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-[0.18em] transition-colors ${
                  active ? "bg-[#ED1C24] text-white" : "text-zinc-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {it.label}
              </NavLink>
            );
          })}
        </div>

        <div className="hidden lg:flex items-center gap-2 border border-white/10 px-3 py-1.5">
          <Cpu className="w-3.5 h-3.5 text-[#ED1C24]" />
          <span className="fs-mono-small text-zinc-400">POWERED BY</span>
          <span className="fs-mono-small text-white">AMD INSTINCT MI300X</span>
        </div>
      </div>
    </nav>
  );
}
