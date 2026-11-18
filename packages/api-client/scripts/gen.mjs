// openapi.yaml -> src/schema.d.ts (ELLE DÜZENLEMEYİN). Sözleşme yolu: knowledge/ veya docs/ (geçiş dönemi).
import { existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const spec = [resolve(root, "knowledge/contracts/openapi.yaml"), resolve(root, "docs/api/openapi.yaml")].find(existsSync);
if (!spec) throw new Error("openapi.yaml bulunamadı");
execFileSync("npx", ["openapi-typescript", spec, "-o", resolve(root, "packages/api-client/src/schema.d.ts")], { stdio: "inherit" });
