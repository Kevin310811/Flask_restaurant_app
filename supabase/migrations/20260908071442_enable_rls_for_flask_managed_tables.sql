/*
# Lock down Flask-managed tables

1. Purpose
- Enable Row Level Security on all application tables exposed by Supabase's Data API.
- The Flask server connects with its private database role and remains responsible for the existing session and ownership checks.

2. Tables
- `menu_items`: public menu catalog managed by the Flask admin area.
- `users`: application accounts managed by Flask authentication.
- `cart_items`: per-user shopping carts.
- `orders`: per-user order records.
- `order_items`: line items belonging to orders.
- `reservations`: per-user table reservations.

3. Security
- RLS is enabled on every table.
- Anonymous and Supabase-authenticated Data API roles receive no direct table access through four explicit deny policies per table.
- The Flask database role is not restricted by these policies, preserving the existing application behavior without exposing private account, cart, order, or reservation data through the public API.

4. Important notes
- No rows, columns, or data are deleted.
- Policies are dropped before recreation so this migration can be safely re-applied.
*/

ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_anon_menu_items_select" ON menu_items;
CREATE POLICY "deny_anon_menu_items_select" ON menu_items FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_menu_items_insert" ON menu_items;
CREATE POLICY "deny_anon_menu_items_insert" ON menu_items FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_menu_items_update" ON menu_items;
CREATE POLICY "deny_anon_menu_items_update" ON menu_items FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_menu_items_delete" ON menu_items;
CREATE POLICY "deny_anon_menu_items_delete" ON menu_items FOR DELETE TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "deny_anon_users_select" ON users;
CREATE POLICY "deny_anon_users_select" ON users FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_users_insert" ON users;
CREATE POLICY "deny_anon_users_insert" ON users FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_users_update" ON users;
CREATE POLICY "deny_anon_users_update" ON users FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_users_delete" ON users;
CREATE POLICY "deny_anon_users_delete" ON users FOR DELETE TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "deny_anon_cart_items_select" ON cart_items;
CREATE POLICY "deny_anon_cart_items_select" ON cart_items FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_cart_items_insert" ON cart_items;
CREATE POLICY "deny_anon_cart_items_insert" ON cart_items FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_cart_items_update" ON cart_items;
CREATE POLICY "deny_anon_cart_items_update" ON cart_items FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_cart_items_delete" ON cart_items;
CREATE POLICY "deny_anon_cart_items_delete" ON cart_items FOR DELETE TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "deny_anon_orders_select" ON orders;
CREATE POLICY "deny_anon_orders_select" ON orders FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_orders_insert" ON orders;
CREATE POLICY "deny_anon_orders_insert" ON orders FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_orders_update" ON orders;
CREATE POLICY "deny_anon_orders_update" ON orders FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_orders_delete" ON orders;
CREATE POLICY "deny_anon_orders_delete" ON orders FOR DELETE TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "deny_anon_order_items_select" ON order_items;
CREATE POLICY "deny_anon_order_items_select" ON order_items FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_order_items_insert" ON order_items;
CREATE POLICY "deny_anon_order_items_insert" ON order_items FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_order_items_update" ON order_items;
CREATE POLICY "deny_anon_order_items_update" ON order_items FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_order_items_delete" ON order_items;
CREATE POLICY "deny_anon_order_items_delete" ON order_items FOR DELETE TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "deny_anon_reservations_select" ON reservations;
CREATE POLICY "deny_anon_reservations_select" ON reservations FOR SELECT TO anon, authenticated USING (false);
DROP POLICY IF EXISTS "deny_anon_reservations_insert" ON reservations;
CREATE POLICY "deny_anon_reservations_insert" ON reservations FOR INSERT TO anon, authenticated WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_reservations_update" ON reservations;
CREATE POLICY "deny_anon_reservations_update" ON reservations FOR UPDATE TO anon, authenticated USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS "deny_anon_reservations_delete" ON reservations;
CREATE POLICY "deny_anon_reservations_delete" ON reservations FOR DELETE TO anon, authenticated USING (false);
