"use client";

import { useState } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

export function ProductGallery({ images, name }: { images: string[]; name: string }) {
  const [active, setActive] = useState(0);
  const current = images[active] ?? images[0];

  if (!current) {
    return (
      <div className="flex aspect-[4/5] items-center justify-center rounded-2xl bg-muted text-sm text-muted-foreground">
        Sin imagen
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-muted">
        <Image
          key={current}
          src={current}
          alt={images.length > 1 ? `${name} — imagen ${active + 1} de ${images.length}` : name}
          fill
          preload={active === 0}
          sizes="(min-width: 1024px) 50vw, 100vw"
          className="object-cover"
        />
      </div>
      {images.length > 1 && (
        <ul className="flex gap-2 overflow-x-auto" aria-label="Imágenes del producto">
          {images.map((image, index) => (
            <li key={image}>
              <button
                type="button"
                onClick={() => setActive(index)}
                aria-label={`Ver imagen ${index + 1}`}
                aria-current={index === active}
                className={cn(
                  "relative block aspect-[4/5] w-20 overflow-hidden rounded-lg border-2 bg-muted",
                  index === active ? "border-primary" : "border-transparent opacity-70 hover:opacity-100",
                )}
              >
                <Image src={image} alt="" fill sizes="80px" className="object-cover" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
