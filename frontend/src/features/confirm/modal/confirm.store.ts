import { create } from "zustand";

export interface ConfirmState {
  isOpen: boolean
  message: string,
  okText: string,
  closeText: string,
  open: (options: { message: string; okText?: string; cancelText?: string; onConfirm: () => void; onCancel?: () => void }) => void,
  close: () => void,
  onConfirm: (() => void) | null,
  onCancel: (() => void) | null
}

export const useConfirmStore = create<ConfirmState>((set) => ({
  isOpen: false,
  message: "",
  okText: "",
  closeText: "",
  open: (options) => set({
    isOpen: true,
    message: options.message,
    okText: options.okText,
    closeText: options.cancelText,
    onConfirm: options.onConfirm,
    onCancel: options.onCancel
  }),
  close: () => set({isOpen: false}),
  onConfirm: null,
  onCancel: null
}))