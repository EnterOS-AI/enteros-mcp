/**
 * Shared input validation utilities for MCP tool handlers.
 *
 * MCP tool arguments arrive as raw JSON (unknown). Before passing them to any
 * business logic, every handler validates them against its Zod schema.
 * On parse failure the handler returns a structured INVALID_ARGUMENTS error
 * (MCP error code -32602) rather than letting type/structure errors surface
 * as INTERNAL_ERROR later in the call stack.
 *
 * This also serves as living documentation: each schema documents exactly what
 * a tool accepts, what types are required/optional, and what constraints apply.
 */

import { ZodError, ZodSchema, z } from "zod";

/** MCP JSON-RPC error codes used by this server. */
export const ErrorCode = {
  InvalidParams: -32602,
  InternalError: -32603,
} as const;

// ---------------------------------------------------------------------------
// INVALID_ARGUMENTS error
// ---------------------------------------------------------------------------

/**
 * Structured MCP error for INVALID_ARGUMENTS.
 *
 * MCP error response shape:
 *   { content: [{ type: "text", text: "<formatted message>" }],
 *     isError: true }
 *
 * The MCP SDK translates a handler that throws `new InvalidArgumentsError(...)`
 * into an INVALID_ARGUMENTS response (JSON-RPC error code -32602).
 * If a handler returns normally the SDK returns isError: false.
 */
export class InvalidArgumentsError extends Error {
  /** Zod validation issues, one per line, human-readable. */
  readonly issues: string[];

  constructor(issues: string[]) {
    super(formatIssues(issues));
    this.name = "InvalidArgumentsError";
    this.issues = issues;
    // Make the error look like an MCP SDK error for the framework.
    Object.setPrototypeOf(this, InvalidArgumentsError.prototype);
  }
}

/** Format a list of Zod issues into a single readable string. */
function formatIssues(issues: string[]): string {
  if (issues.length === 1) return `Invalid argument: ${issues[0]}`;
  return `Invalid arguments (${issues.length} errors):\n${issues.map((e) => `  - ${e}`).join("\n")}`;
}

/**
 * Format a Zod ZodError into a flat list of human-readable issue strings.
 * Each entry is "[field]: [message]" or just "[message]" for root issues.
 */
export function formatZodIssues(err: ZodError): string[] {
  return err.issues.map((issue) => {
    const path = issue.path.length > 0 ? issue.path.join(".") + ": " : "";
    return path + issue.message;
  });
}

// ---------------------------------------------------------------------------
// Core validate helper
// ---------------------------------------------------------------------------

/**
 * Validate `args` against `schema` and return the parsed value on success.
 *
 * Usage — add ONE line at the top of every handler:
 *   const params = validate(args, MyToolSchema);
 *
 * Throws `InvalidArgumentsError` (caught by the MCP SDK → INVALID_ARGUMENTS
 * response) if validation fails. The error message lists every failure.
 *
 * @param args  - Raw JSON object received from the MCP caller.
 * @param schema - Zod schema (sync or async) that describes the expected shape.
 * @returns The parsed and typed arguments.
 * @throws InvalidArgumentsError if args fail validation.
 */
export function validate<T>(args: unknown, schema: ZodSchema<T>): T {
  if (args == null) args = {};

  const result = schema.safeParse(args);

  if (!result.success) {
    throw new InvalidArgumentsError(formatZodIssues(result.error));
  }

  return result.data;
}

// ---------------------------------------------------------------------------
// Optional-param guard
// ---------------------------------------------------------------------------

/**
 * Throw INVALID_ARGUMENTS if `value` is null or undefined.
 * Use for required params that Zod's `.required()` alone cannot catch when
 * the caller sends `null` instead of omitting the key.
 *
 * Example:
 *   const { workspace_id } = validate(args, SomeSchema);
 *   guardRequired(workspace_id, "workspace_id");
 */
export function guardRequired<T>(value: T, fieldName: string): T {
  if (value === null || value === undefined) {
    throw new InvalidArgumentsError([`${fieldName}: required`]);
  }
  return value;
}
