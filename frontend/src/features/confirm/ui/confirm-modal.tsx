import {Button} from "@shared/ui/Button.tsx";
import { useConfirmStore } from "@features/confirm/modal/confirm.store"


export const ConfirmModal = () => {
  const {isOpen, message, okText, onConfirm, onCancel, closeText, close} = useConfirmStore()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="flex flex-col bg-white rounded-2xl p-10 gap-5 max-w-md text-center">
        <h2>{message}</h2>
        <div className="flex justify-between gap-x-4">
          <Button
            size="full"
            intent="whiteBorder"
            onClick={() => {
              onCancel?.()
              close()
            }}
          >
            {closeText}
          </Button>
          <Button
            size="full"
            onClick={() => {
              onConfirm?.()
              close()
            }}
          >
            {okText}
          </Button>
        </div>
      </div>
    </div>
  )
}