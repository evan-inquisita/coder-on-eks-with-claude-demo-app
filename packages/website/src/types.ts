export interface Document {
  id: string;
  name: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
}
