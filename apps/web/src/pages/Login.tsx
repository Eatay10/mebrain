import { zodResolver } from "@hookform/resolvers/zod";
import { ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { ApiError, useLogin } from "../api/hooks";
import { Button, Field, Input } from "../components/ui";

const schema = z.object({
  email: z.string().trim().email("Geçerli bir e-posta girin.").max(254),
  password: z.string().min(1, "Parola zorunlu.").max(128),
});
type Form = z.infer<typeof schema>;

const DEMO = [
  ["director@demo.local", "Direktör"],
  ["unit.cdc@demo.local", "Birim yöneticisi (TEAM-CDC)"],
  ["manager.soc@demo.local", "Yönetici (SOC + Zafiyet)"],
  ["analyst.soc1@demo.local", "Çalışan (SOC)"],
  ["auditor@demo.local", "Denetmen (salt okunur)"],
] as const;

export function LoginPage() {
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation();
  const { register, handleSubmit, setValue, setFocus, formState } = useForm<Form>({ resolver: zodResolver(schema) });
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const serverError =
    login.error instanceof ApiError
      ? login.error.status === 423
        ? "Hesap çok sayıda hatalı deneme nedeniyle geçici olarak kilitlendi. 15 dakika sonra tekrar deneyin."
        : login.error.status === 429
          ? "Çok fazla deneme yapıldı. Lütfen biraz bekleyin."
          : "E-posta veya parola hatalı."
      : login.error
        ? "Sunucuya ulaşılamıyor."
        : null;

  return (
    <div className="grid min-h-full lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-sidebar p-12 text-sidebar-text lg:flex">
        <div className="flex items-center gap-2 text-white">
          <img src="/favicon.svg" alt="" className="size-9" />
          <span className="text-lg font-semibold">Cyber Task Hub</span>
        </div>
        <div className="max-w-md space-y-4">
          <h1 className="text-3xl leading-tight font-semibold text-white">
            Siber güvenlik ekiplerinin günlük işi, tek ekranda.
          </h1>
          <p>
            Rutin ve proje task'ları, etkinlik ve yetkinlik takibi, rol bazlı yetkilendirme, raporlama ve AI asistanları
            için MCP erişimi.
          </p>
        </div>
        <p className="flex items-center gap-2 text-xs">
          <ShieldCheck className="size-4" /> Tüm işlemler denetim kaydına yazılır.
        </p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form
          noValidate
          onSubmit={handleSubmit((v) => login.mutate(v, { onSuccess: () => navigate(from, { replace: true }) }))}
          className="w-full max-w-sm space-y-5"
          aria-describedby={serverError ? "login-error" : undefined}
        >
          <div>
            <h2 className="text-2xl font-semibold text-text">Giriş yap</h2>
            <p className="mt-1 text-sm text-muted">Kurumsal hesabınızla oturum açın.</p>
          </div>
          {serverError && (
            <p id="login-error" role="alert" className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
              {serverError}
            </p>
          )}
          <Field label="E-posta" htmlFor="email" error={formState.errors.email?.message}>
            <Input id="email" type="email" autoComplete="username" {...register("email")} />
          </Field>
          <Field label="Parola" htmlFor="password" error={formState.errors.password?.message}>
            <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
          </Field>
          <Button type="submit" className="w-full" loading={login.isPending}>
            Giriş yap
          </Button>
          <div className="rounded-lg border border-dashed border-border p-3">
            <p className="mb-2 text-xs font-medium text-muted">Demo hesapları (parola: seed ortam değişkeni)</p>
            <div className="flex flex-wrap gap-1.5">
              {DEMO.map(([email, label]) => (
                <button
                  key={email}
                  type="button"
                  onClick={() => {
                    setValue("email", email);
                    setFocus("password");
                  }}
                  className="rounded-md bg-surface-2 px-2 py-1 text-xs text-text hover:bg-primary-soft"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
