// Cross-platform bash launcher: on Windows the `bash` on PATH is usually WSL,
// so locate Git Bash next to git.exe instead. Usage: node scripts/bash.mjs <script> [args...]
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

function findBash() {
  if (process.platform !== "win32") return "bash";
  const candidates = [];
  try {
    // e.g. C:/Program Files/Git/mingw64/libexec/git-core -> C:/Program Files/Git/bin/bash.exe
    const execPath = execFileSync("git", ["--exec-path"], { encoding: "utf8" }).trim();
    candidates.push(path.resolve(execPath, "..", "..", "..", "bin", "bash.exe"));
  } catch {
    // git not on PATH
  }
  candidates.push("C:\\Program Files\\Git\\bin\\bash.exe", "C:\\Program Files (x86)\\Git\\bin\\bash.exe");
  const found = candidates.find((c) => existsSync(c));
  if (!found) {
    console.error("Git Bash não encontrado. Instale o Git for Windows: https://git-scm.com/download/win");
    process.exit(1);
  }
  return found;
}

const result = spawnSync(findBash(), process.argv.slice(2), { stdio: "inherit" });
process.exit(result.status ?? 1);
