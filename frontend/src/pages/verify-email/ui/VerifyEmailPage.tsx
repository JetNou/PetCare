import { Header } from "@widgets/header";
import {Input} from "@shared/ui/Input.tsx";
import {Button} from "@shared/ui/Button.tsx";
import {useNavigate, useSearchParams} from "react-router";
import {useForm} from "react-hook-form";
import {useEffect, useState} from "react";
import {authApi} from "@features/auth/api/auth.api.ts";
import { getApiErrorMessage } from "@shared/lib/apiError";
import { loadSessionUser } from "@entities/user";

const COOLDOWN_TIME = 60;

interface VerifyEmailFormData {
  token: string;
}

interface ResendEmailFormData {
  email: string;
}

export const VerifyEmailPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [secondsLeft, setSecondsLeft] = useState<number>(0);
  const [resendError, setResendError] = useState<string | null>(null);
  const [showEmailForm, setShowEmailForm] = useState<boolean>(false);
  const [isResending, setIsResending] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<VerifyEmailFormData>({
    defaultValues: {
      token: "",
    },
  });

  const {
    register: registerEmail,
    handleSubmit: handleSubmitEmail,
    formState: { errors: emailErrors, isSubmitting: isSubmittingEmail },
    reset: resetEmailForm,
  } = useForm<ResendEmailFormData>({
    defaultValues: {
      email: "",
    },
  });

  useEffect(() => {
    const savedEndTime = localStorage.getItem("resend-cooldown-end");
    if (savedEndTime) {
      const remaining = Math.ceil((Number(savedEndTime) - Date.now()) / 1000);
      if (remaining > 0) setSecondsLeft(remaining);
    }

    const tokenFromUrl = searchParams.get("token");
    if (tokenFromUrl) setValue("token", tokenFromUrl);
  }, [searchParams, setValue]);

  useEffect(() => {
    if (secondsLeft <= 0) return;

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [secondsLeft]);

  const onSubmit = async (data: VerifyEmailFormData) => {
    try {
      const result = await authApi.verifyEmail(data.token);
      localStorage.removeItem("resend-cooldown-end");
      
      if (result.data.refresh_token) {
        localStorage.setItem('refresh_token', result.data.refresh_token);
      }

      try {
        await loadSessionUser();
        navigate("/pets");
      } catch {
        localStorage.removeItem("refresh_token");
        navigate("/login");
      }
    } catch (err) {
      setError("token", {
        message: getApiErrorMessage(err, "Неверный или истёкший токен"),
      });
    }
  };

  const handleResend = async () => {
    if (secondsLeft > 0 || isResending) return;

    try {
      setIsResending(true);
      setResendError(null);

      await authApi.resendVerification();

      const endTime = Date.now() + COOLDOWN_TIME * 1000;
      localStorage.setItem("resend-cooldown-end", endTime.toString());
      setSecondsLeft(COOLDOWN_TIME);

    } catch (err) {
      setResendError(getApiErrorMessage(err, "Ошибка при отправке кода"));
    } finally {
      setIsResending(false);
    }
  };

  const handleResendByEmail = async (data: ResendEmailFormData) => {
    try {
      setResendError(null);
      await authApi.resendVerificationByEmail(data.email);

      const endTime = Date.now() + COOLDOWN_TIME * 1000;
      localStorage.setItem("resend-cooldown-end", endTime.toString());
      setSecondsLeft(COOLDOWN_TIME);
      
      resetEmailForm();
      setShowEmailForm(false);

    } catch (err) {
      setResendError(getApiErrorMessage(err, "Ошибка при отправке письма"));
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">

      <Header type="onlyLogo" />

      <main className="flex-1 flex flex-col items-center justify-center px-4">

        <div className="w-full max-w-100 bg-white rounded-3xl shadow-lg p-6 sm:p-8 flex flex-col gap-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-center text-brand-slate-alt">
            Подтверждение почты
          </h1>

          {!showEmailForm ? (
            <>
              <form className="flex flex-col gap-3" onSubmit={handleSubmit(onSubmit)}>
                <Input
                  label="Токен"
                  placeholder="Введите токен из письма"
                  {...register("token", { required: "Введите токен" })}
                  error={errors.token?.message}
                />

                <div className="flex flex-col items-end gap-1">
                  <button
                    type="button"
                    disabled={secondsLeft > 0 || isResending}
                    className="text-base text-brand-primary disabled:text-gray-400 disabled:cursor-not-allowed hover:underline transition-colors"
                    onClick={handleResend}
                  >
                    {secondsLeft > 0
                      ? `Отправить повторно через ${secondsLeft}с`
                      : "Отправить код повторно"}
                  </button>
                  {resendError && <p className="text-xs text-red-500">{resendError}</p>}
                </div>
                <Button
                  intent="primary"
                  size="full"
                  disabled={isSubmitting}
                >Подтвердить</Button>
              </form>

              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-gray-300"></div>
                <span className="text-sm text-gray-500">или</span>
                <div className="flex-1 h-px bg-gray-300"></div>
              </div>

              <button
                type="button"
                className="w-full py-2 px-4 text-center text-brand-primary hover:underline transition-colors"
                onClick={() => setShowEmailForm(true)}
              >
                Ввести почту для переотправки письма
              </button>
            </>
          ) : (
            <>
              <form className="flex flex-col gap-3" onSubmit={handleSubmitEmail(handleResendByEmail)}>
                <Input
                  label="Электронная почта"
                  type="email"
                  placeholder="Введите вашу почту"
                  {...registerEmail("email", { 
                    required: "Введите почту",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Некорректный адрес почты",
                    }
                  })}
                  error={emailErrors.email?.message}
                />

                <div className="flex flex-col items-end gap-1">
                  {resendError && <p className="text-xs text-red-500">{resendError}</p>}
                </div>

                <Button
                  intent="primary"
                  size="full"
                  disabled={isSubmittingEmail}
                >Отправить письмо</Button>
              </form>

              <button
                type="button"
                className="w-full py-2 px-4 text-center text-brand-primary hover:underline transition-colors"
                onClick={() => setShowEmailForm(false)}
              >
                Вернуться к вводу кода
              </button>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
