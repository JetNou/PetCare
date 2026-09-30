import {Button} from "@shared/ui/Button.tsx";

export const NotFound = () => {
  return (
    <main className="flex flex-col h-screen items-center justify-center text-center px-4 py-20 gap-6">

      <h1 className="text-brand-primary text-6xl md:text-8xl font-extrabold">
        404
      </h1>

      <h2>
        Страница не найдена
      </h2>

      <p className="max-w-md text-brand-wood-alt">
        Похоже, такой страницы не существует или она была перемещена.
        Попробуйте вернуться на главную.
      </p>

      <div className="flex flex-col sm:flex-row  gap-3 w-auto">
        <Button
          className="w-full sm:w-auto"
        >
          На главную
        </Button>

        <Button
          intent="whiteBorder"
          className="w-full sm:w-auto"
        >
          Назад
        </Button>
      </div>

    </main>
  )
}