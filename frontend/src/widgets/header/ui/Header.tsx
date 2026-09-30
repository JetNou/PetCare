import {Logo} from "@shared/ui/Logo.tsx";
import type {HTMLAttributes} from "react";
import {cn} from "@shared/utils/utils.ts";
import {Button} from "@shared/ui/Button.tsx";
import {Menu} from "@shared/ui/Menu.tsx";
import { Profile } from "@widgets/user-profile";
import {useNavigate} from "react-router";
import { useSessionStore, UserRole } from "@entities/user";

export interface HeaderProps extends HTMLAttributes<HTMLElement>{
  type: "landing" | "onlyLogo" | "logoAndProfile" | "onlyAdminButton"
}

function Header({type, className, ...props}: HeaderProps) {
  const navigate = useNavigate()
  const user = useSessionStore((s) => s.user)
  const isAdmin = user?.role_id === UserRole.Admin

  return (
    <>
      {type === "landing" && <header className={cn("fixed top-0 left-0 right-0 z-50 flex h-20 bg-brand-header shadow-xl", className)} {...props}>
          <div className="container flex justify-between items-center">
            <Logo onClick={() => navigate('/')} />
            <div className="hidden sm:flex gap-x-2">
              <Button onClick={() => navigate('/login')} intent="whiteBorder">Вход</Button>
              <Button onClick={() => navigate('/register')}>Начать бесплатно</Button>
            </div>
            <Menu className="flex sm:hidden">
              <Button onClick={() => navigate('/register')} size="full">Начать бесплатно</Button>
              <Button onClick={() => navigate('/login')} size="full" intent="whiteBorder">Войти</Button>
            </Menu>
          </div>
        </header>
      }

      {type === "onlyLogo" && <header className={cn("flex w-full h-20 bg-brand-header shadow-xl", className)} {...props}>
          <div className="container flex justify-center items-center sm:justify-start">
            <Logo onClick={() => navigate('/')} />
          </div>
        </header>
      }

      {type === "logoAndProfile" && <header className={cn("flex w-full h-20 bg-brand-header shadow-xl", className)} {...props}>
          <div className="container flex justify-between items-center">
            <Logo className="hidden sm:block" onClick={() => navigate('/')} />
            <div className="flex items-center gap-x-2">
              {isAdmin && (
                <Button type="button" onClick={() => navigate('/admin')} intent="red" size="small">Админ панель</Button>
              )}
              <Profile />
            </div>
          </div>
        </header>
      }

      {type === "onlyAdminButton" && <header className={cn("flex w-full h-20 bg-brand-header shadow-xl", className)} {...props}>
        <div className="container flex justify-between items-center">
          <Logo className="hidden sm:block" onClick={() => navigate('/')} />
          <div className="flex items-center gap-x-2">
            {isAdmin && (
              <Button type="button" onClick={() => navigate('/admin')} intent="red" size="small">Админ панель</Button>
            )}
          </div>
        </div>
      </header>
      }
    </>
  )
}

export default Header
