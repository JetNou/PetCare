import type {HTMLAttributes, ReactNode} from "react";
import {cn} from "@shared/utils/utils.ts";
import {cva, type VariantProps} from "class-variance-authority";


export interface FeatureCardProps extends HTMLAttributes<HTMLDivElement> {
  title: string,
  description: string
}

export const FeatureCard = ({title, description, className}: FeatureCardProps) => {
  return (
    <div className={cn("bg-brand-bg p-4 rounded-xl flex flex-col justify-center items-center gap-y-2 w-50 h-50", className)}>
      <h3 className="text-center font-medium">{title}</h3>
      <h4 className="text-center text-sm font-normal">{description}</h4>
    </div>
  )
}


export interface StepCardProps {
  icon: ReactNode,
  step: string,
  title: string,
  description: string
}

export const StepCard = ({icon, step, title, description}: StepCardProps) => {
  return (
    <div className="flex flex-col gap-y-3 text-center bg-transparent w-full">
      <div className="flex justify-center items-center mx-auto bg-white shadow-xl rounded-2xl w-20 h-20 md:w-25 md:h-25">
        {icon}
      </div>
      <h2 className="text-brand-primary">Шаг {step}</h2>
      <h3 className="font-medium">{title}</h3>
      <div>
        <p>
          {description}
        </p>
      </div>
    </div>
  )
}


export interface LogHistoryCardProps {
  children: string
}

export const LogHistoryCard = ({children}: LogHistoryCardProps) => {
  return (
    <div className="w-full rounded-2xl bg-brand-cream p-3">
      <p className="text-black font-normal break-all">
        {children}
      </p>
    </div>
  )
}

export interface MedicalHistoryCardProps {
  children: string
}

export const MedicalHistoryCard = ({children}: MedicalHistoryCardProps) => {
  return (
    <div className="w-full rounded-2xl bg-brand-cream p-3">
      <h3 title={children} className="text-black font-normal truncate">
        {children}
      </h3>
    </div>
  )
}

export interface UserCardProps {
  login: string,
  email: string,
  onClick: () => void
}

export const UserCard = ({login, email, onClick}: UserCardProps) => {
  return (
    <div
      className="flex items-center gap-3 w-full p-2 hover:bg-brand-bg rounded-xl cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-center w-11 h-11 bg-brand-sand rounded-full shrink-0">
        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 12.75C8.83 12.75 6.25 10.17 6.25 7C6.25 3.83 8.83 1.25 12 1.25C15.17 1.25 17.75 3.83 17.75 7C17.75 10.17 15.17 12.75 12 12.75ZM12 2.75C9.66 2.75 7.75 4.66 7.75 7C7.75 9.34 9.66 11.25 12 11.25C14.34 11.25 16.25 9.34 16.25 7C16.25 4.66 14.34 2.75 12 2.75Z" fill="black"/>
          <path d="M20.5901 22.75C20.1801 22.75 19.8401 22.41 19.8401 22C19.8401 18.55 16.3202 15.75 12.0002 15.75C7.68015 15.75 4.16016 18.55 4.16016 22C4.16016 22.41 3.82016 22.75 3.41016 22.75C3.00016 22.75 2.66016 22.41 2.66016 22C2.66016 17.73 6.85015 14.25 12.0002 14.25C17.1502 14.25 21.3401 17.73 21.3401 22C21.3401 22.41 21.0001 22.75 20.5901 22.75Z" fill="black"/>
        </svg>
      </div>
      <div className="flex flex-col">
        <span className="text-sm font-medium">{login}</span>
        <span className="text-xs text-brand-wood">{email}</span>
      </div>
    </div>
  )
}

const StatsCardVariants = cva(
  "flex flex-col items-center justify-center rounded-xl bg-brand-beige text-center transition-all",
  {
    variants: {
      size: {
        default: "w-full aspect-square p-6 gap-2",
        small: "w-full p-4 gap-1"
      }
    },
    defaultVariants: {
      size: "default",
    }
  }
)

export interface StatsCardProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof StatsCardVariants> {
  icon: ReactNode,
  title: string,
  description: string,
}


export const StatsCard = ({ icon, title, description, className, size, ...props }: StatsCardProps) => {
  return (
    <div className={cn(StatsCardVariants({ size }), className)} {...props}>
      <div className="flex items-center justify-center">{icon}</div>
      <div className="flex flex-col">
        <span className="text-2xl font-bold">{title}</span>
        <span className="text-sm text-gray-600">{description}</span>
      </div>
    </div>
  )
}


export interface PetCardStaticProps {
  className?: string,
  name: string,
  gender: "male" | "female" | null,
  weight: number,
  date_birth: string,
  photo: string
}

export const PetCardStatic = ({className, name, gender, weight, date_birth, photo}: PetCardStaticProps) => {
  return (
    <div
      className={cn("flex flex-col items-start justify-start w-full max-w-md bg-white rounded-2xl border border-solid border-gray-300 p-4 gap-y-2", className)}
    >

      <div className="flex gap-x-1 sm:gap-x-4 items-center w-full">
        <div className="flex shrink-0 w-20 h-20 sm:w-24 sm:h-24 mx-auto justify-center items-center border border-solid border-black rounded-full overflow-hidden bg-brand-cream">
          <img src={photo} alt="" className="w-full h-full object-cover select-none pointer-events-none" />
        </div>

        <div className="flex flex-col gap-y-2 items-start flex-1 min-w-0">

          <div className="flex items-center w-full gap-x-2">
            <h3 className="truncate min-w-0" title={name}>
              {name}
            </h3>
            <span className="shrink-0">
            {gender === "male" ? (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.25 22.25C5.56 22.25 1.75 18.44 1.75 13.75C1.75 9.06 5.56 5.25 10.25 5.25C14.94 5.25 18.75 9.06 18.75 13.75C18.75 18.44 14.94 22.25 10.25 22.25ZM10.25 6.75C6.39 6.75 3.25 9.89 3.25 13.75C3.25 17.61 6.39 20.75 10.25 20.75C14.11 20.75 17.25 17.61 17.25 13.75C17.25 9.89 14.11 6.75 10.25 6.75Z" fill="#3498db"/>
                <path d="M15.9999 8.74994C15.8099 8.74994 15.6199 8.67994 15.4699 8.52994C15.1799 8.23994 15.1799 7.75994 15.4699 7.46994L20.9699 1.96994C21.2599 1.67994 21.7399 1.67994 22.0299 1.96994C22.3199 2.25994 22.3199 2.73994 22.0299 3.02994L16.5299 8.52994C16.3799 8.67994 16.1899 8.74994 15.9999 8.74994Z" fill="#3498db"/>
                <path d="M21.5 9.75C21.09 9.75 20.75 9.41 20.75 9V3.25H15C14.59 3.25 14.25 2.91 14.25 2.5C14.25 2.09 14.59 1.75 15 1.75H21.5C21.91 1.75 22.25 2.09 22.25 2.5V9C22.25 9.41 21.91 9.75 21.5 9.75Z" fill="#3498db"/>
              </svg>
            ) : gender === "female" ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 16.75C7.73 16.75 4.25 13.27 4.25 9C4.25 4.73 7.73 1.25 12 1.25C16.27 1.25 19.75 4.73 19.75 9C19.75 13.27 16.27 16.75 12 16.75ZM12 2.75C8.55 2.75 5.75 5.55 5.75 9C5.75 12.45 8.55 15.25 12 15.25C15.45 15.25 18.25 12.45 18.25 9C18.25 5.55 15.45 2.75 12 2.75Z" fill="#e91e63"/>
                <path d="M12 22.75C11.59 22.75 11.25 22.41 11.25 22V16C11.25 15.59 11.59 15.25 12 15.25C12.41 15.25 12.75 15.59 12.75 16V22C12.75 22.41 12.41 22.75 12 22.75Z" fill="#e91e63"/>
                <path d="M15 19.75H9C8.59 19.75 8.25 19.41 8.25 19C8.25 18.59 8.59 18.25 9 18.25H15C15.41 18.25 15.75 18.59 15.75 19C15.75 19.41 15.41 19.75 15 19.75Z" fill="#e91e63"/>
              </svg>
            ) : (
              <span className="text-black text-2xl">—</span>
            )}
              
            </span>
          </div>

          <div className="flex text-xl items-center gap-x-1">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 22.75H10C4.57 22.75 2.25 20.43 2.25 15V9C2.25 3.57 4.57 1.25 10 1.25H14C19.43 1.25 21.75 3.57 21.75 9V15C21.75 20.43 19.43 22.75 14 22.75ZM10 2.75C5.39 2.75 3.75 4.39 3.75 9V15C3.75 19.61 5.39 21.25 10 21.25H14C18.61 21.25 20.25 19.61 20.25 15V9C20.25 4.39 18.61 2.75 14 2.75H10Z" fill="#F97316"/>
              <path d="M15.0696 12.5401C14.8896 12.5401 14.7096 12.4701 14.5696 12.3501C13.1096 11.0501 10.8896 11.0501 9.42963 12.3501C9.26963 12.5001 9.04962 12.5601 8.81962 12.5301C8.59962 12.5001 8.40962 12.3701 8.28962 12.1801L6.10963 8.6801C5.91963 8.3701 5.97962 7.9701 6.24962 7.7201C9.52962 4.8101 14.4696 4.8101 17.7496 7.7201C18.0196 7.9601 18.0796 8.3701 17.8896 8.6801L15.7096 12.1801C15.5896 12.3701 15.3996 12.4901 15.1796 12.5301C15.1396 12.5301 15.0996 12.5401 15.0696 12.5401ZM11.9996 9.8701C12.9996 9.8701 13.9896 10.1501 14.8596 10.7001L16.2596 8.4501C13.7296 6.5701 10.2596 6.5701 7.72962 8.4501L9.12963 10.7001C10.0096 10.1401 10.9996 9.8701 11.9996 9.8701Z" fill="#F97316"/>
            </svg>
            <h3>{weight} кг</h3>
          </div>

          <div className="flex items-center text-xl gap-x-1">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16.3799 22.7502H3.23993C2.28993 22.7502 1.40993 22.3103 0.839932 21.5403C0.259932 20.7603 0.0899403 19.7802 0.37994 18.8502L4.58993 5.32019C4.96993 4.06019 6.12995 3.2002 7.44995 3.2002H19.7499C20.9599 3.2002 22.0499 3.92028 22.5099 5.04028C22.7599 5.62028 22.8099 6.2803 22.6599 6.9303L19.2899 20.4602C18.9699 21.8102 17.7699 22.7502 16.3799 22.7502ZM7.45993 4.71021C6.80993 4.71021 6.21993 5.14026 6.02993 5.77026L1.81994 19.3003C1.67994 19.7703 1.75993 20.2603 2.05993 20.6603C2.33993 21.0403 2.77994 21.2603 3.24994 21.2603H16.3899C17.08 21.2603 17.6799 20.7902 17.8399 20.1202L21.2099 6.5802C21.2899 6.2502 21.2699 5.92025 21.1399 5.63025C20.9 5.06025 20.3699 4.7002 19.7599 4.7002H7.45993V4.71021Z" fill="#F97316"/>
              <path d="M20.78 22.75H16C15.59 22.75 15.25 22.41 15.25 22C15.25 21.59 15.59 21.25 16 21.25H20.78C21.19 21.25 21.57 21.08 21.85 20.78C22.13 20.48 22.27 20.08 22.24 19.67L21.25 6.05002C21.22 5.64002 21.53 5.27997 21.94 5.24997C22.35 5.22997 22.71 5.52991 22.74 5.93991L23.73 19.56C23.79 20.38 23.5 21.2 22.94 21.8C22.39 22.41 21.6 22.75 20.78 22.75Z" fill="#F97316"/>
              <path d="M9.67977 7.12971C9.61977 7.12971 9.55977 7.11969 9.49977 7.10969C9.09977 7.00969 8.84979 6.60966 8.94979 6.19966L9.98976 1.87971C10.0898 1.47971 10.4898 1.22966 10.8998 1.32966C11.2998 1.42966 11.5498 1.8297 11.4498 2.2397L10.4098 6.55977C10.3298 6.89977 10.0198 7.12971 9.67977 7.12971Z" fill="#F97316"/>
              <path d="M16.3795 7.13974C16.3295 7.13974 16.2694 7.13972 16.2194 7.11972C15.8194 7.02972 15.5595 6.62971 15.6395 6.22971L16.5794 1.88974C16.6694 1.47974 17.0694 1.22979 17.4694 1.30979C17.8694 1.38979 18.1294 1.79968 18.0494 2.19968L17.1094 6.53977C17.0394 6.89977 16.7295 7.13974 16.3795 7.13974Z" fill="#F97316"/>
              <path d="M15.7002 12.75H7.7002C7.2902 12.75 6.9502 12.41 6.9502 12C6.9502 11.59 7.2902 11.25 7.7002 11.25H15.7002C16.1102 11.25 16.4502 11.59 16.4502 12C16.4502 12.41 16.1102 12.75 15.7002 12.75Z" fill="#F97316"/>
              <path d="M14.7002 16.75H6.7002C6.2902 16.75 5.9502 16.41 5.9502 16C5.9502 15.59 6.2902 15.25 6.7002 15.25H14.7002C15.1102 15.25 15.4502 15.59 15.4502 16C15.4502 16.41 15.1102 16.75 14.7002 16.75Z" fill="#F97316"/>
            </svg>
            <h3>{date_birth}</h3>
          </div>
        </div>
      </div>

      <div>

      </div>

    </div>
  )
}
