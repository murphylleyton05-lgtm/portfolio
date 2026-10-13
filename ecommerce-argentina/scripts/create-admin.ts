/**
 * Crea (o promueve) un usuario administrador del panel.
 *
 *   npm run admin:create -- tu@email.com "una-contraseña-segura"
 *
 * Lee NEXT_PUBLIC_SUPABASE_URL y SUPABASE_SECRET_KEY de .env.local.
 * Si el usuario ya existe en Supabase Auth, solo lo agrega como admin
 * (la contraseña se ignora).
 */
import { createClient } from "@supabase/supabase-js";

async function main() {
  const [email, password] = process.argv.slice(2);
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const secret = process.env.SUPABASE_SECRET_KEY;

  if (!url || !secret) throw new Error("Faltan NEXT_PUBLIC_SUPABASE_URL y/o SUPABASE_SECRET_KEY en .env.local");
  if (!email || !/^\S+@\S+\.\S+$/.test(email))
    throw new Error('Uso: npm run admin:create -- email@dominio.com "contraseña"');

  const supabase = createClient(url, secret, { auth: { persistSession: false, autoRefreshToken: false } });

  let userId: string | undefined;
  const created = await supabase.auth.admin.createUser({ email, password, email_confirm: true });
  if (created.data.user) {
    userId = created.data.user.id;
    console.log(`✓ Usuario creado: ${email}`);
  } else {
    // Ya existe: lo buscamos para darle permisos.
    for (let page = 1; !userId && page <= 50; page++) {
      const { data, error } = await supabase.auth.admin.listUsers({ page, perPage: 200 });
      if (error) throw error;
      userId = data.users.find((user) => user.email?.toLowerCase() === email.toLowerCase())?.id;
      if (data.users.length < 200) break;
    }
    if (!userId) throw new Error(`No se pudo crear el usuario: ${created.error?.message ?? "error desconocido"}`);
    console.log(`• El usuario ${email} ya existía`);
  }

  if (!password && created.data.user) console.warn("  (sin contraseña: usá 'Olvidé mi contraseña' desde Supabase)");

  const { error } = await supabase.from("admin_users").upsert({ user_id: userId }, { onConflict: "user_id" });
  if (error) throw new Error(`No se pudo dar permisos de admin: ${error.message}`);
  console.log("✓ Ahora es admin. Entrá en /admin/login");
}

main().catch((error) => {
  console.error(`✗ ${error instanceof Error ? error.message : error}`);
  process.exit(1);
});
