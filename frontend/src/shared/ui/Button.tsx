import { cva, type VariantProps} from "class-variance-authority";
import { cn } from "@shared/utils/utils"
import {type ButtonHTMLAttributes, forwardRef} from "react";

const buttonVariants = cva(
  "transition-transform duration-150 flex cursor-pointer rounded-2xl justify-center items-center active:scale-95",
  {
    variants: {
      intent: {
        primary: "bg-brand-primary text-white hover:bg-brand-primary/90",
        whiteBorder: "bg-white text-black border border-solid border-black hover:bg-gray-50",
        red: "bg-red-600 text-white hover:bg-red-700",
      },
      size: {
        default: "py-3 px-6 md:py-4 md:px-8 text-base md:text-lg",
        small: "py-2 px-4 text-xs sm:text-sm md:text-base",
        full: "w-full py-4",
      }
    },
    defaultVariants: {
      intent: "primary",
      size: "default"
    },
  }
)

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {

}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({className, intent, size,  ...props}, ref) => {
    return (
      <button
        className={cn(
          buttonVariants({ intent, size }),
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
