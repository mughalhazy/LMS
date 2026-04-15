import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileSessionStore } from "./persistence/fileSessionStore.js";
import { ScormRuntimeService } from "./services/scormRuntimeService.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const store = new FileSessionStore(path.join(__dirname, "../data/scorm-service-data.json"));
await store.init();
const service = new ScormRuntimeService(store);

function json(res, status, payload) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(payload));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 5 * 1024 * 1024) reject(new Error("Payload too large"));
    });
    req.on("end", () => {
      if (!body) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch {
        reject(new Error("Invalid JSON payload"));
      }
    });
    req.on("error", reject);
  });
}

function matchPath(pathname, pattern) {
  const pathParts = pathname.split("/").filter(Boolean);
  const patternParts = pattern.split("/").filter(Boolean);
  if (pathParts.length !== patternParts.length) return null;
  const params = {};
  for (let i = 0; i < patternParts.length; i += 1) {
    if (patternParts[i].startsWith(":")) params[patternParts[i].slice(1)] = pathParts[i];
    else if (patternParts[i] !== pathParts[i]) return null;
  }
  return params;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  try {
    if (req.method === "GET" && url.pathname === "/health") {
      return json(res, 200, { status: "ok", service: "scorm-service" });
    }

    let params = matchPath(url.pathname, "/tenants/:tenantId/scorm/launch");
    if (req.method === "POST" && params) {
      return json(res, 201, await service.launch({ tenantId: params.tenantId, ...(await parseBody(req)) }));
    }

    params = matchPath(url.pathname, "/tenants/:tenantId/scorm/sessions/:sessionId/runtime");
    if (req.method === "POST" && params) {
      return json(
        res,
        200,
        await service.runtimeCall(params.tenantId, params.sessionId, req.headers["x-scorm-session-token"], await parseBody(req))
      );
    }

    params = matchPath(url.pathname, "/tenants/:tenantId/scorm/sessions/:sessionId/commit");
    if (req.method === "POST" && params) {
      return json(res, 200, await service.commit(params.tenantId, params.sessionId, req.headers["x-scorm-session-token"]));
    }

    params = matchPath(url.pathname, "/tenants/:tenantId/scorm/sessions/:sessionId/finish");
    if (req.method === "POST" && params) {
      return json(res, 200, await service.finish(params.tenantId, params.sessionId, req.headers["x-scorm-session-token"]));
    }

    params = matchPath(url.pathname, "/tenants/:tenantId/scorm/sessions/:sessionId");
    if (req.method === "GET" && params) {
      return json(res, 200, await service.getSession(params.tenantId, params.sessionId));
    }

    params = matchPath(url.pathname, "/tenants/:tenantId/scorm/completions");
    if (req.method === "GET" && params) {
      return json(res, 200, await service.listCompletions(params.tenantId, url.searchParams.get("registrationId")));
    }

    return json(res, 404, { error: "Not found" });
  } catch (error) {
    return json(res, 400, { error: error.message });
  }
});

const port = process.env.PORT ?? 8090;
server.listen(port, () => {
  console.log(`scorm-service listening on :${port}`);
});
