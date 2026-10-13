import { siteConfig } from "@site-config";
import { whatsappUrl } from "@/lib/utils";
import { WhatsAppIcon } from "./brand-icons";

/** Botón flotante de WhatsApp (abajo a la derecha). */
export function WhatsAppFloatingButton() {
  if (!siteConfig.contact.whatsapp) return null;
  return (
    <a
      href={whatsappUrl(siteConfig.contact.whatsappDefaultMessage)}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Escribinos por WhatsApp"
      className="fixed right-4 bottom-4 z-40 inline-flex size-14 items-center justify-center rounded-full bg-[#25d366] text-white shadow-lg transition hover:scale-105 focus-visible:outline-offset-4"
    >
      <WhatsAppIcon width={28} height={28} />
    </a>
  );
}

/** Link "Consultar por WhatsApp" con un mensaje armado (producto, pedido, etc.). */
export function WhatsAppLink({
  message,
  label = "Consultar por WhatsApp",
  className,
}: {
  message: string;
  label?: string;
  className?: string;
}) {
  if (!siteConfig.contact.whatsapp) return null;
  return (
    <a
      href={whatsappUrl(message)}
      target="_blank"
      rel="noopener noreferrer"
      className={
        className ??
        "inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-[#25d366] px-4 text-sm font-medium text-[#128c4a] transition hover:bg-[#25d366]/10"
      }
    >
      <WhatsAppIcon width={18} height={18} />
      {label}
    </a>
  );
}
