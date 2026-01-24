# Planning Review Prompt

> **⚠️ Legacy Document**
>
> 이 프롬프트 파일은 초기 버전(v0.1.0)에서 사용되었습니다.
> 현재 시스템은 `src/agentic_orchestrator/debate/protocol.py`에 내장된 프롬프트를 사용합니다.
> 이 파일은 참조용으로만 유지됩니다.

---

Review the planning documents and provide structured feedback.

## Review Scope

You are reviewing:
1. **PRD** - Product Requirements Document
2. **Architecture** - Technical Architecture Document
3. **Tasks** - Task Breakdown
4. **Acceptance Criteria** - Quality Gates

## Evaluation Criteria

### 1. Completeness (0-10)
- Are all sections present?
- Are there gaps in requirements?
- Is the scope well-defined?

### 2. Clarity (0-10)
- Is the writing clear and unambiguous?
- Are technical terms defined?
- Can a developer implement from these docs?

### 3. Feasibility (0-10)
- Is the scope realistic?
- Are the technology choices appropriate?
- Are risks properly identified?

### 4. Technical Soundness (0-10)
- Is the architecture solid?
- Are there obvious technical issues?
- Are security considerations addressed?

## Output Format

# Planning Review

## Overall Assessment
[2-3 sentences summarizing the planning quality]

## Score Breakdown

| Criterion | Score | Notes |
|-----------|-------|-------|
| Completeness | X/10 | ... |
| Clarity | X/10 | ... |
| Feasibility | X/10 | ... |
| Technical Soundness | X/10 | ... |

**OVERALL SCORE: X/10**

## Critical Issues (Must Fix)

Issues that MUST be addressed before development:

1. **[Issue Title]**
   - Location: [Document/Section]
   - Problem: [Description]
   - Recommendation: [How to fix]
   - Severity: CRITICAL

2. ...

## Major Issues (Should Fix)

Issues that should be addressed but aren't blockers:

1. **[Issue Title]**
   - Location: [Document/Section]
   - Problem: [Description]
   - Recommendation: [How to fix]
   - Severity: MAJOR

## Minor Issues (Nice to Fix)

Small improvements:

1. **[Issue Title]**
   - Recommendation: [How to fix]
   - Severity: MINOR

## Risks Identified

| Risk | Probability | Impact | Suggested Mitigation |
|------|-------------|--------|---------------------|
| ... | Low/Med/High | Low/Med/High | ... |

## Test Scenarios to Consider

1. **Scenario**: [Description]
   - Expected behavior: [What should happen]
   - Edge cases: [What could go wrong]

2. ...

## Security Considerations

1. [Security item to verify]
2. [Security item to verify]

## Verdict

**APPROVED** / **NEEDS_REVISION**

Justification: [Why this verdict]

## Summary JSON

```json
{
  "score": X,
  "verdict": "APPROVED/NEEDS_REVISION",
  "critical_issues_count": N,
  "major_issues_count": N,
  "minor_issues_count": N,
  "risks_count": N
}
```

---

## Review Guidelines

When reviewing, be:
- **Thorough**: Check all documents systematically
- **Objective**: Base feedback on concrete issues
- **Constructive**: Provide actionable recommendations
- **Practical**: Focus on issues that matter for implementation

Remember: The goal is to catch problems BEFORE development, not to be overly critical.
