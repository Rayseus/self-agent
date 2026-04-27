export type Lang = "zh" | "en";

export interface Dict {
  header: {
    title: string;
    desc: string;
    newChat: string;
  };
  empty: {
    title: string;
    samples: string[];
  };
  input: {
    placeholder: string;
    send: string;
    sending: string;
  };
  error: {
    request: (status: number) => string;
    unknown: string;
  };
  coldStart: {
    tip: string;
    dismiss: string;
  };
}
