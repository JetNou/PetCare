import {cn} from "@shared/utils/utils.ts";
import {type HTMLAttributes, useEffect, useRef, useState} from "react";

export interface MenuProps extends HTMLAttributes<HTMLDivElement> {}

export const    Menu = ({className, children, ...props}: MenuProps) => {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const lineStyle = "block h-0.5 w-10 bg-black transition-all duration-300 ease-in-out"

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (isOpen && menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener("touchstart", handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener("touchstart", handleClickOutside);
    }
  }, [isOpen])

  return (
    <div
      className={cn("relative", className)}
      ref={menuRef}
      {...props}
    >
      <button
        className={cn("flex w-10 h-10 flex-col gap-y-2 cursor-pointer items-center justify-center")}
        onClick={() => setIsOpen(prev => !prev)}
      >
        <span className={cn(lineStyle, isOpen ? "translate-y-2.5 rotate-45" : '')}></span>
        <span className={cn(lineStyle, isOpen ? 'opacity-0' : 'opacity-100')}></span>
        <span className={cn(lineStyle, isOpen ? "-translate-y-2.5 -rotate-45" : '')}></span>
      </button>

      <div
        className={cn(
          "absolute flex flex-col justify-center items-center gap-y-2 right-0 top-full mt-2 w-75 bg-white rounded-2xl p-6 shadow-xl border border-gray-100 z-40 transition-all duration-300 ease-in-out transform",
          isOpen
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 -translate-y-4 pointer-events-none"
        )}
      >
        {children}
      </div>
    </div>
  )
}