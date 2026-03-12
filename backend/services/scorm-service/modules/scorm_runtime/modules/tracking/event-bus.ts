export interface DomainEventEnvelope<TPayload> {
  eventName: string;
  payload: TPayload;
}

export interface EventBus {
  publish<TPayload>(event: DomainEventEnvelope<TPayload>): Promise<void> | void;
}

export class InMemoryEventBus implements EventBus {
  async publish<TPayload>(_event: DomainEventEnvelope<TPayload>): Promise<void> {
    return;
  }
}
