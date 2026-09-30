import { Header } from "@widgets/header";
import {Input} from "@shared/ui/Input.tsx";
import {Button} from "@shared/ui/Button.tsx";
import { useForm } from "react-hook-form";
import { usersApi } from "@entities/user";
import { getApiErrorMessage } from "@shared/lib/apiError";
import {useNavigate, useSearchParams} from "react-router";
import {useEffect} from "react";

export const RecoverAccountPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    setError,
  } = useForm<{ token: string }>();

  useEffect(() => {
    const tokenFromUrl = searchParams.get("token");
    if (tokenFromUrl) setValue("token", tokenFromUrl);
  }, [searchParams, setValue]);

  const onSubmit = async (data: { token: string }) => {
    try {
      await usersApi.restoreProfile(data.token.trim());
      navigate("/login");
    } catch (e) {
      setError("root", { message: getApiErrorMessage(e) });
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">

      <Header type="onlyLogo" />

      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="w-full max-w-100 bg-white rounded-3xl shadow-lg p-6 sm:p-8 flex flex-col gap-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-center text-brand-slate-alt">
            Восстановление аккаунта
          </h1>

          <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
            <Input
              label="Токен из письма"
              placeholder="Вставьте токен"
              {...register("token", { required: "Обязательное поле" })}
              error={errors.token?.message}
            />
            {errors.root && <p className="text-red-500 text-sm">{errors.root.message}</p>}
            <Button intent="primary" size="full" disabled={isSubmitting} type="submit">
              Восстановить
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
};
