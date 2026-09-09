/**
 * ReferMe Frontend Centralized Diagnostic Logger
 * Provides clean, styled browser console logging and dispatches client telemetry to the central backend.
 */

const API_LOG_ENDPOINT =
  (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1") + "/logs/client";

export interface ClientLogData {
  level?: "INFO" | "WARN" | "ERROR";
  message: string;
  url?: string;
  component?: string;
  stack?: string;
}

export const logger = {
  info(message: string, ...args: any[]) {
    console.log(
      `%c[ReferMe]%c ${message}`,
      "background: #3E0F8D; color: #E4DA72; padding: 2px 6px; border-radius: 4px; font-weight: bold;",
      "color: inherit;",
      ...args
    );
  },

  warn(message: string, ...args: any[]) {
    console.warn(
      `%c[ReferMe Warning]%c ${message}`,
      "background: #854D0E; color: #FEF08A; padding: 2px 6px; border-radius: 4px; font-weight: bold;",
      "color: inherit;",
      ...args
    );
    this.sendBeacon({ level: "WARN", message, stack: args.length ? JSON.stringify(args) : undefined });
  },

  error(message: string, err?: any, component?: string) {
    console.error(
      `%c[ReferMe Error]%c ${message}`,
      "background: #991B1B; color: #FEE2E2; padding: 2px 6px; border-radius: 4px; font-weight: bold;",
      "color: inherit;",
      err || ""
    );

    this.sendBeacon({
      level: "ERROR",
      message,
      component,
      stack: err instanceof Error ? err.stack : typeof err === "object" ? JSON.stringify(err) : String(err || ""),
    });
  },

  api(method: string, url: string, status: number, durationMs: number) {
    const isOk = status >= 200 && status < 400;
    const badgeColor = isOk ? "background: #065F46; color: #A7F3D0;" : "background: #991B1B; color: #FEE2E2;";
    const icon = isOk ? "🟢" : "🔴";

    console.log(
      `%c[API ${status}]%c ${icon} ${method} ${url} (${durationMs.toFixed(1)}ms)`,
      `${badgeColor} padding: 1px 5px; border-radius: 3px; font-weight: bold; font-family: monospace;`,
      "color: inherit;"
    );

    if (!isOk) {
      this.sendBeacon({
        level: "ERROR",
        message: `HTTP ${status} on ${method} ${url} (${durationMs.toFixed(1)}ms)`,
        url,
      });
    }
  },

  sendBeacon(data: ClientLogData) {
    if (typeof window === "undefined") return;

    try {
      const payload = {
        level: data.level || "ERROR",
        message: data.message,
        url: data.url || window.location.href,
        component: data.component,
        stack: data.stack,
        user_agent: navigator.userAgent,
      };

      const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });

      if (navigator.sendBeacon) {
        navigator.sendBeacon(API_LOG_ENDPOINT, blob);
      } else {
        fetch(API_LOG_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          keepalive: true,
        }).catch(() => {});
      }
    } catch {
      // Ignore network errors when dispatching logs
    }
  },
};
