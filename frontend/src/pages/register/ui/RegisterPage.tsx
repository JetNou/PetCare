import { Header } from "@widgets/header";
import {useNavigate} from "react-router";
import {RegisterForm} from "@features/auth/ui/RegisterForm.tsx";

export const RegisterPage = () => {
  const navigate = useNavigate()



  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">

      <Header type="onlyLogo" />

      <main className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-100 bg-white rounded-3xl shadow-lg p-6 sm:p-8 flex flex-col gap-6">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-center text-brand-slate-alt">
            Регистрация
          </h1>

          <RegisterForm />
        </div>

        <p className="mt-6 text-sm text-brand-slate text-center">
           Аккаунт уже есть?{' '}
          <button
            className="text-brand-primary font-bold cursor-pointer hover:underline"
            onClick={() => navigate('/login')}
          >
            Войти
          </button>
        </p>
      </main>
    </div>
  )
}
