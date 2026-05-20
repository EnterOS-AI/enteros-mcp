import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { apiCall, platformGet, toMcpResult } from "../api.js";
import { validate } from "../utils/validation.js";

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const DecideApprovalSchema = z.object({
  workspace_id: z.string().describe("Workspace ID"),
  approval_id: z.string().describe("Approval ID"),
  decision: z.enum(["approved", "denied"]).describe("Decision"),
});
export type DecideApprovalParams = z.infer<typeof DecideApprovalSchema>;

const CreateApprovalSchema = z.object({
  workspace_id: z.string().describe("Workspace ID"),
  action: z.string().describe("What needs approval"),
  reason: z.string().optional().describe("Why it's needed"),
});
export type CreateApprovalParams = z.infer<typeof CreateApprovalSchema>;

const GetWorkspaceApprovalsSchema = z.object({
  workspace_id: z.string().describe("Workspace ID"),
});
export type GetWorkspaceApprovalsParams = z.infer<typeof GetWorkspaceApprovalsSchema>;

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

export async function handleListPendingApprovals(): Promise<ReturnType<typeof toMcpResult>> {
  const data = await platformGet("/approvals/pending");
  return toMcpResult(data);
}

export async function handleDecideApproval(args: unknown): Promise<ReturnType<typeof toMcpResult>> {
  const params = validate(args, DecideApprovalSchema);
  const data = await apiCall(
    "POST",
    `/workspaces/${params.workspace_id}/approvals/${params.approval_id}/decide`,
    { decision: params.decision, decided_by: "mcp-client" }
  );
  return toMcpResult(data);
}

export async function handleCreateApproval(args: unknown): Promise<ReturnType<typeof toMcpResult>> {
  const params = validate(args, CreateApprovalSchema);
  const data = await apiCall(
    "POST",
    `/workspaces/${params.workspace_id}/approvals`,
    { action: params.action, reason: params.reason }
  );
  return toMcpResult(data);
}

export async function handleGetWorkspaceApprovals(args: unknown): Promise<ReturnType<typeof toMcpResult>> {
  const params = validate(args, GetWorkspaceApprovalsSchema);
  const data = await platformGet(`/workspaces/${params.workspace_id}/approvals`);
  return toMcpResult(data);
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

export function registerApprovalTools(srv: McpServer) {
  srv.tool(
    "list_pending_approvals",
    "List all pending approval requests across workspaces",
    {},
    handleListPendingApprovals
  );

  srv.tool(
    "decide_approval",
    "Approve or deny a pending approval request",
    {
      workspace_id: z.string().describe("Workspace ID"),
      approval_id: z.string().describe("Approval ID"),
      decision: z.enum(["approved", "denied"]).describe("Decision"),
    },
    handleDecideApproval
  );

  srv.tool(
    "create_approval",
    "Create an approval request for a workspace",
    {
      workspace_id: z.string().describe("Workspace ID"),
      action: z.string().describe("What needs approval"),
      reason: z.string().optional().describe("Why it's needed"),
    },
    handleCreateApproval
  );

  srv.tool(
    "get_workspace_approvals",
    "List approval requests for a specific workspace",
    { workspace_id: z.string().describe("Workspace ID") },
    handleGetWorkspaceApprovals
  );
}
