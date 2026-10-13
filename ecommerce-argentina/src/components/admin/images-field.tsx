"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight, ImagePlus, X } from "lucide-react";
import { PRODUCT_IMAGES_BUCKET } from "@/lib/admin/schemas";
import { createBrowserSupabase } from "@/lib/supabase/browser";
import { cn } from "@/lib/utils";

const MAX_SIZE = 5 * 1024 * 1024;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/avif", "image/gif"];

/**
 * Sube imágenes directo del navegador a Supabase Storage (con la sesión del
 * admin; la política del bucket exige is_admin()). Guarda solo las URLs.
 */
export function ImagesField({
  value,
  onChange,
  error,
}: {
  value: string[];
  onChange: (images: string[]) => void;
  error?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    setUploadError(null);
    const supabase = createBrowserSupabase();
    const uploaded: string[] = [];
    const list = [...files].slice(0, Math.max(0, 10 - value.length));
    setUploading(true);
    for (const file of list) {
      if (!ACCEPTED.includes(file.type)) {
        setUploadError(`"${file.name}": formato no permitido (JPG, PNG, WebP, AVIF o GIF).`);
        continue;
      }
      if (file.size > MAX_SIZE) {
        setUploadError(`"${file.name}" pesa más de 5 MB.`);
        continue;
      }
      const extension = file.name.split(".").pop()?.toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg";
      const path = `products/${crypto.randomUUID()}.${extension}`;
      const { error } = await supabase.storage
        .from(PRODUCT_IMAGES_BUCKET)
        .upload(path, file, { contentType: file.type, cacheControl: "31536000", upsert: false });
      if (error) {
        setUploadError(`No se pudo subir "${file.name}": ${error.message}`);
        continue;
      }
      uploaded.push(supabase.storage.from(PRODUCT_IMAGES_BUCKET).getPublicUrl(path).data.publicUrl);
    }
    setUploading(false);
    if (uploaded.length) onChange([...value, ...uploaded]);
    if (inputRef.current) inputRef.current.value = "";
  }

  function move(index: number, delta: number) {
    const next = [...value];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-3">
      <ul className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        {value.map((url, index) => (
          <li key={url} className="group relative aspect-[4/5] overflow-hidden rounded-lg border border-border bg-muted">
            <Image src={url} alt={`Imagen ${index + 1}`} fill sizes="160px" unoptimized className="object-cover" />
            {index === 0 && (
              <span className="absolute top-1 left-1 rounded bg-primary px-1.5 py-0.5 text-[10px] text-primary-foreground">Portada</span>
            )}
            <div className="absolute inset-x-1 bottom-1 flex justify-between gap-1">
              <IconButton label="Mover a la izquierda" onClick={() => move(index, -1)} disabled={index === 0}>
                <ChevronLeft className="size-3.5" />
              </IconButton>
              <IconButton label="Quitar imagen" onClick={() => onChange(value.filter((item) => item !== url))}>
                <X className="size-3.5" />
              </IconButton>
              <IconButton label="Mover a la derecha" onClick={() => move(index, 1)} disabled={index === value.length - 1}>
                <ChevronRight className="size-3.5" />
              </IconButton>
            </div>
          </li>
        ))}
        {value.length < 10 && (
          <li>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className={cn(
                "flex aspect-[4/5] w-full flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-border text-xs text-muted-foreground transition hover:border-primary hover:text-foreground",
                uploading && "animate-pulse",
              )}
            >
              <ImagePlus className="size-5" aria-hidden />
              {uploading ? "Subiendo…" : "Agregar imagen"}
            </button>
          </li>
        )}
      </ul>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        multiple
        className="sr-only"
        aria-label="Elegir imágenes"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <p className="text-xs text-muted-foreground">Hasta 10 imágenes de 5 MB. La primera es la portada. Ideal: 4:5 (ej. 1200×1500).</p>
      {(uploadError || error) && (
        <p role="alert" className="text-sm text-red-600">
          {uploadError || error}
        </p>
      )}
    </div>
  );
}

function IconButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
      className="inline-flex size-6 items-center justify-center rounded bg-background/90 shadow disabled:opacity-30"
    >
      {children}
    </button>
  );
}
