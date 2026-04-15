\========================================================  
LMS PLATFORM — MASTER PRODUCT & BUILD SPEC (GROUND TRUTH)  
\========================================================

VERSION: FINAL  
PURPOSE: Single source of truth for product, architecture, and build  
SCOPE: Capability-driven, country-agnostic, segment-agnostic platform

\========================================================  
0\. SYSTEM DEFINITION  
\========================================================

\--------------------------------------------------------

0\.1 HERITAGE STATEMENT

The platform's runtime engine is built on an Enterprise LMS V2 Rails foundation.

Existing references to:

\- "Enterprise LMS V2"  
\- Rails core entities (User, Course, Lesson, Enrollment, Progress, Certificate)  
\- "service extension" language

...in existing repo docs refer to this heritage implementation layer. Those docs remain valid as the runtime engine description.

The Master Spec defines the CAPABILITY-PLATFORM IDENTITY that governs all new architectural decisions.

Rule: Heritage layer provides the learning runtime. Capability platform governs all behavior above it.

Reference: `docs/architecture/ARCH_01_core_system_architecture.md` (implementation), this spec (architecture identity).

\--------------------------------------------------------

The system is defined as:

→ A CAPABILITY-DRIVEN EDUCATION PLATFORM

It manages:

→ LEARNING  
→ OPERATIONS  
→ COMMUNICATION  
→ REVENUE

\--------------------------------------------------------

SYSTEM \=

Global Core  
\+ Capability Registry  
\+ Config System  
\+ Entitlement System  
\+ Domain Capabilities  
\+ Adapter Layer

\--------------------------------------------------------

CRITICAL:

\- No country awareness  
\- No segment awareness  
\- No product-tier awareness

System operates ONLY on:  
→ capabilities  
→ configuration  
→ entitlements

\========================================================  
1\. NON-NEGOTIABLE ARCHITECTURE RULES  
\========================================================

1.1 CORE IMMUTABILITY

Core MUST:

\- remain country-agnostic  
\- remain segment-agnostic  
\- never contain provider-specific logic

\--------------------------------------------------------

1.2 NO SEGMENT CONCEPT IN SYSTEM

The system must NOT:

\- detect segment  
\- branch logic by segment  
\- define segment-based services

\--------------------------------------------------------

1.3 NO COUNTRY CONCEPT IN SYSTEM

The system must NOT:

\- contain Pakistan logic  
\- contain geography-based conditions

\--------------------------------------------------------

1.4 NO FEATURE-BASED DESIGN

Everything must be defined as:

→ CAPABILITIES

\--------------------------------------------------------

1\.5 PERMITTED USE OF SEGMENT AND COUNTRY

The following are PERMITTED as tenant profile metadata inputs:

\- segment\_type (e.g. academy, school, corporate, university)  
\- country\_code (ISO 3166-1 alpha-2)  
\- plan\_type  
\- enabled\_addons

These fields are stored on the Tenant entity and used as declarative inputs to:

→ the entitlement resolver (which capabilities are enabled)  
→ the config resolution chain (which config values apply)

This IS consistent with capability-driven design. The entitlement service outputs enabled/disabled per capability key — it does not branch service logic.

The following are PROHIBITED:

\- Hardcoded segment conditionals inside domain service logic  
\- Country-specific branching inside service code  
\- Geography-based data schema forking  
\- Segment-specific API routing

Rule: segment\_type and country\_code are INPUTS to the entitlement and config systems. They must never become BRANCHES inside service implementations.

\--------------------------------------------------------

\========================================================  
2\. CAPABILITY MODEL (FOUNDATION)  
\========================================================

2.1 DEFINITION

A capability is:

→ an independently enableable, configurable, and monetizable unit

\--------------------------------------------------------

2.2 CAPABILITY MUST DEFINE:

\- unique key  
\- domain  
\- dependencies  
\- usage metrics  
\- billing type  
\- required adapters

\--------------------------------------------------------

2.3 RULE

If something:

\- cannot be enabled/disabled  
\- cannot be measured  
\- cannot be reused

→ it is NOT a valid capability

\--------------------------------------------------------

\========================================================  
3\. CONFIG-DRIVEN BEHAVIOR  
\========================================================

3.1 ALL BEHAVIOR IS CONFIG RESOLVED

Conceptual hierarchy:

global → overrides → tenant

Technical implementation hierarchy (per B2P01 + capability\_resolution.md):

global → country\_profile → segment\_profile → plan → tenant → runtime\_override

NOTE: country\_profile and segment\_profile are declarative tenant metadata discriminators. They are NOT country or segment branching logic inside services. They are keys used to resolve the correct config layer for a given tenant context. All business rules tied to these discriminators are stored in the external config/policy store — not inside service implementations.

Reference: `docs/architecture/B2P01_config_service_design.md`, `docs/anchors/capability_resolution.md`

\--------------------------------------------------------

3.2 RULES

\- No runtime branching inside services  
\- No hardcoded workflows  
\- Deterministic behavior

\--------------------------------------------------------

\========================================================  
4\. ADAPTER LAYER (EXTERNAL ISOLATION)  
\========================================================

ALL EXTERNAL DEPENDENCIES MUST USE ADAPTERS:

\- payments  
\- communication  
\- storage  
\- third-party integrations

\--------------------------------------------------------

RULES:

\- adapters live in /integrations  
\- core services never depend on provider logic  
\- adapters are swappable

\--------------------------------------------------------

\========================================================  
5\. CAPABILITY DOMAINS (FULL SYSTEM SURFACE)  
\========================================================

\----------------------------------------  
5.1 LEARNING CAPABILITIES  
\----------------------------------------

\- course delivery  
\- lesson management  
\- assessments  
\- grading  
\- certification

\----------------------------------------  
5.2 STUDENT LIFECYCLE CAPABILITIES  
\----------------------------------------

\- enrollment tracking  
\- progress tracking  
\- completion tracking

\----------------------------------------  
5.3 FINANCIAL CAPABILITIES  
\----------------------------------------

\- student ledger  
\- payment tracking  
\- revenue allocation

\----------------------------------------  
5.4 COMMERCE CAPABILITIES  
\----------------------------------------

\- product catalog  
\- checkout  
\- billing  
\- subscription  
\- pricing logic

\----------------------------------------  
5.5 MONETIZATION CAPABILITIES  
\----------------------------------------

\- capability-based billing  
\- add-on enablement  
\- usage-based billing

\----------------------------------------  
5.6 OPERATIONS CAPABILITIES  
\----------------------------------------

\- attendance  
\- scheduling  
\- batch/group management  
\- resource allocation

\----------------------------------------  
5.7 COMMUNICATION CAPABILITIES  
\----------------------------------------

\- messaging  
\- notifications  
\- workflow triggers  
\- scheduling

\----------------------------------------  
5.8 WORKFLOW CAPABILITIES  
\----------------------------------------

\- event-driven automation  
\- rule engine  
\- multi-step workflows

\----------------------------------------  
5.9 INTERACTION LAYER CAPABILITIES  
\----------------------------------------

\- conversational interaction (e.g. WhatsApp-like)  
\- action-based replies  
\- stateful interaction flows

STATUS: PLANNED — not yet implemented.  
WhatsApp adapter exists at `integrations/communication/whatsapp_adapter.py`.  
Full interaction layer service and stateful flow engine are not yet built.  
Spec: `docs/specs/interaction_layer_spec.md`  
See Drift Flag DF-03 in `doc_catalogue.md`.

\----------------------------------------  
5.10 ADMIN OPERATIONS CAPABILITIES  
\----------------------------------------

\- operational dashboards  
\- action prioritization  
\- system alerts

\----------------------------------------  
5.11 CONTENT PROTECTION CAPABILITIES  
\----------------------------------------

\- secure media delivery  
\- watermarking  
\- session control  
\- anti-piracy enforcement

\----------------------------------------  
5.12 OFFLINE CAPABILITIES  
\----------------------------------------

\- offline access  
\- local storage  
\- sync engine  
\- conflict resolution

\----------------------------------------  
5.13 PERFORMANCE CAPABILITIES  
\----------------------------------------

\- high concurrency handling  
\- session isolation  
\- load resilience

\----------------------------------------  
5.14 ECONOMIC CAPABILITIES (USER LEVEL)  
\----------------------------------------

\- revenue participation  
\- earnings tracking  
\- payout calculation

\----------------------------------------  
5.15 ECONOMIC CAPABILITIES (SYSTEM LEVEL)  
\----------------------------------------

\- revenue analytics  
\- cost tracking  
\- profitability insights

\----------------------------------------  
5.16 DATA & ANALYTICS CAPABILITIES  
\----------------------------------------

\- performance analytics  
\- benchmarking  
\- ranking systems  
\- optimization insights

\----------------------------------------  
5.17 ONBOARDING CAPABILITIES  
\----------------------------------------

\- instant setup  
\- automated configuration  
\- guided flows

\----------------------------------------  
5.18 ENTERPRISE CAPABILITIES  
\----------------------------------------

\- RBAC  
\- audit logs  
\- compliance  
\- integrations

\----------------------------------------  
5.19 USE-CASE CAPABILITY DOMAIN EXTENSIONS  
\----------------------------------------

The platform includes pre-designed capability domain compositions for common market verticals:

\- Academy operations (batch, attendance, fee tracking, branch management)  
\- School engagement (attendance, grading, parent portal, teacher-parent comms)  
\- Workforce training (onboarding, compliance, role readiness, manager oversight)  
\- University operations (faculty workflows, advanced assessment, research tracking)

RULE: These are NOT segment-forked products.

They are capability domain extensions — groups of capabilities designed for a specific use-case profile and accessed via the entitlement system using segment\_type and plan\_type as selection inputs. The core platform remains unchanged.

Reference: `docs/architecture/domain_capability_extension_model.md`

\--------------------------------------------------------

CAPABILITY DOMAIN STATUS MAP

For full implementation status of all 18 capability domains (built / partial / planned), see:

→ `docs/specs/B0P09_full_capability_domain_map.md`

\--------------------------------------------------------

\========================================================  
6\. SYSTEM OF RECORD (CRITICAL)  
\========================================================

The system must maintain:

→ SINGLE SOURCE OF TRUTH

Includes:

\- student lifecycle  
\- financial ledger  
\- unified profile

RULE:

No duplication of core state across services

\--------------------------------------------------------

\========================================================  
7\. MARKET ENFORCEMENTS (FROM RESEARCH)  
\========================================================

The system must support:

\- mobile-first usage  
\- low-tech operators  
\- asynchronous interaction  
\- unreliable connectivity  
\- instant payment activation  
\- content protection  
\- operational automation

\--------------------------------------------------------

IMPORTANT:

These are NOT implemented as country logic.

They are implemented as:

→ capabilities

\--------------------------------------------------------

\========================================================  
8\. USER EXPERIENCE PRINCIPLES  
\========================================================

\- minimal setup  
\- mobile-first  
\- automation-first  
\- outcome-driven  
\- interaction-first (not dashboard-first)

\--------------------------------------------------------

\========================================================  
9\. MONETIZATION MODEL  
\========================================================

The system must support:

\- free entry  
\- capability-based upgrades  
\- usage-based billing

\--------------------------------------------------------

RULE:

Revenue scales with capability usage

\--------------------------------------------------------

\========================================================  
10\. STRATEGIC INSIGHTS (ENFORCED)  
\========================================================

1\. System must manage operations, not just learning  
2\. System must manage revenue, not just users  
3\. Communication must support action, not just alerts  
4\. Offline capability must be first-class  
5\. Content protection must be enforced  
6\. System must reduce manual work  
7\. Simplicity must be preserved  
8\. AI must assist, not replace

\--------------------------------------------------------

\========================================================  
11\. WHAT SYSTEM MUST NEVER BECOME  
\========================================================

❌ Feature-based LMS    
❌ Country-specific fork    
❌ Segment-specific product    
❌ Dashboard-heavy tool  

\--------------------------------------------------------

\========================================================  
12\. FINAL SYSTEM IDENTITY  
\========================================================

The system is:

→ A GLOBAL CAPABILITY PLATFORM

That can be:

\- configured for any country (via adapters/config)  
\- used by any segment (via capability combinations)

WITHOUT:

\- changing the core  
\- creating separate products

\--------------------------------------------------------

\========================================================  
13\. FINAL SUCCESS CRITERIA  
\========================================================

System is complete when:

\- all functionality is capability-based  
\- no segment logic exists  
\- no country logic exists  
\- all behavior is config-driven  
\- all integrations use adapters  
\- system-of-record is authoritative  
\- offline, security, and performance are enforced  
\- monetization is capability-based  
\- system scales globally without modification

\--------------------------------------------------------

\========================================================  
FINAL STATEMENT  
\========================================================

"Build a capability-driven global platform  
that enables learning, operations, communication,  
and revenue — without embedding country or segment logic  
into the system.”