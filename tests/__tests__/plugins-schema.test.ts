/**
 * KI-006 regression guard: verify plugin tool schemas are anyOf-free.
 *
 * JSON Schema `anyOf` unions are not reliably validated by all MCP client
 * hosts.  zod-to-json-schema with `strictUnions: true` produces clean,
 * non-anyOf schemas for simple Zod types (string, enum, number, boolean).
 *
 * Known zod-to-json-schema quirk: `string().optional().nullable()` produces
 * anyOf; the safe order is `string().nullable().optional()`.
 */
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

describe("KI-006: plugin tool schemas are anyOf-free", () => {
  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function hasAnyOf(schema: unknown): boolean {
    if (typeof schema !== "object" || schema === null) return false;
    const obj = schema as Record<string, unknown>;
    if ("anyOf" in obj) return true;
    for (const val of Object.values(obj)) {
      if (typeof val === "object" && val !== null && hasAnyOf(val)) return true;
    }
    return false;
  }

  // -------------------------------------------------------------------------
  // Schema fixtures — mirrors src/tools/plugins.ts
  // -------------------------------------------------------------------------

  const schemas = {
    list_installed_plugins: z.object({
      workspace_id: z.string().describe("Workspace ID"),
    }),
    install_plugin: z.object({
      workspace_id: z.string().describe("Workspace ID"),
      source: z.string().describe(
        "Source URL: 'local://<name>' for platform registry, 'github://<owner>/<repo>[#<ref>]' for GitHub, or any registered scheme."
      ),
    }),
    uninstall_plugin: z.object({
      workspace_id: z.string().describe("Workspace ID"),
      name: z.string().describe("Plugin name to remove"),
    }),
    list_plugin_sources: z.object({}),
    list_available_plugins: z.object({
      workspace_id: z.string(),
    }),
    check_plugin_compatibility: z.object({
      workspace_id: z.string(),
      runtime: z.string().describe("Target runtime"),
    }),
  } as const;

  // -------------------------------------------------------------------------
  // Tests
  // -------------------------------------------------------------------------

  for (const [tool, schema] of Object.entries(schemas)) {
    describe(tool, () => {
      const json = zodToJsonSchema(schema, { strictUnions: true });
      it("has no anyOf", () => {
        expect(hasAnyOf(json)).toBe(false);
      });
    });
  }

  // -------------------------------------------------------------------------
  // Control: document the optional().nullable() zod-to-json-schema quirk
  // -------------------------------------------------------------------------

  describe("control: optional().nullable() quirk", () => {
    it("string().optional().nullable() → produces anyOf (known zod-to-json-schema issue)", () => {
      const json = zodToJsonSchema(
        z.object({ parent_id: z.string().optional().nullable() }),
        { strictUnions: true }
      );
      expect(hasAnyOf(json)).toBe(true);
    });
    it("string().nullable().optional() → no anyOf (safe order)", () => {
      const json = zodToJsonSchema(
        z.object({ parent_id: z.string().nullable().optional() }),
        { strictUnions: true }
      );
      expect(hasAnyOf(json)).toBe(false);
    });
  });
});
