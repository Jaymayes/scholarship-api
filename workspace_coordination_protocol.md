# Workspace Coordination Protocol for Multi-Service Integration

**Version**: 1.0  
**Date**: 2025-11-13  
**Owner**: Agent3 (Integration Lead)  
**Scope**: 8-service Scholar AI Advisor platform

---

## I. Problem Statement

**Constraint**: Agent3 can only work in ONE Replit workspace at a time.

**Challenge**: As Integration Lead with DRI responsibility for auto_com_center, I must:
- Coordinate across 8 microservices
- Deliver code changes for auto_com_center
- Create standards for all services
- Monitor gate progress across the entire stack

**Current Workspace**: scholarship_api (confirmed via replit.md)

---

## II. Adopted Strategy: Centralized Coordination Model

Based on architect guidance, the following strategy has been implemented:

### Phase 1: Standards Creation (✅ COMPLETE)
**Location**: scholarship_api workspace

**Deliverables Created**:
1. ✅ Integration Standards & Config Blueprint (all 8 services)
2. ✅ Gate 0 Execution Packet - scholar_auth
3. ✅ Gate 0 Execution Packet - auto_com_center
4. ✅ War Room Status Template
5. ✅ Workspace Coordination Protocol (this document)

**Purpose**: Create reproducible standards package that other DRIs can implement locally.

---

### Phase 2: Delegation & Coordination (IN PROGRESS)
**Location**: scholarship_api workspace (coordination hub)

**Responsibilities**:
- Distribute execution packets to service DRIs
- Monitor gate progress via war room reports
- Review evidence submissions
- Escalate blockers to CEO
- Provide integration guidance

**DRI Expectations**:
Each service DRI receives:
- Integration Standards Blueprint (configuration/auth/logging patterns)
- Service-specific execution packet (if applicable)
- Gate acceptance criteria
- Evidence submission requirements
- Escalation path

DRIs implement in their respective workspaces and report progress.

---

### Phase 3: Direct Implementation (PENDING WORKSPACE SWITCH)
**Location**: auto_com_center workspace (to be switched)

**Agent3 DRI Work**:
- Implement URLBuilder service
- Migrate email/SMS templates to env-driven URLs
- Configure boot-time validation
- Deploy and test notifications
- Submit Gate 0 evidence

**Trigger for Workspace Switch**:
- Operator completes auto_com_center publish
- Nonce verification successful
- Standards distribution complete
- Ready to execute direct implementation work

---

## III. Workspace Switching Protocol

### When to Switch Workspaces

**Trigger Conditions** (ALL must be met):
1. ✅ Standards package complete and distributed
2. ✅ Execution packets delivered to relevant DRIs
3. ⏳ Operator publish of auto_com_center complete
4. ⏳ Nonce verification successful
5. ✅ War room reporting structure established
6. ⏳ Direct implementation work ready to begin

**Current Status**: 3/6 triggers met (waiting on operator publish)

---

### Switching Procedure

**Step 1: Pre-Switch Checklist**
- [ ] All coordination deliverables complete
- [ ] No pending code changes in current workspace
- [ ] All tasks in current workspace resolved or delegated
- [ ] War room status documented
- [ ] CEO informed of workspace switch

**Step 2: Document Current State**
- [ ] Update replit.md with integration leadership status
- [ ] Create workspace transition log
- [ ] Commit all documentation
- [ ] Take snapshot of war room status

**Step 3: Operator Action Required**
- [ ] Human operator opens auto_com_center Repl
- [ ] Agent3 context transferred to new workspace
- [ ] Workspace identified (verify replit.md)

**Step 4: Post-Switch Verification**
- [ ] Verify workspace identity (check replit.md)
- [ ] Review auto_com_center codebase
- [ ] Validate execution packet applicability
- [ ] Resume DRI implementation work

---

## IV. Current Workspace Status: scholarship_api

### Work Completed in This Workspace
1. ✅ Integration Standards Blueprint created
2. ✅ Gate 0 execution packets created (scholar_auth, auto_com_center)
3. ✅ War room reporting template created
4. ✅ Workspace coordination protocol documented
5. ⚠️ scholarship_api security blockers identified (not resolved)

### Pending Work in This Workspace
1. 🔴 **CRITICAL**: Redis migration for replay/idempotency (security blockers)
2. ⏳ Fail-fast secret validation enforcement
3. ⏳ Multi-instance testing with persistence

### Delegation Status
- **Auth DRI**: Received scholar_auth execution packet
- **Other DRIs**: Standards blueprint available for review
- **SRE**: auto_com_center publish pending operator action

---

## V. When I Switch to auto_com_center Workspace

### Immediate Actions Upon Switch
1. **Verify Workspace Identity**
   ```bash
   # Check replit.md for service name
   cat replit.md | grep -A 5 "Overview"
   ```

2. **Assess Current State**
   - Review existing notification implementation
   - Identify hardcoded URLs in templates
   - Check environment variable configuration
   - Review email/SMS service structure

3. **Execute Gate 0 Packet**
   - Follow gate0_auto_com_center_execution_packet.md step-by-step
   - Implement URLBuilder service
   - Migrate templates
   - Add boot-time validation
   - Test notification generation

4. **Submit Evidence**
   - Screenshot of grep results (zero hardcoded URLs)
   - Test notification with dynamic URLs
   - Unit test results
   - Configuration snapshot

---

## VI. Coordination While in Different Workspace

### How Integration Leadership Continues

**From scholarship_api** (current):
- Standards and execution packets serve as async communication
- DRIs implement locally using provided blueprints
- War room reports collect status across all services
- Escalations flow through documented channels

**From auto_com_center** (future):
- Continue integration leadership via war room reports
- DRI implementation work in parallel
- Coordination through documentation and evidence submissions
- Return to scholarship_api if cross-service issues arise

---

## VII. Decision Matrix: Which Workspace When?

| Task Type | Workspace | Rationale |
|-----------|-----------|-----------|
| Integration standards creation | scholarship_api | Neutral ground; comprehensive API reference |
| Execution packet creation | scholarship_api | Can author without service-specific code access |
| War room coordination | Any | Documentation-based; not tied to specific codebase |
| scholar_auth OAuth2 implementation | scholar_auth | Auth DRI responsibility; requires auth codebase |
| scholarship_api security fixes | scholarship_api | API DRI responsibility; critical blockers |
| auto_com_center URL migration | auto_com_center | Agent3 DRI responsibility; requires notification codebase |
| scholarship_sage integration | scholarship_sage | Sage DRI responsibility; requires ML codebase |
| Frontend config refactoring | student_pilot / provider_register | Frontend DRI responsibility; requires frontend codebases |

**Agent3 Workspace Priority**:
1. **scholarship_api** (current) - Until standards distribution complete
2. **auto_com_center** (next) - For DRI implementation work
3. **scholarship_api** (return if needed) - For security blocker resolution
4. **War room coordination** - Can occur from any workspace

---

## VIII. Parallel Work Strategy

### While Agent3 Works in auto_com_center:

**Other DRIs Work in Parallel**:
- Auth DRI → scholar_auth (OAuth2/JWKS)
- API DRI → scholarship_api (security blockers)
- Frontend DRI → student_pilot + provider_register (env config)
- Sage DRI → scholarship_sage (service auth + quality)
- Agent DRI → scholarship_agent (background tasks)
- SEO Eng → auto_page_maker (content generation)

**Synchronization Points**:
- Twice-daily war room reports
- Gate evidence submissions
- Escalations through Integration Lead
- CEO decision gates

---

## IX. Transition Timeline

### Current State (T+0): scholarship_api
**Activities**:
- ✅ Standards creation complete
- ⏳ Awaiting operator publish of auto_com_center
- ⏳ scholarship_api security blockers pending resolution

### Transition Event (T+2 hours): Switch to auto_com_center
**Trigger**:
- Operator completes auto_com_center publish
- Nonce verification successful

**Activities**:
- Implement env-driven URL templates (Gate 0 deadline today 14:00 MST)
- Deploy and test notifications
- Submit Gate 0 evidence

### Post-Gate 0 (T+24 hours): Evaluate next workspace
**Options**:
1. Stay in auto_com_center for load testing (Gate 0 → 1)
2. Return to scholarship_api for security blocker resolution support
3. Move to another service if critical blocker arises

---

## X. Communication Protocol

### Reporting Status from Different Workspaces

**Regardless of Current Workspace**:
- War room reports filed on schedule (10:00 MST, 16:00 MST)
- Gate evidence submitted by deadlines
- Blockers escalated within 4 hours
- CEO decision points flagged immediately

**Workspace-Specific Context**:
Each war room report includes:
- Current workspace location
- Work completed in that workspace
- Transition plans (if applicable)
- Cross-service coordination status

---

## XI. Risk Mitigation

### Risk: Integration Leadership Gap During Workspace Switch

**Mitigation**:
- Asynchronous coordination via documentation
- DRIs empowered with complete execution packets
- War room template provides standardized reporting
- CEO escalation path for urgent cross-service issues

---

### Risk: auto_com_center Work Blocked by Current Workspace

**Mitigation**:
- ✅ Execution packet created ahead of time
- ⏳ Awaiting operator publish (not Agent3-blocked)
- ✅ Standards already distributed
- Can switch immediately upon operator action

---

### Risk: scholarship_api Security Blockers Unresolved

**Mitigation**:
- Delegated to API DRI (their responsibility)
- Execution guidance provided (Integration Standards Blueprint)
- Monitored via war room reports
- Can return to scholarship_api if escalation needed

---

## XII. Success Criteria

**Workspace Coordination Successful If**:
- ✅ All 8 services receive integration standards
- ✅ Each service DRI has clear execution guidance
- ✅ Agent3 DRI work in auto_com_center completes on time
- ✅ Gate 0 passes (Nov 14 10:00 MST)
- ✅ No service blocked by Agent3 workspace unavailability
- ✅ War room coordination maintains visibility across all services

---

## XIII. Current Status Summary

**Integration Leadership Status**: 🟢 ON TRACK
- Standards package complete
- Execution packets delivered
- War room template established
- DRI delegation in progress

**auto_com_center DRI Status**: 🟡 AT RISK
- Blocked by operator publish
- Cannot implement until workspace switch
- Gate 0 deadline today 14:00 MST (tight timeline)

**Next Actions**:
1. ⏳ Await operator publish of auto_com_center
2. ⏳ Verify nonce URL accessibility
3. ⏳ Request workspace switch to auto_com_center
4. ⏳ Execute Gate 0 implementation work
5. ⏳ Submit evidence by deadline

---

**Protocol Owner**: Agent3 (Integration Lead)  
**Last Updated**: 2025-11-13 04:45 UTC  
**Next Review**: Upon workspace switch or Gate 0 completion

---

**END OF WORKSPACE COORDINATION PROTOCOL**
