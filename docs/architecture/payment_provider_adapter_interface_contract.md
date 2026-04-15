# Payment Provider Adapter Interface Contract

## Purpose
Define a provider-agnostic payment adapter contract for the **commerce domain** that supports:
- create payment
- verify payment
- refund

This contract intentionally excludes billing concerns (rating, invoicing, tax rules, subscription lifecycle) to keep clear domain boundaries.

## Domain Boundary (Commerce vs Billing)

### Commerce domain responsibilities (this interface)
- Initiate payment intent/authorization/capture requests through external providers.
- Verify payment state with provider.
- Execute refunds via provider.
- Normalize provider responses into a shared commerce model.
- Route requests to an eligible provider based on country + payment method + merchant context.

### Billing domain responsibilities (explicitly out of scope)
- Price calculation, discounts, taxation, invoice generation.
- Ledger accounting and revenue recognition.
- Plan/subscription lifecycle policies.
- Dunning and receivables workflows.

---

## Interface Definition (Provider-Agnostic)

```ts
// Domain identifiers
export type CountryCode = string; // ISO 3166-1 alpha-2 (e.g., "US", "IN")
export type CurrencyCode = string; // ISO 4217
export type PaymentProviderKey = string; // internal provider identifier
export type PaymentMethodType =
  | "card"
  | "bank_transfer"
  | "wallet"
  | "upi"
  | "local_method"
  | "other";

// Commerce-owned statuses (normalized across providers)
export type CommercePaymentStatus =
  | "pending"
  | "requires_action"
  | "authorized"
  | "captured"
  | "failed"
  | "cancelled"
  | "refunded"
  | "partially_refunded";

// Core command contracts
export interface CreatePaymentCommand {
  requestId: string; // idempotency key controlled by commerce domain
  countryCode: CountryCode;
  currency: CurrencyCode;
  amountMinor: number; // minor units (e.g., cents)
  methodType: PaymentMethodType;
  orderId: string;
  customerId: string;
  metadata?: Record<string, string>;
  returnUrl?: string;
  statementDescriptor?: string;
}

export interface VerifyPaymentCommand {
  requestId: string;
  commercePaymentId: string;
  providerPaymentReference?: string;
}

export interface RefundPaymentCommand {
  requestId: string; // idempotent refund request key
  commercePaymentId: string;
  amountMinor?: number; // absent => full refund
  reasonCode?: string;
  metadata?: Record<string, string>;
}

// Standardized result envelopes
export interface PaymentOperationContext {
  provider: PaymentProviderKey;
  providerPaymentReference?: string;
  countryCode: CountryCode;
  methodType: PaymentMethodType;
}

export interface CreatePaymentResult {
  commercePaymentId: string;
  status: CommercePaymentStatus;
  nextActionUrl?: string;
  context: PaymentOperationContext;
  rawProviderCode?: string;
}

export interface VerifyPaymentResult {
  commercePaymentId: string;
  status: CommercePaymentStatus;
  verifiedAt: string; // ISO datetime
  context: PaymentOperationContext;
  rawProviderCode?: string;
}

export interface RefundPaymentResult {
  commercePaymentId: string;
  refundId: string;
  status: "pending" | "succeeded" | "failed";
  refundedAmountMinor: number;
  context: PaymentOperationContext;
  rawProviderCode?: string;
}

// Error model normalized by commerce domain
export interface PaymentAdapterError {
  code:
    | "invalid_request"
    | "not_supported"
    | "provider_unavailable"
    | "provider_rejected"
    | "timeout"
    | "unknown";
  message: string;
  retryable: boolean;
  provider?: PaymentProviderKey;
  providerCode?: string;
}

export type PaymentResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: PaymentAdapterError };

// Main provider adapter contract
export interface PaymentProviderAdapter {
  readonly provider: PaymentProviderKey;
  readonly supportedCountries: readonly CountryCode[];
  readonly supportedMethods: readonly PaymentMethodType[];

  createPayment(command: CreatePaymentCommand): Promise<PaymentResult<CreatePaymentResult>>;
  verifyPayment(command: VerifyPaymentCommand): Promise<PaymentResult<VerifyPaymentResult>>;
  refundPayment(command: RefundPaymentCommand): Promise<PaymentResult<RefundPaymentResult>>;
}
```

---

## Multi-Provider + Country Routing Contract

```ts
export interface ProviderEligibilityQuery {
  countryCode: CountryCode;
  methodType: PaymentMethodType;
  currency: CurrencyCode;
}

export interface PaymentProviderRouter {
  resolve(query: ProviderEligibilityQuery): PaymentProviderAdapter;
  listEligible(query: ProviderEligibilityQuery): PaymentProviderAdapter[];
}
```

**Notes**
- Router owns provider selection policy; adapters never hardcode fallback to other providers.
- Country support is explicit (`supportedCountries`) to enable country-based provider partitioning.
- Multiple providers are supported by registering many adapters behind `PaymentProviderRouter`.

---

## Commerce Domain Integration Contract

```ts
// Commerce-facing port used by application services/use-cases.
export interface CommercePaymentGateway {
  create(command: CreatePaymentCommand): Promise<PaymentResult<CreatePaymentResult>>;
  verify(command: VerifyPaymentCommand): Promise<PaymentResult<VerifyPaymentResult>>;
  refund(command: RefundPaymentCommand): Promise<PaymentResult<RefundPaymentResult>>;
}

export class RoutedCommercePaymentGateway implements CommercePaymentGateway {
  constructor(private readonly router: PaymentProviderRouter) {}

  async create(command: CreatePaymentCommand) {
    const adapter = this.router.resolve({
      countryCode: command.countryCode,
      methodType: command.methodType,
      currency: command.currency,
    });
    return adapter.createPayment(command);
  }

  async verify(command: VerifyPaymentCommand) {
    // Lookup payment aggregate to retrieve country/method/currency for deterministic routing.
    // The lookup is commerce-domain owned (not billing-domain owned).
    throw new Error("implementation depends on commerce payment aggregate lookup");
  }

  async refund(command: RefundPaymentCommand) {
    // Same routing principle as verify: derive adapter from commerce payment aggregate state.
    throw new Error("implementation depends on commerce payment aggregate lookup");
  }
}
```

---

## Example Adapter Structure (No Provider-Specific Logic in Contract)

```ts
// Generic structure only. Concrete provider mappings stay inside implementation modules.
export abstract class BasePaymentProviderAdapter implements PaymentProviderAdapter {
  abstract readonly provider: PaymentProviderKey;
  abstract readonly supportedCountries: readonly CountryCode[];
  abstract readonly supportedMethods: readonly PaymentMethodType[];

  abstract createPayment(
    command: CreatePaymentCommand,
  ): Promise<PaymentResult<CreatePaymentResult>>;

  abstract verifyPayment(
    command: VerifyPaymentCommand,
  ): Promise<PaymentResult<VerifyPaymentResult>>;

  abstract refundPayment(
    command: RefundPaymentCommand,
  ): Promise<PaymentResult<RefundPaymentResult>>;

  protected toAdapterError(input: {
    code?: string;
    message?: string;
    retryable?: boolean;
  }): PaymentAdapterError {
    return {
      code: "unknown",
      message: input.message ?? "Unhandled payment adapter error",
      retryable: input.retryable ?? false,
      provider: this.provider,
      providerCode: input.code,
    };
  }
}

export interface PaymentProviderRegistry {
  register(adapter: PaymentProviderAdapter): void;
  all(): PaymentProviderAdapter[];
}

export class InMemoryPaymentProviderRegistry implements PaymentProviderRegistry {
  private readonly adapters = new Map<PaymentProviderKey, PaymentProviderAdapter>();

  register(adapter: PaymentProviderAdapter): void {
    this.adapters.set(adapter.provider, adapter);
  }

  all(): PaymentProviderAdapter[] {
    return [...this.adapters.values()];
  }
}
```

---

## QC FIX Checklist Mapping
- **No provider-specific logic:** interface uses normalized types and generic adapter contract only.
- **No duplication with billing domain:** billing policies are explicitly excluded; only payment execution operations are included.
- **Supports multiple providers:** registry + router allow N adapters.
- **Clear contract boundaries:** explicit commerce-vs-billing responsibility section.
- **Adapter-pattern compatible:** stable port (`CommercePaymentGateway`) + pluggable implementations (`PaymentProviderAdapter`).

---

## Architectural Contract Cross-Reference: MS-ADAPTER-01 — Adapter Isolation (MS§4)

**Contract name:** MS-ADAPTER-01 (authoritative definition in `docs/specs/adapter_inventory.md`)
**Source authority:** Master Spec §4

**Cross-reference rule for payment adapters:** This interface contract is the enforcement boundary for MS-ADAPTER-01 in the payment domain. All payment provider implementations MUST implement `PaymentProviderAdapter` and MUST be registered in `integrations/payments/`. No service outside `integrations/` may contain payment provider logic, SDK imports, or provider-specific error handling. The `CommercePaymentGateway` port is the only surface exposed to core services — core services are provider-unaware by design.

See `docs/specs/adapter_inventory.md` MS-ADAPTER-01 for the full four-rule adapter isolation contract.
