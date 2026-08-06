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
