import { LoginClient } from "@/components/self-serve/LoginClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ auth_error?: string }> }) {
  const { auth_error } = await searchParams;
  return <LoginClient confirmationFailed={auth_error === "invalid_link"} />;
}
