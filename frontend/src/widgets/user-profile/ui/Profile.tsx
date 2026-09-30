import {useEffect, useState} from "react";
import {cn} from "@shared/utils/utils.ts";
import {Button} from "@shared/ui/Button.tsx";
import {useNavigate} from "react-router";
import { loadSessionUser, useSessionStore } from "@entities/user";
import { resolveMediaUrl } from "@shared/lib/imageUrl";
import { logoutClient } from "@features/auth/lib/logoutClient";

export const Profile = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const navigate = useNavigate()
  const user = useSessionStore((s) => s.user)

  useEffect(() => {
    if (!user && localStorage.getItem("refresh_token")) {
      void loadSessionUser().catch(() => {});
    }
  }, [user]);

  const label = user?.user_full_name || user?.user_login || "Профиль";
  const avatarUrl = user?.user_avatar ? resolveMediaUrl(user.user_avatar) : undefined;

  return (
    <div className={cn("relative")}>
      <button
        type="button"
        className="flex max-w-75 h-13 items-center px-3 bg-brand-primary rounded-2xl gap-x-3 cursor-pointer"
        onClick={() => setIsOpen(prev => !prev)}
      >
        <div className="flex items-center gap-x-1">
          <div className="flex w-10 h-10 bg-white rounded-full justify-center items-center overflow-hidden">
            <img src={avatarUrl} alt="" className={`${avatarUrl?.includes("user-standart") ? 'w-2/3 h-2/3' : 'w-full h-full'} object-cover rounded-full`} />
          </div>
          <h3 title={label} className="truncate font-normal text-lg min-w-0 max-w-23 text-white hidden sm:flex">{label}</h3>
        </div>
        <svg className={cn("transition-transform duration-250", isOpen ? "rotate-180" : "")} width="25" height="17" viewBox="0 0 25 17" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0.772461 0.634766L12.2725 14.6348L23.7725 0.634766" stroke="white" strokeWidth="2"/>
        </svg>
      </button>
      <div
        className={cn(
          "absolute flex flex-col justify-center items-center gap-y-2 right-0 top-full mt-2 max-w-70 bg-white rounded-2xl p-3 shadow-xl border border-gray-100 z-40 transition-all duration-300 ease-in-out transform",
          isOpen
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 -translate-y-4 pointer-events-none"
        )}
      >
        <Button type="button" onClick={() => navigate('/profile')} className="text-lg">Профиль</Button>
        <Button
          type="button"
          onClick={() => void logoutClient().then(() => navigate('/'))}
          intent="red"
          className="text-lg"
        >
          Выйти
        </Button>
      </div>
    </div>
  )
}
