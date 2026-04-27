import type { Dict } from "./types";

const en: Dict = {
  header: {
    title: "Self-Agent",
    desc: "A RAG assistant grounded in my resume and project experience",
    newChat: "New chat",
  },
  empty: {
    title: "Curious about something? Try these:",
    samples: [
      "What is your tech stack?",
      "What did you own in the RAG project?",
      "Walk me through your project experience.",
      "How many years of experience do you have?",
    ],
  },
  input: {
    placeholder: "Ask anything about my career…",
    send: "Send",
    sending: "Thinking…",
  },
  error: {
    request: (status: number) => `Request failed: ${status}`,
    unknown: "Unknown error",
  },
  coldStart: {
    tip: "Free-tier server may take 30-60s to wake up on first ask. Thanks for your patience.",
    dismiss: "Dismiss",
  },
};

export default en;
