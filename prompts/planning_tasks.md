# Task Breakdown Template

> **⚠️ Legacy Document**
>
> 이 프롬프트 파일은 초기 버전(v0.1.0)에서 사용되었습니다.
> 현재 시스템은 `src/agentic_orchestrator/debate/protocol.py`에 내장된 프롬프트를 사용합니다.
> 이 파일은 참조용으로만 유지됩니다.

---

Based on the PRD and Architecture, create a detailed task breakdown.

## Document Structure

# Task Breakdown: [Project Name]

## Overview

**Total Estimated Tasks**: [N]
**Phases**: [N]
**Critical Path Duration**: [estimate]

## Task Format

Each task follows this format:
```
- [ ] **Task ID**: Task Name (Effort: S/M/L)
  - Description: What needs to be done
  - Inputs: What's needed to start
  - Outputs: What will be delivered
  - Definition of Done: How to verify completion
```

Effort Guide:
- **S (Small)**: < 2 hours
- **M (Medium)**: 2-8 hours
- **L (Large)**: 1-3 days

---

## Phase 1: Project Setup

### 1.1 Repository Setup
- [ ] **Task 1.1.1**: Initialize project repository (Effort: S)
  - Description: Create project structure with proper configuration
  - Inputs: Architecture document
  - Outputs: Initialized repository with folder structure
  - Definition of Done: Repository created with README, .gitignore, config files

- [ ] **Task 1.1.2**: Configure development environment (Effort: S)
  - Description: Set up local development configuration
  - Inputs: Technology stack decisions
  - Outputs: Working dev environment
  - Definition of Done: All developers can run project locally

### 1.2 Dependency Setup
- [ ] **Task 1.2.1**: Install and configure dependencies (Effort: S)
  - Description: Install all required packages and libraries
  - Inputs: Technology stack list
  - Outputs: package.json/requirements.txt populated
  - Definition of Done: All dependencies install without errors

---

## Phase 2: Core Development

### 2.1 Backend Development
- [ ] **Task 2.1.1**: Create API structure (Effort: M)
  - Description: Set up API routes and controllers
  - Inputs: API design from architecture
  - Outputs: API skeleton with routes
  - Definition of Done: All routes defined, return placeholder responses

- [ ] **Task 2.1.2**: Implement core service logic (Effort: L)
  - Description: Build main business logic services
  - Inputs: PRD requirements
  - Outputs: Working service layer
  - Definition of Done: Core functionality works with unit tests

- [ ] **Task 2.1.3**: Database integration (Effort: M)
  - Description: Set up database models and migrations
  - Inputs: Data model from architecture
  - Outputs: Working database layer
  - Definition of Done: CRUD operations work correctly

### 2.2 Frontend Development
- [ ] **Task 2.2.1**: Create UI components (Effort: M)
  - Description: Build reusable UI components
  - Inputs: Feature requirements
  - Outputs: Component library
  - Definition of Done: Components render correctly

- [ ] **Task 2.2.2**: Implement pages/views (Effort: M)
  - Description: Build main application pages
  - Inputs: User flows from PRD
  - Outputs: Working pages
  - Definition of Done: All pages navigable and functional

- [ ] **Task 2.2.3**: API integration (Effort: M)
  - Description: Connect frontend to backend APIs
  - Inputs: API endpoints
  - Outputs: Data-connected UI
  - Definition of Done: Data flows correctly between frontend and backend

### 2.3 Blockchain Development (if applicable)
- [ ] **Task 2.3.1**: Write smart contracts (Effort: L)
  - Description: Develop required smart contracts
  - Inputs: Contract requirements from architecture
  - Outputs: Tested smart contracts
  - Definition of Done: Contracts pass all tests

- [ ] **Task 2.3.2**: Contract deployment scripts (Effort: S)
  - Description: Create deployment automation
  - Inputs: Contracts
  - Outputs: Deployment scripts
  - Definition of Done: Can deploy to testnet with one command

---

## Phase 3: Integration

### 3.1 System Integration
- [ ] **Task 3.1.1**: End-to-end integration (Effort: M)
  - Description: Connect all system components
  - Inputs: All developed components
  - Outputs: Integrated system
  - Definition of Done: Full user flow works end-to-end

- [ ] **Task 3.1.2**: External service integration (Effort: M)
  - Description: Integrate third-party services
  - Inputs: API keys and documentation
  - Outputs: Working integrations
  - Definition of Done: External services respond correctly

---

## Phase 4: Testing

### 4.1 Automated Testing
- [ ] **Task 4.1.1**: Write unit tests (Effort: M)
  - Description: Create unit tests for all services
  - Inputs: Service implementations
  - Outputs: Test suite
  - Definition of Done: > 70% code coverage

- [ ] **Task 4.1.2**: Write integration tests (Effort: M)
  - Description: Create integration test suite
  - Inputs: Integrated system
  - Outputs: Integration tests
  - Definition of Done: All critical paths tested

### 4.2 Manual Testing
- [ ] **Task 4.2.1**: User acceptance testing (Effort: M)
  - Description: Validate against acceptance criteria
  - Inputs: Acceptance criteria document
  - Outputs: Test results
  - Definition of Done: All acceptance criteria met

---

## Phase 5: Deployment

### 5.1 Deployment Preparation
- [ ] **Task 5.1.1**: Configure CI/CD (Effort: M)
  - Description: Set up deployment pipeline
  - Inputs: Infrastructure decisions
  - Outputs: Working pipeline
  - Definition of Done: Automated deployments work

- [ ] **Task 5.1.2**: Deploy to staging (Effort: S)
  - Description: Deploy to staging environment
  - Inputs: Passing tests
  - Outputs: Staging deployment
  - Definition of Done: App runs on staging

- [ ] **Task 5.1.3**: Deploy to production (Effort: S)
  - Description: Production deployment
  - Inputs: Staging validation
  - Outputs: Live application
  - Definition of Done: App accessible to users

---

## Dependency Graph

```
Phase 1 → Phase 2.1 ─┐
              ↓      ├→ Phase 3 → Phase 4 → Phase 5
         Phase 2.2 ─┤
              ↓      │
         Phase 2.3 ─┘
```

## Critical Path

1. Repository Setup
2. Backend Core Development
3. Frontend Development
4. Integration
5. Testing
6. Deployment

## Risk Tasks

| Task | Risk | Mitigation |
|------|------|------------|
| Smart Contract Development | Security vulnerabilities | Thorough testing, audit |
| External API Integration | API changes/downtime | Fallback strategies |

---

*Document Version: 1.0*
*Generated by: Agentic Orchestrator*
