import {
  ReactNode,
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import en from "./en";
import type { Dict, Lang } from "./types";
import zh from "./zh";

export type { Dict, Lang };

const STORAGE_KEY = "selfAgent.lang";
const DICTS: Record<Lang, Dict> = { zh, en };

function detectDefault(): Lang {
  if (typeof window === "undefined") return "zh";
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "zh" || saved === "en") return saved;
  const nav = window.navigator.language || "";
  return nav.toLowerCase().startsWith("zh") ? "zh" : "en";
}

interface LangCtx {
  lang: Lang;
  t: Dict;
  setLang: (next: Lang) => void;
}

const LangContext = createContext<LangCtx | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectDefault);

  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    window.localStorage.setItem(STORAGE_KEY, lang);
  }, [lang]);

  const setLang = useCallback((next: Lang) => setLangState(next), []);

  const value = useMemo<LangCtx>(
    () => ({ lang, t: DICTS[lang], setLang }),
    [lang, setLang],
  );

  return createElement(LangContext.Provider, { value }, children);
}

export function useLang(): LangCtx {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used within LangProvider");
  return ctx;
}
