export interface SupabasePublicConfig {
  url: string;
  publishableKey: string;
}

export function getSupabasePublicConfig(): SupabasePublicConfig {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
    ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !publishableKey) {
    throw new Error("Authentication is unavailable because Supabase public configuration is missing.");
  }
  let parsed: URL;
  try { parsed = new URL(url); } catch { throw new Error("Authentication is unavailable because the Supabase URL is invalid."); }
  if (parsed.protocol !== "https:" && parsed.hostname !== "127.0.0.1" && parsed.hostname !== "localhost") {
    throw new Error("Authentication is unavailable because the Supabase URL must use HTTPS.");
  }
  return { url, publishableKey };
}

export function getSupabaseConfigurationError(): string | null {
  try {
    getSupabasePublicConfig();
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : "Authentication configuration is unavailable.";
  }
}
