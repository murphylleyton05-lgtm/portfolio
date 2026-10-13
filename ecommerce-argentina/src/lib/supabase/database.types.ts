/**
 * Tipos de la base de datos (mismo formato que `supabase gen types typescript`).
 * Si cambiás el esquema podés regenerarlos con:
 *   npx supabase gen types typescript --project-id <tu-proyecto> > src/lib/supabase/database.types.ts
 */

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type Database = {
  __InternalSupabase: {
    PostgrestVersion: "12";
  };
  public: {
    Tables: {
      categories: {
        Row: {
          id: string;
          name: string;
          slug: string;
          description: string;
          position: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          slug: string;
          description?: string;
          position?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          slug?: string;
          description?: string;
          position?: number;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      products: {
        Row: {
          id: string;
          category_id: string | null;
          name: string;
          slug: string;
          description: string;
          price: number;
          compare_at_price: number | null;
          images: string[];
          active: boolean;
          featured: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          category_id?: string | null;
          name: string;
          slug: string;
          description?: string;
          price: number;
          compare_at_price?: number | null;
          images?: string[];
          active?: boolean;
          featured?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          category_id?: string | null;
          name?: string;
          slug?: string;
          description?: string;
          price?: number;
          compare_at_price?: number | null;
          images?: string[];
          active?: boolean;
          featured?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "products_category_id_fkey";
            columns: ["category_id"];
            isOneToOne: false;
            referencedRelation: "categories";
            referencedColumns: ["id"];
          },
        ];
      };
      product_variants: {
        Row: {
          id: string;
          product_id: string;
          name: string;
          sku: string | null;
          price: number | null;
          stock: number;
          position: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          product_id: string;
          name?: string;
          sku?: string | null;
          price?: number | null;
          stock?: number;
          position?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          product_id?: string;
          name?: string;
          sku?: string | null;
          price?: number | null;
          stock?: number;
          position?: number;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "product_variants_product_id_fkey";
            columns: ["product_id"];
            isOneToOne: false;
            referencedRelation: "products";
            referencedColumns: ["id"];
          },
        ];
      };
      customers: {
        Row: {
          id: string;
          email: string;
          name: string;
          phone: string | null;
          dni: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          email: string;
          name: string;
          phone?: string | null;
          dni?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          name?: string;
          phone?: string | null;
          dni?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      orders: {
        Row: {
          id: string;
          number: number;
          access_token: string;
          customer_id: string | null;
          status: Database["public"]["Enums"]["order_status"];
          customer_name: string;
          customer_email: string;
          customer_phone: string;
          customer_dni: string | null;
          delivery_method: Database["public"]["Enums"]["delivery_method"];
          shipping_address: Json | null;
          shipping_zone: string | null;
          subtotal: number;
          shipping_cost: number;
          total: number;
          notes: string | null;
          mp_preference_id: string | null;
          mp_init_point: string | null;
          mp_payment_id: string | null;
          mp_payment_status: string | null;
          mp_payment_status_detail: string | null;
          paid_at: string | null;
          stock_applied: boolean;
          confirmation_email_sent_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          access_token?: string;
          customer_id?: string | null;
          status?: Database["public"]["Enums"]["order_status"];
          customer_name: string;
          customer_email: string;
          customer_phone: string;
          customer_dni?: string | null;
          delivery_method: Database["public"]["Enums"]["delivery_method"];
          shipping_address?: Json | null;
          shipping_zone?: string | null;
          subtotal: number;
          shipping_cost?: number;
          total: number;
          notes?: string | null;
          mp_preference_id?: string | null;
          mp_init_point?: string | null;
          mp_payment_id?: string | null;
          mp_payment_status?: string | null;
          mp_payment_status_detail?: string | null;
          paid_at?: string | null;
          stock_applied?: boolean;
          confirmation_email_sent_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          access_token?: string;
          customer_id?: string | null;
          status?: Database["public"]["Enums"]["order_status"];
          customer_name?: string;
          customer_email?: string;
          customer_phone?: string;
          customer_dni?: string | null;
          delivery_method?: Database["public"]["Enums"]["delivery_method"];
          shipping_address?: Json | null;
          shipping_zone?: string | null;
          subtotal?: number;
          shipping_cost?: number;
          total?: number;
          notes?: string | null;
          mp_preference_id?: string | null;
          mp_init_point?: string | null;
          mp_payment_id?: string | null;
          mp_payment_status?: string | null;
          mp_payment_status_detail?: string | null;
          paid_at?: string | null;
          stock_applied?: boolean;
          confirmation_email_sent_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "orders_customer_id_fkey";
            columns: ["customer_id"];
            isOneToOne: false;
            referencedRelation: "customers";
            referencedColumns: ["id"];
          },
        ];
      };
      order_items: {
        Row: {
          id: string;
          order_id: string;
          product_id: string | null;
          variant_id: string | null;
          product_name: string;
          variant_name: string;
          sku: string | null;
          image: string | null;
          unit_price: number;
          quantity: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          order_id: string;
          product_id?: string | null;
          variant_id?: string | null;
          product_name: string;
          variant_name: string;
          sku?: string | null;
          image?: string | null;
          unit_price: number;
          quantity: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          order_id?: string;
          product_id?: string | null;
          variant_id?: string | null;
          product_name?: string;
          variant_name?: string;
          sku?: string | null;
          image?: string | null;
          unit_price?: number;
          quantity?: number;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "order_items_order_id_fkey";
            columns: ["order_id"];
            isOneToOne: false;
            referencedRelation: "orders";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "order_items_product_id_fkey";
            columns: ["product_id"];
            isOneToOne: false;
            referencedRelation: "products";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "order_items_variant_id_fkey";
            columns: ["variant_id"];
            isOneToOne: false;
            referencedRelation: "product_variants";
            referencedColumns: ["id"];
          },
        ];
      };
      admin_users: {
        Row: {
          user_id: string;
          created_at: string;
        };
        Insert: {
          user_id: string;
          created_at?: string;
        };
        Update: {
          user_id?: string;
          created_at?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      is_admin: {
        Args: Record<PropertyKey, never>;
        Returns: boolean;
      };
      confirm_order_payment: {
        Args: {
          p_order_id: string;
          p_payment_id: string;
          p_payment_status: string;
          p_payment_status_detail?: string | null;
        };
        Returns: boolean;
      };
      set_order_status: {
        Args: {
          p_order_id: string;
          p_status: Database["public"]["Enums"]["order_status"];
        };
        Returns: Database["public"]["Enums"]["order_status"];
      };
    };
    Enums: {
      order_status:
        | "pending_payment"
        | "paid"
        | "preparing"
        | "shipped"
        | "ready_for_pickup"
        | "delivered"
        | "cancelled";
      delivery_method: "shipping" | "pickup";
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type PublicSchema = Database["public"];

export type Tables<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Row"];
export type TablesInsert<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Insert"];
export type TablesUpdate<T extends keyof PublicSchema["Tables"]> = PublicSchema["Tables"][T]["Update"];
export type Enums<T extends keyof PublicSchema["Enums"]> = PublicSchema["Enums"][T];

export type OrderStatus = Enums<"order_status">;
export type DeliveryMethod = Enums<"delivery_method">;
