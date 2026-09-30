import {Input, InputPassword} from "@shared/ui/Input.tsx";
import {Button} from "@shared/ui/Button.tsx";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {
  type LoginFormData,
  loginSchema
} from "@features/auth/model/login.schema.ts";
import {useNavigate} from "react-router";
import {authApi} from "@features/auth/api/auth.api.ts";
import { getApiErrorMessage } from "@shared/lib/apiError";
import { loadSessionUser } from "@entities/user";

export const LoginForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema)
  })
  const navigate = useNavigate()

  const onSubmit = async (data: LoginFormData) => {
    try {
      const { data: tokens } = await authApi.login({
        user_identifier: data.loginOrEmail,
        password: data.password,
      });
      localStorage.setItem("refresh_token", tokens.refresh_token);
      await loadSessionUser();
      navigate("/pets");
    } catch (err) {
      const msg = getApiErrorMessage(err, "Неверный логин или пароль");
      if (msg.toLowerCase().includes("email") || msg.toLowerCase().includes("подтверд")) {
        navigate("/verify-email");
        return;
      }
      setError("root", { message: msg });
    }
  };

  return (
    <form
      className="flex flex-col gap-5"
      onSubmit={handleSubmit(onSubmit)}
    >

      <Input
        label="Логин/Email"
        placeholder="Введите Логин или Email"
        {...register("loginOrEmail")}
        error={errors.loginOrEmail?.message}
      />
      <InputPassword
        label="Пароль"
        placeholder="Введите пароль"
        {...register("password")}
        error={errors.password?.message}
      />

      {errors.root && (
        <p className="text-red-500 text-sm">{errors.root.message}</p>
      )
      }

      <Button type="submit" intent="primary" size="full">Войти</Button>
    </form>
  )
}
