from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.models import (
    ConsumerLaunchCompleteRequest,
    ConsumerLaunchCompleteResponse,
    ConsumerLaunchInitiateRequest,
    ConsumerLaunchInitiateResponse,
    ConsumerToolRegistrationRequest,
    ConsumerToolRegistrationResponse,
    GradePassbackRequest,
    GradePassbackResponse,
    IdentityMappingRequest,
    IdentityMappingResponse,
    LaunchValidationRequest,
    LaunchValidationResponse,
    MembershipSyncRequest,
    MembershipSyncResponse,
    OIDCLoginInitiationRequest,
    OIDCLoginInitiationResponse,
    RegistrationStatus,
    RoleNormalizationRequest,
    RoleNormalizationResponse,
    ServiceAccessTokenRequest,
    ServiceAccessTokenResponse,
    SessionProvisioningRequest,
    SessionProvisioningResponse,
    ToolRegistrationRequest,
    ToolRegistrationResponse,
    TrustStatus,
    ValidationActivationRequest,
    ValidationActivationResponse,
    session_expiry,
)


class LTIService:
    def __init__(self) -> None:
        self.provider_tools: dict[str, dict] = {}
        self.consumer_tools: dict[str, dict] = {}
        self.state_nonce_store: dict[str, dict[str, str]] = {}
        self.identities: dict[str, str] = {}

    def register_provider_tool(self, req: ToolRegistrationRequest) -> ToolRegistrationResponse:
        tool_id = f"tool_{uuid4().hex[:12]}"
        client_id = f"client_{uuid4().hex[:12]}"
        deployment_id = f"dep_{uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc)

        record = req.model_dump()
        record.update(
            {
                "tool_id": tool_id,
                "client_id": client_id,
                "deployment_id": deployment_id,
                "created_at": created_at,
                "registration_status": RegistrationStatus.PENDING_VALIDATION,
            }
        )
        self.provider_tools[tool_id] = record

        return ToolRegistrationResponse(
            tool_id=tool_id,
            client_id=client_id,
            deployment_id=deployment_id,
            platform_issuer=f"https://lms.example.com/tenants/{req.tenant_id}",
            authorization_endpoint="https://lms.example.com/api/integrations/lti/authorize",
            keyset_url="https://lms.example.com/api/integrations/lti/.well-known/jwks.json",
            registration_status=RegistrationStatus.PENDING_VALIDATION,
            created_at=created_at,
        )

    def activate_provider_registration(
        self, req: ValidationActivationRequest
    ) -> ValidationActivationResponse:
        tool = self.provider_tools[req.tool_id]
        errors: list[str] = []
        warnings: list[str] = []

        if not req.jwks_fetch_result:
            errors.append("jwks_fetch_failed")
        if not req.redirect_uri_verification_result:
            errors.append("redirect_uri_verification_failed")
        if not req.scope_policy_check:
            errors.append("scope_policy_denied")
        if not req.admin_approval:
            warnings.append("awaiting_admin_approval")

        active = len(errors) == 0 and req.admin_approval
        tool["registration_status"] = (
            RegistrationStatus.ACTIVE if active else RegistrationStatus.PENDING_VALIDATION
        )

        return ValidationActivationResponse(
            validation_report={"errors": errors, "warnings": warnings},
            activation_decision=active,
            activated_scopes=tool["requested_scopes"] if active else [],
            trust_status=TrustStatus.TRUSTED if active else TrustStatus.UNTRUSTED,
            audit_event_id=f"audit_{uuid4().hex[:12]}",
        )

    def initiate_oidc_login(
        self, req: OIDCLoginInitiationRequest
    ) -> OIDCLoginInitiationResponse:
        state = f"state_{uuid4().hex}"
        nonce = req.nonce or f"nonce_{uuid4().hex}"
        correlation_id = f"corr_{uuid4().hex}"
        self.state_nonce_store[state] = {
            "nonce": nonce,
            "deployment_id": req.deployment_id,
            "client_id": req.client_id,
            "iss": req.iss,
        }
        redirect_url = (
            "https://platform.example.com/oidc/auth"
            f"?client_id={req.client_id}&login_hint={req.login_hint}&"
            f"target_link_uri={req.target_link_uri}&state={state}&nonce={nonce}"
        )
        return OIDCLoginInitiationResponse(
            authorization_redirect_url=redirect_url,
            state=state,
            nonce_binding_record={"state": state, "nonce": nonce},
            correlation_id=correlation_id,
        )

    def validate_launch(self, req: LaunchValidationRequest) -> LaunchValidationResponse:
        binding = self.state_nonce_store.get(req.state)
        if not binding:
            raise ValueError("unknown_state")
        if binding["nonce"] != req.nonce:
            raise ValueError("nonce_mismatch")
        if binding["deployment_id"] != req.deployment_id:
            raise ValueError("deployment_mismatch")

        claims = self._decode_jwt_without_verification(req.id_token)
        valid = (
            claims.get("iss") == req.expected_issuer
            and str(claims.get("aud")) == req.expected_audience
            and claims.get("nonce") == req.nonce
            and claims.get("https://purl.imsglobal.org/spec/lti/claim/deployment_id")
            == req.deployment_id
        )

        return LaunchValidationResponse(
            launch_validation_status="valid" if valid else "invalid",
            launch_context_id=f"launch_{uuid4().hex[:14]}",
            resource_link_id=(
                claims.get("https://purl.imsglobal.org/spec/lti/claim/resource_link", {})
                .get("id")
            ),
            context_id=(
                claims.get("https://purl.imsglobal.org/spec/lti/claim/context", {}).get("id")
            ),
            launch_claims_snapshot=claims,
            policy_decisions={"decision": "allow" if valid else "deny", "reason": "validation"},
        )

    def provision_session(self, req: SessionProvisioningRequest) -> SessionProvisioningResponse:
        is_instructor = any("instructor" in role.lower() for role in req.roles)
        view = "instructor" if is_instructor else "learner"
        permissions = ["content:read", "progress:write"]
        if is_instructor:
            permissions.extend(["gradebook:write", "membership:read"])

        return SessionProvisioningResponse(
            lms_session_token=f"lti_session_{uuid4().hex}",
            effective_permissions=permissions,
            learner_or_instructor_view=view,
            landing_route=f"/lti/launch/{req.launch_context_id}",
            session_expiry=session_expiry(),
        )

    def map_identity(self, req: IdentityMappingRequest) -> IdentityMappingResponse:
        key_candidates = [
            ("sub", f"{req.tenant_id}:{req.issuer}:{req.platform_user_sub}"),
            (
                "sourcedid",
                f"{req.tenant_id}:{req.issuer}:{req.lis_person_sourcedid}"
                if req.lis_person_sourcedid
                else None,
            ),
            ("email", f"{req.tenant_id}:{req.email}" if req.email else None),
        ]

        strategy = "sub"
        key = key_candidates[0][1]
        for candidate_strategy, candidate_key in key_candidates:
            if candidate_key and candidate_key in self.identities:
                strategy = candidate_strategy
                key = candidate_key
                break

        created = key not in self.identities
        if created:
            self.identities[key] = f"user_{uuid4().hex[:12]}"

        return IdentityMappingResponse(
            lms_user_id=self.identities[key],
            identity_link_id=f"idlink_{uuid4().hex[:12]}",
            match_strategy_used=strategy,
            account_state="created" if created else "linked",
            remediation_action=None,
        )

    def normalize_roles(self, req: RoleNormalizationRequest) -> RoleNormalizationResponse:
        mapped_roles: list[str] = []
        for role in req.lti_roles:
            role_key = role.split("#")[-1].split("/")[-1].lower()
            mapped_roles.append(req.tenant_role_mapping_rules.get(role_key, role_key))

        if not mapped_roles:
            mapped_roles = [req.default_role_fallback]

        scopes = ["lti.launch"]
        if any(r in {"instructor", "teacher", "admin"} for r in mapped_roles):
            scopes.extend(["ags.write", "nrps.read"])

        actions = ["enroll"]
        if "instructor" in mapped_roles:
            actions.append("upgrade")

        return RoleNormalizationResponse(
            normalized_lms_roles=sorted(set(mapped_roles)),
            enrollment_actions=actions,
            authorization_scope_set=scopes,
            role_mapping_audit_id=f"rolemap_{uuid4().hex[:12]}",
        )

    def issue_service_access_token(
        self, req: ServiceAccessTokenRequest
    ) -> ServiceAccessTokenResponse:
        if req.grant_type != "client_credentials":
            raise ValueError("unsupported_grant_type")
        token_seed = f"{req.tool_id}:{req.deployment_id}:{req.requested_scope}:{uuid4().hex}"
        access_token = base64.urlsafe_b64encode(token_seed.encode()).decode().rstrip("=")

        return ServiceAccessTokenResponse(
            access_token=access_token,
            granted_scopes=req.requested_scope.split(),
            service_endpoints={
                "lineitems": "https://lms.example.com/api/lti/ags/lineitems",
                "scores": "https://lms.example.com/api/lti/ags/scores",
                "memberships": "https://lms.example.com/api/lti/nrps/memberships",
            },
        )

    def grade_passback(self, req: GradePassbackRequest) -> GradePassbackResponse:
        digest = hashlib.sha256(
            f"{req.lineitem_id}:{req.user_id}:{req.timestamp.isoformat()}".encode()
        ).hexdigest()[:16]

        return GradePassbackResponse(
            score_write_status="accepted",
            platform_response_code=202,
            idempotency_key=digest,
            retry_instruction=None,
        )

    def membership_sync(self, req: MembershipSyncRequest) -> MembershipSyncResponse:
        members = [
            {"user_id": "user_1001", "name": "Alex Trainer", "role": "Instructor"},
            {"user_id": "user_2020", "name": "Taylor Learner", "role": "Learner"},
        ]
        if req.role_filter:
            members = [m for m in members if m["role"].lower() == req.role_filter.lower()]

        return MembershipSyncResponse(
            membership_page=members,
            next_cursor=None,
            sync_checkpoint=datetime.now(timezone.utc),
            import_summary={"imported": len(members), "skipped": 0},
        )

    def register_consumer_tool(
        self, req: ConsumerToolRegistrationRequest
    ) -> ConsumerToolRegistrationResponse:
        tool_id = f"consumer_tool_{uuid4().hex[:12]}"
        self.consumer_tools[tool_id] = req.model_dump()
        return ConsumerToolRegistrationResponse(
            tool_id=tool_id,
            status="active",
            redirect_uri_allowlist=[req.target_link_uri],
            security_controls={
                "nonce_state_ttl_seconds": 600,
                "redirect_uri_allowlist_enabled": True,
                "key_rotation_days": 30,
                "tenant_id": req.tenant_id,
            },
        )

    def initiate_consumer_launch(
        self, req: ConsumerLaunchInitiateRequest
    ) -> ConsumerLaunchInitiateResponse:
        tool = self.consumer_tools.get(req.tool_id)
        if not tool:
            raise ValueError("unknown_tool")
        state = f"state_{uuid4().hex}"
        nonce = f"nonce_{uuid4().hex}"
        hint = json.dumps(
            {
                "course_id": req.course_id,
                "resource_link_id": req.resource_link_id,
                "user_id": req.user_id,
                "role": req.role,
                "locale": req.locale,
            }
        )
        self.state_nonce_store[state] = {"nonce": nonce, "tool_id": req.tool_id}
        auth_url = (
            f"{tool['oidc_auth_initiation_url']}?login_hint={req.user_id}&"
            f"lti_message_hint={base64.urlsafe_b64encode(hint.encode()).decode()}&"
            f"state={state}&nonce={nonce}"
        )
        return ConsumerLaunchInitiateResponse(
            auth_request_url=auth_url,
            state=state,
            nonce=nonce,
            launch_hint=hint,
        )

    def complete_consumer_launch(
        self, req: ConsumerLaunchCompleteRequest
    ) -> ConsumerLaunchCompleteResponse:
        binding = self.state_nonce_store.get(req.state)
        if not binding or binding.get("nonce") != req.nonce:
            raise ValueError("invalid_state_or_nonce")
        if binding.get("tool_id") != req.tool_id:
            raise ValueError("tool_state_mismatch")
        claims = self._decode_jwt_without_verification(req.id_token)
        return ConsumerLaunchCompleteResponse(
            launch_status="launched",
            user_binding={
                "sub": str(claims.get("sub", "unknown")),
                "email": str(claims.get("email", "")),
            },
            resource_context={
                "deployment_id": str(
                    claims.get(
                        "https://purl.imsglobal.org/spec/lti/claim/deployment_id", ""
                    )
                ),
                "message_type": str(
                    claims.get("https://purl.imsglobal.org/spec/lti/claim/message_type", "")
                ),
            },
        )

    @staticmethod
    def _decode_jwt_without_verification(token: str) -> dict:
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}
            payload = parts[1]
            payload += "=" * (-len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload.encode())
            return json.loads(decoded)
        except Exception:
            return {}
