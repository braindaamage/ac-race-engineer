# Quickstart: Usage UI

**Branch**: `025-usage-ui` | **Date**: 2026-03-09

## Prerequisites

- Node.js 20 LTS
- npm
- Backend server running on port 57832 (for manual testing only; unit tests mock the API)

## Development

```bash
cd frontend
npm install        # Install dependencies (if needed)
npm run dev        # Start Vite dev server with HMR
```

## Testing

```bash
cd frontend
npm run test                           # Run all tests
npx vitest run tests/lib/format.test.ts              # Format utility tests
npx vitest run tests/hooks/useRecommendationUsage.test.ts  # Hook tests
npx vitest run tests/views/engineer/UsageSummaryBar.test.tsx   # Summary bar tests
npx vitest run tests/views/engineer/UsageDetailModal.test.tsx  # Detail modal tests
```

## Type Checking

```bash
cd frontend
npx tsc --noEmit   # TypeScript strict mode check — must pass with zero errors
```

## Files Changed

### New Files
| File | Purpose |
|------|---------|
| `src/lib/format.ts` | `formatTokenCount()` utility function |
| `src/views/engineer/UsageSummaryBar.tsx` | Inline summary bar component |
| `src/views/engineer/UsageDetailModal.tsx` | Detail modal component |
| `tests/lib/format.test.ts` | Format utility unit tests |
| `tests/hooks/useRecommendationUsage.test.ts` | Hook unit tests |
| `tests/views/engineer/UsageSummaryBar.test.tsx` | Summary bar component tests |
| `tests/views/engineer/UsageDetailModal.test.tsx` | Detail modal component tests |

### Modified Files
| File | Change |
|------|--------|
| `src/lib/types.ts` | Add ToolCallInfo, AgentUsageDetail, UsageTotals, RecommendationUsageResponse |
| `src/hooks/useRecommendations.ts` | Add `useRecommendationUsage` hook export |
| `src/views/engineer/RecommendationCard.tsx` | Render UsageSummaryBar when usage data available |
| `src/views/engineer/index.tsx` | Fetch usage data and pass to RecommendationCard |
| `src/views/engineer/EngineerView.css` | Add `.ace-usage-*` styles |
