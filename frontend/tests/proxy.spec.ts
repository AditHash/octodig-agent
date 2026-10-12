import { expect, test } from "@playwright/test";

test("production proxy sends security headers and rejects oversized bodies", async ({ request }) => {
  test.skip(!process.env.OCTODIG_TEST_NGINX_BIN, "Requires the production proxy fixture");
  const response = await request.get("/");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(response.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response.headers()["referrer-policy"]).toBe("no-referrer");
  const oversized = await request.post("/api/v1/auth/login", { data: "x".repeat(66000) });
  expect(oversized.status()).toBe(413);
  expect((await request.get("/health/live")).status()).toBe(200);
});
