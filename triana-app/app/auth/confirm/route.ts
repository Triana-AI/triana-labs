import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function privateRedirect(request: Request, path: string) {
  const response = NextResponse.redirect(new URL(path, request.url), 303);
  response.headers.set("Cache-Control", "no-store");
  return response;
}

export async function GET(request: Request) {
  const code = new URL(request.url).searchParams.get("code");
  if (!code) return privateRedirect(request, "/login?auth_error=invalid_link");

  try {
    const supabase = await createServerSupabaseClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) return privateRedirect(request, "/login?auth_error=invalid_link");
    return privateRedirect(request, "/agents");
  } catch {
    return new Response("Authentication is unavailable.", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }
}
