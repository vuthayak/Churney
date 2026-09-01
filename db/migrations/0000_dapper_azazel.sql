CREATE EXTENSION IF NOT EXISTS pg_trgm;--> statement-breakpoint
CREATE TYPE "public"."bonus_lifecycle" AS ENUM('pending', 'on_track', 'posted', 'forfeited', 'expired');--> statement-breakpoint
CREATE TYPE "public"."bonus_status" AS ENUM('rumored', 'confirmed', 'active', 'ending_soon', 'expired');--> statement-breakpoint
CREATE TYPE "public"."cap_period" AS ENUM('monthly', 'annual');--> statement-breakpoint
CREATE TYPE "public"."card_network" AS ENUM('amex', 'visa', 'mastercard');--> statement-breakpoint
CREATE TYPE "public"."card_role" AS ENUM('auto', 'keeper', 'churner');--> statement-breakpoint
CREATE TYPE "public"."churn_confidence" AS ENUM('verified', 'community', 'heuristic');--> statement-breakpoint
CREATE TYPE "public"."churn_rule_type" AS ENUM('lifetime_lockout', 'program_lockout', 'cycle_window', 'concurrent_limit', 'inquiry_limit', 'pull_policy', 'switch_vs_new');--> statement-breakpoint
CREATE TYPE "public"."event_state" AS ENUM('planned', 'submitted', 'approved', 'rejected', 'completed');--> statement-breakpoint
CREATE TYPE "public"."offer_status" AS ENUM('draft', 'in_review', 'published', 'retired');--> statement-breakpoint
CREATE TYPE "public"."redemption_kind" AS ENUM('fixed_travel', 'transfer_partner', 'statement_credit', 'gift_card', 'merchandise', 'experiences', 'pay_with_points');--> statement-breakpoint
CREATE TYPE "public"."reward_kind" AS ENUM('points', 'cashback', 'bonus_dollars');--> statement-breakpoint
CREATE TYPE "public"."risk_tolerance" AS ENUM('conservative', 'balanced', 'aggressive');--> statement-breakpoint
CREATE TYPE "public"."rotation_event_ty" AS ENUM('apply', 'product_switch', 'cancel', 'downgrade_no_fee', 'pause', 'convert_to_keeper');--> statement-breakpoint
CREATE TYPE "public"."tx_source" AS ENUM('ios_shortcut', 'manual', 'csv_import');--> statement-breakpoint
CREATE TYPE "public"."tx_status" AS ENUM('draft', 'confirmed', 'ignored', 'merged');--> statement-breakpoint
CREATE TYPE "public"."user_role" AS ENUM('user', 'editor', 'admin');--> statement-breakpoint
CREATE TABLE "devices" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"label" text NOT NULL,
	"token_hash" "bytea" NOT NULL,
	"scopes" text[] DEFAULT '{write:transactions}'::text[] NOT NULL,
	"last_used_at" timestamp with time zone,
	"revoked_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "devices_token_hash_unique" UNIQUE("token_hash")
);
--> statement-breakpoint
CREATE TABLE "profiles" (
	"id" uuid PRIMARY KEY NOT NULL,
	"display_name" text,
	"role" "user_role" DEFAULT 'user' NOT NULL,
	"default_currency" char(3) DEFAULT 'CAD' NOT NULL,
	"timezone" text DEFAULT 'America/Toronto' NOT NULL,
	"risk_tolerance" "risk_tolerance" DEFAULT 'balanced' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "card_versions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"card_id" uuid NOT NULL,
	"valid_from" date NOT NULL,
	"valid_to" date,
	"annual_fee_minor" integer NOT NULL,
	"extra_card_fee_minor" integer,
	"fx_fee_pct" numeric(4, 2),
	"income_req_personal" integer,
	"income_req_household" integer,
	"purchase_apr" numeric(5, 2),
	"cash_apr" numeric(5, 2),
	"source_url" text NOT NULL,
	"verified_at" timestamp with time zone NOT NULL,
	CONSTRAINT "card_versions_card_id_valid_from_unique" UNIQUE("card_id","valid_from")
);
--> statement-breakpoint
CREATE TABLE "cards" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"issuer_id" uuid NOT NULL,
	"program_id" uuid NOT NULL,
	"network_id" "card_network" NOT NULL,
	"name" text NOT NULL,
	"status" text DEFAULT 'live' NOT NULL,
	"image_url" text,
	CONSTRAINT "cards_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "categories" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	CONSTRAINT "categories_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "conversion_bonuses" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"transfer_rate_id" uuid,
	"from_program_id" uuid NOT NULL,
	"to_program_id" uuid NOT NULL,
	"bonus_pct" integer,
	"bonus_ratio_num" integer,
	"bonus_ratio_den" integer,
	"status" "bonus_status" DEFAULT 'rumored' NOT NULL,
	"starts_on" date,
	"ends_on" date NOT NULL,
	"constraints_text" text,
	"source_url" text,
	"verified_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "earn_promotions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"card_id" uuid NOT NULL,
	"category_id" uuid NOT NULL,
	"rate" numeric(6, 3) NOT NULL,
	"stackable" boolean DEFAULT false NOT NULL,
	"starts_on" date NOT NULL,
	"ends_on" date,
	"cap_amount_minor" integer,
	"cap_period" "cap_period",
	"source_url" text,
	"verified_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "earn_rates" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"card_version_id" uuid NOT NULL,
	"category_id" uuid,
	"rate" numeric(6, 3) NOT NULL,
	"kind" "reward_kind" NOT NULL,
	"cap_amount_minor" integer,
	"cap_period" "cap_period",
	"excluded" boolean DEFAULT false NOT NULL
);
--> statement-breakpoint
CREATE TABLE "issuers" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"rules_note" text,
	CONSTRAINT "issuers_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "networks" (
	"id" "card_network" PRIMARY KEY NOT NULL,
	"acceptance_notes" text
);
--> statement-breakpoint
CREATE TABLE "offers" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"card_id" uuid NOT NULL,
	"status" "offer_status" DEFAULT 'draft' NOT NULL,
	"headline" text NOT NULL,
	"min_spend_minor" integer,
	"deadline_days" integer,
	"deadline_end_date" date,
	"reward_points" integer,
	"reward_cashback_minor" integer,
	"eligibility_notes" text,
	"first_year_free" boolean DEFAULT false NOT NULL,
	"source_url" text,
	"verified_at" timestamp with time zone,
	"published_at" timestamp with time zone,
	"retired_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "program_excluded_categories" (
	"program_id" uuid NOT NULL,
	"category_id" uuid NOT NULL,
	"source_url" text,
	"verified_at" timestamp with time zone,
	CONSTRAINT "program_excluded_categories_program_id_category_id_pk" PRIMARY KEY("program_id","category_id")
);
--> statement-breakpoint
CREATE TABLE "program_valuations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"program_id" uuid NOT NULL,
	"context" text NOT NULL,
	"baseline_cpp" numeric(5, 2) NOT NULL,
	"rationale" text,
	"valid_from" date DEFAULT CURRENT_DATE NOT NULL,
	"valid_to" date
);
--> statement-breakpoint
CREATE TABLE "programs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"issuer_id" uuid,
	"reward_kind" "reward_kind" NOT NULL,
	"flexibility_score" numeric(5, 2),
	CONSTRAINT "programs_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "redemption_options" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"program_id" uuid NOT NULL,
	"kind" "redemption_kind" NOT NULL,
	"cpp_min" numeric(5, 2),
	"cpp_typical" numeric(5, 2),
	"cpp_max" numeric(5, 2),
	"example_redemption" text,
	"notes" text,
	"valid_from" date DEFAULT CURRENT_DATE NOT NULL,
	"valid_to" date,
	"source_url" text,
	"verified_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "transfer_rates" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"from_program_id" uuid NOT NULL,
	"to_program_id" uuid NOT NULL,
	"ratio_num" integer NOT NULL,
	"ratio_den" integer NOT NULL,
	"min_transfer" integer,
	"annual_cap" integer,
	"valid_from" date NOT NULL,
	"valid_to" date,
	"source_url" text,
	"verified_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "merchant_aliases" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "merchant_aliases_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"merchant_id" uuid,
	"user_id" uuid,
	"alias_norm" text NOT NULL,
	CONSTRAINT "merchant_aliases_user_id_alias_norm_unique" UNIQUE("user_id","alias_norm")
);
--> statement-breakpoint
CREATE TABLE "merchants" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"norm_name" text NOT NULL,
	"display_name" text NOT NULL,
	"brand_family" text,
	"default_category_id" uuid,
	"accepted_networks" "card_network"[] DEFAULT '{amex,visa,mastercard}'::card_network[] NOT NULL,
	"confidence_global" numeric(3, 2)
);
--> statement-breakpoint
CREATE TABLE "pending_merchants" (
	"norm" text PRIMARY KEY NOT NULL,
	"occurrences" integer DEFAULT 1 NOT NULL,
	"last_seen_at" timestamp with time zone,
	"llm_category_guess" uuid
);
--> statement-breakpoint
CREATE TABLE "applications_log" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"card_id" uuid NOT NULL,
	"offer_id" uuid,
	"state" "event_state" DEFAULT 'submitted' NOT NULL,
	"applied_on" date NOT NULL,
	"decided_on" date,
	"bonus_posted_on" date
);
--> statement-breakpoint
CREATE TABLE "category_overrides" (
	"user_id" uuid,
	"merchant_id" uuid,
	"category_id" uuid,
	CONSTRAINT "category_overrides_user_id_merchant_id_pk" PRIMARY KEY("user_id","merchant_id")
);
--> statement-breakpoint
CREATE TABLE "user_cards" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"card_id" uuid NOT NULL,
	"nickname" text,
	"match_hint" text,
	"opened_on" date,
	"closed_on" date,
	"role" "card_role" DEFAULT 'auto' NOT NULL,
	"bonus_status" "bonus_lifecycle" DEFAULT 'pending' NOT NULL,
	"notes" text,
	CONSTRAINT "user_cards_match_hint_unique" UNIQUE("match_hint")
);
--> statement-breakpoint
CREATE TABLE "ingest_logs" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "ingest_logs_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"device_id" uuid,
	"payload" jsonb NOT NULL,
	"result_code" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "transactions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"user_card_id" uuid,
	"source" "tx_source" NOT NULL,
	"status" "tx_status" DEFAULT 'draft' NOT NULL,
	"occurred_at" timestamp with time zone NOT NULL,
	"merchant_raw" text,
	"merchant_id" uuid,
	"category_override" uuid,
	"amount_minor" integer NOT NULL,
	"currency" char(3) DEFAULT 'CAD' NOT NULL,
	"fx_rate" numeric(12, 8),
	"fx_source" text,
	"fx_rate_date" date,
	"cad_amount_minor" integer GENERATED ALWAYS AS (CASE WHEN currency = 'CAD' THEN amount_minor ELSE round(amount_minor * fx_rate) END) STORED,
	"dedupe_key" text,
	"idempotency_key" text,
	"engine_version" integer DEFAULT 0 NOT NULL,
	"earned_points" bigint,
	"earned_cashback_minor" bigint,
	"value_cpp_snapshot" numeric(5, 2),
	"breakdown" jsonb,
	"best_wallet_alternative" jsonb,
	"confidence" numeric(3, 2),
	"imported_batch_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "churn_recommendations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"generated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"items" jsonb NOT NULL
);
--> statement-breakpoint
CREATE TABLE "churn_rules" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"issuer_id" uuid,
	"card_id" uuid,
	"program_id" uuid,
	"rule_type" "churn_rule_type" NOT NULL,
	"params" jsonb NOT NULL,
	"confidence" "churn_confidence",
	"source_url" text,
	"verified_at" timestamp with time zone,
	"active" boolean DEFAULT true NOT NULL
);
--> statement-breakpoint
CREATE TABLE "rotation_events" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"plan_id" uuid NOT NULL,
	"seq" integer NOT NULL,
	"event_type" "rotation_event_ty" NOT NULL,
	"state" "event_state" DEFAULT 'planned' NOT NULL,
	"card_id" uuid,
	"offer_id" uuid,
	"target_date" date,
	"min_spend_progress_minor" integer DEFAULT 0,
	"explanation" jsonb
);
--> statement-breakpoint
CREATE TABLE "rotation_plans" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"horizon_months" integer DEFAULT 24 NOT NULL,
	"daily_wallet" jsonb,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "change_log" (
	"id" bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "change_log_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START WITH 1 CACHE 1),
	"entity" text NOT NULL,
	"entity_id" uuid NOT NULL,
	"diff" jsonb NOT NULL,
	"reason" text,
	"actor" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "fx_rates" (
	"rate_date" date NOT NULL,
	"pair" text NOT NULL,
	"rate" numeric(12, 8) NOT NULL,
	"source" text NOT NULL,
	"fetched_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "fx_rates_rate_date_pair_pk" PRIMARY KEY("rate_date","pair")
);
--> statement-breakpoint
ALTER TABLE "devices" ADD CONSTRAINT "devices_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "card_versions" ADD CONSTRAINT "card_versions_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "cards" ADD CONSTRAINT "cards_issuer_id_issuers_id_fk" FOREIGN KEY ("issuer_id") REFERENCES "public"."issuers"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "cards" ADD CONSTRAINT "cards_program_id_programs_id_fk" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversion_bonuses" ADD CONSTRAINT "conversion_bonuses_transfer_rate_id_transfer_rates_id_fk" FOREIGN KEY ("transfer_rate_id") REFERENCES "public"."transfer_rates"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversion_bonuses" ADD CONSTRAINT "conversion_bonuses_from_program_id_programs_id_fk" FOREIGN KEY ("from_program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversion_bonuses" ADD CONSTRAINT "conversion_bonuses_to_program_id_programs_id_fk" FOREIGN KEY ("to_program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "earn_promotions" ADD CONSTRAINT "earn_promotions_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "earn_promotions" ADD CONSTRAINT "earn_promotions_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "earn_rates" ADD CONSTRAINT "earn_rates_card_version_id_card_versions_id_fk" FOREIGN KEY ("card_version_id") REFERENCES "public"."card_versions"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "earn_rates" ADD CONSTRAINT "earn_rates_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "offers" ADD CONSTRAINT "offers_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "program_excluded_categories" ADD CONSTRAINT "program_excluded_categories_program_id_programs_id_fk" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "program_excluded_categories" ADD CONSTRAINT "program_excluded_categories_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "program_valuations" ADD CONSTRAINT "program_valuations_program_id_programs_id_fk" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "programs" ADD CONSTRAINT "programs_issuer_id_issuers_id_fk" FOREIGN KEY ("issuer_id") REFERENCES "public"."issuers"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "redemption_options" ADD CONSTRAINT "redemption_options_program_id_programs_id_fk" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transfer_rates" ADD CONSTRAINT "transfer_rates_from_program_id_programs_id_fk" FOREIGN KEY ("from_program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transfer_rates" ADD CONSTRAINT "transfer_rates_to_program_id_programs_id_fk" FOREIGN KEY ("to_program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "merchant_aliases" ADD CONSTRAINT "merchant_aliases_merchant_id_merchants_id_fk" FOREIGN KEY ("merchant_id") REFERENCES "public"."merchants"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "merchant_aliases" ADD CONSTRAINT "merchant_aliases_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "merchants" ADD CONSTRAINT "merchants_default_category_id_categories_id_fk" FOREIGN KEY ("default_category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "pending_merchants" ADD CONSTRAINT "pending_merchants_llm_category_guess_categories_id_fk" FOREIGN KEY ("llm_category_guess") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "applications_log" ADD CONSTRAINT "applications_log_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "applications_log" ADD CONSTRAINT "applications_log_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "applications_log" ADD CONSTRAINT "applications_log_offer_id_offers_id_fk" FOREIGN KEY ("offer_id") REFERENCES "public"."offers"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "category_overrides" ADD CONSTRAINT "category_overrides_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "category_overrides" ADD CONSTRAINT "category_overrides_merchant_id_merchants_id_fk" FOREIGN KEY ("merchant_id") REFERENCES "public"."merchants"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "category_overrides" ADD CONSTRAINT "category_overrides_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "user_cards" ADD CONSTRAINT "user_cards_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "user_cards" ADD CONSTRAINT "user_cards_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ingest_logs" ADD CONSTRAINT "ingest_logs_device_id_devices_id_fk" FOREIGN KEY ("device_id") REFERENCES "public"."devices"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_user_card_id_user_cards_id_fk" FOREIGN KEY ("user_card_id") REFERENCES "public"."user_cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_merchant_id_merchants_id_fk" FOREIGN KEY ("merchant_id") REFERENCES "public"."merchants"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_category_override_categories_id_fk" FOREIGN KEY ("category_override") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "churn_recommendations" ADD CONSTRAINT "churn_recommendations_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "churn_rules" ADD CONSTRAINT "churn_rules_issuer_id_issuers_id_fk" FOREIGN KEY ("issuer_id") REFERENCES "public"."issuers"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "churn_rules" ADD CONSTRAINT "churn_rules_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "churn_rules" ADD CONSTRAINT "churn_rules_program_id_programs_id_fk" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "rotation_events" ADD CONSTRAINT "rotation_events_plan_id_rotation_plans_id_fk" FOREIGN KEY ("plan_id") REFERENCES "public"."rotation_plans"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "rotation_events" ADD CONSTRAINT "rotation_events_card_id_cards_id_fk" FOREIGN KEY ("card_id") REFERENCES "public"."cards"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "rotation_events" ADD CONSTRAINT "rotation_events_offer_id_offers_id_fk" FOREIGN KEY ("offer_id") REFERENCES "public"."offers"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "rotation_plans" ADD CONSTRAINT "rotation_plans_user_id_profiles_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "change_log" ADD CONSTRAINT "change_log_actor_profiles_id_fk" FOREIGN KEY ("actor") REFERENCES "public"."profiles"("id") ON DELETE no action ON UPDATE no action;